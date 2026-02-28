"""OpenAI 兼容 LLM 客户端封装"""

from openai import OpenAI


class LLMClient:
    """通用 LLM 客户端，支持任意 OpenAI 兼容接口"""

    def __init__(self, base_url: str, api_key: str, model: str):
        self.model = model
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )

    def chat(self, messages: list[dict], temperature: float = 0.3) -> str:
        """
        发送对话请求并返回文本响应

        Args:
            messages: OpenAI 格式的消息列表 [{"role": "...", "content": "..."}]
            temperature: 生成温度，分析任务建议用低值

        Returns:
            模型回复的文本内容
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""
