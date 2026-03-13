"""
dl_preview.py - 为课程目录中的文件生成简短预览文本

职责：
- 复用 transcribe.py / extract.py
- 针对不同类型的文件生成有限长度的预览文本，供后续 LLM 角色识别使用
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, List

import config
import extract
import transcribe
from dl_course import CourseFile, ScannedCourse


@dataclass
class FilePreview:
    """单个文件的预览文本及基础元数据。"""

    file: CourseFile
    kind: str  # 与 CourseFile.kind 一致，冗余便于调试
    preview: str


def _preview_text_file(path: Path, max_lines: int = 80) -> str:
    lines: List[str] = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                lines.append(line.rstrip("\n"))
                if i >= max_lines:
                    break
    except Exception as e:
        return f"[预览失败: {e}]"
    return "\n".join(lines)


def _preview_document(path: Path, max_pages: int = 3) -> str:
    """
    对 PDF/PPTX 只抽取前若干页/张作为预览，以控制 token 数量。

    由于 extract.py 当前不支持页数限制，这里简单用全文提取后截断。
    如后续需要，可在 extract.py 内部增加分页控制。
    """
    full = extract.extract_material(str(path))
    if not full:
        return ""

    # 简单启发式：按页标记或空行分段，截取前若干段
    parts = full.split("\n\n")
    if len(parts) <= max_pages:
        return full
    return "\n\n".join(parts[:max_pages])


def _preview_video(path: Path, max_chunks: int = 1) -> str:
    """
    为视频生成预览文本。

    优先直接读取转写缓存 JSON，避免在 dl 模式下对长视频重新完整转写。
    如不存在缓存，则暂时跳过该视频的预览。
    """
    cache_file = Path(config.CACHE_DIR) / f"{path.stem}.json"
    if not cache_file.exists():
        print(f"[dl_preview] 未找到转写缓存，跳过视频预览: {path}")
        return ""

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            segments = json.load(f)
    except Exception as e:
        print(f"[dl_preview] 读取转写缓存失败，跳过视频预览: {cache_file} ({e})")
        return ""

    chunks = transcribe.segments_to_chunks(segments)
    if not chunks:
        return ""
    return "\n\n".join(chunks[:max_chunks])


def build_previews_for_course(
    scanned: ScannedCourse,
    max_doc_pages: int = 3,
    max_text_lines: int = 80,
    max_video_chunks: int = 1,
) -> Dict[str, FilePreview]:
    """
    为扫描到的课程文件生成预览文本。

    返回值：
        key: 文件的相对路径字符串（相对于课程根目录）
        value: FilePreview
    """
    previews: Dict[str, FilePreview] = {}

    for cf in scanned.files:
        rel_str = str(cf.rel_path).replace("\\", "/")
        preview_text = ""

        if cf.kind == "text":
            preview_text = _preview_text_file(cf.path, max_lines=max_text_lines)
        elif cf.kind == "document":
            preview_text = _preview_document(cf.path, max_pages=max_doc_pages)
        elif cf.kind == "video":
            preview_text = _preview_video(cf.path, max_chunks=max_video_chunks)
        else:
            # 其他类型默认不做预览
            preview_text = ""

        previews[rel_str] = FilePreview(file=cf, kind=cf.kind, preview=preview_text)

    print(f"[dl_preview] 预览生成完成: {len(previews)} 个文件")
    return previews


__all__ = [
    "FilePreview",
    "build_previews_for_course",
]

