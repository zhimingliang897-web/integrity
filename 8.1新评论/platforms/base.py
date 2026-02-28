"""
平台爬虫基类定义
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import random
import time

import config


@dataclass
class Content:
    """内容数据结构（视频/笔记/帖子）"""
    platform: str
    content_id: str
    title: str
    url: str
    author: str = ""
    description: str = ""
    likes: int = 0
    comments: int = 0
    views: int = 0
    shares: int = 0
    publish_time: Optional[datetime] = None

    # 筛选状态
    layer1_pass: bool = False
    layer1_reason: str = ""
    layer2_pass: bool = False
    layer2_score: float = 0
    layer2_reason: str = ""
    layer2_type: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'platform': self.platform,
            'content_id': self.content_id,
            'title': self.title,
            'url': self.url,
            'author': self.author,
            'description': self.description,
            'likes': self.likes,
            'comments': self.comments,
            'views': self.views,
            'shares': self.shares,
            'publish_time': self.publish_time.isoformat() if self.publish_time else None,
            'layer1_pass': self.layer1_pass,
            'layer1_reason': self.layer1_reason,
            'layer2_pass': self.layer2_pass,
            'layer2_score': self.layer2_score,
            'layer2_reason': self.layer2_reason,
            'layer2_type': self.layer2_type,
        }


@dataclass
class Comment:
    """评论数据结构"""
    platform: str
    content_id: str
    comment_id: str
    username: str
    text: str
    likes: int = 0
    replies: int = 0
    create_time: Optional[datetime] = None
    ip_location: str = ""

    # 分析结果
    relevance: str = ""
    key_info: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'platform': self.platform,
            'content_id': self.content_id,
            'comment_id': self.comment_id,
            'username': self.username,
            'text': self.text,
            'likes': self.likes,
            'replies': self.replies,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'ip_location': self.ip_location,
            'relevance': self.relevance,
            'key_info': self.key_info,
        }


class BasePlatform(ABC):
    """平台爬虫基类"""

    PLATFORM_NAME: str = "base"

    def __init__(self, cookie: str = "", speed: str = None):
        self.cookie = cookie
        self.speed = speed or config.DEFAULT_SPEED
        self._delay_range = config.SPEED_PRESETS.get(self.speed, config.SPEED_PRESETS["safe"])

    def _random_delay(self):
        """随机延迟"""
        delay = random.uniform(*self._delay_range)
        time.sleep(delay)

    @abstractmethod
    def search(self, keyword: str, max_results: int = None) -> List[Content]:
        """
        搜索内容

        Args:
            keyword: 搜索关键词
            max_results: 最大结果数

        Returns:
            内容列表
        """
        pass

    @abstractmethod
    def get_comments(self, content_id: str, url: str = None,
                     max_count: int = None) -> List[Comment]:
        """
        获取评论

        Args:
            content_id: 内容ID
            url: 内容URL（部分平台需要）
            max_count: 最大评论数

        Returns:
            评论列表
        """
        pass

    def search_and_get_comments(self, keyword: str,
                                max_search: int = None,
                                max_comments: int = None) -> tuple:
        """
        搜索并获取评论（一站式）

        Args:
            keyword: 搜索关键词
            max_search: 每平台最大搜索数
            max_comments: 每内容最大评论数

        Returns:
            (contents, comments) 元组
        """
        max_search = max_search or config.DEFAULT_MAX_SEARCH
        max_comments = max_comments or config.DEFAULT_MAX_COMMENTS

        contents = self.search(keyword, max_search)
        all_comments = []

        for content in contents:
            try:
                comments = self.get_comments(
                    content.content_id,
                    url=content.url,
                    max_count=max_comments
                )
                all_comments.extend(comments)
                self._random_delay()
            except Exception as e:
                print(f"  [!] 获取评论失败 {content.content_id}: {e}")

        return contents, all_comments
