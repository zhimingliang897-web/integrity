#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频下载器 - 极简版
用法:
  python main.py                    # 交互模式，粘贴URL回车
  python main.py <URL>              # 直接下载
  python main.py <URL1> <URL2> ...  # 批量下载
"""

import os
import sys
import subprocess
import re
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────────────
# 脚本所在目录
HERE = Path(__file__).parent

# 下载到哪里（改这里就行）
DOWNLOAD_DIR = HERE / "downloads"

# cookies 文件路径（可选，用于下载需要登录的视频）
COOKIES_FILE = HERE / "cookies.txt"

# ─────────────────────────────────────────────────────────────


def check_ytdlp():
    """检查 yt-dlp 是否已安装，没有就自动安装"""
    try:
        result = subprocess.run([sys.executable, "-m", "yt_dlp", "--version"], capture_output=True, text=True)
        ver = result.stdout.strip()
        print(f"  ✓ yt-dlp {ver}")
        return True
    except FileNotFoundError:
        print("  yt-dlp 未找到，正在安装...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp", "-q"], check=True)
            print("  ✓ yt-dlp 安装成功")
            return True
        except Exception as e:
            print(f"  ✗ 安装失败: {e}")
            print("  请手动运行: pip install yt-dlp")
            return False


def check_ffmpeg():
    """检查 ffmpeg 是否已安装（合并视频流必需）"""
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        # 提取版本号
        version_line = result.stdout.split('\n')[0]
        print(f"  ✓ {version_line}")
        return True
    except FileNotFoundError:
        print("  ⚠️  ffmpeg 未找到（合并视频流时需要）")
        print("  安装方法:")
        print("    macOS:   brew install ffmpeg")
        print("    Windows: 从 https://ffmpeg.org/download.html 下载")
        print("    Linux:   sudo apt install ffmpeg")
        return False


def build_cmd(url: str) -> list:
    """构建 yt-dlp 命令"""
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--no-playlist",           # 不下载整个播放列表
        "-f", "bestvideo+bestaudio/best",  # 最高画质
        "--merge-output-format", "mp4",    # 统一转成 mp4
        "-o", str(DOWNLOAD_DIR / "%(title)s.%(ext)s"),
    ]

    # 如果有 cookies 文件，使用它（可以下载 B站高清、登录后内容等）
    if COOKIES_FILE.exists() and COOKIES_FILE.stat().st_size > 10:
        cmd += ["--cookies", str(COOKIES_FILE)]

    cmd.append(url)
    return cmd


def download(url: str):
    """下载单个 URL"""
    url = url.strip()
    if not url:
        return

    print(f"\n► 开始下载: {url[:80]}{'...' if len(url) > 80 else ''}")
    print(f"  保存到: {DOWNLOAD_DIR}")

    cmd = build_cmd(url)
    try:
        subprocess.run(cmd, check=True)
        print("  ✓ 下载完成！")
    except subprocess.CalledProcessError as e:
        print(f"  ✗ 下载失败 (exit={e.returncode})")
        print("  提示: 如下载需要登录的视频，请先运行 python get_cookies.py 获取 Cookie")
    except KeyboardInterrupt:
        print("\n  已取消")


def interactive_mode():
    """交互模式：循环接收 URL"""
    print("\n  粘贴视频 URL 后按回车即可下载")
    print("  支持: B站、YouTube、抖音、微博、Twitter 等 1000+ 网站")
    print("  输入 q 退出\n")

    while True:
        try:
            raw = input("URL> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n再见！")
            break

        if not raw:
            continue
        if raw.lower() in ("q", "quit", "exit"):
            print("再见！")
            break

        # 支持同时粘贴多个 URL（空格或换行分隔）
        urls = re.split(r'[\s,]+', raw)
        urls = [u for u in urls if u.startswith("http")]

        if not urls:
            print("  ✗ 请粘贴以 http 开头的 URL")
            continue

        for url in urls:
            download(url)


def main():
    print("=" * 50)
    print("  视频下载器")
    print("=" * 50)

    # 确保下载目录存在
    DOWNLOAD_DIR.mkdir(exist_ok=True)

    # 检查依赖
    print("\n检查依赖...")
    ytdlp_ok = check_ytdlp()
    ffmpeg_ok = check_ffmpeg()
    
    if not ytdlp_ok:
        sys.exit(1)
    
    if not ffmpeg_ok:
        print("\n  提示: 没有 ffmpeg 可能无法合并某些视频流，但可以继续尝试\n")

    # 命令行模式：直接下载参数中的 URL
    if len(sys.argv) > 1:
        for url in sys.argv[1:]:
            if url.startswith("http"):
                download(url)
        return

    # 交互模式
    interactive_mode()


if __name__ == "__main__":
    main()
