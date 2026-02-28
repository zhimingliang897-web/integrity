"""
preview.py - 资料速览小工具

快速打印当前目录下（或指定目录下）视频文件的前几句转录文本，
以及 PDF 文件的第一页内容，帮助您快速判断文件属于哪节课。
"""

import argparse
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="速览文件夹内的视频和PDF内容")
    parser.add_argument("dir", nargs="?", default=".", help="要扫描的目录（默认当前目录）")
    args = parser.parse_args()

    scan_dir = Path(args.dir)
    if not scan_dir.exists() or not scan_dir.is_dir():
        print(f"目录不存在: {scan_dir}")
        return

    print("=" * 60)
    print(f" 开始速览目录: {scan_dir.resolve()}")
    print("=" * 60)

    # Preview PDFs
    pdfs = list(scan_dir.glob("*.pdf")) + list(scan_dir.rglob("*.pdf"))
    
    # 去重
    pdfs = list(set(pdfs))
    
    if pdfs:
        try:
            import pdfplumber
        except ImportError:
            print("⚠ 请安装 pdfplumber: pip install pdfplumber")
            pdfplumber = None

        print("\n[📚 PDF 文件速览]")
        for pdf_path in pdfs:
            print(f"\n▶ {pdf_path.name}")
            if pdfplumber:
                try:
                    with pdfplumber.open(pdf_path) as pdf:
                        if pdf.pages:
                            text = pdf.pages[0].extract_text() or ""
                            preview = text[:200].replace('\n', ' ')
                            print(f"  第一页: {preview}...")
                except Exception as e:
                    print(f"  读取失败: {e}")

    # Preview MP4s
    mp4s = list(scan_dir.glob("*.mp4")) + list(scan_dir.rglob("*.mp4"))
    mp4s = list(set(mp4s))
    
    if mp4s:
        print("\n[🎥 视频文件速览]")
        for video_path in mp4s:
            print(f"\n▶ {video_path.name}")
            possible_cache_paths = [
                Path(f"cache/{video_path.stem}.json"),
                Path(f"cache/3d/{video_path.stem}.json"),
                video_path.with_suffix(".json")
            ]
            found = False
            for cache_path in possible_cache_paths:
                if cache_path.exists():
                    try:
                        with open(cache_path, encoding="utf-8") as f:
                            data = json.load(f)
                            if data and len(data) > 0:
                                words = " ".join([seg["text"] for seg in data[:3]])
                                print(f"  前几句: {words[:150]}...")
                                found = True
                                break
                    except Exception:
                        pass
            if not found:
                print("  (尚未转录过，目前无内容，可通过 python main.py 提取。)")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
