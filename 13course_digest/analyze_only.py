"""
analyze_only.py - 单独运行 AI 分析（跳过转录）

适用场景：转录已完成（cache/ 中有对应 JSON），只需重新分析或更换辅助材料时使用。
直接读取缓存的转录文本，调用 Groq API 输出学习指南。

用法：
    python analyze_only.py 6                           # 仅分析（无辅助材料）
    python analyze_only.py 6 --ppt 4.pdf              # 带 PPT
    python analyze_only.py 6 --ppt 4.pdf --syllabus s.pdf --exams e.pdf
    python analyze_only.py 6 --force                  # 强制重新分析（即使 output 已存在）
"""

import argparse
import json
import os
import sys
from pathlib import Path

import analyze
import config
import extract
import transcribe


def main() -> None:
    """
    解析参数，读取转录缓存，调用 AI 分析并输出学习指南。
    """
    parser = argparse.ArgumentParser(
        description="CourseDigest - 仅 AI 分析（跳过转录，直接读缓存）"
    )
    parser.add_argument("name", help="视频名称（不含扩展名），用于定位 cache/{name}.json")
    parser.add_argument("--ppt", default="", help="PPT/PDF 文件路径（可选）")
    parser.add_argument("--syllabus", default="", help="考试大纲 PDF 路径（可选）")
    parser.add_argument("--exams", default="", help="往年真题 PDF 路径（可选）")
    parser.add_argument("--paper", default="", help="论文 PDF 路径（可选）")
    parser.add_argument("--force", action="store_true", help="强制重新分析（覆盖已有输出）")
    args = parser.parse_args()

    # 检查缓存
    cache_file = Path(config.CACHE_DIR) / f"{args.name}.json"
    if not cache_file.exists():
        print(f"[error] 未找到转录缓存: {cache_file}", file=sys.stderr)
        print(f"  请先运行: python main.py {args.name}.mp4", file=sys.stderr)
        sys.exit(1)

    # 检查输出
    output_file = Path(config.OUTPUT_DIR) / f"{args.name}_学习指南.md"
    if output_file.exists() and not args.force:
        print(f"[skip] 学习指南已存在（使用 --force 覆盖）: {output_file}")
        sys.exit(0)

    def resolve(p: str) -> str:
        """若文件不在当前目录，自动到 input/ 目录查找。"""
        if p and not Path(p).exists():
            candidate = Path(config.INPUT_DIR) / p
            if candidate.exists():
                return str(candidate)
        return p

    # 提取辅助材料
    ppt_text      = extract.extract_material(resolve(args.ppt))      if args.ppt      else ""
    syllabus_text = extract.extract_material(resolve(args.syllabus)) if args.syllabus else ""
    exams_text    = extract.extract_material(resolve(args.exams))    if args.exams    else ""
    paper_text    = extract.extract_material(resolve(args.paper))    if args.paper    else ""

    # 读取缓存
    print(f"[analyze_only] 读取缓存: {cache_file}")
    with open(cache_file, encoding="utf-8") as f:
        segments = json.load(f)

    chunks = transcribe.segments_to_chunks(segments)
    print(f"[analyze_only] 共 {len(chunks)} 个分析块，开始调用 Groq API...")

    guide = analyze.analyze_lecture(
        chunks=chunks,
        lecture_name=args.name,
        syllabus=syllabus_text,
        past_exams=exams_text,
        ppt_text=ppt_text,
        paper_text=paper_text,
    )

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(guide)
    print(f"[analyze_only] 学习指南已保存: {output_file}")


if __name__ == "__main__":
    main()
