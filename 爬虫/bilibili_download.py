"""
B站下载脚本 - 下载封面图和视频
用法:
  python bilibili_download.py BV1xxx BV2xxx ...       # 指定 BV 号
  python bilibili_download.py data/20260131_153000_*/  # 指定搜索结果目录 (读取 videos.json)
"""

import json
import sys
from pathlib import Path

from bilibili_client import BilibiliClient

QUALITY_NAMES = {16: "360p", 32: "480p", 64: "720p", 80: "1080p"}


def download_one(client, bvid, out_dir):
    """下载一个视频的封面 + 视频文件"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  --- {bvid} ---")

    # 获取信息
    try:
        info = client.get_video_info(bvid)
    except Exception as e:
        print(f"  [ERR] get info: {e}")
        return

    title = info["title"][:40]
    print(f"  title: {title}")

    # 下载封面
    pic_url = info.get("pic", "")
    if pic_url:
        if pic_url.startswith("//"):
            pic_url = "https:" + pic_url
        ext = pic_url.rsplit(".", 1)[-1].split("?")[0] if "." in pic_url else "jpg"
        cover_path = out_dir / f"{bvid}.{ext}"
        if cover_path.exists():
            print(f"  [SKIP] cover exists: {cover_path}")
        else:
            print(f"  downloading cover...")
            client.download_file(pic_url, cover_path)

    client._sleep()

    # 下载视频
    mp4_path = out_dir / f"{bvid}.mp4"
    if mp4_path.exists():
        print(f"  [SKIP] video exists: {mp4_path}")
        return

    try:
        cid = info.get("cid")
        if not cid:
            print(f"  [ERR] cid not found")
            return

        play = client.get_play_url(bvid, cid, qn=32)
        q = play.get("quality", 0)
        print(f"  quality: {QUALITY_NAMES.get(q, q)}  format: {play.get('format', '?')}")

        if not play["urls"]:
            print(f"  [ERR] no video url")
            return

        vurl = play["urls"][0]["url"]
        size_mb = play["urls"][0]["size"] / 1024 / 1024
        length_s = play["urls"][0]["length"] / 1000
        print(f"  size: {size_mb:.1f}MB  length: {length_s:.0f}s")

        print(f"  downloading video...")
        client.download_file(vurl, mp4_path, max_mb=100)

    except Exception as e:
        print(f"  [ERR] download: {e}")

    client._sleep()


def main():
    if len(sys.argv) < 2:
        print("usage:")
        print("  python bilibili_download.py BV1xxx BV2xxx")
        print("  python bilibili_download.py data/20260131_*/")
        return

    client = BilibiliClient()
    args = sys.argv[1:]

    # 判断参数是 BV 号还是目录
    bvids = []
    out_dir = Path(__file__).parent / "data" / "downloads"

    for arg in args:
        p = Path(arg)
        if p.is_dir():
            # 从目录中读取 videos.json
            jf = p / "videos.json"
            if jf.exists():
                with open(jf, "r", encoding="utf-8") as f:
                    videos = json.load(f)
                for v in videos:
                    bv = v.get("bvid", "")
                    if bv:
                        bvids.append(bv)
                out_dir = p / "media"
                print(f"[OK] loaded {len(bvids)} videos from {jf}")
            else:
                print(f"[ERR] {jf} not found")
        elif arg.startswith("BV"):
            bvids.append(arg)

    if not bvids:
        print("[ERR] no BV ids found")
        return

    print(f"\n{'='*60}")
    print(f"downloading {len(bvids)} videos to: {out_dir}")
    print(f"{'='*60}")

    for i, bvid in enumerate(bvids):
        print(f"\n[{i+1}/{len(bvids)}]", end="")
        download_one(client, bvid, out_dir)

    print(f"\n{'='*60}")
    print(f"Done. Files in: {out_dir}")


if __name__ == "__main__":
    main()
