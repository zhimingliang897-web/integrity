"""
dl_course_context.py - 基于扫描结果和 LLM 分类构建课程级上下文
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import config
import prompts
from analyze import _call_llm
from dl_course import CourseFile, ScannedCourse
from dl_preview import FilePreview


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

    import json

    # LLM 有可能包裹 ```json 代码块，这里做简单清洗
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lstrip().startswith("json"):
            cleaned = cleaned.lstrip()[4:]
    try:
        data = json.loads(cleaned)
    except Exception:
        # 尝试在第一对方括号内切片
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1 and end > start:
            data = json.loads(cleaned[start : end + 1])
        else:
            raise

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

