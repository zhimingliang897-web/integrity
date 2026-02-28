"""小红书笔记搜索模块 — 基于 Playwright 浏览器拦截 + DOM 兜底

搜索 + 评论抓取共用同一个浏览器会话，避免多次建立会话被检测。
"""

import json
import time
import random
import urllib.parse
from datetime import datetime

from .base import BaseSearcher, SearchResult


class XiaohongshuSearcher(BaseSearcher):
    """小红书笔记搜索器（Playwright 方案 + 反检测 + DOM 兜底）"""

    platform_name = "xiaohongshu"

    def search(self, keyword: str, max_results: int = 10) -> list[SearchResult]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("错误: 需要安装 playwright")
            print("运行: pip install playwright && python -m playwright install chromium")
            return []

        from utils.stealth import create_stealth_context

        if not self.cookie:
            print("  警告: 小红书搜索需要提供 Cookie，请在 config.py 中配置 XIAOHONGSHU_COOKIE")
            return []

        search_url = (
            f"https://www.xiaohongshu.com/search_result"
            f"?keyword={urllib.parse.quote(keyword)}"
            f"&source=web_search_result_note"
        )
        collected_data = []

        def handle_response(response):
            """拦截搜索结果 API 响应"""
            url = response.url
            if any(pattern in url for pattern in [
                "search/notes", "search_notes",
                "api/sns/web", "web/search",
                "homefeed", "note/feed",
            ]):
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
                    p, cookie_str=self.cookie, domain=".xiaohongshu.com"
                )
                page = context.new_page()
                page.on("response", handle_response)

                print(f"  小红书搜索: 正在加载搜索页面...")
                try:
                    page.goto(search_url, wait_until="load", timeout=30000)
                except Exception:
                    pass

                time.sleep(10)

                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass

                # 先尝试 API 拦截数据
                results = self._parse_collected(collected_data, results)

                # 如果 API 拦截没数据，从 DOM 解析
                if not results:
                    print("  API 拦截未获取数据，尝试从页面 DOM 解析...")
                    results = self._parse_from_dom(page)

                # 滚动加载更多
                scroll_count = 0
                max_scrolls = max(max_results // 3, 8)

                while len(results) < max_results and scroll_count < max_scrolls:
                    try:
                        page.evaluate("window.scrollBy(0, 600)")
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

                browser.close()

        except Exception as e:
            print(f"  小红书搜索出错: {e}")

        # 过滤无关内容
        results = self.filter_results(results, keyword)
        results = results[:max_results]
        print(f"  小红书搜索「{keyword}」: 找到 {len(results)} 个笔记")
        return results

    def search_and_scrape(self, keyword: str, max_search: int = 5,
                          max_comments: int = 50) -> tuple[list[SearchResult], dict]:
        """
        在同一个浏览器中完成搜索 + 逐个打开笔记抓取评论。

        Returns:
            (search_results, comments_map) 其中 comments_map 是 {note_id: [comment_dict, ...]}
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("错误: 需要安装 playwright")
            return [], {}

        from utils.stealth import create_stealth_context

        if not self.cookie:
            print("  警告: 需要提供 Cookie")
            return [], {}

        search_url = (
            f"https://www.xiaohongshu.com/search_result"
            f"?keyword={urllib.parse.quote(keyword)}"
            f"&source=web_search_result_note"
        )
        search_data = []
        comment_data = []  # 收集评论 API 响应

        def handle_response(response):
            """拦截搜索和评论 API"""
            url = response.url
            try:
                body = response.body()
                data = json.loads(body)
            except Exception:
                return

            # 搜索结果 API
            if any(kw in url for kw in [
                "search/notes", "search_notes",
                "api/sns/web", "web/search",
                "homefeed", "note/feed",
            ]):
                search_data.append(data)

            # 评论 API
            if "comment/page" in url or "comment/sub" in url:
                comment_data.append(data)

        results = []
        comments_map = {}

        try:
            with sync_playwright() as p:
                browser, context = create_stealth_context(
                    p, cookie_str=self.cookie, domain=".xiaohongshu.com",
                    headless=False,
                )
                page = context.new_page()
                page.on("response", handle_response)

                # === 阶段1: 搜索 ===
                print(f"  小红书: 正在搜索 '{keyword}'...")
                try:
                    page.goto(search_url, wait_until="load", timeout=30000)
                except Exception:
                    pass
                time.sleep(10)

                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass

                results = self._parse_collected(search_data, results)
                if not results:
                    results = self._parse_from_dom(page)

                # 滚动获取更多
                scroll_count = 0
                # 多抓一些作为缓冲，以便过滤
                target_count = max_search * 2 if max_search < 20 else max_search + 10
                
                while len(results) < target_count and scroll_count < 8:
                    try:
                        page.evaluate("window.scrollBy(0, 600)")
                    except Exception:
                        break
                    time.sleep(random.uniform(self._delay_min, self._delay_max))
                    scroll_count += 1

                    new_results = self._parse_collected(search_data, results)
                    if len(new_results) > len(results):
                        results = new_results
                    else:
                        dom_results = self._parse_from_dom(page)
                        seen = {r.content_id for r in results}
                        for dr in dom_results:
                            if dr.content_id not in seen:
                                results.append(dr)
                                seen.add(dr.content_id)

                # 过滤无关内容
                results = self.filter_results(results, keyword)
                results = results[:max_search]
                print(f"  小红书搜索「{keyword}」: 找到 {len(results)} 个笔记")

                # === 阶段2: 逐个点击搜索结果，抓取评论 ===
                print(f"\n  小红书: 开始在同一会话中抓取评论...")

                for idx, sr in enumerate(results, 1):
                    note_id = sr.content_id
                    title_display = sr.title[:40] + "..." if len(sr.title) > 40 else sr.title
                    print(f"    [{idx}/{len(results)}] 点击打开 {title_display}")

                    comment_data.clear()

                    # 策略修改: 不直接通过 URL 导航，而是点击页面上的链接
                    # 这样更像真实用户，能避开服务端对直接访问详情页的检测
                    try:
                        # 尝试找到对应的笔记卡片并点击
                        # 1. 精确匹配 note_id 的链接
                        clicked = False
                        selectors = [
                            f'a[href*="/explore/{note_id}"]',
                            f'a[href*="{note_id}"]',
                        ]
                        
                        for sel in selectors:
                            if page.locator(sel).first.is_visible():
                                page.locator(sel).first.click()
                                clicked = True
                                break
                        
                        if not clicked:
                            print(f"      无法在页面上找到笔记卡片 (id={note_id})，跳过")
                            continue

                    except Exception as e:
                        print(f"      点击笔记失败: {e}")
                        continue

                    # 等待笔记弹窗/详情页加载
                    time.sleep(3)
                    try:
                        page.wait_for_load_state("networkidle", timeout=5000)
                    except Exception:
                        pass
                    
                    # 检查是否成功加载 (通常会有 close 按钮或者 URL 变化)
                    # 如果是弹窗模式，URL 可能变也可能不变，取决于具体版本
                    # 但我们主要依赖 comment_data 是否有数据
                    
                    # 给一点时间让 API 响应回来
                    time.sleep(random.uniform(2, 4))

                    # 解析评论
                    note_comments = self._parse_comment_data(comment_data, note_id, max_comments)

                    # 滚动加载更多评论 (在弹窗容器中滚动)
                    if len(note_comments) < max_comments:
                         scroll_count = 0
                         max_scrolls = max(max_comments // 5, 3)
                         no_new = 0
                         prev = len(note_comments)
                         
                         print(f"      初始加载 {len(note_comments)} 条，尝试滚动加载...")

                         while len(note_comments) < max_comments and scroll_count < max_scrolls:
                            try:
                                # 尝试在多种可能的容器中滚动
                                page.evaluate("""() => {
                                    const selectors = [
                                        '.note-detail-mask',     // 弹窗遮罩
                                        '.note-container',       // 笔记容器
                                        '.note-scroller',        // 滚动容器
                                        '[class*="note-detail"]',
                                        '[class*="comment"]'
                                    ];
                                    for (const sel of selectors) {
                                        const el = document.querySelector(sel);
                                        if (el) {
                                            el.scrollTop += 500;
                                        }
                                    }
                                    window.scrollBy(0, 500);
                                }""")
                            except Exception:
                                break

                            delay = random.uniform(self._delay_min, self._delay_max)
                            time.sleep(delay)
                            scroll_count += 1
                            
                            note_comments = self._parse_comment_data(comment_data, note_id, max_comments)

                            if len(note_comments) == prev:
                                no_new += 1
                                if no_new >= 3:
                                    break
                            else:
                                no_new = 0
                            prev = len(note_comments)

                    comments_map[note_id] = note_comments
                    print(f"      ->最终获取 {len(note_comments)} 条评论")

                    # 关闭弹窗/返回
                    try:
                        # 尝试点击关闭按钮 (通常是 X 图标)
                        close_btn = page.locator('.close-circle, .close-icon, [class*="close"]').first
                        if close_btn.is_visible():
                            close_btn.click()
                        else:
                            # 如果没找到关闭按钮，或者不是弹窗模式，尝试后退
                           page.go_back()
                    except Exception:
                        pass
                    
                    # 随机冷却时间，控制访问频率
                    cool_down = random.uniform(self._delay_min, self._delay_max) + 2
                    print(f"      冷却 {cool_down:.1f} 秒...")
                    time.sleep(cool_down)

                browser.close()

        except Exception as e:
            print(f"  小红书搜索抓取出错: {e}")

        return results, comments_map

    @staticmethod
    def _parse_comment_data(comment_data_list: list, note_id: str,
                            max_count: int) -> list[dict]:
        """从拦截的评论 API 数据中解析评论"""
        seen_ids = set()
        comments = []

        for data in comment_data_list:
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

                comments.append({
                    "platform": "xiaohongshu",
                    "comment_id": str(cid),
                    "username": user_info.get("nickname", ""),
                    "content": item.get("content", ""),
                    "like_count": item.get("like_count", 0),
                    "reply_count": item.get("sub_comment_count", 0),
                    "create_time": create_time,
                    "ip_location": item.get("ip_location", ""),
                })

        return comments

    @staticmethod
    def _parse_collected(collected_data: list, existing: list[SearchResult]) -> list[SearchResult]:
        """从拦截数据中解析搜索结果，去重"""
        seen_ids = {r.content_id for r in existing}
        results = list(existing)

        for data in collected_data:
            items = None
            if isinstance(data.get("data"), dict):
                items = (
                    data["data"].get("items")
                    or data["data"].get("notes")
                    or data["data"].get("note_list")
                )
            if not items and isinstance(data.get("data"), list):
                items = data["data"]
            if not items:
                continue

            for item in items:
                note_id = item.get("id", "") or item.get("note_id", "")
                if not note_id or note_id in seen_ids:
                    continue
                seen_ids.add(note_id)

                note_card = item.get("note_card", {})
                user = note_card.get("user", {}) or item.get("user", {})
                interact = note_card.get("interact_info", {}) or item.get("interact_info", {})

                def safe_int(val):
                    try:
                        return int(val)
                    except (ValueError, TypeError):
                        return 0

                title = (
                    note_card.get("display_title", "")
                    or item.get("display_title", "")
                    or item.get("title", "")
                    or note_card.get("title", "")
                )

                results.append(SearchResult(
                    platform="xiaohongshu",
                    content_id=note_id,
                    title=title,
                    url=f"https://www.xiaohongshu.com/explore/{note_id}",
                    author=user.get("nickname", "") or user.get("nick_name", ""),
                    description=note_card.get("desc", "") or item.get("desc", ""),
                    like_count=safe_int(interact.get("liked_count", 0)),
                    comment_count=safe_int(interact.get("comment_count", 0)),
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
                const links = document.querySelectorAll('a[href*="/explore/"]');
                for (const link of links) {
                    const href = link.getAttribute('href') || '';
                    const match = href.match(/\\/explore\\/([0-9a-f]{24})/);
                    if (!match) continue;
                    const noteId = match[1];

                    let title = '';
                    const card = link.closest('section')
                        || link.closest('[class*="card"]')
                        || link.closest('[class*="note"]')
                        || link;

                    if (card) {
                        const titleEl = card.querySelector('[class*="title"]')
                            || card.querySelector('.note-text')
                            || card.querySelector('span[class*="title"]')
                            || card.querySelector('p');
                        if (titleEl) title = titleEl.textContent.trim();
                    }
                    if (!title) {
                        title = link.getAttribute('title') || link.textContent.trim() || '';
                    }

                    let author = '';
                    if (card) {
                        const authorEl = card.querySelector('[class*="author"]')
                            || card.querySelector('[class*="name"]')
                            || card.querySelector('[class*="nickname"]')
                            || card.querySelector('.author-wrapper span');
                        if (authorEl) author = authorEl.textContent.trim();
                    }

                    let likeCount = '';
                    if (card) {
                        const likeEl = card.querySelector('[class*="like"]')
                            || card.querySelector('[class*="count"]');
                        if (likeEl) likeCount = likeEl.textContent.trim();
                    }

                    results.push({
                        noteId: noteId,
                        title: title.substring(0, 200),
                        author: author.substring(0, 50),
                        likeCount: likeCount,
                    });
                }
                return results;
            }""")

            for item in items:
                nid = item.get("noteId", "")
                if not nid or nid in seen_ids:
                    continue
                seen_ids.add(nid)

                like_str = item.get("likeCount", "")
                like_count = 0
                try:
                    cleaned = like_str.replace(",", "").replace(" ", "")
                    if "万" in cleaned or "w" in cleaned.lower():
                        cleaned = cleaned.replace("万", "").replace("w", "").replace("W", "")
                        like_count = int(float(cleaned) * 10000)
                    else:
                        like_count = int(cleaned) if cleaned else 0
                except (ValueError, AttributeError):
                    pass

                results.append(SearchResult(
                    platform="xiaohongshu",
                    content_id=nid,
                    title=item.get("title", ""),
                    url=f"https://www.xiaohongshu.com/explore/{nid}",
                    author=item.get("author", ""),
                    like_count=like_count,
                ))

        except Exception as e:
            print(f"  小红书 DOM 解析失败: {e}")

        return results
