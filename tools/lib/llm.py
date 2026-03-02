"""llm.py — API 配置加载、LLM 调用、JSON 提取"""
import json
import os
import re
import sys
from pathlib import Path

import yaml

from .utils import RED


def _read_yaml_api(yaml_path: Path, cfg: dict) -> bool:
    """从 yaml 文件读取 api 配置块，成功读取到 key 返回 True。"""
    if not yaml_path.exists():
        return False
    try:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        api = data.get("api", {})
        if api.get("api_key"):
            cfg["api_key"] = api["api_key"]
        if api.get("model"):
            cfg["model"] = api["model"]
        if api.get("provider"):
            cfg["provider"] = api["provider"]
        return bool(cfg["api_key"])
    except Exception:
        return False


def load_api_config(script_dir: Path, target_dir: Path, cli_key: str) -> dict:
    """
    优先级（低 → 高，后者覆盖前者）：
      organize_config.yaml（脚本同目录）
      → config.yaml（目标目录）
      → 环境变量 DASHSCOPE_API_KEY / OPENAI_API_KEY
      → --api-key 命令行参数
    """
    cfg = {
        "api_key": "",
        "model": "qwen-plus",
        "provider": "dashscope",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    }
    for name in ["organize_config.yaml", "organize_config.yml"]:
        if _read_yaml_api(script_dir / name, cfg):
            break
    for name in ["config.yaml", "config.yml"]:
        if _read_yaml_api(target_dir / name, cfg):
            break
    env_key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if env_key:
        cfg["api_key"] = env_key
    if cli_key:
        cfg["api_key"] = cli_key

    provider_urls = {
        "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "openai":    "https://api.openai.com/v1",
        "groq":      "https://api.groq.com/openai/v1",
    }
    cfg["base_url"] = provider_urls.get(cfg["provider"], cfg["base_url"])
    return cfg


def call_llm(cfg: dict, messages: list, max_tokens: int = 4096) -> str:
    """调用 OpenAI-compatible API，返回模型回复文本。"""
    try:
        from openai import OpenAI
    except ImportError:
        print(RED("  [LLM] 未安装 openai 包：pip install openai"))
        sys.exit(1)
    if not cfg["api_key"]:
        print(RED("  [错误] 未找到 API Key，请配置 organize_config.yaml"))
        sys.exit(1)
    client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])
    resp = client.chat.completions.create(
        model=cfg["model"],
        messages=messages,
        temperature=0.2,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()


def extract_json(text: str):
    """从 LLM 输出中提取 JSON（兼容 ```json ... ``` 代码块包裹）。"""
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1).strip()
    start = next((i for i, c in enumerate(text) if c in "{["), 0)
    return json.loads(text[start:])
