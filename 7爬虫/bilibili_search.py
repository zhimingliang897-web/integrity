"""
B站搜索脚本
用法: python bilibili_search.py "关键词"

每次搜索创建独立文件夹: data/20260131_153000_关键词/
"""

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

from bilibili_client import BilibiliClient

DATA_DIR = Path(__file__).parent / "data"


def fmt_num(n):
    if n >= 10000:
        return f"{n/10000:.1f}w"
    return str(n)


def save_json(data, filepath):
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] saved: {filepath}")


def save_csv(rows, headers, filepath):
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"[OK] saved: {filepath}")


def main():
    keyword = sys.argv[1] if len(sys.argv) > 1 else "Python爬虫"

    # 创建 时间戳_关键词 文件夹
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = keyword.replace("/", "_").replace("\\", "_").replace(":", "_")
    task_dir = DATA_DIR / f"{ts}_{safe_name}"
    task_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"B站搜索: {keyword}")
    print(f"保存到:  {task_dir}")
    print("=" * 60)

    client = BilibiliClient()

    # 1. 搜索
    print(f"\n[1] 搜索视频...")
    results = client.search_video(keyword, page_size=10)

    for i, v in enumerate(results, 1):
        print(f"  {i}. {v['title']}")
        print(f"     UP: {v['author']}  |  播放: {fmt_num(v['play'])}  |  BV: {v['bvid']}")

    csv_rows = [[v["title"], v["bvid"], v["author"], v["play"], v["duration"], v["description"]]
                for v in results]
    save_csv(csv_rows,
             ["title", "bvid", "author", "play", "duration", "description"],
             task_dir / "search.csv")

    client._sleep()

    # 2. 每个视频的详情 + 评论
    print(f"\n[2] 获取视频详情和评论...")
    all_info = []
    for i, v in enumerate(results):
        bvid = v["bvid"]
        if not bvid:
            continue

        print(f"  [{i+1}/{len(results)}] {bvid} ... ", end="", flush=True)
        try:
            info = client.get_video_info(bvid)
            all_info.append(info)

            client._sleep()

            comments = client.get_comments(info["aid"], count=5)
            info["top_comments"] = comments
            print(f"{info['title'][:30]}  ({len(comments)} comments)")

            client._sleep()

        except Exception as e:
            print(f"ERR: {e}")

    save_json(all_info, task_dir / "videos.json")

    print(f"\n[OK] Done. Results in: {task_dir}")


if __name__ == "__main__":
    main()
