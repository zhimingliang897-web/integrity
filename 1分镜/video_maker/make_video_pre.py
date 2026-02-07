# -*- coding: utf-8 -*-
"""
分镜视频生成器（最终整合·白边均匀版）
用法: python make_video.py <项目文件夹名>
例如: python make_video.py 新3谁新

项目文件夹结构:
  项目文件夹/
    input/    ← 放图片和文本（文本.txt、图片.png）
    output/   ← 自动生成输出

文本格式:
  - 角色标记: M1: M2: (男) / F1: F2: (女)
  - 场景分隔: ---
  - 其他行自动忽略
"""

import asyncio
import edge_tts
import math
import os
import re
import statistics
import subprocess
import sys
from PIL import Image, ImageDraw

# ============================================================
# 路径定义（由命令行参数决定）
# ============================================================

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def init_paths(project_name: str):
    """根据项目文件夹名初始化路径"""
    global PROJECT_DIR, INPUT_DIR, OUTPUT_DIR
    PROJECT_DIR = os.path.join(ROOT_DIR, project_name)
    INPUT_DIR = os.path.join(PROJECT_DIR, "input")
    OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")

    if not os.path.isdir(INPUT_DIR):
        print(f"[错误] 项目文件夹不存在: {INPUT_DIR}")
        sys.exit(1)


# ============================================================
# 声音池
# ============================================================

MALE_VOICES = [
    "en-US-GuyNeural",
    "en-US-ChristopherNeural",
    "en-US-EricNeural",
    "en-US-AndrewNeural",
]

FEMALE_VOICES = [
    "en-US-JennyNeural",
    "en-US-AriaNeural",
    "en-US-MichelleNeural",
    "en-US-AnaNeural",
]


# ============================================================
# 可调参数（切割与留白策略）
# ============================================================

# —— 1) 2x2 分割线检测开关（推荐开）
ENABLE_SPLITLINE_DETECT = True

# —— 2) 分割线去除：切块后内缩（避免切到中间白线）
INSET_PX_MIN = 18             # 最少内缩像素（16~28）
INSET_PCT_FALLBACK = 0.02     # 兜底内缩比例（2%）

# —— 3) “白边不均匀”的根治：自动剥离 panel 外侧纯色边框
#      容差越大越容易把“接近背景”的像素当背景裁掉；一般 10~18 很稳
STRIP_BORDER_TOL = 14
#      边缘一行/一列里，背景像素占比 >= 该比例，就认为是“纯边框”继续剥
STRIP_BORDER_RATIO = 0.97
#      每次剥离的最大循环次数（防卡死）
STRIP_BORDER_MAX_ITERS = 4000

# —— 4) 统一输出 panel 画布
PANEL_OUT_SIZE = (1280, 660)
PANEL_PAPER_COLOR = (248, 246, 240)  # 暖白纸色（仅在极端比例时可见）
PANEL_PAPER_BORDER = 0               # 无纸边，图片铺满
PANEL_INNER_PAD = 0                  # 无内边距

# ============================================================
# 视频/字幕相关参数
# ============================================================

TITLE_DURATION = 1.5
SLOW_RATE = "-30%"
VOCAB_DURATION = 6.0  # 保留（你未来可能用），当前不强制用


# ============================================================
# subprocess / ffmpeg 工具函数（修复 GBK UnicodeDecodeError）
# ============================================================

def _bytes_to_text(b: bytes) -> str:
    """安全解码 bytes -> str（尽量不报错）"""
    if not b:
        return ""
    try:
        return b.decode("utf-8", errors="ignore")
    except Exception:
        try:
            return b.decode(errors="ignore")
        except Exception:
            return ""


def run_cmd(args, desc=""):
    """
    统一的 subprocess.run：强制 bytes 模式，避免 Windows/GBK 解码炸线程
    """
    result = subprocess.run(
        args,
        capture_output=True,
        text=False,          # 关键：永远不要 text=True
        encoding=None,
        errors=None
    )
    if result.returncode != 0:
        print(f"  [错误] {desc}")
        stderr = _bytes_to_text(result.stderr)
        stdout = _bytes_to_text(result.stdout)
        if stderr:
            print(stderr[-1200:])
        elif stdout:
            print(stdout[-1200:])
        else:
            print("无错误输出")
        raise RuntimeError(f"命令失败: {desc}")
    return result


def ffmpeg_run(args, desc=""):
    return run_cmd(args, desc=desc)


def get_audio_duration(file_path: str) -> float:
    """ffprobe 获取音频时长（秒）"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            capture_output=True,
            text=False,
            encoding=None,
            errors=None
        )
        if result.returncode != 0:
            return 0.0
        s = _bytes_to_text(result.stdout).strip()
        return float(s) if s else 0.0
    except Exception:
        return 0.0


def format_srt_time(seconds: float) -> str:
    """秒数 → SRT 时间格式 00:00:00,000"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


