"""
搜索引擎 - 核心流程编排
"""
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from platforms import BilibiliPlatform, DouyinPlatform, XiaohongshuPlatform
from platforms.base import Content, Comment
from filters import Layer1Filter, Layer2Filter, FilterRules
from llm import LLMClient
from storage import Database
from storage.export import backup_raw_data
from .session import SearchSession

import config


class SearchEngine:
    """搜索引擎"""

    PLATFORM_MAP = {
        'bilibili': BilibiliPlatform,
        'douyin': DouyinPlatform,
        'xiaohongshu': XiaohongshuPlatform,
    }

    def __init__(self,
                 db: Database = None,
                 llm_client: LLMClient = None,
                 rules: FilterRules = None):
        self.db = db or Database(config.DB_PATH)
        self.llm_client = llm_client or LLMClient()
        self.rules = rules or FilterRules.from_config()

        self.layer1 = Layer1Filter(self.rules)
        self.layer2 = Layer2Filter(self.llm_client, self.rules)

    def search(self,
               keyword: str,
               platforms: List[str] = None,
               max_search: int = None,
               max_comments: int = None,
               on_progress: Callable[[str], None] = None) -> SearchSession:
        """
        执行搜索

        Args:
            keyword: 搜索关键词
            platforms: 平台列表，默认全部
            max_search: 每平台最大搜索数
            max_comments: 每内容最大评论数
            on_progress: 进度回调函数

        Returns:
            搜索会话
        """
        platforms = platforms or ['bilibili', 'douyin', 'xiaohongshu']
        max_search = max_search or config.DEFAULT_MAX_SEARCH
        max_comments = max_comments or config.DEFAULT_MAX_COMMENTS

        def log(msg: str):
            print(msg)
            if on_progress:
                on_progress(msg)

        # 创建会话
        session = SearchSession.create(keyword, platforms)
        log(f"\n[会话] {session.session_id} - 搜索: {keyword}")
        log(f"[平台] {', '.join(platforms)}")

        # 保存会话到数据库
        self.db.create_session(session.session_id, keyword, platforms)

        # 重置筛选器状态
        self.layer1.reset()

        # ============================================================
        # 阶段1: 多平台搜索
        # ============================================================
        log(f"\n[阶段1/4] 多平台搜索...")

        all_contents = []
        all_comments = []

        for platform in platforms:
            if platform not in self.PLATFORM_MAP:
                log(f"  [!] 未知平台: {platform}")
                continue

            platform_class = self.PLATFORM_MAP[platform]

            try:
                # 根据平台类型获取 Cookie
                if platform == 'bilibili':
                    cookie = config.BILIBILI_COOKIE
                elif platform == 'douyin':
                    cookie = config.DOUYIN_COOKIE
                elif platform == 'xiaohongshu':
                    cookie = config.XIAOHONGSHU_COOKIE
                else:
                    cookie = ""

                scraper = platform_class(cookie=cookie)

                # 小红书使用同会话模式
                if platform == 'xiaohongshu':
                    contents, comments = scraper.search_and_get_comments(
                        keyword, max_search, max_comments
                    )
                    all_contents.extend(contents)
                    all_comments.extend(comments)
                else:
                    contents = scraper.search(keyword, max_search)
                    all_contents.extend(contents)

            except Exception as e:
                log(f"  [!] {platform} 搜索失败: {e}")

        session.all_contents = all_contents
        log(f"  共搜索到 {len(all_contents)} 个内容")

        # ============================================================
        # 阶段2: Layer1 规则粗筛
        # ============================================================
        log(f"\n[阶段2/4] 规则粗筛...")

        layer1_passed, layer1_rejected = self.layer1.filter(all_contents)
        session.layer1_contents = layer1_passed
        session.rejected_contents.extend(layer1_rejected)

        log(f"  粗筛结果: {len(layer1_passed)}/{len(all_contents)} 通过")

        if layer1_rejected:
            reject_reasons = {}
            for c in layer1_rejected:
                reason = c.layer1_reason.split('(')[0]  # 取主要原因
                reject_reasons[reason] = reject_reasons.get(reason, 0) + 1
            for reason, count in reject_reasons.items():
                log(f"    - {reason}: {count}个")

        # ============================================================
        # 阶段3: Layer2 LLM 精筛
        # ============================================================
        log(f"\n[阶段3/4] LLM 精筛...")

        if layer1_passed:
            layer2_passed, layer2_rejected = self.layer2.filter(layer1_passed, keyword)
            session.layer2_contents = layer2_passed
            session.rejected_contents.extend(layer2_rejected)

            log(f"  精筛结果: {len(layer2_passed)}/{len(layer1_passed)} 通过")
        else:
            layer2_passed = []
            log(f"  无内容需要精筛")

        # ============================================================
        # 阶段4: 评论抓取
        # ============================================================
        log(f"\n[阶段4/4] 评论抓取...")

        # 对非小红书平台的内容抓取评论
        for content in layer2_passed:
            if content.platform == 'xiaohongshu':
                # 小红书评论已在搜索阶段抓取
                continue

            try:
                platform_class = self.PLATFORM_MAP.get(content.platform)
                if not platform_class:
                    continue

                if content.platform == 'bilibili':
                    cookie = config.BILIBILI_COOKIE
                elif content.platform == 'douyin':
                    cookie = config.DOUYIN_COOKIE
                else:
                    cookie = ""

                scraper = platform_class(cookie=cookie)
                comments = scraper.get_comments(
                    content.content_id,
                    url=content.url,
                    max_count=max_comments
                )
                all_comments.extend(comments)

            except Exception as e:
                log(f"  [!] 评论抓取失败 {content.content_id}: {e}")

        session.all_comments = all_comments
        log(f"  共获取 {len(all_comments)} 条评论")

        # ============================================================
        # 保存结果
        # ============================================================
        log(f"\n[保存] 写入数据库...")

        # 保存内容
        contents_data = [c.to_dict() for c in all_contents]
        self.db.insert_contents(session.session_id, contents_data)

        # 保存评论
        comments_data = [c.to_dict() for c in all_comments]
        self.db.insert_comments(session.session_id, comments_data)

        # 更新会话统计
        self.db.update_session_stats(
            session.session_id,
            total_contents=len(all_contents),
            layer1_passed=len(layer1_passed),
            layer2_passed=len(layer2_passed),
            total_comments=len(all_comments),
        )

        # 备份原始数据到 CSV
        backup_raw_data(session.session_id, contents_data, comments_data)

        session.is_completed = True

        # 打印摘要
        log(f"\n{'='*50}")
        log(f"[完成] 会话 {session.session_id}")
        log(f"  搜索内容: {len(all_contents)} 个")
        log(f"  粗筛通过: {len(layer1_passed)} 个")
        log(f"  精筛通过: {len(layer2_passed)} 个")
        log(f"  评论数量: {len(all_comments)} 条")
        log(f"{'='*50}")

        return session

    def get_session_results(self, session_id: str) -> Dict[str, Any]:
        """获取会话结果"""
        session = self.db.get_session(session_id)
        if not session:
            return None

        contents = self.db.get_contents(session_id)
        layer1_contents = self.db.get_contents(session_id, layer1_only=True)
        layer2_contents = self.db.get_contents(session_id, layer2_only=True)
        comments = self.db.get_comments(session_id)

        return {
            'session': session,
            'contents': {
                'all': contents,
                'layer1': layer1_contents,
                'layer2': layer2_contents,
            },
            'comments': comments,
        }

    def save_session(self, session_id: str, notes: str = None):
        """标记会话为已保存"""
        self.db.mark_session_saved(session_id, True, notes)

    def get_history(self, limit: int = 20) -> List[Dict]:
        """获取历史会话"""
        return self.db.get_recent_sessions(limit)
