"""
小红书爬虫 - 搜索 + 评论抓取
使用 Playwright 同步 API（兼容 Gradio 线程）+ 同会话策略
"""
import re
import json
import time
import random
from datetime import datetime
from typing import List, Optional, Tuple
from urllib.parse import quote

from playwright.sync_api import sync_playwright

from .base import BasePlatform, Content, Comment
from utils.stealth import create_stealth_context
import config


class XiaohongshuPlatform(BasePlatform):
    """小红书爬虫"""

    PLATFORM_NAME = "xiaohongshu"

    def __init__(self, cookie: str = None, speed: str = None):
        super().__init__(cookie or config.XIAOHONGSHU_COOKIE, speed)

    def search(self, keyword: str, max_results: int = None) -> List[Content]:
        """搜索笔记"""
        max_results = max_results or config.DEFAULT_MAX_SEARCH
        results = []
        api_results = []

        print(f"  [小红书] 搜索: {keyword}")

        def handle_response(response):
            """拦截搜索 API"""
            try:
                url = response.url
                if 'search/notes' in url or 'search_notes' in url:
                    body = response.body()
                    data = json.loads(body)
                    items = data.get('data', {}).get('items', [])
                    if isinstance(items, list):
                        api_results.extend(items)
            except:
                pass

        try:
            with sync_playwright() as p:
                browser, context = create_stealth_context(
                    p,
                    cookie_str=self.cookie,
                    domain=".xiaohongshu.com",
                    headless=False,
                )
                page = context.new_page()
                page.on("response", handle_response)

                # 先访问首页预热
                print(f"    预热会话...")
                try:
                    page.goto("https://www.xiaohongshu.com", wait_until="load", timeout=20000)
                except:
                    pass
                time.sleep(3)

                # 访问搜索页
                search_url = f"https://www.xiaohongshu.com/search_result?keyword={quote(keyword)}&source=web_search_result_notes"
                try:
                    page.goto(search_url, wait_until="load", timeout=30000)
                except:
                    pass
                time.sleep(3)

                # 滚动加载更多
                scroll_count = 0
                max_scrolls = max(3, max_results // 5)

                while len(api_results) < max_results and scroll_count < max_scrolls:
                    page.evaluate("window.scrollBy(0, 800)")
                    time.sleep(random.uniform(1, 2))
                    scroll_count += 1

                browser.close()

        except Exception as e:
            print(f"    [!] 搜索出错: {e}")

        # 解析结果
        results = self._parse_search_results(api_results, max_results)
        print(f"    找到 {len(results)} 篇笔记")
        return results

    def _parse_search_results(self, api_results: list, max_results: int) -> List[Content]:
        """解析搜索 API 结果"""
        results = []
        seen_ids = set()

        for item in api_results:
            try:
                note_card = item.get('note_card', item)
                note_id = item.get('id', '') or note_card.get('note_id', '')

                if not note_id or note_id in seen_ids:
                    continue
                seen_ids.add(note_id)

                interact_info = note_card.get('interact_info', {})

                content = Content(
                    platform=self.PLATFORM_NAME,
                    content_id=note_id,
                    title=note_card.get('display_title', note_card.get('title', '')),
                    url=f"https://www.xiaohongshu.com/explore/{note_id}",
                    author=note_card.get('user', {}).get('nickname', ''),
                    description=note_card.get('desc', ''),
                    likes=self._parse_count(interact_info.get('liked_count', 0)),
                    comments=self._parse_count(interact_info.get('comment_count', 0)),
                )
                results.append(content)

                if len(results) >= max_results:
                    break
            except:
                continue

        return results

    @staticmethod
    def _parse_count(value) -> int:
        """解析数字（处理 '1.2万' 这种格式）"""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            value = value.strip()
            if '万' in value:
                try:
                    return int(float(value.replace('万', '')) * 10000)
                except:
                    return 0
            try:
                return int(value)
            except:
                return 0
        return 0

    def get_comments(self, content_id: str, url: str = None,
                     max_count: int = None) -> List[Comment]:
        """获取笔记评论"""
        max_count = max_count or config.DEFAULT_MAX_COMMENTS
        api_comments = []

        note_url = url or f"https://www.xiaohongshu.com/explore/{content_id}"
        print(f"      获取评论: {content_id}")

        def handle_response(response):
            """拦截评论 API"""
            try:
                if 'comment/page' in response.url or 'comment/sub' in response.url:
                    body = response.body()
                    data = json.loads(body)
                    items = data.get('data', {}).get('comments', [])
                    if isinstance(items, list):
                        api_comments.extend(items)
            except:
                pass

        try:
            with sync_playwright() as p:
                browser, context = create_stealth_context(
                    p,
                    cookie_str=self.cookie,
                    domain=".xiaohongshu.com",
                    headless=False,
                )
                page = context.new_page()
                page.on("response", handle_response)

                # 先访问首页预热（避免 461 错误）
                print(f"        预热会话...")
                try:
                    page.goto("https://www.xiaohongshu.com", wait_until="load", timeout=20000)
                except:
                    pass
                time.sleep(2)

                # 访问笔记页面
                try:
                    page.goto(note_url, wait_until="load", timeout=30000)
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
        comments = self._parse_comments(api_comments, content_id, max_count)
        print(f"      获取 {len(comments)} 条评论")
        return comments

    def search_and_get_comments(self, keyword: str,
                                max_search: int = None,
                                max_comments: int = None) -> Tuple[List[Content], List[Comment]]:
        """
        搜索并获取评论（同会话模式）
        小红书需要在同一个浏览器会话中完成搜索和抓取，避免 461 错误
        """
        max_search = max_search or config.DEFAULT_MAX_SEARCH
        max_comments = max_comments or config.DEFAULT_MAX_COMMENTS

        contents = []
        all_comments = []
        api_results = []

        print(f"  [小红书] 同会话搜索: {keyword}")

        def handle_search_response(response):
            """拦截搜索 API"""
            try:
                url = response.url
                if 'search/notes' in url or 'search_notes' in url:
                    body = response.body()
                    data = json.loads(body)
                    items = data.get('data', {}).get('items', [])
                    if isinstance(items, list):
                        api_results.extend(items)
            except:
                pass

        try:
            with sync_playwright() as p:
                browser, context = create_stealth_context(
                    p,
                    cookie_str=self.cookie,
                    domain=".xiaohongshu.com",
                    headless=False,
                )
                page = context.new_page()
                page.on("response", handle_search_response)

                # 首页预热
                print(f"    预热会话...")
                try:
                    page.goto("https://www.xiaohongshu.com", wait_until="load", timeout=20000)
                except:
                    pass
                time.sleep(3)

                # 搜索
                search_url = f"https://www.xiaohongshu.com/search_result?keyword={quote(keyword)}&source=web_search_result_notes"
                try:
                    page.goto(search_url, wait_until="load", timeout=30000)
                except:
                    pass
                time.sleep(3)

                # 滚动加载搜索结果
                scroll_count = 0
                while len(api_results) < max_search and scroll_count < 5:
                    page.evaluate("window.scrollBy(0, 800)")
                    time.sleep(random.uniform(1, 2))
                    scroll_count += 1

                # 解析搜索结果
                contents = self._parse_search_results(api_results, max_search)
                print(f"    找到 {len(contents)} 篇笔记")

                # 获取每篇笔记的评论（通过点击笔记卡片）
                for i, content in enumerate(contents):
                    title_short = content.title[:30] + '...' if len(content.title or '') > 30 else content.title
                    print(f"    抓取评论 [{i+1}/{len(contents)}]: {title_short}")

                    api_comments = []

                    def comment_handler(response):
                        """拦截评论 API"""
                        try:
                            if 'comment/page' in response.url or 'comment/sub' in response.url:
                                body = response.body()
                                data = json.loads(body)
                                items = data.get('data', {}).get('comments', [])
                                if isinstance(items, list):
                                    api_comments.extend(items)
                        except:
                            pass

                    page.on("response", comment_handler)

                    try:
                        # 点击笔记卡片打开详情
                        selector = f'a[href*="{content.content_id}"]'
                        note_el = page.query_selector(selector)

                        if note_el:
                            note_el.click()
                            time.sleep(2)

                            # 滚动加载评论
                            for _ in range(max(1, max_comments // 10)):
                                page.evaluate("window.scrollBy(0, 300)")
                                time.sleep(0.8)

                            # 关闭弹窗
                            close_btn = page.query_selector('[class*="close"]')
                            if close_btn:
                                close_btn.click()
                            else:
                                page.keyboard.press('Escape')

                            time.sleep(0.5)

                    except Exception as e:
                        print(f"      [!] 评论抓取失败: {e}")

                    # 解析评论
                    comments = self._parse_comments(api_comments, content.content_id, max_comments)
                    all_comments.extend(comments)

                    page.remove_listener("response", comment_handler)
                    time.sleep(random.uniform(self._delay_min, self._delay_max))

                browser.close()

        except Exception as e:
            print(f"    [!] 同会话搜索出错: {e}")

        print(f"    总计获取 {len(all_comments)} 条评论")
        return contents, all_comments

    def _parse_comments(self, api_comments: List[dict], content_id: str,
                        max_count: int) -> List[Comment]:
        """解析评论数据"""
        comments = []
        seen_ids = set()

        for item in api_comments:
            try:
                cid = item.get('id', '')
                if cid in seen_ids:
                    continue
                seen_ids.add(cid)

                user = item.get('user_info', {})

                # 时间解析
                create_time = None
                time_str = item.get('create_time')
                if time_str:
                    try:
                        create_time = datetime.fromtimestamp(int(time_str) / 1000)
                    except:
                        pass

                comment = Comment(
                    platform=self.PLATFORM_NAME,
                    content_id=content_id,
                    comment_id=cid,
                    username=user.get('nickname', ''),
                    text=item.get('content', ''),
                    likes=item.get('like_count', 0),
                    replies=item.get('sub_comment_count', 0),
                    create_time=create_time,
                    ip_location=item.get('ip_location', ''),
                )
                comments.append(comment)

                if len(comments) >= max_count:
                    break
            except:
                continue

        return comments