async def generate_audio(text: str, output_file: str, voice: str, rate="+0%"):
    """Edge TTS 生成单句语音"""
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_file)


# ============================================================
# 文本解析
# ============================================================

SPEAKER_PATTERN = re.compile(r'^([MF]\d+)\s*[:：]\s*(.+)$')
STAGE_DIRECTION = re.compile(r'\([^)]*\)\s*')


def parse_text_file(text_path: str):
    """
    返回 (title, scenes, speakers_set, vocab_lines)
    scenes: [ [{"speaker","text","text_cn"}, ...], ... ]
    vocab_lines: 读取 === 之后的“短语 — 中文 — 例句”行；过滤 Panel 说明等
    """
    with open(text_path, "r", encoding="utf-8") as f:
        raw_lines = f.read().splitlines()

    main_lines = []
    vocab_lines = []
    in_vocab = False

    for raw in raw_lines:
        if raw.strip() == "===":
            in_vocab = True
            continue

        if in_vocab:
            s = raw.strip()
            if not s:
                continue

            # 过滤 “Panel/分镜说明”
            if re.search(r'\bpanel\b', s, flags=re.IGNORECASE):
                continue
            if any(k in s for k in ["分镜", "镜头", "画面", "场景说明"]):
                continue

            # 只保留 “短语 — 中文 — 例句”（恰好两个 em dash）
            if s.count("—") != 2:
                continue

            vocab_lines.append(s)
        else:
            main_lines.append(raw)

    scenes = []
    current_scene = []
    speakers = set()
    title = None
    found_first_dialogue = False

    for raw in main_lines:
        line = raw.strip()
        if not line:
            continue

        if line == "---":
            if current_scene:
                scenes.append(current_scene)
                current_scene = []
            continue

        m = SPEAKER_PATTERN.match(line)
        if m:
            found_first_dialogue = True
            speaker = m.group(1).upper()
            full_text = STAGE_DIRECTION.sub('', m.group(2)).strip()

            if '|' in full_text:
                parts = full_text.split('|', 1)
                text = parts[0].strip()
                text_cn = parts[1].strip()
            else:
                text = full_text
                text_cn = ""

            if text:
                current_scene.append({"speaker": speaker, "text": text, "text_cn": text_cn})
                speakers.add(speaker)
        else:
            if not found_first_dialogue and title is None:
                title = line

    if current_scene:
        scenes.append(current_scene)

    return title, scenes, speakers, vocab_lines


def assign_voices(speakers):
    """M1/M2... F1/F2... 自动分配"""
    voices = {}
    for s in sorted(speakers):
        gender = s[0]
        num = int(s[1:])
        if gender == 'M':
            voices[s] = MALE_VOICES[(num - 1) % len(MALE_VOICES)]
        else:
            voices[s] = FEMALE_VOICES[(num - 1) % len(FEMALE_VOICES)]
    return voices


def calc_grid(scene_count: int):
    """根据场景数量计算网格布局"""
    if scene_count <= 1:
        return (1, 1)
    if scene_count == 2:
        return (1, 2)
    if scene_count == 3:
        return (1, 3)
    if scene_count == 4:
        return (2, 2)
    if scene_count <= 6:
        return (2, 3)
    if scene_count <= 8:
        return (2, 4)
    if scene_count <= 9:
        return (3, 3)
    cols = math.ceil(math.sqrt(scene_count))
    rows = math.ceil(scene_count / cols)
    return (rows, cols)


def find_source_image():
    """在 input/ 中找第一张图片"""
    for fname in os.listdir(INPUT_DIR):
        if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp')):
            return fname
    return None


# ============================================================
# 图片切割：分割线检测 + 均分回退 + 白边统一化
# ============================================================

def _convert_to_rgb_with_white_bg(img: Image.Image) -> Image.Image:
    """透明图转白底RGB"""
    if img.mode in ("RGBA", "LA"):
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        bg.paste(img, (0, 0), img)
        return bg.convert("RGB")
    return img.convert("RGB")


def _calc_inset(cell_w: int, cell_h: int):
    inset_x = max(INSET_PX_MIN, int(cell_w * INSET_PCT_FALLBACK))
    inset_y = max(INSET_PX_MIN, int(cell_h * INSET_PCT_FALLBACK))
    return inset_x, inset_y


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _crop_safe(img: Image.Image, box):
    """保证 box 不越界，至少 2px"""
    w, h = img.size
    x1, y1, x2, y2 = box
    x1 = _clamp(int(x1), 0, w - 2)
    y1 = _clamp(int(y1), 0, h - 2)
    x2 = _clamp(int(x2), x1 + 2, w)
    y2 = _clamp(int(y2), y1 + 2, h)
    return img.crop((x1, y1, x2, y2))


