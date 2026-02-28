"""
第二层精筛 - LLM 深度相关性判断
筛选：高相关性、有实质性干货的内容
"""
from typing import List, Tuple, Dict, Any

from platforms.base import Content
from llm.client import LLMClient
from .rules import FilterRules


class Layer2Filter:
    """第二层 LLM 精筛器"""

    SYSTEM_PROMPT = """你是一个内容质量评估专家。请评估搜索结果与用户查询的相关性和内容价值。

评估维度:
1. 相关性: 内容是否直接回应用户的搜索意图（1-5分）
2. 实质性: 是否包含有价值的信息（经验分享、数据、案例、具体建议）
3. 内容类型: 经验分享/数据/案例/教程/讨论/无

评分标准:
- 5分: 完全相关，直接回答问题，有大量干货
- 4分: 高度相关，有实质内容
- 3分: 基本相关，有一定参考价值
- 2分: 略微相关，价值有限
- 1分: 不相关或纯广告

请对每个内容进行评估，返回严格的 JSON 数组格式。"""

    USER_PROMPT_TEMPLATE = """用户搜索: {keyword}

待评估内容:
{contents}

请评估每个内容，返回 JSON 数组，格式如下:
[
  {{
    "content_id": "xxx",
    "score": 1-5,
    "pass": true/false,
    "reason": "简短评价",
    "type": "经验分享/数据/案例/教程/讨论/无"
  }},
  ...
]

只返回 JSON 数组，不要其他内容。"""

    def __init__(self, client: LLMClient = None, rules: FilterRules = None):
        self.client = client or LLMClient()
        self.rules = rules or FilterRules.from_config()

    def filter(self, contents: List[Content], keyword: str) -> Tuple[List[Content], List[Content]]:
        """
        执行 LLM 精筛

        Args:
            contents: 待筛选内容列表（通常是 Layer1 通过的）
            keyword: 搜索关键词

        Returns:
            (passed, rejected) - 通过的内容和被拒绝的内容
        """
        if not contents:
            return [], []

        if not self.client.is_configured():
            print("    [!] LLM 未配置，跳过精筛")
            # 未配置时全部通过
            for c in contents:
                c.layer2_pass = True
                c.layer2_score = 0
                c.layer2_reason = "LLM未配置，自动通过"
            return contents, []

        passed = []
        rejected = []

        # 批量处理
        for i in range(0, len(contents), self.rules.batch_size):
            batch = contents[i:i + self.rules.batch_size]
            evaluations = self._evaluate_batch(batch, keyword)

            for content, eval_result in zip(batch, evaluations):
                score = eval_result.get('score', 0)
                is_pass = eval_result.get('pass', False)

                # 检查是否满足最低分数
                if score >= self.rules.llm_min_score and is_pass:
                    content.layer2_pass = True
                    passed.append(content)
                else:
                    content.layer2_pass = False
                    rejected.append(content)

                content.layer2_score = score
                content.layer2_reason = eval_result.get('reason', '')
                content.layer2_type = eval_result.get('type', '')

        return passed, rejected

    def _evaluate_batch(self, batch: List[Content], keyword: str) -> List[Dict[str, Any]]:
        """批量评估内容"""
        # 构建内容描述
        content_text = "\n\n".join([
            f"[{c.content_id}]\n"
            f"标题: {c.title}\n"
            f"作者: {c.author}\n"
            f"描述: {(c.description or '')[:200]}\n"
            f"点赞: {c.likes} | 评论: {c.comments} | 播放: {c.views}"
            for c in batch
        ])

        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            keyword=keyword,
            contents=content_text
        )

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        try:
            result = self.client.chat_json(messages, temperature=0.3)

            # 确保结果是列表
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                return [result]
            else:
                raise ValueError(f"意外的响应格式: {type(result)}")

        except Exception as e:
            print(f"    [!] LLM 评估失败: {e}")
            # 失败时返回默认通过
            return [
                {
                    'content_id': c.content_id,
                    'score': 3,
                    'pass': True,
                    'reason': '评估失败，默认通过',
                    'type': '未知'
                }
                for c in batch
            ]

    def evaluate_single(self, content: Content, keyword: str) -> Dict[str, Any]:
        """评估单个内容"""
        results = self._evaluate_batch([content], keyword)
        return results[0] if results else {
            'score': 0,
            'pass': False,
            'reason': '评估失败',
            'type': ''
        }
