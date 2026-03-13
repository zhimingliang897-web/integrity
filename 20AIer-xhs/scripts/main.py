#!/usr/bin/env python3
"""
小红书图文生成器 v4.0
=====================
用法：python main.py <文章.txt> [--no-comments]
输出：output/<文件名>/ 包含封面+内容页+评论区文案
"""
import sys
import os
import platform

sys.path.insert(0, os.path.dirname(__file__))

from config import MODEL, OUTPUT_BASE, API_KEY, BASE_URL
from llm_formatter import format_text_to_slides, generate_plain_summary
from image_generator import generate_images, render_cover
from comment_generator import generate_comments, save_comments


def print_banner():
    print(f"\n{'═' * 45}")
    print(f"  小红书图文生成器 v4.0")
    print(f"  Model: {MODEL}")
    print(f"{'═' * 45}\n")


def open_folder(path: str):
    """跨平台打开文件夹"""
    system = platform.system()
    if system == "Darwin":
        os.system(f"open '{path}'")
    elif system == "Windows":
        os.startfile(path)
    elif system == "Linux":
        os.system(f"xdg-open '{path}'")


def main():
    print_banner()

    if not API_KEY:
        print("未检测到 API Key。请设置环境变量 `XHS_API_KEY`，或在 `20AIer-xhs/config.local.yaml` 里配置 `api.api_key`。")
        print(f"当前 base_url={BASE_URL!r}, model={MODEL!r}")
        sys.exit(1)

    # 解析参数
    args = sys.argv[1:]
    no_comments = "--no-comments" in args
    comments_only = "--comments-only" in args
    args = [a for a in args if not a.startswith("--")]

    if len(args) < 1:
        print("\n用法：python main.py <文章.txt> [--no-comments] [--comments-only]\n")
        sys.exit(1)

    txt_path = os.path.abspath(args[0])
    if not os.path.isfile(txt_path):
        print(f"\n❌ 找不到文件：{txt_path}\n")
        sys.exit(1)

    # 用文件名（不含扩展名）作为输出文件夹名
    folder_name = os.path.splitext(os.path.basename(txt_path))[0]
    out_dir = os.path.join(OUTPUT_BASE, folder_name)

    with open(txt_path, "r", encoding="utf-8") as f:
        raw_text = f.read().strip()

    if not raw_text:
        print("❌ 文件内容为空，退出。")
        sys.exit(1)

    print(f"输入文件：{txt_path}  ({len(raw_text)} 字符)")
    print(f"输出文件夹：{out_dir}")
    if comments_only:
        print("模式：仅生成评论区文案\n")
    else:
        print(f"评论区建议：{'关闭' if no_comments else '开启'}\n")

    slides = []
    cover_title = ""
    if not comments_only:
        # Step 1: LLM 生成内容
        print("─" * 45)
        print("Step 1/3: 生成文案")
        print("─" * 45)
        try:
            result = format_text_to_slides(raw_text)
            slides = result["slides"]
            cover_title = result.get("cover_title", "")
        except Exception as e:
            print(f"\nLLM 调用失败：{e}")
            sys.exit(1)

    paths = []
    if not comments_only:
        # Step 2: 渲染图片
        print("\n" + "─" * 45)
        print(f"Step 2/3: 渲染 {len(slides) + 1} 张图片")
        print("─" * 45)
        try:
            out_dir = os.path.join(OUTPUT_BASE, folder_name)
            os.makedirs(out_dir, exist_ok=True)

            # 首图：使用 LLM 生成的封面标题，fallback 到第一张 slide 标题
            first_slide = slides[0]
            final_cover_title = cover_title if cover_title else first_slide.get("title", "分享一些干货")

            img = render_cover(final_cover_title)
            cover_path = os.path.join(out_dir, "slide_00_cover.png")
            img.save(cover_path)
            paths.append(cover_path)
            print(f"  OK 封面 [{final_cover_title}] -> {cover_path}")

            # 内容页
            content_paths = generate_images(slides, folder_name)
            paths.extend(content_paths)
        except Exception as e:
            print(f"\n图片生成失败：{e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    # Step 2.5: 生成纯干货版本（保存到 ixnd 文件夹）
    if not comments_only:
        print("\n" + "─" * 45)
        print("生成纯干货版本（用于评论区）")
        print("─" * 45)
        try:
            plain_summary = generate_plain_summary(raw_text)
            ixnd_dir = os.path.join(OUTPUT_BASE, "ixnd")
            os.makedirs(ixnd_dir, exist_ok=True)
            plain_path = os.path.join(ixnd_dir, f"{folder_name}.txt")
            with open(plain_path, "w", encoding="utf-8") as f:
                f.write(plain_summary)
            print(f"  OK 纯干货版本 -> {plain_path}")
        except Exception as e:
            print(f"\n纯干货版本生成失败（不影响图片）：{e}")

    # Step 3: 生成评论区文案
    comment_text = None
    if not no_comments:
        print("\n" + "─" * 45)
        print("生成评论区文案")
        print("─" * 45)
        try:
            # 提取slides摘要给评论生成器参考
            slides_summary = " | ".join([s.get("title", "") for s in slides]) if slides else ""
            comment_data = generate_comments(raw_text, slides_summary)
            comment_path = os.path.join(out_dir, "comments.txt")
            comment_text = save_comments(comment_data, comment_path)
        except Exception as e:
            print(f"\n评论生成失败（不影响图片）：{e}")

    # 完成
    print(f"\n{'═'*45}")
    print("完成！")
    print(f"{'═'*45}")
    print(f"\n输出目录：{out_dir}")
    if paths:
        print(f"  - 图片：{len(paths)} 张")
    if comment_text:
        print("  - comments.txt（评论区文案）")

    # 预览评论区内容
    if comment_text:
        print(f"\n{'─'*45}")
        print("评论区文案：")
        print("─" * 45)
        print(comment_text)
        print("─" * 45)

    # 打开输出文件夹
    open_folder(out_dir)


if __name__ == "__main__":
    main()
