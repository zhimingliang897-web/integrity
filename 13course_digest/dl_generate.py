"""
dl_generate.py - 一键从课程目录生成复习指南与考试指南

用法示例：
    python dl_generate.py cache/dl/AI6131
"""

from __future__ import annotations

import argparse
from pathlib import Path

import config
import prompts
from analyze import _call_llm
from dl_course import scan_course_dir
from dl_course_context import build_course_context, classify_files_with_llm
from dl_preview import build_previews_for_course
import transcribe


def generate_for_course_dir(course_dir: str, transcribe_all: bool = False) -> None:
    scanned = scan_course_dir(course_dir)

    if transcribe_all:
        print(f"[dl_generate] 开始为该课程目录下的共 {len(scanned.videos)} 个视频生成/刷新转写缓存...")
        failed = []
        for vf in scanned.videos:
            print(f"[dl_generate] 转写视频: {vf.path.name}")
            try:
                transcribe.transcribe(str(vf.path))
            except Exception as e:
                print(f"[dl_generate] 转写失败，跳过: {vf.path.name} —— {e}")
                failed.append((vf.path.name, str(e)))
        if failed:
            print(f"[dl_generate] 视频转写阶段完成，其中 {len(failed)} 个失败: {[n for n, _ in failed]}")
        else:
            print("[dl_generate] 视频转写阶段完成。")

    previews = build_previews_for_course(scanned)

    if not previews:
        print(f"[dl_generate] 未在 {scanned.root_dir} 中发现可用文件，退出。")
        return

    roles = classify_files_with_llm(previews)
    ctx = build_course_context(scanned, previews, roles)

    # 自动检测学科类型
    all_texts = [
        ctx.course_overview,
        ctx.lecture_materials_text,
        ctx.past_exams_text,
    ]
    subject = prompts.detect_subject(all_texts)
    print(f"[dl_generate] 检测到学科类型: {subject}")

    # 为 Study/Exam prompt 构建精简上下文字典
    course_context_payload = {
        "course_name": ctx.course_name,
        "course_overview": ctx.course_overview,
        "course_requirements": ctx.course_requirements,
        "exam_raw_text": ctx.exam_raw_text,
        "past_exams_text": ctx.past_exams_text,
        "lecture_summary": ctx.lecture_materials_text,
        "exam_policy_notes": ctx.exam_policy_notes,
        "key_topics": "",  # 如后续增加结构化提取可填充
    }

    system = prompts.build_system_prompt(subject)

    # 复习指南
    study_user = prompts.build_dl_study_guide_prompt(course_context_payload, subject)
    study_md = _call_llm(system, study_user)

    # 考试指南
    exam_user = prompts.build_dl_exam_guide_prompt(course_context_payload, subject)
    exam_md = _call_llm(system, exam_user)

    out_dir = Path(config.OUTPUT_DIR)
    out_dir.mkdir(exist_ok=True)

    study_path = out_dir / f"{ctx.course_name}_复习指南.md"
    exam_path = out_dir / f"{ctx.course_name}_考试指南.md"

    study_path.write_text(study_md, encoding="utf-8")
    exam_path.write_text(exam_md, encoding="utf-8")

    print(f"[dl_generate] 复习指南已生成: {study_path}")
    print(f"[dl_generate] 考试指南已生成: {exam_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="从课程资料目录生成复习指南与考试指南（dl 模式）"
    )
    parser.add_argument(
        "course_dir",
        help="课程目录路径，例如 13course_digest/cache/dl/AI6131",
    )
    parser.add_argument(
        "--transcribe-all",
        action="store_true",
        help="在生成课程级指南前，先对该目录下所有视频执行一次转写（会写入/复用 cache/*.json）",
    )
    args = parser.parse_args()

    generate_for_course_dir(args.course_dir, transcribe_all=args.transcribe_all)


if __name__ == "__main__":
    main()

