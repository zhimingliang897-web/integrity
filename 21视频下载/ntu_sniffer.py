import re
import sys
import subprocess
from pathlib import Path
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("正在安装依赖...请稍候")
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    from playwright.sync_api import sync_playwright

# ── NTU 视频特征匹配（增强版）────────────────────────────────────────
VIDEO_PATTERNS = [
    r'\.(m3u8|mp4|webm|ts|m4v|flv)(\?|#|$)',
    r'/manifest(\.f4m|/video)',
    r'/playlist\b',
    r'master\.m3u8',
    r'chunklist.*?\.m3u8',
    r'/kaltura.*/p/',           # Kaltura 特征
    r'/delivery.*video',         # Kaltura delivery
    r'videoplayback',
    r'media\..*?\.mp4',
    r'chunk.*\.m4v',
    r'panopto\.com.*delivery',   # Panopto 特征
    r'ntu\.edu\.sg.*\.m3u8',     # NTU 域名的 m3u8
]

IGNORE_PATTERNS = [
    r'thumbnail', r'poster', r'pixel', r'analytics', r'tracking', 
    r'\.jpg', r'\.png', r'\.gif', r'\.webp', r'favicon', r'\.css', r'\.js'
]

def is_video_url(url: str) -> bool:
    """判断是否为视频URL"""
    # 过滤掉图片等
    for ig in IGNORE_PATTERNS:
        if re.search(ig, url, re.IGNORECASE):
            return False
    # 匹配视频
    for pat in VIDEO_PATTERNS:
        if re.search(pat, url, re.IGNORECASE):
            return True
    return False

def find_video_in_ntu(url: str):
    """
    用 Playwright 打开 NTU 的大链接，监听网络请求，捕获隐藏的 .m3u8 或 .mp4 地址
    """
    print(f"\n[🔍 嗅探中] 正在打开大链接: {url[:80]}...")
    
    found_urls = []
    
    with sync_playwright() as p:
        # 使用有头浏览器，让用户可以手动登录
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # 监听所有网络请求（使用正确的事件监听方式）
        def handle_request(request):
            request_url = request.url
            # 使用增强的视频URL判断
            if is_video_url(request_url) and request_url not in found_urls:
                found_urls.append(request_url)
                print(f"\n[🎯 抓到了！] 真实视频流地址:")
                print(f"-> {request_url}\n")

        # 使用事件监听而不是 route
        page.on("request", handle_request)
        
        print("\n" + "=" * 60)
        print("👉 步骤 1: 浏览器已打开！如果跳出NTU登录界面，请手动完成登录。")
        print("👉 步骤 2: 登录后，找到视频，务必【点击播放按钮】！")
        print("           (即使视频卡住或黑屏，只要点播放，真实地址就会暴露)")
        print("👉 步骤 3: 看到 [🎯 抓到了！] 提示后，可以关闭浏览器。")
        print("=" * 60 + "\n")
        
        # 跳转到页面
        try:
            # 使用 commit 而不是 domcontentloaded，对慢速页面更友好
            page.goto(url, wait_until="commit", timeout=60000)
        except Exception as e:
            print(f"[⚠️ 提示] 网页加载较慢，但仍在监听... 请在浏览器里操作。")
        
        try:
            # 等待最多 5 分钟（300秒），给用户足够时间登录和操作
            for i in range(300):
                page.wait_for_timeout(1000)
                
                if found_urls and i % 5 == 0:
                    print(f"\n[✅ 已捕获 {len(found_urls)} 个视频] 你可以随时关闭浏览器...")
                elif not found_urls and (i + 1) % 15 == 0:
                    print(f" [⏳ 等待中 {i+1}s / 300s] 监听中... (记得登录并点击播放！)")
                    
        except Exception as e:
            # 用户关闭浏览器会触发这个
            if "Target closed" not in str(e):
                print(f"\n[⚠️] 浏览器提前结束：{e}")
        
        finally:
            print("\n[⏹️ 嗅探结束] 监听停止。")
            try:
                browser.close()
            except:
                pass
        
    return found_urls

def download_with_ytdlp(video_url: str):
    """使用 yt-dlp 下载视频"""
    print(f"\n[📥 下载] 使用 yt-dlp 开始下载...")
    
    download_dir = Path(__file__).parent / "downloads"
    download_dir.mkdir(exist_ok=True)
    
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "-o", str(download_dir / "%(title)s.%(ext)s"),
        video_url
    ]
    
    # 添加 cookies 支持
    cookies_file = Path(__file__).parent / "cookies.txt"
    if cookies_file.exists() and cookies_file.stat().st_size > 10:
        cmd += ["--cookies", str(cookies_file)]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✓ 视频下载成功！保存在 {download_dir} 目录")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ 下载出错：{e}")
        print("提示: 如需登录权限，请先运行 python get_cookies.py 获取 Cookie")

if __name__ == "__main__":
    print("=" * 60)
    print("  NTU 视频嗅探器（专治 NTU Learn 大链接）")
    print("=" * 60)
    
    url = input("\n请粘贴 NTU Learn 的视频页面链接:\n> ").strip()
    if not url:
        sys.exit()
        
    real_urls = find_video_in_ntu(url)
    
    if not real_urls:
        print("\n[😭 抱歉] 没有嗅探到视频流。")
        print("可能原因：")
        print("1. 你没有登录成功，网页卡住了。")
        print("2. 你【没有点击视频的播放键】(很重要！)")
        print("3. 视频使用了超强 DRM 加密。")
        print("\n请重试，在浏览器里手动点击播放按钮！")
        sys.exit()
    
    print(f"\n" + "=" * 60)
    print(f"🎉 嗅探成功！找到 {len(real_urls)} 个视频地址。")
    print("=" * 60)
    
    # 优先选择 m3u8，如果没有就选 mp4
    m3u8s = [u for u in real_urls if '.m3u8' in u]
    mp4s = [u for u in real_urls if '.mp4' in u]
    best_url = (m3u8s + mp4s + real_urls)[0]
    
    print(f"\n🤖 推荐最佳画质流链接：")
    print(f"{best_url}")
    
    # 如果找到多个，显示所有
    if len(real_urls) > 1:
        print(f"\n其他找到的地址：")
        for i, u in enumerate(real_urls[1:], 1):
            print(f"{i}. {u[:100]}...")
    
    ans = input("\n👉 是否直接用 yt-dlp 下载？(y/n) [默认: y]: ").strip().lower()
    if ans == '' or ans == 'y':
        download_with_ytdlp(best_url)
    else:
        print("\n取消下载。你可以手动复制上面的链接使用。")

