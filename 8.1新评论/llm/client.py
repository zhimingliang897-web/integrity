"""
LLM 客户端 - OpenAI 兼容接口
"""
import json
from typing import List, Dict, Any, Optional

from openai import OpenAI

import config


class LLMClient:
    """LLM API 客户端"""

    def __init__(self,
                 base_url: str = None,
                 api_key: str = None,
                 model: str = None,
                 timeout: int = None):
        self.base_url = base_url or config.LLM_BASE_URL
        self.api_key = api_key or config.LLM_API_KEY
        self.model = model or config.LLM_MODEL
        self.timeout = timeout or config.LLM_TIMEOUT

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
        )

    def chat(self, messages: List[Dict[str, str]],
             temperature: float = 0.7,
             max_tokens: int = 4096) -> str:
        """
        发送聊天请求

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大输出 token 数

        Returns:
            模型回复内容
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"LLM API 调用失败: {e}")

    def chat_json(self, messages: List[Dict[str, str]],
                  temperature: float = 0.3) -> Any:
        """
        发送聊天请求并解析 JSON 响应

        Args:
            messages: 消息列表
            temperature: 温度参数（JSON 模式建议用较低温度）

        Returns:
            解析后的 JSON 对象
        """
        response = self.chat(messages, temperature=temperature)
        return self._parse_json(response)

    @staticmethod
    def _parse_json(text: str) -> Any:
        """解析 JSON 响应（处理 markdown 代码块）"""
        text = text.strip()

        # 移除 markdown 代码块
        if text.startswith('```'):
            lines = text.split('\n')
            # 移除首尾的 ``` 行
            lines = [l for l in lines if not l.strip().startswith('```')]
            text = '\n'.join(lines)

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 解析失败: {e}\n原始响应: {text[:500]}")

    def is_configured(self) -> bool:
        """检查是否已配置 API Key"""
        return bool(self.api_key and self.api_key.strip())
