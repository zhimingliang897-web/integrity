"""
抖音爬虫 - 搜索 + 评论抓取
使用 Playwright 同步 API（兼容 Gradio 线程）
"""
import re
import json
import time
import random
from datetime import datetime
from typing import List, Optional
from urllib.parse import quote

from playwright.sync_api import sync_playwright

from .base import BasePlatform, Content, Comment
from utils.stealth import create_stealth_context
import config


class DouyinPlatform(BasePlatform):
    """抖音爬虫"""

    PLATFORM_NAME = "douyin"

    def __init__(self, cookie: str = None, speed: str = None):
        super().__init__(cookie or config.DOUYIN_COOKIE, speed)

    def search(self, keyword: str, max_results: int = None) -> List[Content]:
        """搜索视频"""
        max_results = max_results or config.DEFAULT_MAX_SEARCH
        results = []
        api_results = []

        print(f"  [抖音] 搜索: {keyword}")

        def handle_response(response):
            """拦截搜索 API 响应"""
            try:
                url = response.url
                if 'search' in url and ('aweme' in url or 'item' in url):
                    body = response.body()
                    data = json.loads(body)
                    items = data.get('data', []) or data.get('aweme_list', [])
                    if isinstance(items, list):
                        api_results.extend(items)
            except:
                pass

        try:
            with sync_playwright() as p:
                browser, context = create_stealth_context(
                    p,
                    cookie_str=self.cookie,
                    domain=".douyin.com",
                    headless=False,
                )
                page = context.new_page()
                page.on("response", handle_response)

                # 先访问首页预热
                print(f"    预热会话...")
                try:
                    page.goto("https://www.douyin.com", wait_until="load", timeout=20000)
                except:
                    pass
                time.sleep(3)

                # 检查是否有验证码
                if self._is_captcha_page(page):
                    print("    首页遇到验证码，等待中...")
                    time.sleep(5)

                # 尝试通过搜索框搜索
                if not self._is_captcha_page(page):
                    results = self._search_via_input(page, keyword, max_results, api_results)
                else:
                    # 直接访问搜索 URL
                    print("    直接访问搜索页...")
                    search_url = f"https://www.douyin.com/search/{quote(keyword)}?type=video"
                    try:
                        page.goto(search_url, wait_until="load", timeout=30000)
                    except:
                        pass
                    time.sleep(5)
                    results = self._extract_results(page, keyword, max_results, api_results)

                browser.close()

        except Exception as e:
            print(f"    [!] 搜索出错: {e}")

        print(f"    找到 {len(results)} 个视频")
        return results

    def _search_via_input(self, page, keyword: str, max_results: int, api_results: list) -> List[Content]:
        """通过搜索框输入关键词搜索"""
        try:
            # 寻找搜索框
            search_input = (
                page.query_selector('input[data-e2e="searchbar-input"]') or
                page.query_selector('input[placeholder*="搜索"]') or
                page.query_selector('#search-bar-box input')
            )

            if search_input:
                search_input.click()
                time.sleep(0.5)
                search_input.fill(keyword)
                time.sleep(0.5)
                search_input.press("Enter")
                time.sleep(5)

                # 尝试点击"视频"标签
                try:
                    video_tab = (
                        page.query_selector('span:text("视频")') or
                        page.query_selector('[data-e2e="search-tab-video"]')
                    )
                    if video_tab:
                        video_tab.click()
                        time.sleep(2)
                except:
                    pass

                return self._extract_results(page, keyword, max_results, api_results)
            else:
                # 搜索框未找到，直接导航到搜索页
                search_url = f"https://www.douyin.com/search/{quote(keyword)}?type=video"
                page.goto(search_url, wait_until="load", timeout=30000)
                time.sleep(5)
                return self._extract_results(page, keyword, max_results, api_results)

        except Exception as e:
            print(f"    [!] 搜索框方式失败: {e}")
            # 兜底
            try:
                search_url = f"https://www.douyin.com/search/{quote(keyword)}?type=video"
                page.goto(search_url, wait_until="load", timeout=30000)
                time.sleep(5)
                return self._extract_results(page, keyword, max_results, api_results)
            except:
                return []

    def _extract_results(self, page, keyword: str, max_results: int, api_results: list) -> List[Content]:
        """从 API 拦截和 DOM 中提取结果"""
        results = []

        # 检查验证码
        if self._is_captcha_page(page):
            print("    搜索页遇到验证码")
            return results

        # 先从 API 拦截数据解析
        results = self._parse_api_results(api_results)

        # 滚动加载更多
        scroll_count = 0
        max_scrolls = max(3, max_results // 3)

        while len(results) < max_results and scroll_count < max_scrolls:
            try:
                page.evaluate("window.scrollBy(0, 800)")
            except:
                break
            time.sleep(random.uniform(self._delay_min, self._delay_max))
            scroll_count += 1

            new_results = self._parse_api_results(api_results)
            if len(new_results) > len(results):
                results = new_results

        # 如果 API 没数据，尝试从 DOM 解析
        if not results:
            print("    API 未获取数据，尝试 DOM 解析...")
            results = self._parse_dom(page)

        return results[:max_results]

    def _parse_api_results(self, api_results: list) -> List[Content]:
        """解析 API 拦截到的数据"""
        results = []
        seen_ids = set()

        for item in api_results:
            try:
                aweme = item if 'aweme_id' in item else item.get('aweme_info', item)
                aweme_id = str(aweme.get('aweme_id', ''))

                if not aweme_id or aweme_id in seen_ids:
                    continue
                seen_ids.add(aweme_id)

                statistics = aweme.get('statistics', {})
                author_info = aweme.get('author', {})

                content = Content(
                    platform=self.PLATFORM_NAME,
                    content_id=aweme_id,
                    title=aweme.get('desc', ''),
                    url=f"https://www.douyin.com/video/{aweme_id}",
                    author=author_info.get('nickname', ''),
                    description=aweme.get('desc', ''),
                    likes=statistics.get('digg_count', 0),
                    comments=statistics.get('comment_count', 0),
                    views=statistics.get('play_count', 0),
                    shares=statistics.get('share_count', 0),
                    publish_time=datetime.fromtimestamp(aweme.get('create_time', 0)) if aweme.get('create_time') else None,
                )
                results.append(content)
            except:
                continue

        return results

    def _parse_dom(self, page) -> List[Content]:
        """从 DOM 解析搜索结果"""
        results = []
        seen_ids = set()

        try:
            items = page.evaluate("""() => {
                const results = [];
                const links = document.querySelectorAll('a[href*="/video/"]');
                for (const link of links) {
                    const href = link.getAttribute('href') || '';
                    const match = href.match(/\\/video\\/(\\d+)/);
                    if (!match) continue;
                    const videoId = match[1];

                    let title = '';
                    const card = link.closest('[class*="card"]')
                        || link.closest('[class*="item"]')
                        || link.parentElement;
                    if (card) {
                        const titleEl = card.querySelector('[class*="title"]')
                            || card.querySelector('p')
                            || card.querySelector('span');
                        if (titleEl) title = titleEl.textContent.trim();
                    }
                    if (!title) {
                        title = link.textContent.trim()
                            || link.getAttribute('title') || '';
                    }

                    let author = '';
                    if (card) {
                        const authorEl = card.querySelector('[class*="author"]')
                            || card.querySelector('[class*="nickname"]')
                            || card.querySelector('[class*="name"]');
                        if (authorEl) author = authorEl.textContent.trim();
                    }

                    results.push({
                        videoId: videoId,
                        title: title.substring(0, 200),
                        author: author.substring(0, 50),
                    });
                }
                return results;
            }""")

            for item in items:
                vid = item.get("videoId", "")
                if not vid or vid in seen_ids:
                    continue
                seen_ids.add(vid)
                results.append(Content(
                    platform=self.PLATFORM_NAME,
                    content_id=vid,
                    title=item.get("title", ""),
                    url=f"https://www.douyin.com/video/{vid}",
                    author=item.get("author", ""),
                ))

        except Exception as e:
            print(f"    [!] DOM 解析失败: {e}")

        return results

    @staticmethod
    def _is_captcha_page(page) -> bool:
        """检测是否为验证码页"""
        try:
            title = page.title()
            if "验证" in title or "captcha" in title.lower():
                return True
            captcha_el = (
                page.query_selector('#captcha-verify-image') or
                page.query_selector('[class*="captcha"]') or
                page.query_selector('[class*="verify-wrap"]')
            )
            return captcha_el is not None
        except:
            return False

    def get_comments(self, content_id: str, url: str = None,
                     max_count: int = None) -> List[Comment]:
        """获取视频评论"""
        max_count = max_count or config.DEFAULT_MAX_COMMENTS
        comments = []
        api_comments = []

        video_url = url or f"https://www.douyin.com/video/{content_id}"
        print(f"      获取评论: {content_id}")

        def handle_response(response):
            """拦截评论 API"""
            try:
                if 'comment/list' in response.url or 'comment_list' in response.url:
                    body = response.body()
                    data = json.loads(body)
                    items = data.get('comments', [])
                    if isinstance(items, list):
                        api_comments.extend(items)
            except:
                pass

        try:
            with sync_playwright() as p:
                browser, context = create_stealth_context(
                    p,
                    cookie_str=self.cookie,
                    domain=".douyin.com",
                    headless=False,
                )
                page = context.new_page()
                page.on("response", handle_response)

                try:
                    page.goto(video_url, wait_until="load", timeout=30000)
                except:
                    pass
                time.sleep(3)

                # 滚动加载评论
                scroll_count = 0
                max_scrolls = max(3, max_count // 10)

                while len(api_comments) < max_count and scroll_count < max_scrolls:
                    page.evaluate("window.scrollBy(0, 500)")
                    time.sleep(random.uniform(1, 2))
                    scroll_count += 1

                browser.close()

        except Exception as e:
            print(f"      [!] 获取评论出错: {e}")

        # 解析评论
        seen_ids = set()
        for item in api_comments:
            try:
                cid = item.get('cid', '')
                if cid in seen_ids:
                    continue
                seen_ids.add(cid)

                user = item.get('user', {})

                comment = Comment(
                    platform=self.PLATFORM_NAME,
                    content_id=content_id,
                    comment_id=cid,
                    username=user.get('nickname', ''),
                    text=item.get('text', ''),
                    likes=item.get('digg_count', 0),
                    replies=item.get('reply_comment_total', 0),
                    create_time=datetime.fromtimestamp(item.get('create_time', 0)) if item.get('create_time') else None,
                    ip_location=item.get('ip_label', ''),
                )
                comments.append(comment)

                if len(comments) >= max_count:
                    break
            except:
                continue

        print(f"      获取 {len(comments)} 条评论")
        return comments
