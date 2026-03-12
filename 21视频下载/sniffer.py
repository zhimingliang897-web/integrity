#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网页视频嗅探器
专门解决：只给一个大网页链接，找不到视频真实下载地址（如 NTU Learn 视频）的问题。
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from typing import List

def install_dependencies():
    """检查并安装 Playwright"""
    try:
        import playwright
        return
    except ImportError:
        print("首次使用嗅探功能，正在安装核心依赖 playwright...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "playwright", "-q"], check=True)
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            print("✓ playwright 安装成功！")
        except subprocess.CalledProcessError as e:
            print(f"✗ 安装核心依赖失败: {e}")
            print("请手动执行: pip install playwright && playwright install chromium")
            sys.exit(1)

# ── 视频特征匹配（增强 NTU 支持）────────────────────────────────────────
VIDEO_PATTERNS = [
    r'\.(m3u8|mp4|webm|ts|m4v|flv)(\?|#|$)',
    r'/manifest(\.f4m|/video)',
    r'/playlist\b',
    r'master\.m3u8',
    r'chunklist.*?\.m3u8',
    r'/kaltura.*/p/',           # Kaltura 特征（NTU 常用）
    r'/delivery.*video',         # Kaltura delivery
    r'videoplayback',
    r'media\..*?\.mp4',
    r'chunk.*\.m4v',
    r'panopto\.com.*delivery',   # Panopto 特征（NTU 常用）
    r'ntu\.edu\.sg.*\.m3u8',     # NTU 域名的 m3u8
    r'ntu\.edu\.sg.*\.mp4',      # NTU 域名的 mp4
]

IGNORE_PATTERNS = [
    r'thumbnail', r'poster', r'pixel', r'analytics', r'tracking', 
    r'\.jpg', r'\.png', r'\.gif', r'\.webp', r'favicon', r'\.css', r'\.js'
]

def is_video_url(url: str) -> bool:
    # 过滤掉图片等
    for ig in IGNORE_PATTERNS:
        if re.search(ig, url, re.IGNORECASE):
            return False
    # 匹配视频
    for pat in VIDEO_PATTERNS:
        if re.search(pat, url, re.IGNORECASE):
            return True
    return False

def extract_video_from_page(url: str) -> List[str]:
    """使用浏览器模拟打开大链接，窃听网络请求，找出所有真实视频地址"""
    install_dependencies()
    from playwright.sync_api import sync_playwright

    found_videos = []

    print(f"\n[🚀 启动嗅探] 正在打开一个真实的浏览器...")
    print(f"-> 网址: {url[:80]}...")

    with sync_playwright() as p:
        # headless=False: 必须弹出浏览器让用户手动操作
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        def handle_request(request):
            req_url = request.url
            if is_video_url(req_url) and req_url not in found_videos:
                found_videos.append(req_url)
                print(f"\n[🎯 抓到了！]")
                print(f"-> {req_url}")

        page.on("request", handle_request)

        print("\n=======================================================")
        print("👉 步骤 1: 浏览器已打开！如果跳出登录界面，请手动完成账号登录。")
        print("👉 步骤 2: 登录进网页后，找到你要下的那个视频，务必【鼠标点击播放键】！")
        print("           (哪怕视频卡住或者黑屏，只要你点播放，真实地址就会暴露)")
        print("👉 步骤 3: 只要看见控制台提示 [🎯 抓到了！]，你就可以随手关掉浏览器了。")
        print("=======================================================\n")
        
        try:
            # wait_until="commit" 非常关键，意思是只要服务器一响应就放过，不苦等某些卡死的网课页面加载完全
            page.goto(url, wait_until="commit", timeout=60000)
        except Exception as e:
            # 即使 goto 报错（比如超时），只要浏览器没关，我们一样抓请求！
            print(f"[⚠️ 提示] 网页加载较慢，但我仍在持续监听... 请在弹出的浏览器里操作。")

        try:
            # 这里改成循环等待 300 秒（整整 5 分钟！），足够通过手机 2FA 登录和载入了
            for i in range(300):
                page.wait_for_timeout(1000)
                
                if found_videos and i % 5 == 0:
                    print("\n[✅ 已捕获到视频] 你可以随时【关闭弹出的测试浏览器】，结束监听...")
                elif not found_videos and (i + 1) % 15 == 0:
                    print(f" [⏳ 等待中 {i+1}s / 300s] 默默监听中... (只要还没出画面，就耐心等，记得登进去点播放！)")

        except Exception as e:
            # 正常关闭浏览器会触发这个，如果是用户主动关掉，属于正常现象，直接退出监听
            if "Target closed" not in str(e):
                print(f"\n[⚠️] 浏览器提前结束：{e}")

        finally:
            print("\n[⏹️ 嗅探结束] 监听停止，浏览器已关闭。")
            try:
                browser.close()
            except:
                pass

    return found_videos

def main():
    print("=" * 50)
    print("  网页视频嗅探器（专治各种“大链接”不服）")
    print("=" * 50)
    
    url = input("\n请粘贴那个带有视频网页的“大链接”:\n> ").strip()
    if not url:
        return

    real_urls = extract_video_from_page(url)

    if not real_urls:
        print("\n[😭 抱歉] 没有嗅探到视频流。")
        print("原因可能如下：")
        print("1. 你没有登录成功，网页卡住了。")
        print("2. 你【没有点击视频的播放键】(很重要！)")
        print("3. 这个网站的视频是用超强 DRM 加密的，完全不走普通流量。")
        print("这三种情况重试一次，【在网页里手动按一下播放视频，哪怕缓冲也行】！")
        return

    print(f"\n========================================")
    print(f"🎉 嗅探大成功！总共找到 {len(real_urls)} 个视频信号片段。")
    print(f"========================================")

    # 优先选择 m3u8，如果没拿到就挑 mp4
    m3u8s = [u for u in real_urls if '.m3u8' in u]
    mp4s = [u for u in real_urls if '.mp4' in u]
    best_url = (m3u8s + mp4s + real_urls)[0]

    print(f"\n🤖 推荐最佳画质流链接：\n {best_url}")

    ans = input("\n👉 是否直接发给 yt-dlp 开始下载？(y/n) [默认: y]: ").strip().lower()
    if ans == '' or ans == 'y':
        print(f"\n► 交给 yt-dlp 开始合并下载...")
        download_dir = Path(__file__).parent / "downloads"
        download_dir.mkdir(exist_ok=True)
        
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "-f", "bestvideo+bestaudio/best",
            "--merge-output-format", "mp4",
            "-o", str(download_dir / "%(title)s.%(ext)s"),
            best_url
        ]

        cookies_file = Path(__file__).parent / "cookies.txt"
        if cookies_file.exists() and cookies_file.stat().st_size > 10:
            cmd += ["--cookies", str(cookies_file)]

        try:
            subprocess.run(cmd, check=True)
            print("\n✓ 视频下载成功！全都保存在 downloads/ 目录")
        except subprocess.CalledProcessError as e:
            print(f"\n✗ 下载出错啦：{e}")
    else:
        print("\n取消自动下载。如果需要，请手动复制上面的链接。")


if __name__ == "__main__":
    main()
