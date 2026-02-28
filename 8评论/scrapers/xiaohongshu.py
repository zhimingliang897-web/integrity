"""小红书评论抓取模块 — 基于 Playwright 浏览器拦截"""

import re
import json
import time
import random
from datetime import datetime

from .base import BaseScraper


class XiaohongshuScraper(BaseScraper):
    """小红书笔记评论抓取器（Playwright 浏览器方案 + 首页预热）"""

    platform_name = "xiaohongshu"

    def extract_id(self, url: str) -> str:
        """
        从小红书链接中提取笔记ID (note_id)

        支持格式:
        - https://www.xiaohongshu.com/explore/xxxxxxxxxxxxxxxx
        - https://www.xiaohongshu.com/explore/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx (UUID)
        - https://www.xiaohongshu.com/discovery/item/xxxxxxxxxxxxxxxx
        - https://xhslink.com/xxxxx (短链接)
        - 纯 note_id
        """
        url = url.strip()
        url = url.split("#")[0]

        if re.match(r"^[0-9a-f]{24}$", url):
            return url

        # UUID 格式
        uuid_match = re.search(
            r"(?:explore|discovery/item|note)/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", url
        )
        if uuid_match:
            return uuid_match.group(1)

        # 标准24位十六进制
        match = re.search(r"(?:explore|discovery/item|note)/([0-9a-f]{24})", url)
        if match:
            return match.group(1)

        # 短链接
        if "xhslink.com" in url:
            try:
                resp = self.session.get(url, allow_redirects=True, timeout=10)
                resolved = resp.url.split("#")[0]
                match = re.search(r"(?:explore|discovery/item|note)/([0-9a-f]{24})", resolved)
                if match:
                    return match.group(1)
            except Exception as e:
                print(f"短链接解析失败: {e}")

        raise ValueError(f"无法从链接中提取笔记ID: {url}")

    def fetch_comments(self, url: str, max_count: int = 100) -> list[dict]:
        """通过 Playwright 打开笔记页面，拦截评论 API 响应来抓取评论"""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("错误: 需要安装 playwright")
            print("运行: pip install playwright && python -m playwright install chromium")
            return []

        from utils.stealth import create_stealth_context

        if not self.cookie:
            print("警告: 小红书抓取需要提供 Cookie，请在 config.py 中配置")
            return []

        note_id = self.extract_id(url)
        note_url = f"https://www.xiaohongshu.com/explore/{note_id}"
        comments = []
        collected_data = []

        print(f"开始抓取小红书笔记 (id={note_id}) 的评论...")
        print(f"速度档位: {self.speed} (延迟 {self._delay_min}-{self._delay_max}s)")

        def handle_response(response):
            """拦截评论 API 的响应"""
            url_str = response.url
            if "comment/page" not in url_str and "comment/sub" not in url_str:
                return
            try:
                body = response.body()
                data = json.loads(body)
                collected_data.append(data)
            except Exception:
                pass

        try:
            with sync_playwright() as p:
                # 从代理池获取代理（如果有）
                proxy = self.proxy_pool.get_proxy() if self.proxy_pool else None

                browser, context = create_stealth_context(
                    p, cookie_str=self.cookie, domain=".xiaohongshu.com",
                    headless=False,
                    proxy=proxy,
                )
                page = context.new_page()
                page.on("response", handle_response)

                # === 先访问首页建立会话 ===
                print("  预热会话中...")
                try:
                    page.goto("https://www.xiaohongshu.com/explore", wait_until="load", timeout=20000)
                except Exception:
                    pass
                time.sleep(5)

                # === 再导航到笔记详情页 ===
                print(f"  加载笔记页面...")
                try:
                    page.goto(note_url, wait_until="load", timeout=30000)
                except Exception:
                    pass

                # 等待页面渲染和评论加载
                time.sleep(8)

                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass

                # 检查页面是否被重定向回首页
                current_url = page.url
                if note_id not in current_url:
                    print(f"  笔记页面加载失败（可能被重定向），尝试点击方式...")
                    # 重定向回首页了，尝试用搜索方式找到笔记
                    comments = self._fallback_search_note(page, note_id, max_count, collected_data)
                else:
                    # 页面加载成功，正常抓取
                    comments = self._scrape_from_page(page, max_count, collected_data)

                browser.close()

        except Exception as e:
            print(f"  抓取出错: {e}")

        print(f"抓取完成，共 {len(comments)} 条评论")
        return comments

    def _fallback_search_note(self, page, note_id: str, max_count: int, collected_data: list) -> list[dict]:
        """在首页通过URL导航的方式尝试加载笔记弹窗"""
        comments = []

        try:
            # 尝试在当前页面用JS方式打开笔记（模拟点击）
            # 小红书首页的笔记卡片点击会弹出笔记详情
            page.evaluate(f"""() => {{
                window.location.href = 'https://www.xiaohongshu.com/explore/{note_id}';
            }}""")
            time.sleep(8)

            current_url = page.url
            if note_id in current_url:
                print("  导航成功")
                comments = self._scrape_from_page(page, max_count, collected_data)
            else:
                print("  笔记详情页无法访问（Cookie 可能已失效或被限制）")
                print("  建议: 请在浏览器中重新登录小红书，更新 config.py 中的 XIAOHONGSHU_COOKIE")
        except Exception as e:
            print(f"  兜底方案失败: {e}")

        return comments

    def _scrape_from_page(self, page, max_count: int, collected_data: list) -> list[dict]:
        """从已加载的笔记页面中抓取评论"""
        comments = []

        # 解析已有评论数据
        comments = self._parse_comments(collected_data, comments, max_count)
        print(f"  初始加载: {len(comments)} 条评论")

        # 滚动加载更多评论
        scroll_count = 0
        max_scrolls = max(max_count // 3, 15)
        no_new_count = 0
        prev_total = len(comments)

        while len(comments) < max_count and scroll_count < max_scrolls:
            try:
                page.evaluate("""() => {
                    const selectors = [
                        '.note-scroller',
                        '[class*="comment"][class*="container"]',
                        '[class*="comments-container"]',
                        '.content-container',
                        '.note-content',
                    ];
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (el && el.scrollHeight > el.clientHeight + 50) {
                            el.scrollTop += 600;
                            return;
                        }
                    }
                    window.scrollBy(0, 600);
                }""")
            except Exception:
                break

            delay = random.uniform(self._delay_min, self._delay_max)
            time.sleep(delay)
            scroll_count += 1

            comments = self._parse_comments(collected_data, comments, max_count)

            if len(comments) == prev_total:
                no_new_count += 1
                if no_new_count >= 6:
                    print("  连续多次无新评论，停止滚动")
                    break
            else:
                no_new_count = 0
            prev_total = len(comments)

            if scroll_count % 5 == 0:
                print(f"  滚动 {scroll_count} 次 | {self._progress_bar(len(comments), max_count)}")

        return comments

    def _parse_comments(self, collected_data: list, existing: list[dict], max_count: int) -> list[dict]:
        """从拦截的 API 数据中解析评论，去重"""
        seen_ids = {c["comment_id"] for c in existing}
        comments = list(existing)

        for data in collected_data:
            if not data.get("success", False):
                continue

            data_body = data.get("data", {})
            comment_list = data_body.get("comments") or []

            for item in comment_list:
                if len(comments) >= max_count:
                    break

                cid = item.get("id", "")
                if cid in seen_ids:
                    continue
                seen_ids.add(cid)

                create_time = item.get("create_time", "")
                if isinstance(create_time, (int, float)) and create_time > 0:
                    create_time = datetime.fromtimestamp(create_time / 1000).strftime("%Y-%m-%d %H:%M:%S")

                user_info = item.get("user_info", {})

                comments.append(self._build_comment(
                    comment_id=cid,
                    username=user_info.get("nickname", ""),
                    content=item.get("content", ""),
                    like_count=item.get("like_count", 0),
                    reply_count=item.get("sub_comment_count", 0),
                    create_time=create_time,
                    ip_location=item.get("ip_location", ""),
                ))

        return comments
