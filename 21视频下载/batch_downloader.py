#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量视频下载器 - 智能版 v2.1
专门解决：一个课程页面有多个视频，想一次性全部下载的问题

核心改进：
1. 边收集边下载 - 解决 token 过期问题
2. 增强网络监听 - 同时监听 request 和 response
3. 改进 iframe 处理 - 更好地处理跨域视频
4. 添加重试机制 - 下载失败自动重试
5. 线程安全的进度保存
"""

import re
import sys
import json
import time
import subprocess
import threading
import queue
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout
except ImportError:
    print("正在安装依赖 playwright...")
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout


# ── 配置 ──────────────────────────────────────────────────────
HERE = Path(__file__).parent
DOWNLOAD_DIR = HERE / "downloads"
COOKIES_FILE = HERE / "cookies.txt"
PROGRESS_FILE = HERE / "batch_progress.json"

# 视频特征匹配
VIDEO_PATTERNS = [
    r'\.(m3u8|mp4|webm|ts|m4v|flv)(\?|#|$)',
    r'/manifest(\.f4m|/video)',
    r'/playlist\b',
    r'master\.m3u8',
    r'chunklist.*?\.m3u8',
    r'/kaltura.*/p/',
    r'/delivery.*video',
    r'videoplayback',
    r'media\..*?\.mp4',
    r'panopto\.com.*delivery',
    r'ntu\.edu\.sg.*\.m3u8',
    r'ntu\.edu\.sg.*\.mp4',
]

IGNORE_PATTERNS = [
    r'thumbnail', r'poster', r'pixel', r'analytics', r'tracking',
    r'\.jpg', r'\.png', r'\.gif', r'\.webp', r'favicon', r'\.css', r'\.js'
]


def is_video_url(url: str) -> bool:
    """判断是否为视频URL"""
    for ig in IGNORE_PATTERNS:
        if re.search(ig, url, re.IGNORECASE):
            return False
    for pat in VIDEO_PATTERNS:
        if re.search(pat, url, re.IGNORECASE):
            return True
    return False


class VideoInfo:
    """视频信息类"""
    def __init__(self, index: int, title: str = "", element_selector: str = ""):
        self.index = index
        self.title = title or f"视频_{index}"
        self.element_selector = element_selector
        self.video_urls: List[str] = []
        self.best_url: str = ""
        self.status: str = "pending"  # pending, collected, downloading, completed, failed, skipped
        self.download_path: str = ""
        self.error: str = ""
        self.retry_count: int = 0
        self.max_retries: int = 3
    
    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "title": self.title,
            "element_selector": self.element_selector,
            "video_urls": self.video_urls,
            "best_url": self.best_url,
            "status": self.status,
            "download_path": self.download_path,
            "error": self.error,
            "retry_count": self.retry_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'VideoInfo':
        video = cls(data["index"], data["title"], data["element_selector"])
        video.video_urls = data.get("video_urls", [])
        video.best_url = data.get("best_url", "")
        video.status = data.get("status", "pending")
        video.download_path = data.get("download_path", "")
        video.error = data.get("error", "")
        video.retry_count = data.get("retry_count", 0)
        return video


class BatchDownloader:
    """批量下载器 - 边收集边下载版本"""
    
    def __init__(self, page_url: str, max_concurrent: int = 3):
        self.page_url = page_url
        self.max_concurrent = max_concurrent
        self.videos: List[VideoInfo] = []
        self.found_urls_lock = threading.Lock()
        self.found_urls_buffer: Set[str] = set()
        self.progress_lock = threading.Lock()
        self.download_queue: queue.Queue = queue.Queue()
        self.download_threads: List[threading.Thread] = []
        self.stop_downloading = threading.Event()
        
    def save_progress(self):
        """线程安全的进度保存"""
        with self.progress_lock:
            data = {
                "page_url": self.page_url,
                "timestamp": datetime.now().isoformat(),
                "videos": [v.to_dict() for v in self.videos]
            }
            PROGRESS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    @classmethod
    def load_progress(cls, page_url: str) -> Optional['BatchDownloader']:
        """从文件加载进度"""
        if not PROGRESS_FILE.exists():
            return None
        
        try:
            data = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
            if data["page_url"] != page_url:
                return None
            
            downloader = cls(page_url)
            downloader.videos = [VideoInfo.from_dict(v) for v in data["videos"]]
            print(f"  ✓ 已加载之前的进度（{len(downloader.videos)} 个视频）")
            return downloader
        except Exception as e:
            print(f"  ⚠️  加载进度失败: {e}")
            return None
    
    def scan_page_for_videos(self, page: Page) -> List[VideoInfo]:
        """扫描页面，找出所有视频元素"""
        print("\n[🔍 扫描页面] 正在查找所有视频元素...")
        
        videos = []
        
        # 策略1: 查找所有 iframe（NTU Learn 常用）
        iframes = page.query_selector_all("iframe")
        print(f"  找到 {len(iframes)} 个 iframe")
        
        for i, iframe in enumerate(iframes, 1):
            src = iframe.get_attribute("src") or ""
            title = iframe.get_attribute("title") or f"iframe_{i}"
            
            # 过滤掉明显不是视频的 iframe
            if any(x in src.lower() for x in ["kaltura", "panopto", "video", "media", "player"]):
                video = VideoInfo(len(videos) + 1, title, f"iframe:nth-of-type({i})")
                videos.append(video)
                print(f"    ✓ 视频 {video.index}: {title[:50]}")
        
        # 策略2: 查找所有 video 标签
        video_tags = page.query_selector_all("video")
        print(f"  找到 {len(video_tags)} 个 <video> 标签")
        
        for i, video_tag in enumerate(video_tags, 1):
            src = video_tag.get_attribute("src") or ""
            title = f"video_tag_{len(videos) + 1}"
            video = VideoInfo(len(videos) + 1, title, f"video:nth-of-type({i})")
            videos.append(video)
            print(f"    ✓ 视频 {video.index}: {title}")
        
        # 策略3: 查找包含特定关键词的链接
        links = page.query_selector_all("a")
        for link in links:
            href = link.get_attribute("href") or ""
            text = link.inner_text()[:50] if link.inner_text() else ""
            
            if any(x in href.lower() for x in ["video", "media", "watch", "play"]) and text:
                video = VideoInfo(len(videos) + 1, text, f"a[href*='{href[:30]}']")
                videos.append(video)
                print(f"    ✓ 视频 {video.index}: {text}")
        
        if not videos:
            print("  ⚠️  未找到明显的视频元素，将尝试监听整个页面的网络请求")
        
        return videos
    
    def collect_video_urls(self, page, video: VideoInfo, timeout: int = 30):
        """收集单个视频的真实URL - 改进版"""
        print(f"\n[🎯 收集] 视频 {video.index}: {video.title[:50]}")
        
        # 清空缓冲区
        with self.found_urls_lock:
            self.found_urls_buffer.clear()
        
        try:
            # 尝试找到并点击视频元素
            if video.element_selector.startswith("iframe"):
                selector = video.element_selector
                element = page.query_selector(selector)
                
                if element:
                    # 滚动到元素可见
                    element.scroll_into_view_if_needed()
                    time.sleep(1)
                    
                    # 尝试点击 iframe 区域
                    try:
                        element.click(timeout=5000, force=True)
                        print(f"    ✓ 已点击 iframe")
                    except Exception as e:
                        print(f"    ⚠️  点击iframe失败: {e}")
                    
                    # 尝试在页面上查找播放按钮（不进入iframe）
                    time.sleep(2)
                    play_selectors = [
                        "button[aria-label*='play' i]",
                        "button[title*='play' i]",
                        "button[class*='play' i]",
                        ".play-button",
                        "[class*='PlayButton']",
                        "button.vjs-big-play-button",
                    ]
                    
                    for selector in play_selectors:
                        try:
                            buttons = page.query_selector_all(selector)
                            for btn in buttons:
                                if btn.is_visible():
                                    btn.click(timeout=2000)
                                    print(f"    ✓ 已点击播放按钮")
                                    break
                        except:
                            continue
            
            elif video.element_selector.startswith("video"):
                # 对于 video 标签，直接调用 play()
                try:
                    page.eval_on_selector(video.element_selector, "el => el.play()")
                    print(f"    ✓ 已触发播放")
                except Exception as e:
                    print(f"    ⚠️  触发播放失败: {e}")
            
            elif video.element_selector.startswith("a"):
                # 对于链接，点击它
                try:
                    element = page.query_selector(video.element_selector)
                    if element:
                        element.click()
                        print(f"    ✓ 已点击链接")
                        time.sleep(3)  # 等待页面加载
                except Exception as e:
                    print(f"    ⚠️  点击链接失败: {e}")
            
            # 等待视频URL出现
            print(f"    ⏳ 等待 {timeout} 秒收集视频流...")
            for i in range(timeout):
                time.sleep(1)
                with self.found_urls_lock:
                    if len(self.found_urls_buffer) > 0:
                        break
                if i % 5 == 0 and i > 0:
                    print(f"       等待中... {i}s")
            
            # 收集结果
            with self.found_urls_lock:
                video.video_urls = list(self.found_urls_buffer)
            
            if video.video_urls:
                # 选择最佳URL
                m3u8s = [u for u in video.video_urls if '.m3u8' in u]
                mp4s = [u for u in video.video_urls if '.mp4' in u]
                video.best_url = (m3u8s + mp4s + video.video_urls)[0]
                video.status = "collected"
                print(f"    ✅ 成功！找到 {len(video.video_urls)} 个地址")
                print(f"       最佳: {video.best_url[:80]}...")
                return True
            else:
                video.status = "failed"
                video.error = "未捕获到视频流"
                print(f"    ❌ 未捕获到视频流")
                return False
        
        except Exception as e:
            video.status = "failed"
            video.error = str(e)
            print(f"    ❌ 出错: {e}")
            return False
    
    def collect_all_videos(self):
        """收集所有视频的真实地址"""
        print("\n" + "=" * 70)
        print("  批量视频收集器")
        print("=" * 70)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            # 设置网络监听 - 同时监听 request 和 response
            def handle_request(request):
                url = request.url
                if is_video_url(url):
                    with self.found_urls_lock:
                        self.found_urls_buffer.add(url)
                        print(f"\n    [🎯 捕获 Request] {url[:100]}...")
            
            def handle_response(response):
                url = response.url
                if is_video_url(url):
                    with self.found_urls_lock:
                        self.found_urls_buffer.add(url)
                        print(f"\n    [🎯 捕获 Response] {url[:100]}...")
            
            page.on("request", handle_request)
            page.on("response", handle_response)
            
            # 打开页面
            print(f"\n[🌐 打开页面] {self.page_url[:80]}...")
            try:
                page.goto(self.page_url, wait_until="commit", timeout=60000)
                print("  ✓ 页面已加载")
            except Exception as e:
                print(f"  ⚠️  页面加载较慢: {e}")
            
            # 等待用户登录
            print("\n" + "=" * 70)
            print("👉 如果需要登录，请在浏览器中完成登录")
            print("👉 登录完成后，按回车继续...")
            print("=" * 70)
            input()
            
            # 扫描页面
            if not self.videos:
                self.videos = self.scan_page_for_videos(page)
            
            if not self.videos:
                print("\n  ⚠️  未找到视频元素，将监听整个页面 60 秒")
                print("  请手动点击页面上的视频播放")
                
                for i in range(60):
                    time.sleep(1)
                    if i % 10 == 0 and i > 0:
                        print(f"    等待中... {i}s")
                
                # 创建一个通用视频对象
                if self.found_urls_buffer:
                    video = VideoInfo(1, "手动收集的视频")
                    with self.found_urls_lock:
                        video.video_urls = list(self.found_urls_buffer)
                    m3u8s = [u for u in video.video_urls if '.m3u8' in u]
                    mp4s = [u for u in video.video_urls if '.mp4' in u]
                    video.best_url = (m3u8s + mp4s + video.video_urls)[0]
                    video.status = "collected"
                    self.videos.append(video)
            else:
                # 依次收集每个视频
                print(f"\n[📋 开始收集] 共 {len(self.videos)} 个视频")
                
                for video in self.videos:
                    if video.status == "collected" or video.status == "completed":
                        print(f"\n[⏭️  跳过] 视频 {video.index} 已处理")
                        continue
                    
                    self.collect_video_urls(page, video, timeout=30)
                    self.save_progress()
                    
                    # 短暂休息
                    time.sleep(2)
            
            browser.close()
        
        # 统计结果
        collected = [v for v in self.videos if v.status == "collected"]
        failed = [v for v in self.videos if v.status == "failed"]
        
        print("\n" + "=" * 70)
        print(f"  收集完成！")
        print(f"  成功: {len(collected)} 个")
        print(f"  失败: {len(failed)} 个")
        print("=" * 70)
        
        return collected
    
    def collect_and_download_immediately(self):
        """边收集边下载 - 解决 token 过期问题"""
        print("\n" + "=" * 70)
        print("  批量视频下载器 - 边收集边下载模式")
        print("=" * 70)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            # 设置网络监听 - 同时监听 request 和 response
            def handle_request(request):
                url = request.url
                if is_video_url(url):
                    with self.found_urls_lock:
                        self.found_urls_buffer.add(url)
                        print(f"\n    [🎯 捕获 Request] {url[:100]}...")
            
            def handle_response(response):
                url = response.url
                if is_video_url(url):
                    with self.found_urls_lock:
                        self.found_urls_buffer.add(url)
                        print(f"\n    [🎯 捕获 Response] {url[:100]}...")
            
            page.on("request", handle_request)
            page.on("response", handle_response)
            
            # 打开页面
            print(f"\n[🌐 打开页面] {self.page_url[:80]}...")
            try:
                page.goto(self.page_url, wait_until="commit", timeout=60000)
                print("  ✓ 页面已加载")
            except Exception as e:
                print(f"  ⚠️  页面加载较慢: {e}")
            
            # 等待用户登录
            print("\n" + "=" * 70)
            print("👉 如果需要登录，请在浏览器中完成登录")
            print("👉 登录完成后，按回车继续...")
            print("=" * 70)
            input()
            
            # 扫描页面
            if not self.videos:
                self.videos = self.scan_page_for_videos(page)
            
            if not self.videos:
                print("\n  ⚠️  未找到视频元素，将监听整个页面")
                print("  请手动点击页面上的视频播放")
                browser.close()
                return []
            
            # 依次收集并立即下载每个视频
            print(f"\n[📋 开始处理] 共 {len(self.videos)} 个视频")
            print("  策略：收集一个，立即下载一个（避免 token 过期）")
            
            for video in self.videos:
                if video.status == "completed":
                    print(f"\n[⏭️  跳过] 视频 {video.index} 已完成")
                    continue
                
                # 收集视频URL
                success = self.collect_video_urls(page, video, timeout=30)
                
                if success:
                    # 立即下载（趁 token 还有效）
                    print(f"  ⚡ 立即下载（避免 token 过期）...")
                    self.download_video(video, retry=True)
                else:
                    print(f"  ⏭️  跳过下载（收集失败）")
                
                self.save_progress()
                
                # 短暂休息
                time.sleep(2)
            
            browser.close()
        
        # 统计结果
        completed = [v for v in self.videos if v.status == "completed"]
        failed = [v for v in self.videos if v.status == "failed"]
        
        print("\n" + "=" * 70)
        print(f"  全部完成！")
        print(f"  成功: {len(completed)} 个")
        print(f"  失败: {len(failed)} 个")
        print(f"  保存位置: {DOWNLOAD_DIR}")
        print("=" * 70)
        
        return completed
    
    def download_video(self, video: VideoInfo, retry: bool = True) -> bool:
        """下载单个视频 - 带重试机制"""
        if not video.best_url:
            return False
        
        print(f"\n[📥 下载] 视频 {video.index}: {video.title[:50]}")
        
        DOWNLOAD_DIR.mkdir(exist_ok=True)
        
        # 清理文件名
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', video.title)
        output_path = DOWNLOAD_DIR / f"{video.index:02d}_{safe_title}.mp4"
        
        # 检查是否已存在
        if output_path.exists():
            print(f"  ⏭️  文件已存在，跳过")
            video.status = "completed"
            video.download_path = str(output_path)
            return True
        
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "-f", "bestvideo+bestaudio/best",
            "--merge-output-format", "mp4",
            "-o", str(DOWNLOAD_DIR / f"{video.index:02d}_{safe_title}.%(ext)s"),
            video.best_url
        ]
        
        if COOKIES_FILE.exists():
            cmd += ["--cookies", str(COOKIES_FILE)]
        
        max_retries = video.max_retries if retry else 1
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"  🔄 重试 {attempt}/{max_retries-1}...")
                
                video.status = "downloading"
                self.save_progress()
                
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                video.status = "completed"
                video.download_path = str(output_path)
                print(f"  ✅ 完成")
                self.save_progress()
                return True
                
            except subprocess.CalledProcessError as e:
                video.retry_count = attempt + 1
                error_msg = e.stderr[-200:] if e.stderr else str(e)
                
                if attempt < max_retries - 1:
                    print(f"  ⚠️  下载失败，等待重试...")
                    time.sleep(3)
                else:
                    video.status = "failed"
                    video.error = f"下载失败 (重试{max_retries}次): {error_msg}"
                    print(f"  ❌ 失败: {video.error}")
                    self.save_progress()
                    return False
        
        return False
    
    def download_all(self, selected_indices: Optional[List[int]] = None):
        """并发下载所有视频"""
        # 筛选要下载的视频
        to_download = []
        for video in self.videos:
            if video.status != "collected":
                continue
            if selected_indices and video.index not in selected_indices:
                continue
            to_download.append(video)
        
        if not to_download:
            print("\n  ⚠️  没有可下载的视频")
            return
        
        print(f"\n[🚀 开始下载] 共 {len(to_download)} 个视频，并发数: {self.max_concurrent}")
        
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            futures = {executor.submit(self.download_video, video): video for video in to_download}
            
            for future in as_completed(futures):
                video = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"  ❌ 视频 {video.index} 下载异常: {e}")
                finally:
                    self.save_progress()
        
        # 统计结果
        completed = [v for v in to_download if v.status == "completed"]
        failed = [v for v in to_download if v.status == "failed"]
        
        print("\n" + "=" * 70)
        print(f"  下载完成！")
        print(f"  成功: {len(completed)} 个")
        print(f"  失败: {len(failed)} 个")
        print(f"  保存位置: {DOWNLOAD_DIR}")
        print("=" * 70)


def main():
    print("=" * 70)
    print("  批量视频下载器 - 智能版 v2.1")
    print("=" * 70)
    
    url = input("\n请粘贴课程页面链接（包含多个视频的页面）:\n> ").strip()
    if not url:
        return
    
    # 尝试加载之前的进度
    downloader = BatchDownloader.load_progress(url)
    
    if downloader:
        print("\n发现之前的下载进度！")
        choice = input("是否继续之前的进度？(y/n) [默认: y]: ").strip().lower()
        if choice == 'n':
            downloader = BatchDownloader(url)
    else:
        downloader = BatchDownloader(url)
    
    # 选择模式
    print("\n选择下载模式：")
    print("  1. 边收集边下载（推荐，避免 token 过期）⭐")
    print("  2. 先收集后下载（传统模式，可能遇到 token 过期）")
    
    mode = input("\n请选择 (1-2) [默认: 1]: ").strip() or "1"
    
    if mode == "1":
        # 边收集边下载模式
        downloader.collect_and_download_immediately()
    else:
        # 传统模式：先收集后下载
        # 收集视频地址
        if not any(v.status == "collected" for v in downloader.videos):
            collected = downloader.collect_all_videos()
            
            if not collected:
                print("\n  ❌ 未收集到任何视频")
                return
        else:
            collected = [v for v in downloader.videos if v.status == "collected"]
        
        # 显示收集到的视频
        print("\n" + "=" * 70)
        print("  收集到的视频列表：")
        print("=" * 70)
        for video in collected:
            status_icon = "✅" if video.status == "completed" else "⏳"
            print(f"{status_icon} [{video.index}] {video.title[:60]}")
        
        # 选择要下载的视频
        print("\n选择下载方式：")
        print("  1. 全部下载")
        print("  2. 选择部分下载")
        print("  3. 退出")
        
        choice = input("\n请选择 (1-3) [默认: 1]: ").strip() or "1"
        
        if choice == "1":
            downloader.download_all()
        elif choice == "2":
            indices_str = input("请输入要下载的视频编号（用逗号分隔，如: 1,3,5-8）: ").strip()
            indices = []
            
            for part in indices_str.split(','):
                part = part.strip()
                if '-' in part:
                    start, end = part.split('-')
                    indices.extend(range(int(start), int(end) + 1))
                else:
                    indices.append(int(part))
            
            downloader.download_all(indices)
        else:
            print("\n再见！")


if __name__ == "__main__":
    main()
