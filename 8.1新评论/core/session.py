"""
搜索会话管理
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from platforms.base import Content, Comment


@dataclass
class SearchSession:
    """搜索会话"""
    session_id: str
    keyword: str
    platforms: List[str]
    created_at: datetime = field(default_factory=datetime.now)

    # 搜索结果
    all_contents: List[Content] = field(default_factory=list)
    layer1_contents: List[Content] = field(default_factory=list)
    layer2_contents: List[Content] = field(default_factory=list)
    rejected_contents: List[Content] = field(default_factory=list)

    # 评论
    all_comments: List[Comment] = field(default_factory=list)

    # 状态
    is_completed: bool = False
    is_saved: bool = False

    @classmethod
    def create(cls, keyword: str, platforms: List[str]) -> 'SearchSession':
        """创建新会话"""
        return cls(
            session_id=str(uuid.uuid4())[:8],
            keyword=keyword,
            platforms=platforms,
        )

    def get_stats(self) -> Dict[str, Any]:
        """获取会话统计"""
        return {
            'session_id': self.session_id,
            'keyword': self.keyword,
            'platforms': self.platforms,
            'created_at': self.created_at.isoformat(),
            'total_contents': len(self.all_contents),
            'layer1_passed': len(self.layer1_contents),
            'layer2_passed': len(self.layer2_contents),
            'rejected': len(self.rejected_contents),
            'total_comments': len(self.all_comments),
            'is_completed': self.is_completed,
            'is_saved': self.is_saved,
        }

    def get_contents_by_platform(self, platform: str) -> List[Content]:
        """按平台获取内容"""
        return [c for c in self.all_contents if c.platform == platform]

    def get_comments_by_content(self, content_id: str) -> List[Comment]:
        """按内容ID获取评论"""
        return [c for c in self.all_comments if c.content_id == content_id]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于存储）"""
        return {
            'session_id': self.session_id,
            'keyword': self.keyword,
            'platforms': self.platforms,
            'created_at': self.created_at.isoformat(),
            'total_contents': len(self.all_contents),
            'layer1_passed': len(self.layer1_contents),
            'layer2_passed': len(self.layer2_contents),
            'total_comments': len(self.all_comments),
            'is_completed': self.is_completed,
            'is_saved': self.is_saved,
        }
