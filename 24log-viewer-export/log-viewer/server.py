"""
Claude CLI 日志查看器 - Python 本地服务
与 Node 版 server.js 行为一致：从 ~/.claude/projects 读取 transcript，提供相同 API 与配置（explain-config、项目显示名等）。
"""
from __future__ import annotations

import errno
import hashlib
import json
import mimetypes
import os
import re
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, unquote, urlparse
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
HOME_DIR = Path(os.getenv("USERPROFILE") or os.getenv("HOME") or ".").resolve()
CLAUDE_PROJECTS_DIR = Path(
    os.getenv("CLAUDE_PROJECTS_DIR")
    or str(HOME_DIR / ".claude" / "projects")
).resolve()
PORT = int(os.getenv("CLAUDE_LOG_VIEWER_PORT", "3847"))
VIEWER_DIR = (BASE_DIR / "public").resolve()
CONFIG_PATH = BASE_DIR / "explain-config.json"
DISPLAY_NAMES_PATH = BASE_DIR / "projects-display-names.json"
LOG_SCHEMA_VERSION = 1
TIMELINE_CACHE_TTL_SEC = 2.0

_TIMELINE_CACHE: dict[str, Any] = {
    "signature": "",
    "builtAt": 0.0,
    "data": {
        "projects": {},
        "projectsIndex": [],
        "sessions": {},
        "sessionsByProject": {},
    },
}


def load_explain_config() -> dict:
    env_api_url = (os.getenv("EXPLAIN_API_URL") or "").strip()
    env_api_key = (os.getenv("EXPLAIN_API_KEY") or "").strip()
    env_model = (os.getenv("EXPLAIN_MODEL") or "").strip()
    file_config = {}
    if CONFIG_PATH.exists():
        try:
            file_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            file_config = {}
    return {
        "apiUrl": env_api_url or str(file_config.get("apiUrl") or ""),
        "apiKey": env_api_key or str(file_config.get("apiKey") or ""),
        "model": env_model or str(file_config.get("model") or "qwen-turbo"),
    }


def ensure_chat_completions_url(api_url: str) -> str:
    api_url = (api_url or "").strip()
    if not api_url:
        return ""
    if api_url.endswith("/chat/completions"):
        return api_url
    return api_url.rstrip("/") + "/chat/completions"


def _sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()


