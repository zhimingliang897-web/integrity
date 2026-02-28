"""搜索器基类 — 定义统一的内容搜索接口"""

import time
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import requests

from scrapers.base import SPEED_PROFILES


@dataclass
class SearchResult:
    """统一的搜索结果数据结构"""
    platform: str           # 平台名: bilibili / douyin / xiaohongshu
    content_id: str         # 内容ID（视频ID/笔记ID）
    title: str              # 标题
    url: str                # 完整URL（可直接传给对应的 scraper）
    author: str = ""        # 作者
    description: str = ""   # 描述/简介
    like_count: int = 0     # 点赞数
    comment_count: int = 0  # 评论数
    view_count: int = 0     # 播放/浏览数
    publish_time: str = ""  # 发布时间
    extra: dict = field(default_factory=dict)


class BaseSearcher(ABC):
    """内容搜索器基类"""

    platform_name: str = ""

    def __init__(self, cookie: str = "", speed: str = "normal"):
        self.session = requests.Session()
        self.cookie = cookie
        self.speed = speed
        self._delay_min, self._delay_max = SPEED_PROFILES.get(
            speed, SPEED_PROFILES["normal"]
        )
        self._setup_session()

    def _setup_session(self):
        """设置通用请求头"""
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })
        if self.cookie:
            self.session.headers["Cookie"] = self.cookie

    @abstractmethod
    def search(self, keyword: str, max_results: int = 10) -> list[SearchResult]:
        """
        根据关键词搜索内容

        Args:
            keyword: 搜索关键词
            max_results: 最大返回结果数

        Returns:
            SearchResult 列表
        """
        pass

    def _delay(self):
        """按当前速度档位进行随机延迟"""
        delay = random.uniform(self._delay_min, self._delay_max)
        time.sleep(delay)

    def filter_results(self, results: list[SearchResult], keyword: str) -> list[SearchResult]:
        """
        根据关键词过滤搜索结果（简单包含匹配）
        
        策略:
        1. 将关键词按空格拆分
        2. 标题必须包含拆分后的 *所有* 关键词部分 (AND 逻辑)
        3. 忽略大小写
        """
        if not keyword:
            return results
            
        filtered = []
        # 预处理关键词: 转小写，拆分，去除空串
        keywords = [k.lower() for k in keyword.split() if k.strip()]
        
        if not keywords:
            return results
            
        for r in results:
            title_lower = r.title.lower()
            # 检查是否所有关键词都在标题中
            if all(k in title_lower for k in keywords):
                filtered.append(r)
            else:
                # 某些平台标题可能为空，或者关键词在描述中？暂时只查标题
                pass
                
        print(f"  关键词过滤: {len(results)} -> {len(filtered)} (过滤掉无关内容)")
        return filtered