def _detect_split_lines_2x2(img: Image.Image):
    """
    检测 2x2 中间白分割线（返回 vx_center, hy_center, v_width, h_width 或 None）
    """
    g = img.convert("L")
    w, h = g.size
    px = g.load()

    x_lo, x_hi = int(w * 0.35), int(w * 0.65)
    y_lo, y_hi = int(h * 0.35), int(h * 0.65)
    white_thr = 245

    col_score = [0.0] * w
    for x in range(x_lo, x_hi):
        cnt = 0
        for y in range(0, h, 2):
            if px[x, y] >= white_thr:
                cnt += 1
        col_score[x] = cnt / (h / 2)

    row_score = [0.0] * h
    for y in range(y_lo, y_hi):
        cnt = 0
        for x in range(0, w, 2):
            if px[x, y] >= white_thr:
                cnt += 1
        row_score[y] = cnt / (w / 2)

    vx = max(range(x_lo, x_hi), key=lambda i: col_score[i])
    hy = max(range(y_lo, y_hi), key=lambda i: row_score[i])

    if col_score[vx] < 0.65 or row_score[hy] < 0.65:
        return None

    def estimate_width(scores, center, lo, hi, drop=0.15):
        peak = scores[center]
        left = center
        while left - 1 >= lo and scores[left - 1] >= peak - drop:
            left -= 1
        right = center
        while right + 1 < hi and scores[right + 1] >= peak - drop:
            right += 1
        return (left + right) // 2, (right - left + 1)

    vx_center, v_width = estimate_width(col_score, vx, x_lo, x_hi)
    hy_center, h_width = estimate_width(row_score, hy, y_lo, y_hi)
    return vx_center, hy_center, v_width, h_width


def _estimate_bg_color(im: Image.Image, inset=6, patch=14):
    """用四角小块的 median 估计背景色（用于剥边）"""
    im = im.convert("RGB")
    w, h = im.size
    px = im.load()
    coords = [
        (inset, inset),
        (w - inset - patch, inset),
        (inset, h - inset - patch),
        (w - inset - patch, h - inset - patch),
    ]
    samples = []
    for x0, y0 in coords:
        for yy in range(y0, min(h, y0 + patch)):
            for xx in range(x0, min(w, x0 + patch)):
                if 0 <= xx < w and 0 <= yy < h:
                    samples.append(px[xx, yy])
    rs = [c[0] for c in samples]
    gs = [c[1] for c in samples]
    bs = [c[2] for c in samples]
    return (int(statistics.median(rs)), int(statistics.median(gs)), int(statistics.median(bs)))


def _strip_solid_border(im: Image.Image,
                        tol=STRIP_BORDER_TOL,
                        ratio=STRIP_BORDER_RATIO,
                        max_iters=STRIP_BORDER_MAX_ITERS,
                        step=2) -> Image.Image:
    """
    逐像素剥离四边“纯色边框”，直到边缘不再是背景为主。
    这是解决“白边不均匀”的关键。
    """
    im = im.convert("RGB")
    bg = _estimate_bg_color(im)

    def is_bg(rgb):
        return (abs(rgb[0] - bg[0]) <= tol and
                abs(rgb[1] - bg[1]) <= tol and
                abs(rgb[2] - bg[2]) <= tol)

    for _ in range(max_iters):
        w, h = im.size
        if w < 60 or h < 60:
            break

        px = im.load()

        def edge_ratio(side):
            if side in ("top", "bottom"):
                y = 0 if side == "top" else h - 1
                cnt = 0
                total = 0
                for x in range(0, w, step):
                    total += 1
                    if is_bg(px[x, y]):
                        cnt += 1
                return cnt / total if total else 0.0
            else:
                x = 0 if side == "left" else w - 1
                cnt = 0
                total = 0
                for y in range(0, h, step):
                    total += 1
                    if is_bg(px[x, y]):
                        cnt += 1
                return cnt / total if total else 0.0

        changed = False

        if edge_ratio("top") >= ratio:
            im = im.crop((0, 1, w, h))
            changed = True
        w, h = im.size
        px = im.load()
        if edge_ratio("bottom") >= ratio:
            im = im.crop((0, 0, w, h - 1))
            changed = True
        w, h = im.size
        px = im.load()
        if edge_ratio("left") >= ratio:
            im = im.crop((1, 0, w, h))
            changed = True
        w, h = im.size
        px = im.load()
        if edge_ratio("right") >= ratio:
            im = im.crop((0, 0, w - 1, h))
            changed = True

        if not changed:
            break

    return im


def _make_panel_card(panel: Image.Image) -> Image.Image:
    """
    面板标准化：
    1) 自动剥离不均匀纯色白边
    2) cover 模式缩放铺满画布（1280x660），裁掉溢出部分，无白边
    """
    panel = panel.convert("RGB")

    # 先剥掉不均匀白边
    panel = _strip_solid_border(panel)

    W, H = PANEL_OUT_SIZE
    iw, ih = panel.size

    # cover 模式：缩放到完全覆盖画布，然后居中裁切
    scale = max(W / iw, H / ih)
    nw, nh = max(2, int(iw * scale)), max(2, int(ih * scale))
    panel = panel.resize((nw, nh), Image.LANCZOS)

    # 居中裁切到目标尺寸
    left = (nw - W) // 2
    top = (nh - H) // 2
    panel = panel.crop((left, top, left + W, top + H))
    return panel


