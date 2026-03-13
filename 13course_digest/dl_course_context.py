"""
dl_course_context.py - 基于扫描结果和 LLM 分类构建课程级上下文
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import config
import prompts
from analyze import _call_llm
from dl_course import CourseFile, ScannedCourse
from dl_preview import FilePreview


def _extract_json_array(text: str) -> str:
    """从文本中提取第一个完整的 JSON 数组（按方括号配对）。"""
    start = text.find("[")
    if start == -1:
        return "[]"
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return text[start : text.rfind("]") + 1] if text.rfind("]") >= start else "[]"


def _fix_trailing_commas(json_str: str) -> str:
    """去掉 JSON 中对象/数组末尾的尾逗号，便于标准解析。"""
    return re.sub(r",\s*([}\]])", r"\1", json_str)


def _fix_unescaped_quotes_in_strings(json_str: str) -> str:
    """
    在字符串值内将未转义的双引号替换为 \\"，并将未转义的换行替换为空格，避免 LLM 输出导致 JSON 解析失败。
    """
    result: List[str] = []
    i = 0
    in_string = False
    escape_next = False
    while i < len(json_str):
        c = json_str[i]
        if escape_next:
            result.append(c)
            escape_next = False
        elif c == "\\" and in_string:
            result.append(c)
            escape_next = True
        elif c == '"':
            if not in_string:
                in_string = True
                result.append(c)
            else:
                rest = json_str[i + 1 :].lstrip()
                # 正常结束键或值：下一非空字符是 : } ] , 则不转义
                if rest.startswith(":") or rest.startswith("}") or rest.startswith("]") or rest.startswith(","):
                    in_string = False
                    result.append(c)
                else:
                    result.append('\\"')
        elif in_string and c in "\n\r":
            result.append(" ")
        else:
            result.append(c)
        i += 1
    return "".join(result)


def _parse_classify_json(raw: str) -> List[dict]:
    """
    解析 LLM 返回的“文件角色分类”JSON，容错处理代码块、尾逗号、未转义引号等。
    若标准 JSON 解析仍失败，则用正则逐条提取 path/role/confidence/exam_policy_notes 作为回退。
    """
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```\s*json\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"```\s*$", "", cleaned)
    cleaned = cleaned.strip()
    array_str = _extract_json_array(cleaned)
    array_str = _fix_trailing_commas(array_str)
    array_str = _fix_unescaped_quotes_in_strings(array_str)

    try:
        return json.loads(array_str)
    except json.JSONDecodeError:
        pass

    # 回退：用正则从原文中逐个匹配对象（只匹配我们需要的四个字段）
    objects: List[dict] = []
    # 匹配 "path": "xxx" 或 "path": "xxx" 其中 xxx 可能含 \"，再匹配 role、confidence、exam_policy_notes
    block = re.findall(
        r'\{\s*"path"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"role"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"confidence"\s*:\s*(\d+)\s*,\s*"exam_policy_notes"\s*:\s*"((?:[^"\\]|\\.)*)"',
        array_str,
        re.DOTALL,
    )
    for path_val, role_val, conf_val, notes_val in block:
        def unquote(s: str) -> str:
            return s.replace('\\"', '"').replace("\\\\", "\\")
        objects.append({
            "path": unquote(path_val),
            "role": unquote(role_val),
            "confidence": int(conf_val),
            "exam_policy_notes": unquote(notes_val),
        })
    if objects:
        return objects

    # 更宽松的回退：按 "path" 分段，再在每个块里找 role / confidence / exam_policy_notes
    parts = re.split(r'"path"\s*:\s*"', array_str)
    for part in parts[1:]:
        m_path = re.match(r'^((?:[^"\\]|\\.)*)"', part)
        if not m_path:
            continue
        path_val = m_path.group(1).replace('\\"', '"')
        rest = part[m_path.end() :]
        m_role = re.search(r'"role"\s*:\s*"([^"]*)"', rest)
        m_conf = re.search(r'"confidence"\s*:\s*(\d+)', rest)
        m_notes = re.search(r'"exam_policy_notes"\s*:\s*"((?:[^"\\]|\\.)*)"', rest)
        role_val = m_role.group(1) if m_role else "other"
        conf_val = int(m_conf.group(1)) if m_conf else 0
        notes_val = (m_notes.group(1).replace('\\"', '"') if m_notes else "") or ""
        objects.append({
            "path": path_val,
            "role": role_val,
            "confidence": conf_val,
            "exam_policy_notes": notes_val,
        })
    return objects


@dataclass
class FileRoleInfo:
    path: str
    role: str
    confidence: int
    exam_policy_notes: str


@dataclass
class CourseContext:
    course_name: str
    root_dir: Path
    files: List[CourseFile]
    roles: Dict[str, FileRoleInfo]  # key: rel_path

    # 聚合后的文本
    course_overview: str = ""
    course_requirements: str = ""
    exam_raw_text: str = ""
    past_exams_text: str = ""
    lecture_materials_text: str = ""
    exam_policy_notes: str = ""


def classify_files_with_llm(previews: Dict[str, FilePreview]) -> Dict[str, FileRoleInfo]:
    """
    调用 LLM 对每个文件进行角色分类。
    """
    file_items = []
    for rel, pv in previews.items():
        file_items.append(
            {
                "path": rel,
                "ext": pv.file.suffix,
                "kind": pv.kind,
                "preview": pv.preview,
            }
        )

    user = prompts.build_dl_classify_prompt(file_items)
    # 简化：沿用 analyze 中的系统提示 & 调用逻辑
    system = prompts.build_system_prompt()
    raw = _call_llm(system, user)

    data = _parse_classify_json(raw)
    if not data:
        raise ValueError("LLM 未返回有效的文件角色分类 JSON 数组，请重试或检查模型输出。")

    result: Dict[str, FileRoleInfo] = {}
    for item in data:
        path = item.get("path", "")
        if not path:
            continue
        result[path] = FileRoleInfo(
            path=path,
            role=item.get("role", "other"),
            confidence=int(item.get("confidence", 0) or 0),
            exam_policy_notes=item.get("exam_policy_notes", "") or "",
        )

    return result


def build_course_context(
    scanned: ScannedCourse, previews: Dict[str, FilePreview], roles: Dict[str, FileRoleInfo]
) -> CourseContext:
    """
    将 LLM 角色分类结果与预览文本聚合为课程级上下文。
    """
    def collect(role_names: List[str]) -> List[str]:
        texts: List[str] = []
        for rel, info in roles.items():
            if info.role in role_names:
                pv = previews.get(rel)
                if not pv or not pv.preview:
                    continue
                texts.append(f"--- FILE: {rel} (role={info.role}) ---\n{pv.preview}")
        return texts

    overview_parts = collect(["course_overview"])
    req_parts = collect(["course_requirements"])
    exam_parts = collect(["exam_requirements"])
    past_exam_parts = collect(["past_exams"])
    lecture_parts = collect(["lecture_slides", "reference"])

    # 聚合 exam_policy_notes
    policy_notes: List[str] = []
    for rel, info in roles.items():
        if info.exam_policy_notes:
            policy_notes.append(f"[{rel}] {info.exam_policy_notes}")

    ctx = CourseContext(
        course_name=scanned.course_name,
        root_dir=scanned.root_dir,
        files=scanned.files,
        roles=roles,
        course_overview="\n\n".join(overview_parts),
        course_requirements="\n\n".join(req_parts),
        exam_raw_text="\n\n".join(exam_parts),
        past_exams_text="\n\n".join(past_exam_parts),
        lecture_materials_text="\n\n".join(lecture_parts),
        exam_policy_notes="\n".join(policy_notes),
    )

    return ctx


__all__ = [
    "FileRoleInfo",
    "CourseContext",
    "classify_files_with_llm",
    "build_course_context",
]

