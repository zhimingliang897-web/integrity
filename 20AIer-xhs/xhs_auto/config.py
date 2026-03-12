"""
配置加载器 - 从 config.yaml 读取所有配置
"""
import os
import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_HERE, "config.yaml")


def _load() -> dict:
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


_cfg = _load()

# ── API ───────────────────────────────────────────────────────────────────────
API_KEY  = _cfg["api"]["api_key"]
BASE_URL = _cfg["api"]["base_url"]
MODEL    = _cfg["api"]["model"]

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

# 支持相对路径（相对于 config.yaml 所在项目目录）
_raw_out = _style["output_base_dir"]
if _raw_out.startswith("~"):
    OUTPUT_BASE = os.path.expanduser(_raw_out)
elif os.path.isabs(_raw_out):
    OUTPUT_BASE = _raw_out
else:
    OUTPUT_BASE = os.path.join(_HERE, _raw_out)
