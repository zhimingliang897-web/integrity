"""通用 LLM 客户端，支持任意 OpenAI 兼容接口 + 流式输出"""

from openai import OpenAI


class LLMClient:
    """通用 LLM 客户端"""

    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 60):
        self.model = model
        self.client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout)

    def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """同步完整响应（用于裁判评分等场景）"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    def chat_stream(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 2000):
        """流式响应，yield 每个 token（用于辩论实时展示）"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