def step0_load_config():
    """自动从 input/ 文本 + 图片生成 config"""
    print("=" * 50)
    print("步骤 0: 加载配置")
    print("=" * 50)

    text_path = None
    for fname in os.listdir(INPUT_DIR):
        if fname.lower().endswith('.txt'):
            text_path = os.path.join(INPUT_DIR, fname)
            break

    if not text_path:
        print("  [错误] input/ 中没有 .txt 文本文件！")
        sys.exit(1)

    print(f"  发现文本: {os.path.basename(text_path)}")
    title, scenes_data, speakers, vocab_lines = parse_text_file(text_path)

    if not scenes_data:
        print("  [错误] 文本中未解析到任何台词！")
        sys.exit(1)

    voices = assign_voices(speakers)
    source_image = find_source_image()
    grid = calc_grid(len(scenes_data))

    config = {
        "source_image": source_image,
        "grid": list(grid),
        "voices": voices,
        "gap": 0.5,
        "output": os.path.basename(PROJECT_DIR) + ".mp4",
        "title": title,
        "vocab": vocab_lines,
        "scenes": []
    }

    for i, scene_lines in enumerate(scenes_data):
        config["scenes"].append({
            "image": f"scene_{i + 1:02d}.png",
            "lines": scene_lines
        })

    print(f"  场景数量: {len(config['scenes'])}")
    print(f"  网格布局: {grid[0]}×{grid[1]}")
    print("  角色配音:")
    for s in sorted(voices):
        print(f"    {s} → {voices[s]}")
    print(f"  源图片:   {source_image or '无'}")
    print(f"  标题:     {title or '无'}")
    print(f"  核心表达: {len(vocab_lines)} 条")
    print(f"  输出文件: {config['output']}\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return config


def step1_cut_images(config):
    """
    切割 2x2 四宫格：
    - 优先检测分割线，按检测值切（更准）
    - 失败回退均分切割（round 边界更均匀）
    - 每块切完：自动剥边 + 统一纸底留白（根治白边不均匀）
    """
    print("=" * 50)
    print("步骤 1: 准备图片")
    print("=" * 50)

    if not (config.get("source_image") and config.get("grid")):
        raise RuntimeError("config 缺少 source_image/grid，无法切割")

    src = os.path.join(INPUT_DIR, config["source_image"])
    if not os.path.exists(src):
        raise FileNotFoundError(f"图片不存在: {src}")

    rows, cols = config["grid"]
    img = _convert_to_rgb_with_white_bg(Image.open(src))
    w, h = img.size
    print(f"  源图: {w}x{h}  网格: {rows}x{cols}")

    idx = 0

    # 2x2 特化：检测中线
    if rows == 2 and cols == 2 and ENABLE_SPLITLINE_DETECT:
        detect = _detect_split_lines_2x2(img)
        if detect:
            vx, hy, v_width, h_width = detect
            line_based_inset = int(max(v_width, h_width) * 0.9)
            inset = max(INSET_PX_MIN, line_based_inset)

            left_x2 = vx - v_width // 2
            right_x1 = vx + (v_width - v_width // 2)
            top_y2 = hy - h_width // 2
            bot_y1 = hy + (h_width - h_width // 2)

            boxes = [
                (0 + inset, 0 + inset, left_x2 - inset, top_y2 - inset),          # TL
                (right_x1 + inset, 0 + inset, w - inset, top_y2 - inset),         # TR
                (0 + inset, bot_y1 + inset, left_x2 - inset, h - inset),          # BL
                (right_x1 + inset, bot_y1 + inset, w - inset, h - inset),         # BR
            ]

            print(f"  检测分割线: vx={vx} (w={v_width}), hy={hy} (h={h_width}), inset={inset}px")

            for b in boxes:
                if idx >= len(config["scenes"]):
                    break
                cropped = _crop_safe(img, b)
                panel = _make_panel_card(cropped)
                out_path = os.path.join(OUTPUT_DIR, config["scenes"][idx]["image"])
                panel.save(out_path, quality=95)
                print(f"  切割: {config['scenes'][idx]['image']}")
                idx += 1

            print(f"  切出 {idx} 张图片 → output/\n")
            return

        print("  [提示] 分割线检测失败，回退为均分切割。")

    # —— 通用均分切割（round 边界避免像素丢失/偏移）
    cell_w = w / cols
    cell_h = h / rows
    inset_x, inset_y = _calc_inset(int(cell_w), int(cell_h))
    print(f"  均分切割: cell≈{cell_w:.2f}x{cell_h:.2f}, inset=({inset_x},{inset_y})")

    for r in range(rows):
        for c in range(cols):
            if idx >= len(config["scenes"]):
                break

            x1 = int(round(c * cell_w))
            y1 = int(round(r * cell_h))
            x2 = int(round((c + 1) * cell_w))
            y2 = int(round((r + 1) * cell_h))

            box = (x1 + inset_x, y1 + inset_y, x2 - inset_x, y2 - inset_y)
            cropped = _crop_safe(img, box)
            panel = _make_panel_card(cropped)

            out_path = os.path.join(OUTPUT_DIR, config["scenes"][idx]["image"])
            panel.save(out_path, quality=95)
            print(f"  切割: {config['scenes'][idx]['image']}")
            idx += 1

    print(f"  切出 {idx} 张图片 → output/\n")


# ============================================================
# 音频 / 字幕 / 合成
# ============================================================

async def step2_generate_audio(config, slow=False):
    """为每句台词生成语音到 output/audio_clips/"""
    rate = SLOW_RATE if slow else "+0%"
    suffix = "_slow" if slow else ""
    label = "慢速" if slow else "正常"

    print("=" * 50)
    print(f"步骤 2: 生成语音（{label}）")
    print("=" * 50)

    voices = config.get("voices", {})
    default_voice = config.get("voice", "en-US-GuyNeural")

    audio_dir = os.path.join(OUTPUT_DIR, f"audio_clips{suffix}")
    os.makedirs(audio_dir, exist_ok=True)

    all_lines = []
    line_index = 0

    for scene_idx, scene in enumerate(config["scenes"]):
        for line in scene["lines"]:
            line_index += 1
            text = line.get("text", "") if isinstance(line, dict) else str(line)
            speaker = line.get("speaker", "") if isinstance(line, dict) else ""
            text_cn = line.get("text_cn", "") if isinstance(line, dict) else ""
            voice = voices.get(speaker, default_voice)

            audio_file = os.path.join(audio_dir, f"line_{line_index:02d}.mp3")
            print(f"  [{line_index}] ({speaker or '旁白'}) {text[:60]}...")

            await generate_audio(text, audio_file, voice, rate=rate)
            duration = get_audio_duration(audio_file)

            all_lines.append({
                "scene_idx": scene_idx,
                "text": text,
                "text_cn": text_cn,
                "speaker": speaker,
                "audio_file": audio_file,
                "duration": duration
            })

    print(f"  共 {len(all_lines)} 条语音（{label}）\n")
    return all_lines


def step3_calc_durations(config, all_lines):
    """根据实际语音时长，计算每个场景显示时长"""
    print("=" * 50)
    print("步骤 3: 计算时长")
    print("=" * 50)

    gap = float(config.get("gap", 0.5))
    scene_durations = []

    for scene_idx in range(len(config["scenes"])):
        lines = [l for l in all_lines if l["scene_idx"] == scene_idx]
        total = sum((l.get("duration") or 0.0) + gap for l in lines)
        scene_durations.append(total)
        print(f"  场景 {scene_idx + 1}: {total:.2f}s ({len(lines)} 句)")

    print(f"  总时长: {sum(scene_durations):.2f}s\n")
    return scene_durations


def step4_generate_srt(config, all_lines, time_offset=0.0):
    """生成 SRT（双语：英文\\N中文）"""
    print("=" * 50)
    print("步骤 4: 生成字幕")
    print("=" * 50)

    gap = float(config.get("gap", 0.5))
    srt_content = []
    current_time = time_offset

    for i, line_info in enumerate(all_lines, 1):
        start = current_time
        end = current_time + (line_info.get("duration") or 0.0)

        srt_content.append(f"{i}")
        srt_content.append(f"{format_srt_time(start)} --> {format_srt_time(end)}")

        text = line_info.get("text", "")
        text_cn = line_info.get("text_cn", "")
        if text_cn:
            srt_content.append(f"{text}\\N{text_cn}")
        else:
            srt_content.append(text)

        srt_content.append("")
        current_time = end + gap

    srt_path = os.path.join(OUTPUT_DIR, "subtitles.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_content))

    print("  保存: output/subtitles.srt\n")
    return srt_path


def step5_merge_audio(config, all_lines):
    """拼接所有语音到 output/voiceover.mp3"""
    print("=" * 50)
    print("步骤 5: 拼接音频")
    print("=" * 50)

    gap = float(config.get("gap", 0.5))

    silence = os.path.join(OUTPUT_DIR, "_silence.mp3")
    ffmpeg_run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
        "-t", str(gap), "-c:a", "libmp3lame", silence
    ], "生成静音文件")

    concat_list = os.path.join(OUTPUT_DIR, "_audio_concat.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for line_info in all_lines:
            f.write(f"file '{line_info['audio_file'].replace(chr(92), '/')}'\n")
            f.write(f"file '{silence.replace(chr(92), '/')}'\n")

    merged = os.path.join(OUTPUT_DIR, "voiceover.mp3")
    ffmpeg_run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c:a", "libmp3lame", merged
    ], "拼接音频")

    for p in (silence, concat_list):
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass

    print("  保存: output/voiceover.mp3\n")
    return merged


# ============================================================
# 标题卡 / 海报
# ============================================================

_CN_FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]


