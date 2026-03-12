"""
字体自动检测 - 跨平台（macOS / Windows / Linux）
按优先级尝试各系统的中文字体，返回 (路径, regular_index, bold_index)
"""
import sys
import os
from PIL import ImageFont

# ── 各平台候选字体（按优先级排列）────────────────────────────────────────────
_CANDIDATES = {
    "darwin": [   # macOS
        # (path, regular_idx, bold_idx, description) - 按美观度排序
        ("/System/Library/Fonts/PingFang.ttc",           0, 6, "苹方-简 常规+中"),  # 苹方最好看
        ("/System/Library/Fonts/PingFang SC Regular.ttc",0, 0, "苹方 常规"),
        ("/System/Library/Fonts/PingFang SC Medium.ttc", 0, 0, "苹方 中等"),
        ("/System/Library/Fonts/Hiragino Sans GB.ttc",   0, 1, "Hiragino Sans GB"),
        ("/System/Library/Fonts/STHeiti Medium.ttc",     0, 0, "STHeiti Medium"),
        ("/System/Library/Fonts/STHeiti Light.ttc",      0, 0, "STHeiti Light"),
    ],
    "win32": [    # Windows
        # 思源黑体最美观，微软雅黑备选
        ("C:/Windows/Fonts/SourceHanSansSC-Regular.otf",0, 0, "思源黑体 常规"),
        ("C:/Windows/Fonts/SourceHanSansSC-Medium.otf", 0, 0, "思源黑体 中等"),
        ("C:/Windows/Fonts/SourceHanSansSC-Bold.otf",   0, 0, "思源黑体 粗体"),
        ("C:/Windows/Fonts/msyh.ttc",     0, 1, "微软雅黑 常规+粗体"),
        ("C:/Windows/Fonts/simhei.ttf",   0, 0, "黑体"),
        ("C:/Windows/Fonts/simsun.ttc",   1, 1, "宋体"),
    ],
    "linux": [    # Linux
        ("/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf", 0, 0, "Noto Sans CJK SC"),
        ("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",   2, 2, "Noto Sans CJK"),
        ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",           0, 0, "WQY MicroHei"),
        ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",             0, 0, "WQY ZenHei"),
        ("/usr/share/fonts/truetype/arphic/uming.ttc",               0, 0, "AR PL UMing"),
    ],
}

# 通用后备（Pillow 内置，无 CJK 支持但不会崩溃）
_FALLBACK = (None, 0, 0, "Pillow default (no CJK)")


def _probe(path: str, index: int, size: int = 36) -> bool:
    """检测字体文件是否可用"""
    try:
        if not os.path.isfile(path):
            return False
        ImageFont.truetype(path, size, index=index)
        return True
    except Exception:
        return False


def detect_font() -> tuple[str | None, int, int]:
    """
    返回 (font_path, regular_index, bold_index)
    font_path 为 None 时使用 Pillow 默认字体
    """
    platform = sys.platform   # 'darwin' | 'win32' | 'linux'

    # 非标准 Linux 平台 key 统一用 'linux'
    key = platform if platform in _CANDIDATES else "linux"

    for path, ri, bi, name in _CANDIDATES[key]:
        if _probe(path, ri):
            # bold index 不一定存在，退化为 regular
            bi_ok = bi if _probe(path, bi) else ri
            print(f"[Font] Found: {name}  ({path})")
            return path, ri, bi_ok

    print(f"[Font] Warning: No CJK font found, using Pillow default")
    return _FALLBACK[0], _FALLBACK[1], _FALLBACK[2]


# 模块加载时执行一次检测
FONT_PATH, FONT_INDEX_REGULAR, FONT_INDEX_BOLD = detect_font()
