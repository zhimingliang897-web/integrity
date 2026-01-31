"""抽象基类，定义统一的评论抓取接口"""

import time
import random
from abc import ABC, abstractmethod

import requests


# 速度档位配置: (最小延迟, 最大延迟) 单位秒
SPEED_PROFILES = {
    "fast":   (0.5, 1.0),
    "normal": (1.5, 3.0),
    "slow":   (3.0, 6.0),
    "safe":   (5.0, 10.0),
}


class BaseScraper(ABC):
    """评论抓取器基类"""

    platform_name: str = ""

    def __init__(self, cookie: str = "", speed: str = "normal"):
        self.session = requests.Session()
        self.cookie = cookie
        self.speed = speed
        self._delay_min, self._delay_max = SPEED_PROFILES.get(speed, SPEED_PROFILES["normal"])
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
    def extract_id(self, url: str) -> str:
        """从 URL 中提取内容 ID（视频ID/笔记ID等）"""
        pass

    @abstractmethod
    def fetch_comments(self, url: str, max_count: int = 100) -> list[dict]:
        """抓取评论列表"""
        pass

    def _build_comment(
        self,
        comment_id: str,
        username: str,
        content: str,
        like_count: int = 0,
        reply_count: int = 0,
        create_time: str = "",
        ip_location: str = "",
    ) -> dict:
        """构造统一格式的评论字典"""
        return {
            "platform": self.platform_name,
            "comment_id": str(comment_id),
            "username": username,
            "content": content,
            "like_count": like_count,
            "reply_count": reply_count,
            "create_time": create_time,
            "ip_location": ip_location,
        }

    def _delay(self):
        """按当前速度档位进行随机延迟"""
        delay = random.uniform(self._delay_min, self._delay_max)
        time.sleep(delay)

    @staticmethod
    def _progress_bar(current: int, total: int, width: int = 30) -> str:
        """生成文本进度条"""
        if total <= 0:
            return f"[{'=' * width}] {current}"
        pct = min(current / total, 1.0)
        filled = int(width * pct)
        bar = "=" * filled + "-" * (width - filled)
        return f"[{bar}] {current}/{total} ({pct:.0%})"
