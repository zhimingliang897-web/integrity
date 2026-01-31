"""抖音评论抓取模块 — 基于 Playwright 浏览器拦截"""

import re
import time
import random
from datetime import datetime

from .base import BaseScraper

# 用于在页面中查找并滚动评论容器的 JS 脚本
SCROLL_COMMENT_JS = """() => {
    // 优先尝试已知的评论区滚动容器选择器
    const selectors = [
        '.route-scroll-container',
        '[class*="comment"][class*="container"]',
        '[class*="listContainer"]',
    ];
    for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el && el.scrollHeight > el.clientHeight + 50) {
            el.scrollTop += 800;
            return 'ok:' + sel;
        }
    }
    // 兜底：找所有可滚动的 div 并滚动
    const all = document.querySelectorAll('div');
    let scrolled = 0;
    for (const el of all) {
        const s = window.getComputedStyle(el);
        if ((s.overflowY === 'auto' || s.overflowY === 'scroll')
            && el.scrollHeight > el.clientHeight + 100) {
            el.scrollTop += 800;
            scrolled++;
        }
    }
    return scrolled > 0 ? 'ok:fallback(' + scrolled + ')' : 'none';
}"""


class DouyinScraper(BaseScraper):
    """抖音视频评论抓取器（Playwright 方案）"""

    platform_name = "douyin"

    def extract_id(self, url: str) -> str:
        """
        从抖音链接中提取视频ID (aweme_id)

        支持格式:
        - https://www.douyin.com/video/7xxxxxxxxxxxxxxxxx
        - https://www.douyin.com/jingxuan?modal_id=7xxxxxxxxxxxxxxxxx
        - https://v.douyin.com/xxxxx (短链接)
        - 纯数字视频ID
        """
        url = url.strip()

        if url.isdigit():
            return url

        match = re.search(r"video/(\d+)", url)
        if match:
            return match.group(1)

        match = re.search(r"modal_id=(\d+)", url)
        if match:
            return match.group(1)

        if "v.douyin.com" in url or "iesdouyin.com" in url:
            try:
                resp = self.session.get(url, allow_redirects=True, timeout=10)
                match = re.search(r"video/(\d+)", resp.url)
                if match:
                    return match.group(1)
                match = re.search(r"modal_id=(\d+)", resp.url)
                if match:
                    return match.group(1)
            except Exception as e:
                print(f"短链接解析失败: {e}")

        raise ValueError(f"无法从链接中提取视频ID: {url}")

    def fetch_comments(self, url: str, max_count: int = 100) -> list[dict]:
        """通过 Playwright 打开浏览器，拦截评论 API 响应来抓取评论"""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("错误: 需要安装 playwright")
            print("运行: pip install playwright && python -m playwright install chromium")
            return []

        aweme_id = self.extract_id(url)
        video_url = f"https://www.douyin.com/video/{aweme_id}"
        comments = []
        collected_data = []

        print(f"抖音视频 id={aweme_id} | 目标抓取: {max_count}")
        print(f"速度档位: {self.speed} (滚动延迟 {self._delay_min}-{self._delay_max}s)")
        print("正在启动浏览器...\n")

        def handle_response(response):
            """拦截评论 API 的响应"""
            if "comment/list" not in response.url:
                return
            try:
                data = response.json()
                collected_data.append(data)
            except Exception:
                pass

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0"
                    ),
                    viewport={"width": 1920, "height": 1080},
                )

                # 注入 Cookie
                if self.cookie:
                    cookies = []
                    for item in self.cookie.split("; "):
                        if "=" in item:
                            name, value = item.split("=", 1)
                            cookies.append({
                                "name": name.strip(),
                                "value": value.strip(),
                                "domain": ".douyin.com",
                                "path": "/",
                            })
                    context.add_cookies(cookies)

                page = context.new_page()
                page.on("response", handle_response)

                print("  正在加载页面...")
                try:
                    page.goto(video_url, wait_until="domcontentloaded", timeout=30000)
                except Exception:
                    pass

                # 等待页面和评论区渲染完成
                time.sleep(6)

                # 滚动评论容器加载更多
                scroll_count = 0
                max_scrolls = max(max_count // 5, 20)
                no_new_count = 0
                prev_total = 0

                while scroll_count < max_scrolls:
                    total = sum(len(d.get("comments") or []) for d in collected_data)

                    if total >= max_count:
                        break

                    if total == prev_total:
                        no_new_count += 1
                        if no_new_count >= 8:
                            print("  连续多次无新评论加载，停止滚动")
                            break
                    else:
                        no_new_count = 0
                    prev_total = total

                    # 滚动评论区容器（非全局页面）
                    try:
                        page.evaluate(SCROLL_COMMENT_JS)
                    except Exception:
                        break

                    delay = random.uniform(self._delay_min, self._delay_max)
                    time.sleep(delay)
                    scroll_count += 1

                    if scroll_count % 5 == 0:
                        print(f"  滚动 {scroll_count} 次 | {self._progress_bar(total, max_count)}")

                # 最终统计
                final_total = sum(len(d.get("comments") or []) for d in collected_data)
                print(f"  滚动结束 | 共拦截 {final_total} 条原始评论")

                browser.close()

        except KeyboardInterrupt:
            print(f"\n  用户中断，已拦截的数据将保留导出")

        # 解析所有拦截到的数据，去重
        seen_ids = set()
        for data in collected_data:
            for item in (data.get("comments") or []):
                if len(comments) >= max_count:
                    break

                cid = item.get("cid", "")
                if cid in seen_ids:
                    continue
                seen_ids.add(cid)

                ctime = item.get("create_time", 0)
                time_str = datetime.fromtimestamp(ctime).strftime("%Y-%m-%d %H:%M:%S") if ctime else ""

                comments.append(self._build_comment(
                    comment_id=cid,
                    username=item.get("user", {}).get("nickname", ""),
                    content=item.get("text", ""),
                    like_count=item.get("digg_count", 0),
                    reply_count=item.get("reply_comment_total", 0),
                    create_time=time_str,
                    ip_location=item.get("ip_label", ""),
                ))

        print(f"\n抓取完成，共 {len(comments)} 条评论（去重后）")
        return comments
