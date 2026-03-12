"""
图片渲染模块 v5 — 小红书爆款风格
设计：浅蓝背景 + 白卡片 + 彩色圆点装饰 + 饱满内容
"""
import os
import re
from PIL import Image, ImageDraw, ImageFont
from config import IMG_WIDTH, IMG_HEIGHT, FONT_PATH, FONT_INDEX_REGULAR, FONT_INDEX_BOLD

# ── 路径 ──────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
from config import OUTPUT_BASE as _RAW
OUTPUT_BASE = (
    os.path.expanduser(_RAW) if _RAW.startswith("~")
    else _RAW if os.path.isabs(_RAW)
    else os.path.join(_HERE, _RAW)
)

# ── 配色方案 ─────────────────────────────────────────────────────────────────
COLORS = {
    "bg": "#E3F2FD",            # 浅蓝背景
    "card": "#FFFFFF",          # 白色卡片
    "title": "#1565C0",         # 深蓝标题
    "title_accent": "#FF6F00",  # 橙色强调
    "body": "#37474F",          # 深灰正文
    "subtitle": "#1976D2",      # 副标题蓝
    "underline": "#FFB300",     # 金黄下划线
    "dots": ["#EF5350", "#26A69A", "#42A5F5", "#66BB6A", "#FFA726", "#AB47BC"],
    # 区块颜色
    "normal_bg": "#FFFFFF",
    "normal_icon": "#90CAF9",
    "key_bg": "#FFF8E1",
    "key_icon": "#FF8F00",
    "bad_bg": "#FFEBEE",
    "bad_icon": "#E53935",
    "good_bg": "#E8F5E9",
    "good_icon": "#43A047",
    "note_bg": "#E3F2FD",
    "note_icon": "#1E88E5",
}

# ── 字体 ──────────────────────────────────────────────────────────────────────
def _FR(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size, index=FONT_INDEX_REGULAR)

def _FB(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size, index=FONT_INDEX_BOLD)

# ── 工具函数 ──────────────────────────────────────────────────────────────────
_EMOJI_RE = re.compile(
    r'[\U0001F300-\U0001F9FF\U0001FA00-\U0001FA9F'
    r'\U00002600-\U000027BF\U0000FE0F\U0000200D\U0001F004\U0001F0CF]+',
    re.UNICODE,
)

def _clean(t: str) -> str:
    return _EMOJI_RE.sub("", t).strip()

def _wrap(text: str, font, max_w: int) -> list[str]:
    lines, cur = [], ""
    for ch in text:
        if font.getlength(cur + ch) <= max_w:
            cur += ch
        else:
            if cur:
                lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines

def _rrect(draw: ImageDraw.Draw, box, r: int, fill: str):
    x0, y0, x1, y1 = box
    draw.rectangle([x0+r, y0, x1-r, y1], fill=fill)
    draw.rectangle([x0, y0+r, x1, y1-r], fill=fill)
    for cx, cy in [(x0, y0), (x1-2*r, y0), (x0, y1-2*r), (x1-2*r, y1-2*r)]:
        draw.ellipse([cx, cy, cx+2*r, cy+2*r], fill=fill)