def _load_font(size, prefer_cn=False):
    from PIL import ImageFont
    if prefer_cn:
        for fp in _CN_FONT_CANDIDATES:
            if os.path.exists(fp):
                try:
                    return ImageFont.truetype(fp, size)
                except OSError:
                    continue
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _wrap_text(draw, text, font, max_width):
    """按像素宽度自动换行（中英文混合）"""
    lines = []
    current = ""
    i = 0
    while i < len(text):
        ch = text[i]
        if ch.isascii() and (ch.isalpha() or ch == "'"):
            word = ""
            while i < len(text) and text[i].isascii() and not text[i].isspace():
                word += text[i]
                i += 1
            test = (current + " " + word).strip() if current else word
        elif ch == ' ':
            test = current + ch
            i += 1
        else:
            test = current + ch
            i += 1

        bbox = draw.textbbox((0, 0), test, font=font)
        if (bbox[2] - bbox[0]) <= max_width or not current:
            current = test
        else:
            lines.append(current.rstrip())
            if ch.isascii() and (ch.isalpha() or ch == "'"):
                current = word
            elif ch == ' ':
                current = ""
            else:
                current = ch

    if current.strip():
        lines.append(current.rstrip())
    return lines if lines else [text]


def generate_title_frame(title: str):
    """标题卡（1280x720 黑底）"""
    W, H = 1280, 720
    MARGIN_X = 80
    content_w = W - MARGIN_X * 2

    img = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    parts = re.split(r'\s*[—–]\s*', title, maxsplit=1)
    main_title = parts[0].strip()
    sub_title = parts[1].strip() if len(parts) > 1 else ""

    for size in [44, 38, 32, 28]:
        font_main = _load_font(size, prefer_cn=True)
        wrapped_main = _wrap_text(draw, main_title, font_main, content_w)
        if len(wrapped_main) <= 2:
            break

    font_sub = _load_font(28, prefer_cn=True)
    line_h_main = draw.textbbox((0, 0), "Ag中", font=font_main)[3] + 8
    total_h = line_h_main * len(wrapped_main)

    if sub_title:
        line_h_sub = draw.textbbox((0, 0), "Ag中", font=font_sub)[3] + 8
        total_h += 30 + line_h_sub

    y = (H - total_h) // 2

    for line in wrapped_main:
        bbox = draw.textbbox((0, 0), line, font=font_main)
        lw = bbox[2] - bbox[0]
        draw.text(((W - lw) // 2, y), line, fill=(255, 255, 255), font=font_main)
        y += line_h_main

    if sub_title:
        y += 10
        draw.line([(W // 2 - 100, y), (W // 2 + 100, y)], fill=(100, 100, 100), width=1)
        y += 20
        bbox = draw.textbbox((0, 0), sub_title, font=font_sub)
        lw = bbox[2] - bbox[0]
        draw.text(((W - lw) // 2, y), sub_title, fill=(200, 200, 200), font=font_sub)

    out_path = os.path.join(OUTPUT_DIR, "_title_card.png")
    img.save(out_path)
    return out_path


def generate_poster(vocab_lines, title=None, episode_num=None):
    """学习海报 — 卡片式排版"""
    import datetime

    if not vocab_lines:
        return None

    WIDTH = 1080
    PX = 50
    CARD_PX = 24
    CARD_PY = 20
    CARD_GAP = 18
    BG = (216, 200, 172)
    CARD_BG = (245, 240, 230)
    CARD_RADIUS = 14

    C_DARK = (38, 32, 26)
    C_MID = (90, 75, 58)
    C_LIGHT = (120, 105, 85)
    C_NUM = (190, 110, 45)
    C_HEADER_BG = (52, 42, 32)
    C_HEADER_TXT = (245, 238, 225)
    C_SERIAL = (155, 140, 118)

    font_header = _load_font(34, prefer_cn=True)
    font_serial = _load_font(20, prefer_cn=True)
    font_num = _load_font(30, prefer_cn=True)
    font_phrase = _load_font(30, prefer_cn=True)
    font_def = _load_font(24, prefer_cn=True)
    font_ex = _load_font(20, prefer_cn=True)

    card_inner_w = WIDTH - PX * 2 - CARD_PX * 2
    HEADER_H = 76

    raw_title = title or "Core Expressions"
    title_parts = re.split(r'\s*[—–]\s*', raw_title, maxsplit=1)
    header_text = "今日学习 | " + title_parts[0].strip()

    tmp_img = Image.new("RGB", (WIDTH, 100))
    td = ImageDraw.Draw(tmp_img)

    def _text_h(draw_obj, txt, font):
        bb = draw_obj.textbbox((0, 0), txt, font=font)
        return bb[3] - bb[1]

    card_heights = []
    for line in vocab_lines:
        parts = [p.strip() for p in line.split("—")]
        h = CARD_PY * 2
        if len(parts) >= 1 and parts[0]:
            for wl in _wrap_text(td, parts[0], font_phrase, card_inner_w - 50):
                h += _text_h(td, wl, font_phrase) + 6
            h += 6
        if len(parts) >= 2 and parts[1]:
            for wl in _wrap_text(td, parts[1], font_def, card_inner_w):
                h += _text_h(td, wl, font_def) + 4
            h += 6
        if len(parts) >= 3 and parts[2]:
            for wl in _wrap_text(td, f'e.g. {parts[2]}', font_ex, card_inner_w):
                h += _text_h(td, wl, font_ex) + 4
        card_heights.append(h)

    serial_row_h = 40
    top_section = 60 + HEADER_H + 16 + serial_row_h
    cards_total = sum(card_heights) + CARD_GAP * (len(card_heights) - 1) if card_heights else 0
    total_height = max(top_section + cards_total + 60, 500)

    img = Image.new("RGB", (WIDTH, total_height), BG)
    draw = ImageDraw.Draw(img)
    y = 60

    hr = [(PX, y), (WIDTH - PX, y + HEADER_H)]
    if hasattr(draw, "rounded_rectangle"):
        draw.rounded_rectangle(hr, radius=12, fill=C_HEADER_BG)
    else:
        draw.rectangle(hr, fill=C_HEADER_BG)
    bb = draw.textbbox((0, 0), header_text, font=font_header)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    draw.text(((WIDTH - tw) // 2, y + (HEADER_H - th) // 2),
              header_text, fill=C_HEADER_TXT, font=font_header)
    y += HEADER_H + 16

    today = datetime.date.today().strftime("%Y.%m.%d")
    ep = f"EP.{episode_num}  " if episode_num else ""
    serial = f"{ep}{today}"
    sb = draw.textbbox((0, 0), serial, font=font_serial)
    draw.text((WIDTH - PX - (sb[2] - sb[0]), y + 4), serial,
              fill=C_SERIAL, font=font_serial)
    y += serial_row_h

    for i, line in enumerate(vocab_lines):
        parts = [p.strip() for p in line.split("—")]
        ch = card_heights[i]

        card_rect = [(PX, y), (WIDTH - PX, y + ch)]
        if hasattr(draw, "rounded_rectangle"):
            draw.rounded_rectangle(card_rect, radius=CARD_RADIUS, fill=CARD_BG)
        else:
            draw.rectangle(card_rect, fill=CARD_BG)

        cy = y + CARD_PY
        left = PX + CARD_PX

        if len(parts) >= 1 and parts[0]:
            num_str = f"{i + 1}"
            nb = draw.textbbox((0, 0), num_str, font=font_num)
            nw = nb[2] - nb[0]
            draw.text((left, cy), num_str, fill=C_NUM, font=font_num)
            phrase_left = left + nw + 10
            for wl in _wrap_text(draw, parts[0], font_phrase, card_inner_w - nw - 10):
                draw.text((phrase_left, cy), wl, fill=C_DARK, font=font_phrase)
                cy += _text_h(draw, wl, font_phrase) + 6
            cy += 6

        if len(parts) >= 2 and parts[1]:
            for wl in _wrap_text(draw, parts[1], font_def, card_inner_w):
                draw.text((left, cy), wl, fill=C_MID, font=font_def)
                cy += _text_h(draw, wl, font_def) + 4
            cy += 6

        if len(parts) >= 3 and parts[2]:
            for wl in _wrap_text(draw, f'e.g. {parts[2]}', font_ex, card_inner_w):
                draw.text((left, cy), wl, fill=C_LIGHT, font=font_ex)
                cy += _text_h(draw, wl, font_ex) + 4

        y += ch + CARD_GAP

    poster_path = os.path.join(OUTPUT_DIR, "poster.png")
    img.save(poster_path, quality=95)
    print(f"  海报已生成: output/poster.png  ({WIDTH}x{total_height})")
    return poster_path


def step6_make_video(config, scene_durations, merged_audio, srt_path):
    """图片转视频 → 合并音频 → 烧录字幕"""
    print("=" * 50)
    print("步骤 6: 合成视频")
    print("=" * 50)

    output = os.path.join(OUTPUT_DIR, config["output"])
    title = config.get("title")
    temp_files = []

    # 6a 图片序列 → 无声视频
    img_list = os.path.join(OUTPUT_DIR, "_img_concat.txt")
    temp_files.append(img_list)

    with open(img_list, "w", encoding="utf-8") as f:
        if title:
            title_img = generate_title_frame(title)
            temp_files.append(title_img)
            f.write(f"file '{title_img.replace(chr(92), '/')}'\n")
            f.write(f"duration {TITLE_DURATION}\n")

        for i, scene in enumerate(config["scenes"]):
            img_path = os.path.join(OUTPUT_DIR, scene["image"]).replace("\\", "/")
            f.write(f"file '{img_path}'\n")
            f.write(f"duration {scene_durations[i]}\n")

        last_img = os.path.join(OUTPUT_DIR, config["scenes"][-1]["image"]).replace("\\", "/")
        f.write(f"file '{last_img}'\n")

    temp1 = os.path.join(OUTPUT_DIR, "_temp_video.mp4")
    temp_files.append(temp1)

    print("  [6a] 图片 → 视频（无声）...")
    ffmpeg_run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", img_list,
        "-vf", "scale=1280:660:force_original_aspect_ratio=decrease,"
               "pad=1280:720:(ow-iw)/2:0:color=black",
        "-c:v", "libx264", "-crf", "0", "-pix_fmt", "yuv420p", "-r", "30", temp1
    ], "图片转视频")

    # 6b 标题卡静音 + 正文配音
    temp_audio = os.path.join(OUTPUT_DIR, "_temp_full_audio.mp3")
    temp_files.append(temp_audio)

    audio_parts_list = os.path.join(OUTPUT_DIR, "_audio_full_concat.txt")
    temp_files.append(audio_parts_list)

    print("  [6b] 合并音频...")
    with open(audio_parts_list, "w", encoding="utf-8") as f:
        if title:
            title_silence = os.path.join(OUTPUT_DIR, "_title_silence.mp3")
            temp_files.append(title_silence)
            ffmpeg_run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                "-t", str(TITLE_DURATION), "-c:a", "libmp3lame", title_silence
            ], "标题静音")
            f.write(f"file '{title_silence.replace(chr(92), '/')}'\n")

        f.write(f"file '{merged_audio.replace(chr(92), '/')}'\n")

    ffmpeg_run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", audio_parts_list, "-c:a", "libmp3lame", temp_audio
    ], "拼接完整音频")

    # 6c 合并音视频 + 烧录字幕
    srt_escaped = srt_path.replace("\\", "/").replace(":", "\\:")

    style = "FontSize=14,PrimaryColour=&Hffffff,OutlineColour=&H000000,BorderStyle=1,Outline=1,Shadow=0,MarginV=8,Alignment=2"
    if os.name == "nt":
        style = "FontName=Microsoft YaHei," + style

    print("  [6c] 合并音视频 + 烧录字幕...")
    ffmpeg_run([
        "ffmpeg", "-y", "-i", temp1, "-i", temp_audio,
        "-vf", f"subtitles='{srt_escaped}':force_style='{style}'",
        "-c:v", "libx264", "-crf", "18", "-preset", "slow",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0", "-shortest",
        "-movflags", "+faststart",
        output
    ], "合并音视频+烧录字幕")

    # 清理临时文件
    for p in temp_files:
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass

    print(f"\n  输出: output/{config['output']}\n")
    return output


# ============================================================
# 主流程
# ============================================================

async def build_video(config, slow=False):
    """生成单个版本（正常/慢速）"""
    label = "慢速版" if slow else "正常版"

    print("\n" + "#" * 50)
    print(f"  生成{label}")
    print("#" * 50 + "\n")

    all_lines = await step2_generate_audio(config, slow=slow)
    scene_durations = step3_calc_durations(config, all_lines)

    srt_offset = TITLE_DURATION if config.get("title") else 0.0
    srt_path = step4_generate_srt(config, all_lines, time_offset=srt_offset)

    merged_audio = step5_merge_audio(config, all_lines)

    base_name = config["output"]
    if slow:
        name, ext = os.path.splitext(base_name)
        config_copy = dict(config)
        config_copy["output"] = f"{name}_slow{ext}"
    else:
        config_copy = config

    output = step6_make_video(config_copy, scene_durations, merged_audio, srt_path)
    return output


async def main():
    if len(sys.argv) < 2:
        print("用法: python make_video.py <项目文件夹名>")
        sys.exit(1)

    project_name = sys.argv[1]
    init_paths(project_name)

    print(f"项目: {project_name}")
    print(f"路径: {PROJECT_DIR}\n")

    config = step0_load_config()
    step1_cut_images(config)

    output_normal = await build_video(config, slow=False)
    output_slow = await build_video(config, slow=True)

    poster_path = None
    vocab = config.get("vocab", [])
    if vocab:
        print("=" * 50)
        print("生成要点海报")
        print("=" * 50)
        ep_match = re.match(r'(\d+)', os.path.basename(PROJECT_DIR))
        ep_num = int(ep_match.group(1)) if ep_match else None
        poster_path = generate_poster(vocab, title=config.get("title"), episode_num=ep_num)

    print("=" * 50)
    print("完成！")
    print(f"  正常版: {output_normal}")
    print(f"  慢速版: {output_slow}")
    if poster_path:
        print(f"  要点海报: {poster_path}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
