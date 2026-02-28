"""
配置模板文件（请复制为 config.py 后使用）

快速步骤:
1. 复制本文件为 config.py
2. 填写各平台 Cookie 和 LLM 配置
3. 不要将真实 config.py 提交到公开仓库
"""

# B站 Cookie（可选）
BILIBILI_COOKIE = ""

# 抖音 Cookie（必填）
DOUYIN_COOKIE = ""

# 小红书 Cookie（必填）
XIAOHONGSHU_COOKIE = ""

# 导出设置
OUTPUT_DIR = "output"
OUTPUT_FORMAT = "csv"  # "csv" 或 "excel"

# 速度档位: "fast" / "normal" / "slow" / "safe"
DEFAULT_SPEED = "safe"

# ========== LLM 配置 ==========
# 支持 OpenAI 兼容接口（DeepSeek、Qwen、OpenAI 等）
LLM_BASE_URL = ""
LLM_API_KEY = ""
LLM_MODEL = "deepseek-v3.1"
LLM_BATCH_SIZE = 50

# ========== 话题搜索配置 ==========
TOPIC_MAX_SEARCH = 5
TOPIC_MAX_COMMENTS = 50
