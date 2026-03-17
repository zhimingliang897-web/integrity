"""
config.py - 全局配置模块

支持从 config.yaml 读取配置，同时保持向后兼容环境变量。
优先顺序：config.yaml > 环境变量 > 默认值
"""

import os
import yaml
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent

# ── 加载 config.yaml ─────────────────────────────────────────
_config = {}
_config_path = PROJECT_ROOT / "config.yaml"
if _config_path.exists():
    with open(_config_path, "r", encoding="utf-8") as f:
        _config = yaml.safe_load(f) or {}

def _get(path: str, default=None, env_override: str = None):
    """
    从 config.yaml 获取配置，支持嵌套路径 (如 "api.model")
    同时检查环境变量作为_override
    """
    # 环境变量优先
    if env_override and os.environ.get(env_override):
        return os.environ.get(env_override)
    
    # 从 yaml 获取
    keys = path.split(".")
    value = _config
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            break
    return value if value is not None else default

# ── 路径配置（相对路径均基于 PROJECT_ROOT，保证任意 cwd 下一致）────────────────
_input_dir  = _get("input_dir", "input")
_cache_dir  = _get("cache_dir", "cache")
_output_dir = _get("output_dir", "output")
INPUT_DIR   = (PROJECT_ROOT / _input_dir).resolve() if not Path(_input_dir).is_absolute() else Path(_input_dir)
CACHE_DIR   = (PROJECT_ROOT / _cache_dir).resolve() if not Path(_cache_dir).is_absolute() else Path(_cache_dir)
OUTPUT_DIR  = (PROJECT_ROOT / _output_dir).resolve() if not Path(_output_dir).is_absolute() else Path(_output_dir)

# ── faster-whisper 配置 ───────────────────────────────────
WHISPER_ENGINE       = _get("whisper.engine", "faster")  # faster 或 fast
WHISPER_MODEL        = _get("whisper.model", "small")
WHISPER_DEVICE       = _get("whisper.device", "cuda")
WHISPER_COMPUTE_TYPE = _get("whisper.compute_type", "int8")
WHISPER_LANGUAGE     = _get("whisper.language", "en")
WHISPER_BEAM_SIZE    = int(_get("whisper.beam_size", 1))

# ── API 配置 ──────────────────────────────────────────────
API_PROVIDER = _get("api.provider", "groq")

# 千问 (DashScope) API 配置
DASHSCOPE_API_KEY = _get("api.api_key", "", env_override="DASHSCOPE_API_KEY")
QWEN_MODEL        = _get("api.model", "qwen-plus")

# Groq API 配置 (备用)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.3-70b-versatile"

# ── 分析分块配置 ──────────────────────────────────────────
CHUNK_MINUTES = _get("analysis.chunk_minutes", 30)
TEMPERATURE   = _get("analysis.temperature", 0.3)
MAX_TOKENS    = _get("analysis.max_tokens", 4096)
