"""
配置示例文件
复制此文件为 config.py 并填入你的 API Key

使用方式：
1. 复制 config_example.py 为 config.py
2. 填入你的 API Key
3. 或者设置环境变量 DASHSCOPE_API_KEY 和 OPENAI_API_KEY
"""

# ==================== API 配置 ====================
# 方式1: 直接在这里填入 API Key
DASHSCOPE_API_KEY = "your-dashscope-api-key-here"
OPENAI_API_KEY = "your-openai-api-key-here"

# 方式2: 使用环境变量 (更安全)
# import os
# DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
# OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
OPENAI_BASE_URL = "https://api.openai.com/v1"

# ==================== 模型配置 ====================
MODELS = {
    "阿里云百炼": [
        {"id": "qwen-turbo", "name": "Qwen Turbo", "price_input": 0.001, "price_output": 0.002},
        {"id": "qwen-plus", "name": "Qwen Plus", "price_input": 0.004, "price_output": 0.012},
        {"id": "qwen-max", "name": "Qwen Max", "price_input": 0.02, "price_output": 0.06},
        {"id": "qwen-vl-plus", "name": "Qwen VL Plus", "price_input": 0.005, "price_output": 0.015},
    ],
    "OpenAI": [
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "price_input": 0.00015, "price_output": 0.0006},
        {"id": "gpt-4o", "name": "GPT-4o", "price_input": 0.0025, "price_output": 0.01},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "price_input": 0.01, "price_output": 0.03},
    ]
}

# ==================== UI 配置 ====================
MODEL_CHOICES = [
    "阿里云百炼: qwen-plus",
    "阿里云百炼: qwen-turbo",
    "阿里云百炼: qwen-max",
    "OpenAI: gpt-4o-mini",
    "OpenAI: gpt-4o",
]

LANGUAGE_CHOICES = ["中文", "英文", "图片中文"]

# ==================== 翻译映射表 ====================
TRANSLATION_MAP = {
    "北京今天天气怎么样": "What's the weather like in Beijing today?",
    "你好": "Hello",
    "今天天气怎么样": "What's the weather like today?",
    "人工智能是什么": "What is artificial intelligence?",
    "什么是机器学习": "What is machine learning?",
    "如何学习Python": "How to learn Python?",
}

# ==================== 应用配置 ====================
APP_CONFIG = {
    "title": "Token消耗对比工具",
    "version": "2.0",
    "server_name": "127.0.0.1",
    "server_port": 7862,
}

# ==================== 主题配置 ====================
THEME = {
    "primary_hue": "indigo",
    "secondary_hue": "blue",
    "neutral_hue": "slate",
    "font": ["Microsoft YaHei", "Arial", "sans-serif"],
}

CSS = """
#header {
    text-align: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
    border-radius: 10px;
    color: white !important;
}
.gradio-container {
    max-width: 1400px !important;
}
"""