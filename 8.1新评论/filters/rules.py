"""
筛选规则配置
"""
from dataclasses import dataclass, field
from typing import List

import config


@dataclass
class FilterRules:
    """筛选规则配置"""

    # Layer 1 规则粗筛
    min_likes: int = 10
    min_comments: int = 5
    min_views: int = 100
    duplicate_threshold: float = 0.85

    # 广告关键词
    ad_keywords: List[str] = field(default_factory=lambda: [
        "私信", "加微", "VX", "vx", "微信", "wx", "WX",
        "优惠", "限时", "折扣", "福利", "免费领", "领取",
        "加群", "进群", "群聊", "合作", "商务",
        "咨询", "报名", "链接", "点击", "购买",
    ])

    # 标题党关键词
    clickbait_keywords: List[str] = field(default_factory=lambda: [
        "震惊", "必看", "绝了", "太强了", "99%", "90%",
        "最后一个", "第一个", "千万别", "一定要",
        "真相", "内幕", "揭秘", "曝光",
        "吓人", "恐怖", "惊呆", "泪目",
    ])

    # Layer 2 LLM 精筛
    llm_min_score: int = 3
    require_substance: bool = True
    batch_size: int = 10

    @classmethod
    def from_config(cls) -> 'FilterRules':
        """从配置文件加载规则"""
        l1 = config.LAYER1_CONFIG
        l2 = config.LAYER2_CONFIG

        return cls(
            min_likes=l1.get('min_likes', 10),
            min_comments=l1.get('min_comments', 5),
            min_views=l1.get('min_views', 100),
            duplicate_threshold=l1.get('duplicate_threshold', 0.85),
            ad_keywords=l1.get('ad_keywords', []),
            clickbait_keywords=l1.get('clickbait_keywords', []),
            llm_min_score=l2.get('min_score', 3),
            require_substance=l2.get('require_substance', True),
            batch_size=l2.get('batch_size', 10),
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'min_likes': self.min_likes,
            'min_comments': self.min_comments,
            'min_views': self.min_views,
            'duplicate_threshold': self.duplicate_threshold,
            'ad_keywords': self.ad_keywords,
            'clickbait_keywords': self.clickbait_keywords,
            'llm_min_score': self.llm_min_score,
            'require_substance': self.require_substance,
            'batch_size': self.batch_size,
        }
