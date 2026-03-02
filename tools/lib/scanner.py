"""scanner.py — 目录扫描，收集文件元信息和内容预览"""
from pathlib import Path

from .utils import SKIP_DIRS, SKIP_EXTS, MAX_FILE_SIZE_FOR_PREVIEW, CONTENT_PREVIEW_LINES, fmt_size

TEXT_EXTS = {
    ".py", ".js", ".ts", ".md", ".txt", ".yaml", ".yml",
    ".json", ".toml", ".cfg", ".ini", ".bat", ".sh",
    ".html", ".css", ".rst", ".csv", ".log",
}


def scan_directory(root: Path, max_depth: int = 3) -> list[dict]:
    """
    递归扫描目录，返回文件信息列表。

    每项字段：rel_path, abs_path, size_bytes, extension, is_text, content_preview, depth
    """
    results = []

    def _walk(dir_path: Path, depth: int):
        if depth > max_depth:
            return
        try:
            entries = sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name))
        except PermissionError:
            return
        for entry in entries:
            if entry.name in SKIP_DIRS:
                continue
            if entry.is_dir():
                _walk(entry, depth + 1)
            elif entry.is_file():
                ext = entry.suffix.lower()
                if ext in SKIP_EXTS:
                    continue
                try:
                    size = entry.stat().st_size
                except OSError:
                    size = 0

                content_preview, is_text = "", False
                if ext in TEXT_EXTS and size < MAX_FILE_SIZE_FOR_PREVIEW:
                    try:
                        raw = entry.read_text(encoding="utf-8", errors="replace")
                        lines = raw.splitlines()
                        content_preview = "\n".join(lines[:CONTENT_PREVIEW_LINES])
                        if len(lines) > CONTENT_PREVIEW_LINES:
                            content_preview += f"\n... ({len(lines) - CONTENT_PREVIEW_LINES} more lines)"
                        is_text = True
                    except Exception:
                        pass

                results.append({
                    "rel_path":       str(entry.relative_to(root)),
                    "abs_path":       str(entry.resolve()),
                    "size_bytes":     size,
                    "extension":      ext,
                    "is_text":        is_text,
                    "content_preview": content_preview,
                    "depth":          depth,
                })

    _walk(root, 0)
    return results


def build_user_prompt(root: Path, files: list[dict]) -> str:
    """把扫描结果格式化为发给 LLM 的用户 prompt。"""
    lines = [f"项目根目录: {root}", "", "文件列表（格式：[大小] 路径 | 内容预览）：", "=" * 60]
    for f in files:
        lines.append(f"\n[{fmt_size(f['size_bytes'])}] {f['rel_path']}")
        if f["content_preview"]:
            for line in f["content_preview"][:800].splitlines()[:15]:
                lines.append(f"    | {line}")
    lines += ["\n" + "=" * 60, "请根据以上信息，输出整理建议 JSON。"]
    return "\n".join(lines)
