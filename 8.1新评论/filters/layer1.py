"""
第一层粗筛 - 基于规则的快速过滤
过滤：广告、标题党、低互动、重复内容
"""
from typing import List, Tuple, Dict, Any

from platforms.base import Content
from .rules import FilterRules


class Layer1Filter:
    """第一层规则粗筛器"""

    def __init__(self, rules: FilterRules = None):
        self.rules = rules or FilterRules.from_config()
        self._seen_titles = []

    def reset(self):
        """重置状态（新会话时调用）"""
        self._seen_titles = []

    def filter(self, contents: List[Content]) -> Tuple[List[Content], List[Content]]:
        """
        执行粗筛

        Args:
            contents: 待筛选内容列表

        Returns:
            (passed, rejected) - 通过的内容和被拒绝的内容
        """
        passed = []
        rejected = []

        for content in contents:
            reason = self._check(content)

            if reason is None:
                # 通过
                content.layer1_pass = True
                content.layer1_reason = ""
                passed.append(content)
                self._seen_titles.append(content.title)
            else:
                # 拒绝
                content.layer1_pass = False
                content.layer1_reason = reason
                rejected.append(content)

        return passed, rejected

    def filter_single(self, content: Content) -> Tuple[bool, str]:
        """
        筛选单个内容

        Returns:
            (passed, reason) - 是否通过及原因
        """
        reason = self._check(content)
        if reason is None:
            content.layer1_pass = True
            self._seen_titles.append(content.title)
            return True, ""
        else:
            content.layer1_pass = False
            content.layer1_reason = reason
            return False, reason

    def _check(self, content: Content) -> str | None:
        """
        检查单个内容

        Returns:
            淘汰原因，None 表示通过
        """
        # 1. 低互动过滤
        if content.likes < self.rules.min_likes:
            return f"点赞数过低({content.likes}<{self.rules.min_likes})"

        if content.comments < self.rules.min_comments:
            return f"评论数过低({content.comments}<{self.rules.min_comments})"

        if content.views > 0 and content.views < self.rules.min_views:
            return f"播放量过低({content.views}<{self.rules.min_views})"

        # 2. 广告检测
        ad_reason = self._check_ads(content)
        if ad_reason:
            return ad_reason

        # 3. 标题党检测
        clickbait_reason = self._check_clickbait(content)
        if clickbait_reason:
            return clickbait_reason

        # 4. 重复内容检测
        duplicate_reason = self._check_duplicate(content)
        if duplicate_reason:
            return duplicate_reason

        return None

    def _check_ads(self, content: Content) -> str | None:
        """检查广告"""
        text = (content.title + " " + content.description).lower()

        for kw in self.rules.ad_keywords:
            if kw.lower() in text:
                return f"疑似广告(含'{kw}')"

        return None

    def _check_clickbait(self, content: Content) -> str | None:
        """检查标题党"""
        title = content.title.lower()

        for kw in self.rules.clickbait_keywords:
            if kw.lower() in title:
                return f"疑似标题党(含'{kw}')"

        return None

    def _check_duplicate(self, content: Content) -> str | None:
        """检查重复内容"""
        for seen_title in self._seen_titles:
            similarity = self._similarity(content.title, seen_title)
            if similarity > self.rules.duplicate_threshold:
                return f"内容重复(与'{seen_title[:30]}...'相似度{similarity:.0%})"

        return None

    @staticmethod
    def _similarity(s1: str, s2: str) -> float:
        """计算字符重叠相似度"""
        if not s1 or not s2:
            return 0.0

        set1 = set(s1)
        set2 = set(s2)

        intersection = len(set1 & set2)
        union = max(len(set1), len(set2))

        return intersection / union if union > 0 else 0.0

    def get_stats(self) -> Dict[str, Any]:
        """获取筛选统计"""
        return {
            'rules': self.rules.to_dict(),
            'seen_titles_count': len(self._seen_titles),
        }
