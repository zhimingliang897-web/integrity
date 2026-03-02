"""
LLM客户端 - 调用阿里千问百炼平台API
"""

import json
import re
from openai import OpenAI
from typing import Optional
import yaml
from pathlib import Path


def load_config() -> dict:
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


class QwenClient:
    """千问API客户端"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        config = load_config()
        self.api_key = api_key or config['api']['api_key']
        self.model = model or config['api']['model']
        self.base_url = config['api']['base_url']

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def generate(self, prompt: str, temperature: float = 0.7) -> tuple[str, str]:
        """
        生成内容

        Args:
            prompt: 提示词
            temperature: 温度参数

        Returns:
            tuple: (生成的内容, 推理过程/reasoning_content)
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature
        )

        content = response.choices[0].message.content
        # 千问API可能没有单独的reasoning字段，这里用空字符串
        reasoning = ""

        return content, reasoning

    def generate_json(self, prompt: str, temperature: float = 0.7) -> tuple[dict, str]:
        """
        生成JSON格式的内容

        Args:
            prompt: 提示词
            temperature: 温度参数

        Returns:
            tuple: (解析后的JSON对象, 推理过程)
        """
        content, reasoning = self.generate(prompt, temperature)

        # 尝试提取JSON
        json_obj = self._extract_json(content)

        return json_obj, reasoning

    def _extract_json(self, text: str) -> dict:
        """从文本中提取JSON"""
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试提取```json ... ```块
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取{ ... }块
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"无法从响应中提取JSON: {text[:200]}...")


# 便捷函数
_client = None

def get_client() -> QwenClient:
    """获取全局客户端实例"""
    global _client
    if _client is None:
        _client = QwenClient()
    return _client


def generate_topic(category: str = "随机", phrase_count: int = 5, custom_topic: str = None) -> tuple[dict, str]:
    """
    生成选题

    Args:
        category: 分类
        phrase_count: 短语数量
        custom_topic: 自定义主题（如果提供，将基于此生成内容）

    Returns:
        tuple: (选题JSON, 推理过程)
    """
    from prompts import TOPIC_GENERATION_PROMPT, CUSTOM_TOPIC_PROMPT

    if custom_topic:
        # 使用自定义主题的prompt
        prompt = CUSTOM_TOPIC_PROMPT.format(
            custom_topic=custom_topic,
            phrase_count=phrase_count
        )
    else:
        prompt = TOPIC_GENERATION_PROMPT.format(
            category=category,
            phrase_count=phrase_count
        )

    client = get_client()
    return client.generate_json(prompt)


def generate_content(topic_json: dict) -> tuple[dict, str]:
    """
    生成文案内容

    Args:
        topic_json: 选题信息

    Returns:
        tuple: (内容JSON, 推理过程)
    """
    from prompts import CONTENT_GENERATION_PROMPT

    topic_str = json.dumps(topic_json, ensure_ascii=False, indent=2)
    prompt = CONTENT_GENERATION_PROMPT.format(topic_json=topic_str)

    client = get_client()
    return client.generate_json(prompt)


if __name__ == "__main__":
    # 测试
    print("测试选题生成...")
    topic, _ = generate_topic("餐饮美食", 5)
    print(json.dumps(topic, ensure_ascii=False, indent=2))

    print("\n测试文案生成...")
    content, _ = generate_content(topic)
    print(json.dumps(content, ensure_ascii=False, indent=2))