def _draw_dots(draw: ImageDraw.Draw, y: int, style: str = "minimal"):
    """绘制装饰元素"""
    if style == "minimal":
        # 极简风格：3个小圆点，柔和配色
        dots = [
            {"x": IMG_WIDTH // 2 - 40, "r": 6, "color": "#90CAF9"},
            {"x": IMG_WIDTH // 2, "r": 8, "color": "#64B5F6"},
            {"x": IMG_WIDTH // 2 + 40, "r": 6, "color": "#90CAF9"},
        ]
        for d in dots:
            draw.ellipse([d["x"] - d["r"], y - d["r"], d["x"] + d["r"], y + d["r"]], fill=d["color"])
    elif style == "line":
        # 细线风格
        line_w = 120
        draw.rectangle(
            [(IMG_WIDTH - line_w) // 2, y - 2, (IMG_WIDTH + line_w) // 2, y + 2],
            fill="#90CAF9"
        )

# ── 计算区块高度 ─────────────────────────────────────────────────────────────
def _calc_block_height(block: dict, w: int, font_body, font_label) -> int:
    """预计算区块高度"""
    btype = block.get("type", "normal")
    text = _clean(block.get("text", ""))
    label = _clean(block.get("label", ""))
    if not text:
        return 0

    pad = 24
    icon_space = 50
    inner_w = w - pad * 2 - icon_space

    lines = _wrap(text, font_body, inner_w)
    line_h = int(font_body.size * 1.6)

    has_label = bool(label) and btype != "normal"
    label_h = (font_label.size + 12) if has_label else 0

    return pad * 2 + label_h + len(lines) * line_h

# ── 绘制内容区块 ─────────────────────────────────────────────────────────────
def _draw_block(draw: ImageDraw.Draw, block: dict, x: int, y: int, w: int) -> int:
    """绘制一个内容区块，返回下边缘 y"""
    btype = block.get("type", "normal")
    text = _clean(block.get("text", "")).replace("###", "").replace("##", "")
    label = _clean(block.get("label", ""))
    if not text:
        return y

    # 字体 - 增大尺寸
    font_label = _FB(28)
    font_body = _FR(32)

    # 区块样式
    styles = {
        "normal": {"bg": COLORS["normal_bg"], "icon": "●", "icon_bg": COLORS["normal_icon"], "icon_fg": "#FFFFFF"},
        "key":    {"bg": COLORS["key_bg"],    "icon": "★", "icon_bg": COLORS["key_icon"],    "icon_fg": "#FFFFFF"},
        "bad":    {"bg": COLORS["bad_bg"],    "icon": "✕", "icon_bg": COLORS["bad_icon"],    "icon_fg": "#FFFFFF"},
        "good":   {"bg": COLORS["good_bg"],   "icon": "✓", "icon_bg": COLORS["good_icon"],   "icon_fg": "#FFFFFF"},
        "note":   {"bg": COLORS["note_bg"],   "icon": "!", "icon_bg": COLORS["note_icon"],   "icon_fg": "#FFFFFF"},
    }
    style = styles.get(btype, styles["normal"])

    pad = 24
    icon_size = 36
    icon_space = 50
    inner_x = x + pad + icon_space
    inner_w = w - pad * 2 - icon_space

    # 计算文本
    lines = _wrap(text, font_body, inner_w)
    line_h = int(font_body.size * 1.6)

    has_label = bool(label) and btype != "normal"
    label_h = (font_label.size + 12) if has_label else 0

    block_h = pad * 2 + label_h + len(lines) * line_h

    # 绘制背景卡片
    _rrect(draw, (x, y, x + w, y + block_h), r=16, fill=style["bg"])

    # 绘制左侧图标
    icon_x = x + pad
    icon_y = y + pad + (label_h if has_label else 0) + (line_h - icon_size) // 2
    draw.ellipse([icon_x, icon_y, icon_x + icon_size, icon_y + icon_size], fill=style["icon_bg"])

    # 图标文字
    icon_font = _FB(20)
    icon_text = style["icon"]
    bbox = draw.textbbox((0, 0), icon_text, font=icon_font)
    icon_tw = bbox[2] - bbox[0]
    icon_th = bbox[3] - bbox[1]
    draw.text((icon_x + (icon_size - icon_tw) // 2, icon_y + (icon_size - icon_th) // 2 - 2),
              icon_text, font=icon_font, fill=style["icon_fg"])

    ty = y + pad

    # 绘制标签
    if has_label:
        draw.text((inner_x, ty), label, font=font_label, fill=style["icon_bg"])
        ty += font_label.size + 12

    # 绘制正文
    for line in lines:
        draw.text((inner_x, ty), line, font=font_body, fill=COLORS["body"])
        ty += line_h

    return y + block_h

# ── 主渲染函数 ───────────────────────────────────────────────────────────────
def render_slide(title: str, content: list[dict], num: int, total: int) -> Image.Image:
    """渲染一张内容页"""
    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    margin = 36

    # 顶部装饰（极简风格）
    _draw_dots(draw, 36, "minimal")

    # 白色主卡片
    card_top = 70
    card_bottom = IMG_HEIGHT - 36
    _rrect(draw, (margin, card_top, IMG_WIDTH - margin, card_bottom), r=24, fill=COLORS["card"])

    # 标题
    title_clean = _clean(title)
    title_font = _FB(48)
    title_x = margin + 36
    title_y = card_top + 36
    title_w = IMG_WIDTH - margin * 2 - 72

    title_lines = _wrap(title_clean, title_font, title_w)
    for i, line in enumerate(title_lines):
        color = COLORS["title_accent"] if i == 0 else COLORS["title"]
        draw.text((title_x, title_y), line, font=title_font, fill=color)
        title_y += int(title_font.size * 1.3)

    # 下划线
    underline_y = title_y + 12
    underline_w = min(240, title_w // 2)
    draw.rectangle([title_x, underline_y, title_x + underline_w, underline_y + 5],
                   fill=COLORS["underline"])

    # 内容区域
    content_start_y = underline_y + 36
    content_x = margin + 28
    content_w = IMG_WIDTH - margin * 2 - 56
    bottom_limit = card_bottom - 36

    # 预计算所有区块高度
    font_body = _FR(32)
    font_label = _FB(28)

    total_content_h = 0
    block_heights = []
    for blk in content:
        if isinstance(blk, str):
            blk = {"type": "normal", "text": blk}
        h = _calc_block_height(blk, content_w, font_body, font_label)
        block_heights.append(h)
        total_content_h += h

    # 计算可用空间和间距
    available_h = bottom_limit - content_start_y
    valid_blocks = [h for h in block_heights if h > 0]

    if len(valid_blocks) > 1:
        # 动态计算间距，让内容均匀分布
        remaining_space = available_h - total_content_h
        gap = max(16, min(remaining_space // (len(valid_blocks)), 40))
    else:
        gap = 20

    # 绘制区块
    y = content_start_y
    for i, blk in enumerate(content):
        if isinstance(blk, str):
            blk = {"type": "normal", "text": blk}

        if y + block_heights[i] > bottom_limit:
            break

        if block_heights[i] > 0:
            y = _draw_block(draw, blk, content_x, y, content_w)
            y += gap

    return img

# ── 封面渲染 ─────────────────────────────────────────────────────────────────
def render_cover(title: str, subtitle: str = "") -> Image.Image:
    """渲染封面"""
    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    margin = 36

    # 顶部装饰（极简风格）
    _draw_dots(draw, 36, "minimal")

    # 白色卡片
    card_top = 70
    card_bottom = IMG_HEIGHT - 70
    _rrect(draw, (margin, card_top, IMG_WIDTH - margin, card_bottom), r=24, fill=COLORS["card"])

    # 标题处理
    title_clean = _clean(title)

    def split_title(text: str) -> list[str]:
        for sep in ['：', ':', '—', '｜', '|', '？', '?', '！', '!']:
            if sep in text:
                parts = text.split(sep, 1)
                if len(parts[0]) >= 2:
                    suffix = sep if sep in '：:？?！!' else ''
                    return [parts[0].strip() + suffix, parts[1].strip()]
        if len(text) > 12:
            mid = len(text) // 2
            for i in range(mid, min(mid + 6, len(text))):
                if text[i] in '，、。':
                    return [text[:i+1], text[i+1:]]
            return [text[:mid], text[mid:]]
        return [text]

    lines = split_title(title_clean)

    # 字体
    if len(lines) >= 2:
        fonts = [_FB(52), _FB(64)]
    else:
        fonts = [_FB(72)]

    # 居中绘制
    card_h = card_bottom - card_top
    total_h = sum(int(fonts[min(i, len(fonts)-1)].size * 1.5) for i in range(len(lines)))
    start_y = card_top + (card_h - total_h) // 2

    for i, line in enumerate(lines):
        font = fonts[min(i, len(fonts) - 1)]
        line_w = font.getlength(line)
        x = (IMG_WIDTH - line_w) // 2
        y = start_y + sum(int(fonts[min(j, len(fonts)-1)].size * 1.5) for j in range(i))

        color = COLORS["title_accent"] if i == 0 else COLORS["title"]
        draw.text((x, y), line, font=font, fill=color)

    # 下划线
    last_font = fonts[min(len(lines) - 1, len(fonts) - 1)]
    last_w = last_font.getlength(lines[-1])
    ul_w = int(last_w * 0.5)
    ul_x = (IMG_WIDTH - ul_w) // 2
    ul_y = start_y + total_h + 24
    draw.rectangle([ul_x, ul_y, ul_x + ul_w, ul_y + 6], fill=COLORS["underline"])

    # 底部装饰（细线风格）
    _draw_dots(draw, IMG_HEIGHT - 36, "line")

    return img

# ── 批量生成 ──────────────────────────────────────────────────────────────────
def generate_images(slides: list[dict], folder_name: str) -> list[str]:
    out_dir = os.path.join(OUTPUT_BASE, folder_name)
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    total = len(slides)

    for i, slide in enumerate(slides, 1):
        img = render_slide(slide.get("title", ""), slide.get("content", []), i, total)
        path = os.path.join(out_dir, f"slide_{i:02d}.png")
        img.save(path)
        paths.append(path)
        print(f"  ✅ {i}/{total} → {path}")

    return paths
