"""
API调用模块
===========
封装所有API调用相关的功能
"""

import requests
import base64
import os
import time
from typing import Dict, Tuple

from config import (
    DASHSCOPE_API_KEY,
    OPENAI_API_KEY,
    DASHSCOPE_BASE_URL,
    OPENAI_BASE_URL,
    MODELS,
)


def get_api_config(model: str) -> Tuple[str, str, bool]:
    """
    根据模型ID获取API配置

    Args:
        model: 模型ID

    Returns:
        (base_url, api_key, is_dashscope)
    """
    dashscope_models = [m["id"] for m in MODELS["阿里云百炼"]]

    if model in dashscope_models:
        return DASHSCOPE_BASE_URL, DASHSCOPE_API_KEY, True
    else:
        return OPENAI_BASE_URL, OPENAI_API_KEY, False


def build_image_content(image_path: str) -> list:
    """
    构建图片消息内容

    Args:
        image_path: 图片文件路径

    Returns:
        消息内容列表
    """
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {'.jpg': 'jpeg', '.jpeg': 'jpeg', '.png': 'png', '.webp': 'webp'}
    mime_type = mime_map.get(ext, 'jpeg')

    return [
        {"type": "image_url", "image_url": {"url": f"data:image/{mime_type};base64,{img_b64}"}},
        {"type": "text", "text": "请用中文回答图片中的问题"}
    ]


def call_api(model: str, content, is_image: bool = False) -> Tuple[Dict, str]:
    """
    调用API并返回使用量和响应

    Args:
        model: 模型ID
        content: 文本内容或图片路径
        is_image: 是否为图片模式

    Returns:
        (usage_dict, response_text)
    """
    start_time = time.time()

    # 获取API配置
    base_url, api_key, _ = get_api_config(model)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 构建消息内容
    if is_image and isinstance(content, str):
        message_content = build_image_content(content)
    else:
        message_content = content

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": message_content}],
        "temperature": 0.7
    }

    try:
        resp = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()

        latency = (time.time() - start_time) * 1000  # 毫秒

        usage = data.get("usage", {})
        response_text = data["choices"][0]["message"]["content"]

        return {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "latency_ms": int(latency)
        }, response_text

    except Exception as e:
        return {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "latency_ms": 0,
            "error": str(e)
        }, f"错误: {str(e)}"


def calculate_cost(model_id: str, usage: Dict) -> float:
    """
    计算API调用成本（美元）

    Args:
        model_id: 模型ID
        usage: 使用量字典

    Returns:
        成本（美元）
    """
    for provider in MODELS.values():
        for model in provider:
            if model["id"] == model_id:
                input_price = model["price_input"]  # 每1K tokens
                output_price = model["price_output"]

                input_cost = (usage["prompt_tokens"] / 1000) * input_price
                output_cost = (usage["completion_tokens"] / 1000) * output_price

                return round(input_cost + output_cost, 6)

    return 0.0


def get_model_name(model_id: str) -> str:
    """
    获取模型显示名称

    Args:
        model_id: 模型ID

    Returns:
        模型显示名称
    """
    for provider in MODELS.values():
        for model in provider:
            if model["id"] == model_id:
                return model["name"]
    return model_id
