"""
dl_course.py - 课程级目录扫描与上下文构建

职责：
- 扫描 `cache/dl/<课程名>/` 或任意课程目录，按扩展名进行初步分类
- 生成后续 LLM 角色识别与课程级分析所需的基础数据结构
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Literal, Optional


FileRole = Literal[
    "video",
    "document",
    "text",
    "other",
]


@dataclass
class CourseFile:
    """课程目录中的单个文件及其静态信息。"""

    path: Path
    rel_path: Path
    suffix: str
    size_bytes: int
    kind: FileRole


@dataclass
class ScannedCourse:
    """扫描结果：仅包含静态文件信息，不包含任何 LLM 或预览内容。"""

    course_name: str
    root_dir: Path
    files: List[CourseFile] = field(default_factory=list)

    @property
    def videos(self) -> List[CourseFile]:
        return [f for f in self.files if f.kind == "video"]

    @property
    def documents(self) -> List[CourseFile]:
        return [f for f in self.files if f.kind == "document"]

    @property
    def texts(self) -> List[CourseFile]:
        return [f for f in self.files if f.kind == "text"]


def _classify_suffix(suffix: str) -> FileRole:
    """
    根据扩展名做静态粗分类，不依赖 LLM。

    Args:
        suffix: 如 ".pdf"、".mp4"
    """
    s = suffix.lower()
    if s in {".mp4", ".mkv", ".mov"}:
        return "video"
    if s in {".pdf", ".pptx", ".ppt"}:
        return "document"
    if s in {".md", ".txt"}:
        return "text"
    return "other"


def scan_course_dir(course_dir: str | Path) -> ScannedCourse:
    """
    递归扫描课程目录，并按扩展名做静态分类。

    约定：
    - `course_dir` 可以是绝对路径或相对路径
    - `course_name` 默认取目录名（例如 cache/dl/AI6131 -> "AI6131"）
    """
    root = Path(course_dir).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"[dl_course] 课程目录不存在: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"[dl_course] 目标不是目录: {root}")

    course_name = root.name
    files: List[CourseFile] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        kind = _classify_suffix(path.suffix)
        files.append(
            CourseFile(
                path=path,
                rel_path=rel,
                suffix=path.suffix.lower(),
                size_bytes=size,
                kind=kind,
            )
        )

    print(f"[dl_course] 课程目录扫描完成: {root} ({len(files)} 个文件)")
    kind_counts: Dict[FileRole, int] = {"video": 0, "document": 0, "text": 0, "other": 0}
    for f in files:
        kind_counts[f.kind] += 1
    print(
        f"[dl_course] 分类统计: "
        f"video={kind_counts['video']}, "
        f"document={kind_counts['document']}, "
        f"text={kind_counts['text']}, "
        f"other={kind_counts['other']}"
    )

    return ScannedCourse(course_name=course_name, root_dir=root, files=files)


__all__ = [
    "FileRole",
    "CourseFile",
    "ScannedCourse",
    "scan_course_dir",
]

