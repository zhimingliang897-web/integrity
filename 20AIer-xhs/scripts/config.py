"""
配置加载器 - 从 config.yaml 读取所有配置
"""
import os
import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)   # scripts/ → project root
_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config.yaml")
_CONFIG_LOCAL_PATH = os.path.join(_PROJECT_ROOT, "config.local.yaml")


def _load() -> dict:
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


_cfg = _load()


def _deep_update(base: dict, patch: dict) -> dict:
    """递归合并 dict（local 配置覆盖默认配置）。"""
    for k, v in (patch or {}).items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_update(base[k], v)
        else:
            base[k] = v
    return base


def _load_local_if_any():
    if not os.path.isfile(_CONFIG_LOCAL_PATH):
        return
    with open(_CONFIG_LOCAL_PATH, "r", encoding="utf-8") as f:
        local_cfg = yaml.safe_load(f) or {}
    _deep_update(_cfg, local_cfg)


_load_local_if_any()

# ── API ───────────────────────────────────────────────────────────────────────
_api = _cfg.get("api", {}) or {}

# 环境变量优先，避免把 key 写进仓库
API_KEY = (
    os.getenv("XHS_API_KEY")
    or os.getenv("DASHSCOPE_API_KEY")
    or os.getenv("OPENAI_API_KEY")
    or _api.get("api_key", "")
)
BASE_URL = os.getenv("XHS_BASE_URL") or _api.get("base_url", "")
MODEL = os.getenv("XHS_MODEL") or _api.get("model", "")
TIMEOUT_SEC = float(os.getenv("XHS_TIMEOUT_SEC") or _api.get("timeout_sec", 60))

# ── 图片样式 ──────────────────────────────────────────────────────────────────
_style = _cfg["style"]
IMG_WIDTH  = _style["img_width"]
IMG_HEIGHT = _style["img_height"]
MARGIN     = _style["margin"]
MAX_SLIDES = _style["max_slides"]

# 引入跨平台字体探测模块
from font_detector import FONT_PATH, FONT_INDEX_REGULAR, FONT_INDEX_BOLD

THEME      = _style["theme"]
FONT_SIZES = _style["font_sizes"]

# 支持相对路径（相对于项目根目录）
_raw_out = _style["output_base_dir"]
if _raw_out.startswith("~"):
    OUTPUT_BASE = os.path.expanduser(_raw_out)
elif os.path.isabs(_raw_out):
    OUTPUT_BASE = _raw_out
else:
    OUTPUT_BASE = os.path.join(_PROJECT_ROOT, _raw_out)
