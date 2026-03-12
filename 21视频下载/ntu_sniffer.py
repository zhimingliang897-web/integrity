import re
import sys
import subprocess
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("正在安装依赖...请稍候")
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    from playwright.sync_api import sync_playwright

def find_video_in_ntu(url: str):
    """
    用 Playwright 打开 NTU 的大链接，监听网络请求，拦截隐藏的 .m3u8 或 .mp4 地址
    """
    print(f"\n[🔍 嗅探中] 正在打开大链接: {url[:80]}...")
    
    found_urls = set()
    
    with sync_playwright() as p:
        # 为了保留 NTU 的登录状态，这里建议用带用户数据的浏览器
        # 注意: 这里使用普通的有头浏览器，第一次你可能需要在弹出的窗口里手工登录一下 NTU
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # 拦截所有网络请求
        def handle_request(route):
            request_url = route.request.url
            # 抓取真实视频流 (基于常见的 NTU Panopto/Kaltura 特征)
            if re.search(r'\.(m3u8|mp4|webm|ts)(\?|$)', request_url, re.IGNORECASE) or \
               'manifest/video' in request_url or \
               'master.m3u8' in request_url:
                   
                # 排除一些小图标或者广告
                if not re.search(r'thumbnail|poster|pixel', request_url, re.IGNORECASE):
                    found_urls.add(request_url)
                    print(f"\n[🎯 抓到了！] 真实视频流地址:\n{request_url}\n")
            
            route.continue_()

        # 开始拦截
        page.route("**/*", handle_request)
        
        # 跳转到页面并等待几秒钟让视频加载
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            print("[⌛ 等待] 页面已打开，正在等待视频流加载 (如果你看到NTU登录界面，请迅速登录)...")
            
            # 等待15秒，确保网页能开始请求视频。如果网页死活没有，可能要你手动点一下播放键
            page.wait_for_timeout(15000) 
        except Exception as e:
            print(f"[⚠️] 页面加载有些问题或超时: {e}")
            
        browser.close()
        
    return list(found_urls)

def download_with_ytdlp(video_url: str):
    print(f"\n[📥 下载] 使用 yt-dlp 开始下载...")
    cmd = [
        "yt-dlp",
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        video_url
    ]
    subprocess.run(cmd)

if __name__ == "__main__":
    url = input("请输入 NTU 烦人的大链接: ").strip()
    if not url:
        sys.exit()
        
    real_urls = find_video_in_ntu(url)
    
    if real_urls:
        print(f"\n共找到了 {len(real_urls)} 个视频地址！")
        # 优先选择 m3u8
        best_url = next((u for u in real_urls if '.m3u8' in u), real_urls[0])
        print(f"-> 即将下载最合适的流: {best_url[:100]}...\n")
        
        download_with_ytdlp(best_url)
    else:
        print("\n[😭 抱歉] 没有嗅探到隐藏视频流。你可以尝试把 headless=False 改在代码里打开，手动点一下网页上的播放按钮。")

