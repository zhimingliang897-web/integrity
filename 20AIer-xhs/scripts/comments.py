#!/usr/bin/env python3
"""
单独生成评论区文案（避免阻塞主流程）

用法：
  python scripts/comments.py <文章.txt>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from config import OUTPUT_BASE
from comment_generator import generate_comments, save_comments


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 1:
        print("用法：python scripts/comments.py <文章.txt>")
        sys.exit(1)

    txt_path = os.path.abspath(args[0])
    if not os.path.isfile(txt_path):
        print(f"找不到文件：{txt_path}")
        sys.exit(1)

    folder_name = os.path.splitext(os.path.basename(txt_path))[0]
    out_dir = os.path.join(OUTPUT_BASE, folder_name)
    os.makedirs(out_dir, exist_ok=True)

    with open(txt_path, "r", encoding="utf-8") as f:
        raw_text = f.read().strip()
    if not raw_text:
        print("文件内容为空，退出。")
        sys.exit(1)

    comment_data = generate_comments(raw_text, slides_summary="")
    comment_path = os.path.join(out_dir, "comments.txt")
    text = save_comments(comment_data, comment_path)
    print(f"OK -> {comment_path}")
    print(text)


if __name__ == "__main__":
    main()

