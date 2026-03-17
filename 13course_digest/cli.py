"""
cli.py - 统一命令行入口

用法：
    python cli.py transcribe <课程目录>   # 视频转文字
    python cli.py generate <课程目录>     # 生成指南（使用已有转写）
    python cli.py all <课程目录>          # 一键全流程
    python cli.py preview <课程目录>      # 预览资料
    python cli.py match <课程目录>        # 智能匹配视频和PDF
"""

import argparse
import json
from pathlib import Path

import config
import transcribe
import extract
from dl_course import scan_course_dir
from dl_preview import build_previews_for_course
from dl_generate import generate_for_course_dir


def cmd_transcribe(args):
    """只执行视频转写，不生成指南"""
    scanned = scan_course_dir(args.course_dir)

    if not scanned.videos:
        print(f"[transcribe] 未找到视频文件: {scanned.root_dir}")
        return

    print(f"[transcribe] 发现 {len(scanned.videos)} 个视频，开始转写...")
    for vf in scanned.videos:
        print(f"[transcribe] 转写视频: {vf.path.name}")
        transcribe.transcribe(str(vf.path))

    print(f"[transcribe] 完成，共转写 {len(scanned.videos)} 个视频")


def cmd_generate(args):
    """使用已有转写生成指南"""
    generate_for_course_dir(args.course_dir, transcribe_all=False)


def cmd_all(args):
    """一键全流程：转写 + 生成"""
    generate_for_course_dir(args.course_dir, transcribe_all=True)


def cmd_preview(args):
    """预览课程资料"""
    scanned = scan_course_dir(args.course_dir)
    previews = build_previews_for_course(scanned)

    print(f"\n{'='*60}")
    print(f"课程: {scanned.course_name}")
    print(f"{'='*60}")

    # 按类型分组显示
    for kind in ["video", "document", "text"]:
        files_of_kind = [f for f in scanned.files if f.kind == kind]
        if not files_of_kind:
            continue

        icon = {"video": "🎥", "document": "📄", "text": "📝"}.get(kind, "📁")
        print(f"\n{icon} {kind.upper()} ({len(files_of_kind)} 个文件)")
        print("-" * 40)

        for cf in files_of_kind:
            rel = str(cf.rel_path).replace("\\", "/")
            pv = previews.get(rel)
            preview_text = pv.preview[:200] if pv and pv.preview else "(无预览)"
            print(f"\n▶ {rel}")
            print(f"  {preview_text}...")

    print(f"\n{'='*60}")


def cmd_match(args):
    """智能匹配视频和PDF"""
    import analyze

    scanned = scan_course_dir(args.course_dir)
    videos = scanned.videos
    pdfs = [f for f in scanned.documents if f.suffix == ".pdf"]

    if not videos or not pdfs:
        print(f"[match] 需要至少一个视频和一个PDF")
        return

    print(f"[match] 发现 {len(videos)} 个视频, {len(pdfs)} 个PDF")

    # 提取 PDF 特征
    import pdfplumber
    pdf_features = {}
    for p in pdfs:
        try:
            with pdfplumber.open(p.path) as pdf:
                if pdf.pages:
                    text = pdf.pages[0].extract_text() or ""
                    pdf_features[str(p.path)] = text[:400].replace('\n', ' ')
        except Exception:
            pass

    # 提取视频特征（从缓存）
    video_features = {}
    for v in videos:
        cache_path = Path(config.CACHE_DIR) / f"{v.path.stem}.json"
        text = ""
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    text = " ".join([s["text"] for s in data[:5]])
            except Exception:
                pass
        video_features[str(v.path)] = text[:400] if text else "(无转写缓存)"

    # 构建 prompt
    prompt = f"""
你是一个课程助教。我们有一些课程视频和一些课件或论文PDF，需要正确搭配。
下面是视频前几句话的文字特征，以及 PDF 第一页的文字特征。

【视频列表特征】：
{json.dumps(video_features, ensure_ascii=False, indent=2)}

【PDF列表特征】：
{json.dumps(pdf_features, ensure_ascii=False, indent=2)}

请为每个视频找出最适合作为其配套课件的 PPT（选1个）和补充论文 Paper（选1个，也可为空）。
必须仅输出一个合法的 JSON，不要输出任何额外的标记解释和 Markdown 格式符号。结构如下：
{{
   "视频的完整路径": {{"ppt": "PPT文件的完整路径", "paper": "论文文件的完整路径或null"}},
   "下一个视频的路径": {{"ppt": "...", "paper": "..."}}
}}
"""

    print("[match] 正在请求 AI 进行匹配...")
    system = "You are a helpful assistant. Output ONLY valid JSON."
    result = analyze._call_llm(system, prompt)

    try:
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("```", 1)[0]
        if result.startswith("json"):
            result = result[4:]

        matchings = json.loads(result.strip())

        # 生成批处理脚本
        script_name = "run_matched.bat"
        with open(script_name, "w", encoding="utf-8") as f:
            f.write("@echo off\n")
            f.write("echo 开始执行 AI 自动匹配生成的任务组合...\n\n")
            for v, doc in matchings.items():
                cmd = f"python cli.py transcribe-single \"{v}\""
                if doc.get("ppt") and doc["ppt"] != "null":
                    cmd += f" --ppt \"{doc['ppt']}\""
                if doc.get("paper") and doc["paper"] != "null":
                    cmd += f" --paper \"{doc['paper']}\""
                f.write(f"echo ===============================\n")
                f.write(f"echo 正在处理 AI 匹配的视频: {Path(v).name}...\n")
                f.write(cmd + "\n\n")
            f.write("echo 所有匹配任务执行完毕。\n")

        print(f"[match] 匹配成功！已生成批处理脚本: {script_name}")

    except Exception as e:
        print(f"[match] 解析失败: {e}")
        print(f"AI 原始输出: {result}")


def main():
    parser = argparse.ArgumentParser(
        description="CourseDigest - 智能课程复习助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python cli.py transcribe cache/dl/6103   # 只转写视频
  python cli.py generate cache/dl/6103     # 生成指南
  python cli.py all cache/dl/6103          # 一键全流程
  python cli.py preview cache/dl/6103      # 预览资料
  python cli.py match cache/dl/6103        # 智能匹配
        """
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # transcribe 子命令
    p_t = subparsers.add_parser("transcribe", help="视频转文字")
    p_t.add_argument("course_dir", help="课程目录路径")
    p_t.set_defaults(func=cmd_transcribe)

    # generate 子命令
    p_g = subparsers.add_parser("generate", help="生成复习/考试指南")
    p_g.add_argument("course_dir", help="课程目录路径")
    p_g.set_defaults(func=cmd_generate)

    # all 子命令
    p_a = subparsers.add_parser("all", help="一键全流程")
    p_a.add_argument("course_dir", help="课程目录路径")
    p_a.set_defaults(func=cmd_all)

    # preview 子命令
    p_p = subparsers.add_parser("preview", help="预览课程资料")
    p_p.add_argument("course_dir", help="课程目录路径")
    p_p.set_defaults(func=cmd_preview)

    # match 子命令
    p_m = subparsers.add_parser("match", help="智能匹配视频和PDF")
    p_m.add_argument("course_dir", help="课程目录路径")
    p_m.set_defaults(func=cmd_match)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()