def _json_dumps_stable(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    except Exception:
        return str(value)


def _safe_json_loads(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return None


def _iso_or_empty(value: Any) -> str:
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return ""
        return s
    return ""


def _normalize_tool_output(value: Any) -> Any:
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return ""
        as_json = _safe_json_loads(s)
        return as_json if as_json is not None else s
    return value


def _extract_text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if isinstance(item, str):
            parts.append(item)
            continue
        if not isinstance(item, dict):
            continue
        t = item.get("type")
        if t in {"text", "thinking"}:
            text = item.get("text") or item.get("thinking")
            if text:
                parts.append(str(text))
    return "\n".join(p for p in parts if p).strip()


def _build_event(
    *,
    session_id: str,
    event_type: str,
    timestamp: str,
    trace_id: str = "",
    tool_name: str = "",
    tool_input: Any = None,
    tool_output: Any = None,
    error: str = "",
    content: str = "",
    cwd: str = "",
    raw: Any = None,
) -> dict[str, Any]:
    normalized_input = {} if tool_input is None else tool_input
    normalized_output = _normalize_tool_output(tool_output)
    data = {
        "schemaVersion": LOG_SCHEMA_VERSION,
        "sessionId": session_id or "",
        "traceId": trace_id or "",
        "source": "transcript",
        "sourceConfidence": 100,
        "eventType": event_type or "system",
        "toolName": tool_name or "",
        "toolInput": normalized_input,
        "toolOutput": normalized_output if normalized_output is not None else {},
        "error": error or "",
        "content": content or "",
        "timestamp": _iso_or_empty(timestamp),
        "cwd": cwd or "",
        "raw": raw if raw is not None else {},
    }
    digest_payload = "|".join(
        [
            data["sessionId"],
            data["eventType"],
            data["traceId"],
            data["timestamp"][:19],
            data["toolName"],
            _sha1_text(_json_dumps_stable(data["toolInput"]))[:12],
            _sha1_text(_json_dumps_stable(data["toolOutput"]))[:12],
            _sha1_text(data["content"][:320])[:12],
        ]
    )
    data["eventId"] = _sha1_text(digest_payload)[:20]
    return data


def _event_dedupe_key(event: dict[str, Any]) -> str:
    trace_id = str(event.get("traceId") or "").strip()
    if trace_id:
        return f"{event.get('eventType')}|{trace_id}"
    return "|".join(
        [
            str(event.get("eventType") or ""),
            str(event.get("toolName") or ""),
            str(event.get("timestamp") or "")[:19],
            _sha1_text(_json_dumps_stable(event.get("toolInput") or {}))[:8],
            _sha1_text(_json_dumps_stable(event.get("toolOutput") or {}))[:8],
            _sha1_text(str(event.get("content") or "")[:220])[:8],
        ]
    )


def _parse_transcript_line(obj: dict[str, Any], fallback_session: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    session_id = str(obj.get("sessionId") or fallback_session or "")
    timestamp = str(obj.get("timestamp") or "")
    cwd = str(obj.get("cwd") or "")
    line_type = str(obj.get("type") or "").strip().lower()

    # Cursor-style transcript: {"role":"user","message":{"content":[...]}}
    if not line_type and isinstance(obj.get("role"), str):
        role = str(obj.get("role")).lower()
        message = obj.get("message") or {}
        content = ""
        if isinstance(message, dict):
            content = _extract_text_from_content(message.get("content"))
        event_type = "user_input" if role == "user" else "assistant_output"
        if content:
            result.append(
                _build_event(
                    session_id=session_id,
                    event_type=event_type,
                    timestamp=timestamp,
                    content=content,
                    cwd=cwd,
                    raw=obj,
                )
            )
        return result

    if line_type == "user":
        message = obj.get("message") or {}
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, list):
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") == "tool_result":
                        trace_id = str(item.get("tool_use_id") or "")
                        output = item.get("content")
                        error = ""
                        if item.get("is_error") is True:
                            error = "tool_result_error"
                        event_type = "tool_failure" if error else "post_tool"
                        result.append(
                            _build_event(
                                session_id=session_id,
                                event_type=event_type,
                                timestamp=timestamp,
                                trace_id=trace_id,
                                tool_output=output,
                                error=error,
                                cwd=cwd,
                                raw=obj,
                            )
                        )
                plain = _extract_text_from_content(content)
                if plain:
                    result.append(
                        _build_event(
                            session_id=session_id,
                            event_type="user_input",
                            timestamp=timestamp,
                            content=plain,
                            cwd=cwd,
                            raw=obj,
                        )
                    )
            elif isinstance(content, str):
                result.append(
                    _build_event(
                        session_id=session_id,
                        event_type="user_input",
                        timestamp=timestamp,
                        content=content,
                        cwd=cwd,
                        raw=obj,
                    )
                )
        return result

    if line_type == "assistant":
        message = obj.get("message") or {}
        msg_content = message.get("content") if isinstance(message, dict) else None
        if isinstance(msg_content, list):
            for item in msg_content:
                if not isinstance(item, dict):
                    continue
                ctype = str(item.get("type") or "")
                if ctype == "tool_use":
                    result.append(
                        _build_event(
                            session_id=session_id,
                            event_type="pre_tool",
                            timestamp=timestamp,
                            trace_id=str(item.get("id") or ""),
                            tool_name=str(item.get("name") or ""),
                            tool_input=item.get("input") or {},
                            cwd=cwd,
                            raw=obj,
                        )
                    )
                elif ctype == "text":
                    text = str(item.get("text") or "")
                    if text.strip():
                        result.append(
                            _build_event(
                                session_id=session_id,
                                event_type="assistant_output",
                                timestamp=timestamp,
                                content=text,
                                cwd=cwd,
                                raw=obj,
                            )
                        )
        elif isinstance(msg_content, str) and msg_content.strip():
            result.append(
                _build_event(
                    session_id=session_id,
                    event_type="assistant_output",
                    timestamp=timestamp,
                    content=msg_content,
                    cwd=cwd,
                    raw=obj,
                )
            )
        return result

    if line_type == "file-history-snapshot":
        result.append(
            _build_event(
                session_id=session_id,
                event_type="system",
                timestamp=timestamp or str((obj.get("snapshot") or {}).get("timestamp") or ""),
                content="file-history-snapshot",
                cwd=cwd,
                raw=obj,
            )
        )
    return result


def _project_key_for_file(file_path: Path) -> str:
    try:
        rel = file_path.resolve().relative_to(CLAUDE_PROJECTS_DIR)
        if rel.parts:
            return rel.parts[0]
    except Exception:
        pass
    return "unknown-project"


def _parse_transcript_file(file_path: Path) -> tuple[list[dict[str, Any]], str]:
    events: list[dict[str, Any]] = []
    session_id = file_path.stem
    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            obj = _safe_json_loads(line)
            if not isinstance(obj, dict):
                continue
            session_id = str(obj.get("sessionId") or session_id)
            events.extend(_parse_transcript_line(obj, session_id))
    return events, session_id


def _load_project_display_names() -> dict[str, str]:
    """加载项目显示名映射（与 Node projects-display-names.json 同格式）。"""
    if not DISPLAY_NAMES_PATH.exists():
        return {}
    try:
        data = json.loads(DISPLAY_NAMES_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _discover_project_transcripts() -> tuple[list[Path], str]:
    files: list[Path] = []
    if CLAUDE_PROJECTS_DIR.exists():
        for p in CLAUDE_PROJECTS_DIR.rglob("*.jsonl"):
            if "subagents" in [x.lower() for x in p.parts]:
                continue
            files.append(p.resolve())
    records: list[tuple[str, int, int]] = []
    for fp in files:
        try:
            st = fp.stat()
            records.append((str(fp), int(st.st_mtime_ns), int(st.st_size)))
        except Exception:
            continue
    signature = _sha1_text(_json_dumps_stable(sorted(records)))
    return sorted(files), signature


def _build_timeline_data() -> dict[str, Any]:
    transcript_files, signature = _discover_project_transcripts()
    cache = _TIMELINE_CACHE
    now = time.time()
    if (
        cache.get("data")
        and cache.get("signature") == signature
        and (now - float(cache.get("builtAt") or 0)) < TIMELINE_CACHE_TTL_SEC
    ):
        return cache["data"]

    display_names = _load_project_display_names()

    def _project_display_name(pid: str) -> str:
        v = display_names.get(pid)
        if v is not None and isinstance(v, str) and v.strip():
            return v.strip()
        return pid

    events_by_session: dict[str, list[dict[str, Any]]] = {}
    session_meta: dict[str, dict[str, Any]] = {}
    projects: dict[str, dict[str, Any]] = {}

    for file_path in transcript_files:
        try:
            parsed, sid = _parse_transcript_file(file_path)
        except Exception:
            continue
        project_id = _project_key_for_file(file_path)
        st = None
        try:
            st = file_path.stat()
        except Exception:
            st = None
        if project_id not in projects:
            projects[project_id] = {
                "id": project_id,
                "name": _project_display_name(project_id),
                "sessionCount": 0,
                "eventCount": 0,
                "mtime": "",
            }
        if sid:
            meta = session_meta.get(
                sid,
                {
                    "id": sid,
                    "filename": file_path.name,
                    "mtime": "",
                    "size": 0,
                    "cwd": None,
                    "projectId": project_id,
                    "projectName": _project_display_name(project_id),
                },
            )
            session_meta[sid] = meta
            meta["projectId"] = project_id
            meta["projectName"] = _project_display_name(project_id)
            meta["filename"] = file_path.name
            if st:
                meta["size"] = st.st_size
                meta["mtime"] = (
                    datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
                    .replace(microsecond=0)
                    .isoformat()
                    .replace("+00:00", "Z")
                )
        for event in parsed:
            sid2 = event.get("sessionId") or sid or file_path.stem
            event["sessionId"] = sid2
            events_by_session.setdefault(sid2, []).append(event)

    sessions: dict[str, dict[str, Any]] = {}
    sessions_by_project: dict[str, list[dict[str, Any]]] = {}
    for sid, raw_events in events_by_session.items():
        dedupe_map: dict[str, dict[str, Any]] = {}
        duplicate_count = 0
        for event in raw_events:
            key = _event_dedupe_key(event)
            if key in dedupe_map:
                duplicate_count += 1
            else:
                dedupe_map[key] = event
        merged_events = list(dedupe_map.values())
        merged_events.sort(key=lambda e: str(e.get("timestamp") or ""), reverse=True)

        pre_ids = {str(e.get("traceId")) for e in merged_events if e.get("eventType") == "pre_tool" and str(e.get("traceId") or "").strip()}
        post_ids = {str(e.get("traceId")) for e in merged_events if e.get("eventType") in {"post_tool", "tool_failure"} and str(e.get("traceId") or "").strip()}
        missing_post = sorted(list(pre_ids - post_ids))
        health = {
            "totalEvents": len(merged_events),
            "preToolCount": sum(1 for e in merged_events if e.get("eventType") == "pre_tool"),
            "postToolCount": sum(1 for e in merged_events if e.get("eventType") == "post_tool"),
            "failureCount": sum(1 for e in merged_events if e.get("eventType") == "tool_failure"),
            "userInputCount": sum(1 for e in merged_events if e.get("eventType") == "user_input"),
            "assistantOutputCount": sum(1 for e in merged_events if e.get("eventType") == "assistant_output"),
            "duplicateCollapsed": duplicate_count,
            "missingPostCount": len(missing_post),
            "missingPostTraceIds": missing_post[:30],
            "sourceCountsBeforeMerge": {"transcript": len(raw_events)},
        }
        tools = sorted(
            {
                str(e.get("toolName"))
                for e in merged_events
                if isinstance(e.get("toolName"), str) and e.get("toolName")
            }
        )

        meta = session_meta.get(
            sid,
            {"id": sid, "filename": f"{sid}.txt", "mtime": "", "size": 0, "cwd": None},
        )
        last_activity = meta.get("mtime") or ""
        if merged_events and merged_events[0].get("timestamp"):
            last_activity = str(merged_events[0].get("timestamp"))
        meta["mtime"] = last_activity

        session_data = {
            "meta": meta,
            "events": merged_events,
            "health": health,
            "tools": tools,
            "projectId": meta.get("projectId") or "unknown-project",
        }
        sessions[sid] = session_data
        project_id = meta.get("projectId") or "unknown-project"
        sess_item = {
            "id": sid,
            "projectId": project_id,
            "projectName": meta.get("projectName") or project_id,
            "mtime": last_activity,
            "cwd": meta.get("cwd"),
            "size": meta.get("size") or 0,
            "eventCount": len(merged_events),
            "health": {
                "missingPostCount": health["missingPostCount"],
                "failureCount": health["failureCount"],
                "duplicateCollapsed": health["duplicateCollapsed"],
            },
        }
        sessions_by_project.setdefault(project_id, []).append(sess_item)
        p = projects.setdefault(project_id, {"id": project_id, "name": _project_display_name(project_id), "sessionCount": 0, "eventCount": 0, "mtime": ""})
        p["sessionCount"] = p.get("sessionCount", 0) + 1
        p["eventCount"] = p.get("eventCount", 0) + len(merged_events)
        if str(last_activity) > str(p.get("mtime") or ""):
            p["mtime"] = last_activity

    for project_id in list(sessions_by_project.keys()):
        sessions_by_project[project_id].sort(key=lambda s: str(s.get("mtime") or ""), reverse=True)

    projects_index = sorted(projects.values(), key=lambda p: str(p.get("mtime") or ""), reverse=True)
    data = {
        "projects": projects,
        "projectsIndex": projects_index,
        "sessions": sessions,
        "sessionsByProject": sessions_by_project,
    }
    _TIMELINE_CACHE["data"] = data
    _TIMELINE_CACHE["signature"] = signature
    _TIMELINE_CACHE["builtAt"] = now
    return data


def parse_model_text(out: dict) -> str:
    def join_content(content):
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    parts.append(str(item.get("text") or ""))
            return "".join(parts).strip()
        if content is None:
            return ""
        return str(content).strip()

    text = ""
    output = out.get("output")
    if isinstance(output, dict):
        choices = output.get("choices")
        if isinstance(choices, list) and choices:
            m = choices[0].get("message") if isinstance(choices[0], dict) else choices[0]
            if isinstance(m, dict):
                text = join_content(m.get("content")) or str(m.get("text") or "").strip()
            else:
                text = str(m or "").strip()
        if not text:
            text = str(output.get("text") or "").strip()
    elif isinstance(output, str):
        text = output.strip()

    if not text:
        choices = out.get("choices")
        if isinstance(choices, list) and choices:
            m = choices[0].get("message") if isinstance(choices[0], dict) else choices[0]
            if isinstance(m, dict):
                text = join_content(m.get("content")) or str(m.get("text") or "").strip()
            else:
                text = str(m or "").strip()
    if not text:
        text = str(out.get("content") or out.get("text") or "").strip()
    if not text and isinstance(out.get("result"), dict):
        result = out["result"]
        output_value = result.get("output")
        if isinstance(output_value, dict):
            text = str(output_value.get("text") or output_value.get("content") or "").strip()
        elif output_value is not None:
            text = str(output_value).strip()
        if not text:
            text = str(result.get("text") or "").strip()
    return text

def create_server_with_fallback(preferred_port: int, max_tries: int = 20):
    """
    Try preferred port first, then fallback to nearby ports.
    This avoids startup failure when a local port is occupied/reserved.
    """
    ports_to_try = [preferred_port]
    ports_to_try.extend(preferred_port + i for i in range(1, max_tries + 1))
    last_error = None

    for candidate_port in ports_to_try:
        try:
            server = ThreadingHTTPServer(("127.0.0.1", candidate_port), Handler)
            return server, candidate_port
        except OSError as exc:
            last_error = exc
            win_err = getattr(exc, "winerror", None)
            if exc.errno in {errno.EADDRINUSE, errno.EACCES} or win_err in {10013, 10048}:
                continue
            raise

    raise RuntimeError(
        f"无法绑定 127.0.0.1:{preferred_port} 及其后续 {max_tries} 个端口。"
        "请设置环境变量 CLAUDE_LOG_VIEWER_PORT 为可用端口后重试。"
    ) from last_error


class Handler(BaseHTTPRequestHandler):
    server_version = "ClaudeLogViewerPython/1.0"

    def _send_json(self, status: int, payload: dict | list):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, status: int, text: str, content_type: str = "text/plain; charset=utf-8"):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except Exception as exc:
            raise ValueError("Invalid JSON") from exc

    def _handle_projects(self):
        try:
            data = _build_timeline_data()
            self._send_json(200, {"schemaVersion": LOG_SCHEMA_VERSION, "projects": data.get("projectsIndex", [])})
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})

    def _handle_project_sessions(self, path_name: str):
        match = re.fullmatch(r"/api/projects/([^/]+)/sessions", path_name)
        if not match:
            self._send_json(404, {"error": "Not found"})
            return
        pid = unquote(match.group(1))
        data = _build_timeline_data()
        sessions = data.get("sessionsByProject", {}).get(pid, [])
        self._send_json(200, {"schemaVersion": LOG_SCHEMA_VERSION, "projectId": pid, "sessions": sessions})

    def _handle_timeline_events(self, path_name: str, query: dict[str, list[str]]):
        match = re.fullmatch(r"/api/timelines/([^/]+)/events", path_name)
        if not match:
            self._send_json(404, {"error": "Not found"})
            return
        sid = unquote(match.group(1))
        data = _build_timeline_data()
        session = data.get("sessions", {}).get(sid)
        if not session:
            self._send_json(404, {"error": "Session not found"})
            return
        events = list(session.get("events", []))
        event_type = (query.get("eventType") or [""])[0].strip()
        tool_name = (query.get("toolName") or [""])[0].strip()
        source = (query.get("source") or [""])[0].strip()
        keyword = (query.get("q") or [""])[0].strip().lower()
        if event_type:
            events = [e for e in events if str(e.get("eventType") or "") == event_type]
        if tool_name:
            events = [e for e in events if str(e.get("toolName") or "") == tool_name]
        if source:
            events = [e for e in events if str(e.get("source") or "") == source]
        if keyword:
            events = [
                e for e in events
                if keyword in _json_dumps_stable(e.get("toolInput") or {}).lower()
                or keyword in _json_dumps_stable(e.get("toolOutput") or {}).lower()
                or keyword in str(e.get("content") or "").lower()
                or keyword in str(e.get("toolName") or "").lower()
            ]
        try:
            offset = max(0, int((query.get("offset") or ["0"])[0]))
        except ValueError:
            offset = 0
        try:
            limit = max(1, min(2000, int((query.get("limit") or ["300"])[0])))
        except ValueError:
            limit = 300
        paged = events[offset: offset + limit]
        self._send_json(
            200,
            {
                "schemaVersion": LOG_SCHEMA_VERSION,
                "sessionId": sid,
                "offset": offset,
                "limit": limit,
                "total": len(events),
                "tools": session.get("tools", []),
                "health": session.get("health", {}),
                "projectId": session.get("projectId"),
                "events": paged,
            },
        )

    def _handle_timeline_health(self, path_name: str):
        match = re.fullmatch(r"/api/timelines/([^/]+)/health", path_name)
        if not match:
            self._send_json(404, {"error": "Not found"})
            return
        sid = unquote(match.group(1))
        data = _build_timeline_data()
        session = data.get("sessions", {}).get(sid)
        if not session:
            self._send_json(404, {"error": "Session not found"})
            return
        self._send_json(200, {"schemaVersion": LOG_SCHEMA_VERSION, "sessionId": sid, "health": session.get("health", {})})

    def _handle_explain_config_get(self):
        try:
            if CONFIG_PATH.exists():
                obj = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            else:
                obj = {}
            self._send_json(
                200,
                {
                    "apiUrl": obj.get("apiUrl") or "",
                    "apiKey": obj.get("apiKey") or "",
                    "model": obj.get("model") or "qwen-turbo",
                },
            )
        except Exception:
            self._send_json(200, {"apiUrl": "", "apiKey": "", "model": "qwen-turbo"})

    def _handle_explain_config_post(self):
        try:
            obj = self._read_json_body()
            api_url = ensure_chat_completions_url(str(obj.get("apiUrl") or obj.get("baseUrl") or ""))
            config = {
                "apiUrl": api_url,
                "apiKey": str(obj.get("apiKey") or "").strip(),
                "model": str(obj.get("model") or "qwen-turbo").strip(),
            }
            CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
            self._send_json(200, {"ok": True})
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
        except Exception as exc:
            self._send_json(400, {"error": str(exc)})

    def _handle_explain(self):
        config = load_explain_config()
        if not config.get("apiUrl") or not config.get("apiKey"):
            self._send_json(
                200,
                {
                    "error": "未配置解说 API。请在 log-viewer/explain-config.json 中填写 apiUrl、apiKey，或设置环境变量 EXPLAIN_API_URL、EXPLAIN_API_KEY。"
                },
            )
            return
        try:
            payload = self._read_json_body()
        except ValueError:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        tool_name = payload.get("toolName") or payload.get("tool_name") or "?"
        tool_input = payload.get("toolInput")
        if tool_input is None:
            tool_input = payload.get("tool_input") or {}
        tool_response = payload.get("toolResponse")
        if tool_response is None:
            tool_response = payload.get("tool_response")
        if tool_response is None:
            tool_response = payload.get("tool_output") or {}
        event = payload.get("event") or ""

        def summarize(obj, limit):
            if isinstance(obj, str):
                return obj[:limit]
            try:
                return json.dumps(obj, ensure_ascii=False)[:limit]
            except Exception:
                return str(obj)[:limit]

        prompt = (
            "你是一个 Claude Code 日志分析专家。请详细分析下面这条工具调用日志，用 2-4 句话中文说明：\n"
            "1. 这个工具调用的目的是什么？\n"
            "2. 输入参数是什么含义？\n"
            "3. 执行结果如何？\n"
            "4. 如果是文件操作，说明文件路径和操作内容；如果是命令执行，说明命令用途。\n\n"
            f"事件: {event}\n"
            f"工具: {tool_name}\n"
            f"输入参数: {summarize(tool_input, 600)}\n"
            f"执行结果: {summarize(tool_response, 1000)}\n\n"
            "请给出详细的中文解说："
        )

        request_body = json.dumps(
            {
                "model": config.get("model") or "qwen-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        api_url = ensure_chat_completions_url(config.get("apiUrl") or "")
        req = Request(
            url=api_url,
            method="POST",
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + str(config["apiKey"]),
            },
        )
        try:
            with urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                status_code = resp.getcode()
        except HTTPError as exc:
            status_code = exc.code
            body = exc.read().decode("utf-8", errors="ignore")
        except URLError as exc:
            self._send_json(200, {"error": f"请求解说 API 失败: {exc.reason}"})
            return
        except Exception as exc:
            self._send_json(200, {"error": f"请求解说 API 失败: {exc}"})
            return

        try:
            out = json.loads(body) if body else {}
        except Exception:
            self._send_json(200, {"error": "解说 API 返回非 JSON: " + (body[:200] if body else "空响应")})
            return

        if status_code >= 400:
            msg = (
                out.get("message")
                or (out.get("error") or {}).get("message")
                or out.get("msg")
                or out.get("error")
                or str(out.get("code") or status_code)
            )
            self._send_json(200, {"error": f"解说 API HTTP {status_code}: {msg}"})
            return

        if out.get("code") not in (None, "", 0, "0"):
            msg = (
                out.get("message")
                or (out.get("error") or {}).get("message")
                or out.get("msg")
                or out.get("error")
                or str(out.get("code"))
            )
            self._send_json(200, {"error": f"API 错误: {msg}"})
            return

        if isinstance(out.get("error"), dict) and (out["error"].get("code") or out["error"].get("message")):
            self._send_json(200, {"error": "API 错误: " + str(out["error"].get("message") or out["error"].get("code"))})
            return

        text = parse_model_text(out)
        self._send_json(200, {"explanation": text or "（模型未返回文本，请检查 API 与模型）"})

    def _handle_question(self):
        config = load_explain_config()
        if not config.get("apiUrl") or not config.get("apiKey"):
            self._send_json(200, {"error": "未配置解说 API。请在 log-viewer/explain-config.json 中填写 apiUrl、apiKey，或设置环境变量 EXPLAIN_API_URL、EXPLAIN_API_KEY。"})
            return
        try:
            payload = self._read_json_body()
        except ValueError:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        question = (payload.get("question") or "").strip()
        log_json = (payload.get("logJson") or "").strip()

        if not question:
            self._send_json(400, {"error": "请提供问题"})
            return
        if not log_json:
            self._send_json(400, {"error": "请提供日志内容"})
            return

        prompt = (
            "你是一个 Claude Code 日志分析专家。用户对一条工具调用日志有疑问，请根据日志内容回答用户的问题。\n\n"
            f"日志内容:\n{log_json[:3000]}\n\n"
            f"用户问题: {question}\n\n"
            "请根据日志内容给出详细、准确的中文回答。如果日志中没有足够信息回答，请说明需要查看更多信息："
        )

        request_body = json.dumps(
            {
                "model": config.get("model") or "qwen-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 400,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        api_url = ensure_chat_completions_url(config.get("apiUrl") or "")
        req = Request(
            url=api_url,
            method="POST",
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + str(config["apiKey"]),
            },
        )
        try:
            with urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                status_code = resp.getcode()
        except HTTPError as exc:
            status_code = exc.code
            body = exc.read().decode("utf-8", errors="ignore")
        except URLError as exc:
            self._send_json(200, {"error": f"请求 API 失败: {exc.reason}"})
            return
        except Exception as exc:
            self._send_json(200, {"error": f"请求 API 失败: {exc}"})
            return

        try:
            out = json.loads(body) if body else {}
        except Exception:
            self._send_json(200, {"error": "API 返回非 JSON: " + (body[:200] if body else "空响应")})
            return

        if status_code >= 400:
            msg = out.get("message") or (out.get("error") or {}).get("message") or out.get("msg") or out.get("error") or str(out.get("code") or status_code)
            self._send_json(200, {"error": f"API HTTP {status_code}: {msg}"})
            return

        if out.get("code") not in (None, "", 0, "0"):
            msg = out.get("message") or (out.get("error") or {}).get("message") or out.get("msg") or out.get("error") or str(out.get("code"))
            self._send_json(200, {"error": f"API 错误: {msg}"})
            return

        if isinstance(out.get("error"), dict) and (out["error"].get("code") or out["error"].get("message")):
            self._send_json(200, {"error": "API 错误: " + str(out["error"].get("message") or out["error"].get("code"))})
            return

        text = parse_model_text(out)
        self._send_json(200, {"answer": text or "（模型未返回文本，请检查 API 与模型）"})

    def _serve_static(self, path_name: str):
        rel = "index.html" if path_name == "/" else path_name.lstrip("/")
        file_path = (VIEWER_DIR / rel).resolve()
        if VIEWER_DIR not in file_path.parents and file_path != VIEWER_DIR:
            self.send_response(404)
            self.end_headers()
            return
        if file_path.exists() and file_path.is_file():
            content_type, _ = mimetypes.guess_type(str(file_path))
            if not content_type:
                content_type = "application/octet-stream"
            if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
                content_type += "; charset=utf-8"
            body = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path_name = parsed.path
        query = parse_qs(parsed.query or "")
        if path_name == "/api/projects":
            self._handle_projects()
            return
        if path_name == "/api/explain-config":
            self._handle_explain_config_get()
            return
        if re.fullmatch(r"/api/projects/[^/]+/sessions", path_name):
            self._handle_project_sessions(path_name)
            return
        if re.fullmatch(r"/api/timelines/[^/]+/events", path_name):
            self._handle_timeline_events(path_name, query)
            return
        if re.fullmatch(r"/api/timelines/[^/]+/health", path_name):
            self._handle_timeline_health(path_name)
            return
        self._serve_static(path_name)

    def do_POST(self):
        parsed = urlparse(self.path)
        path_name = parsed.path
        if path_name == "/api/explain-config":
            self._handle_explain_config_post()
            return
        if path_name == "/api/explain":
            self._handle_explain()
            return
        if path_name == "/api/question":
            self._handle_question()
            return
        self.send_response(404)
        self.end_headers()

    def do_PUT(self):
        self.send_response(405)
        self.end_headers()

    def do_DELETE(self):
        self.send_response(405)
        self.end_headers()


def main():
    server, bound_port = create_server_with_fallback(PORT)
    if bound_port != PORT:
        print(f"提示: 端口 {PORT} 不可用，已自动切换到 {bound_port}")
    print(f"Claude 工具日志查看器: http://127.0.0.1:{bound_port}")
    print(f"日志目录: {CLAUDE_PROJECTS_DIR}")
    server.serve_forever()


if __name__ == "__main__":
    main()
