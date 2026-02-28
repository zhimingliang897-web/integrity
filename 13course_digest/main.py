"""
main.py - 主入口

串联完整流程：视频转录 → 材料提取 → AI 分析 → 输出学习指南。
通过命令行参数指定视频和辅助材料路径。

用法示例：
    # 仅处理视频（无辅助材料）
    python main.py lecture1.mp4

    # 完整模式（推荐）
    python main.py lecture1.mp4 --ppt slides.pptx --syllabus syllabus.pdf --exams past_exams.pdf

    # 批量处理多个视频
    python main.py lecture1.mp4 lecture2.mp4 lecture3.mp4 --syllabus syllabus.pdf
"""

import argparse
import os
import sys
from pathlib import Path

import config
import analyze
import extract
import transcribe


def process_one(
    video_path: str,
    ppt_text: str,
    syllabus_text: str,
    past_exams_text: str,
    paper_text: str,
) -> None:
    """
    处理单个视频文件，输出 Markdown 学习指南到 output/ 目录。

    Args:
        video_path: 视频文件路径
        ppt_text: PPT 提取的文字（空字符串表示未提供）
        syllabus_text: 考试大纲文字
        past_exams_text: 往年真题文字
        paper_text: 补充论文文字
    """
    lecture_name = Path(video_path).stem
    output_file = Path(config.OUTPUT_DIR) / f"{lecture_name}_学习指南.md"

    if output_file.exists():
        print(f"[main] 已存在学习指南，跳过: {output_file}")
        return

    print(f"\n{'='*50}")
    print(f"[main] 处理: {lecture_name}")
    print(f"{'='*50}")

    # Step 1: 转录（带缓存）
    segments = transcribe.transcribe(video_path)
    chunks = transcribe.segments_to_chunks(segments)
    print(f"[main] 转录完成，共 {len(chunks)} 个分析块")

    # Step 2: AI 分析
    guide = analyze.analyze_lecture(
        chunks=chunks,
        lecture_name=lecture_name,
        syllabus=syllabus_text,
        past_exams=past_exams_text,
        ppt_text=ppt_text,
        paper_text=paper_text,
    )

    # Step 3: 保存输出
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(guide)
    print(f"[main] 学习指南已保存: {output_file}")


def main() -> None:
    """
    解析命令行参数，依次处理所有指定的视频文件。
    """
    parser = argparse.ArgumentParser(
        description="CourseDigest - 课程视频考点提取工具"
    )
    parser.add_argument("videos", nargs="+", help="视频文件路径（可以多个）")
    parser.add_argument("--ppt", default="", help="PPT/PPTX 文件路径（可选）")
    parser.add_argument("--syllabus", default="", help="考试大纲 PDF 路径（可选）")
    parser.add_argument("--exams", default="", help="往年真题 PDF 路径（可选）")
    parser.add_argument("--paper", default="", help="论文 PDF 路径（可选）")
    args = parser.parse_args()

    def resolve(p: str) -> str:
        """智能路径解析：支持当前路径、绝对路径及 input/cache 目录下的递归搜索。"""
        if not p:
            return ""
            
        # 1. 如果是绝对路径或相对当前目录直接存在，直接返回
        path_p = Path(p)
        if path_p.exists():
            return str(path_p.absolute())
            
        # 2. 在常见目录下递归搜索（支持用户只传入文件名）
        # 搜索顺序：input -> cache
        search_roots = [Path(config.INPUT_DIR), Path(config.CACHE_DIR)]
        for root in search_roots:
            if root.exists():
                matches = list(root.rglob(p))
                if matches:
                    return str(matches[0].absolute())
                
        return p

    # 一次性提取辅助材料（所有视频共享）
    global_ppt = extract.extract_material(resolve(args.ppt)) if args.ppt else ""
    global_syllabus = extract.extract_material(resolve(args.syllabus)) if args.syllabus else ""
    global_exams = extract.extract_material(resolve(args.exams)) if args.exams else ""
    global_paper = extract.extract_material(resolve(args.paper)) if args.paper else ""

    for video in args.videos:
        video_path = Path(resolve(video))
        if not video_path.exists():
            print(f"[main] 视频文件不存在，跳过: {video}", file=sys.stderr)
            continue
            
        # 自动发现同名辅助材料
        def find_auto(suffixes: list[str]) -> str:
            for suf in suffixes:
                candidate = video_path.parent / f"{video_path.stem}{suf}"
                if candidate.exists():
                    print(f"[main] [自动发现] 补充材料: {candidate}")
                    return extract.extract_material(str(candidate))
            return ""

        local_ppt = global_ppt or find_auto(["_ppt.pdf", "_ppt.pptx", "_slides.pdf", "_slides.pptx"])
        local_paper = global_paper or find_auto(["_paper.pdf"])
        local_exams = global_exams or find_auto(["_exams.pdf", "_quiz.pdf"])

        process_one(str(video_path), local_ppt, global_syllabus, local_exams, local_paper)

    print("\n[main] 全部完成！学习指南位于 output/ 目录")


if __name__ == "__main__":
    main()
