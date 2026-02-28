"""抖音视频搜索模块 — 先访问首页获取会话，再搜索"""

import json
import time
import random
import urllib.parse

from .base import BaseSearcher, SearchResult


class DouyinSearcher(BaseSearcher):
    """抖音视频搜索器（Playwright 方案 + 首页预热 + DOM 兜底）"""

    platform_name = "douyin"

    def search(self, keyword: str, max_results: int = 10) -> list[SearchResult]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("错误: 需要安装 playwright")
            print("运行: pip install playwright && python -m playwright install chromium")
            return []

        from utils.stealth import create_stealth_context

        collected_data = []

        def handle_response(response):
            """拦截搜索结果 API 响应"""
            url = response.url
            if any(kw in url for kw in ["search/item", "general/search", "/aweme/v1/"]):
                try:
                    body = response.body()
                    data = json.loads(body)
                    collected_data.append(data)
                except Exception:
                    pass

        results = []
        try:
            with sync_playwright() as p:
                browser, context = create_stealth_context(
                    p, cookie_str=self.cookie, domain=".douyin.com",
                    headless=False,
                )
                page = context.new_page()
                page.on("response", handle_response)

                # === 策略1: 先访问首页，让 Cookie / 会话建立，再导航到搜索页 ===
                print(f"  抖音搜索: 正在预热会话...")
                try:
                    page.goto("https://www.douyin.com/", wait_until="load", timeout=20000)
                except Exception:
                    pass
                time.sleep(5)

                # 检查是否在验证码页面
                is_captcha = self._is_captcha_page(page)
                if is_captcha:
                    print("  抖音首页遇到验证码，尝试等待...")
                    time.sleep(5)
                    is_captcha = self._is_captcha_page(page)

                if not is_captcha:
                    # 首页正常，使用搜索框搜索（模拟用户行为，比直接 URL 跳转更不容易触发验证码）
                    print(f"  抖音搜索: 通过搜索框搜索 '{keyword}'...")
                    results = self._search_via_input(page, keyword, max_results, collected_data)
                else:
                    print("  抖音首页仍有验证码，尝试直接访问搜索 URL...")
                    # 直接尝试搜索 URL
                    search_url = f"https://www.douyin.com/search/{urllib.parse.quote(keyword)}?type=video"
                    try:
                        page.goto(search_url, wait_until="load", timeout=30000)
                    except Exception:
                        pass
                    time.sleep(10)

                    if not self._is_captcha_page(page):
                        results = self._extract_results(page, keyword, max_results, collected_data)

                browser.close()

        except Exception as e:
            print(f"  抖音搜索出错: {e}")

        # 过滤无关内容
        results = self.filter_results(results, keyword)
        results = results[:max_results]
        print(f"  抖音搜索「{keyword}」: 找到 {len(results)} 个视频")
        return results

    def _search_via_input(self, page, keyword: str, max_results: int, collected_data: list) -> list[SearchResult]:
        """通过搜索框输入关键词搜索（更模拟真人行为）"""
        try:
            # 尝试点击搜索框
            search_input = page.query_selector('input[data-e2e="searchbar-input"]') \
                or page.query_selector('input[placeholder*="搜索"]') \
                or page.query_selector('#search-bar-box input') \
                or page.query_selector('input[type="search"]')

            if search_input:
                search_input.click()
                time.sleep(1)
                search_input.fill(keyword)
                time.sleep(0.5)

                # 按回车或点击搜索按钮
                search_input.press("Enter")
                time.sleep(8)

                # 点击 "视频" tab
                try:
                    video_tab = page.query_selector('span:text("视频")') \
                        or page.query_selector('[data-e2e="search-tab-video"]')
                    if video_tab:
                        video_tab.click()
                        time.sleep(3)
                except Exception:
                    pass

                return self._extract_results(page, keyword, max_results, collected_data)
            else:
                # 搜索框未找到，直接导航
                search_url = f"https://www.douyin.com/search/{urllib.parse.quote(keyword)}?type=video"
                page.goto(search_url, wait_until="load", timeout=30000)
                time.sleep(10)
                return self._extract_results(page, keyword, max_results, collected_data)

        except Exception as e:
            print(f"  搜索框方式失败: {e}")
            # 兜底：搜索框被登录弹层遮挡时，尝试直接访问搜索页
            try:
                search_url = f"https://www.douyin.com/search/{urllib.parse.quote(keyword)}?type=video"
                page.goto(search_url, wait_until="load", timeout=30000)
                time.sleep(10)
                return self._extract_results(page, keyword, max_results, collected_data)
            except Exception as fallback_err:
                print(f"  搜索页直达兜底失败: {fallback_err}")
                return []

    def _extract_results(self, page, keyword: str, max_results: int, collected_data: list) -> list[SearchResult]:
        """从当前页面提取搜索结果（API + DOM）"""
        results = []

        # 检查验证码
        if self._is_captcha_page(page):
            print("  搜索页面遇到验证码，无法获取结果")
            return results

        # 先尝试 API 拦截数据
        results = self._parse_collected(collected_data, results)

        # 如果 API 没拿到，用 DOM
        if not results:
            print("  API 拦截未获取数据，尝试从页面 DOM 解析...")
            results = self._parse_from_dom(page)

        # 滚动加载更多
        scroll_count = 0
        max_scrolls = max(max_results // 3, 10)

        while len(results) < max_results and scroll_count < max_scrolls:
            try:
                page.evaluate("window.scrollBy(0, 800)")
            except Exception:
                break
            time.sleep(random.uniform(self._delay_min, self._delay_max))
            scroll_count += 1

            new_results = self._parse_collected(collected_data, results)
            if len(new_results) > len(results):
                results = new_results
            else:
                dom_results = self._parse_from_dom(page)
                seen = {r.content_id for r in results}
                for dr in dom_results:
                    if dr.content_id not in seen:
                        results.append(dr)
                        seen.add(dr.content_id)

        return results

    @staticmethod
    def _is_captcha_page(page) -> bool:
        """检测当前页面是否为验证码页"""
        try:
            title = page.title()
            if "验证" in title or "captcha" in title.lower():
                return True
            # 检查 DOM 中是否有验证码元素
            captcha_el = page.query_selector('#captcha-verify-image') \
                or page.query_selector('[class*="captcha"]') \
                or page.query_selector('[class*="verify-wrap"]')
            return captcha_el is not None
        except Exception:
            return False

    @staticmethod
    def _parse_collected(collected_data: list, existing: list[SearchResult]) -> list[SearchResult]:
        """从拦截数据中解析搜索结果，去重"""
        seen_ids = {r.content_id for r in existing}
        results = list(existing)

        for data in collected_data:
            # 格式1: data.data 为列表
            items = data.get("data") or []
            if isinstance(items, list):
                for item in items:
                    aweme = item.get("aweme_info") or item
                    aweme_id = str(aweme.get("aweme_id", ""))
                    if not aweme_id or aweme_id in seen_ids:
                        continue
                    seen_ids.add(aweme_id)
                    stats = aweme.get("statistics", {})
                    author_info = aweme.get("author", {})
                    results.append(SearchResult(
                        platform="douyin",
                        content_id=aweme_id,
                        title=aweme.get("desc", ""),
                        url=f"https://www.douyin.com/video/{aweme_id}",
                        author=author_info.get("nickname", ""),
                        comment_count=stats.get("comment_count", 0),
                        like_count=stats.get("digg_count", 0),
                        view_count=stats.get("play_count", 0),
                    ))

            # 格式2: data.aweme_list
            aweme_list = data.get("aweme_list") or []
            for aweme in aweme_list:
                aweme_id = str(aweme.get("aweme_id", ""))
                if not aweme_id or aweme_id in seen_ids:
                    continue
                seen_ids.add(aweme_id)
                stats = aweme.get("statistics", {})
                author_info = aweme.get("author", {})
                results.append(SearchResult(
                    platform="douyin",
                    content_id=aweme_id,
                    title=aweme.get("desc", ""),
                    url=f"https://www.douyin.com/video/{aweme_id}",
                    author=author_info.get("nickname", ""),
                    comment_count=stats.get("comment_count", 0),
                    like_count=stats.get("digg_count", 0),
                    view_count=stats.get("play_count", 0),
                ))

        return results

    @staticmethod
    def _parse_from_dom(page) -> list[SearchResult]:
        """从页面 DOM 中解析搜索结果（兜底方案）"""
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
                results.append(SearchResult(
                    platform="douyin",
                    content_id=vid,
                    title=item.get("title", ""),
                    url=f"https://www.douyin.com/video/{vid}",
                    author=item.get("author", ""),
                ))

        except Exception as e:
            print(f"  抖音 DOM 解析失败: {e}")

        return results
