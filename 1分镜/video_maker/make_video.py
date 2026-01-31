# -*- coding: utf-8 -*-
"""
分镜视频生成器
用法: python make_video.py <项目文件夹名>
例如: python make_video.py 3地铁搭讪

项目文件夹结构:
  项目文件夹/
    input/    ← 放图片和文本
    output/   ← 自动生成所有输出

文本格式:
  - 角色标记: M1: M2: (男) / F1: F2: (女)
  - 场景分隔: ---
  - 其他行自动忽略（如 Scene: / Setting: 等描述）
"""
import asyncio
import edge_tts
import json
import math
import os
import re
import subprocess
import sys
from PIL import Image


# ============================================================
# 路径定义（由命令行参数决定）
# ============================================================

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def init_paths(project_name):
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
# 工具函数
# ============================================================

def get_audio_duration(file_path):
    """用 ffprobe 获取音频文件的实际时长（秒）"""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", file_path],
        capture_output=True
    )
    return float(result.stdout.decode("utf-8").strip())


def format_srt_time(seconds):
    """秒数 → SRT 时间格式 00:00:00,000"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def ffmpeg_run(args, desc=""):
    """运行 FFmpeg 命令，失败时打印错误信息"""
    result = subprocess.run(args, capture_output=True)
    if result.returncode != 0:
        print(f"  [错误] {desc}")
        stderr = result.stderr.decode("utf-8", errors="ignore")
        print(stderr[-500:] if stderr else "无错误输出")
        raise RuntimeError(f"FFmpeg 失败: {desc}")
    return result


async def generate_audio(text, output_file, voice, rate="+0%"):
    """调用 Edge TTS 生成单句语音，rate 控制语速如 '-30%'"""
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_file)


# ============================================================
# 文本解析
# ============================================================

# 匹配 M1: / F2: / M10: 等格式（冒号后面是台词）
SPEAKER_PATTERN = re.compile(r'^([MF]\d+)\s*[:：]\s*(.+)$')
# 匹配括号内的舞台提示，如 (laughs) (standing near the door)
STAGE_DIRECTION = re.compile(r'\([^)]*\)\s*')


def parse_text_file(text_path):
    """
    解析文本文件，返回 (title, scenes, speakers_set, vocab_lines)
    title: 开头标题字符串，无则为 None
    scenes: [ [{"speaker": "M1", "text": "...", "text_cn": "..."}, ...], ... ]
    speakers_set: {"M1", "F1", ...}
    vocab_lines: ["get off at — 在…下车 — ...", ...]
    """
    with open(text_path, "r", encoding="utf-8") as f:
        raw_lines = f.read().splitlines()

    # 分离 === 之后的核心表达部分
    main_lines = []
    vocab_lines = []
    in_vocab = False
    for raw in raw_lines:
        if raw.strip() == "===":
            in_vocab = True
            continue
        if in_vocab:
            if raw.strip():
                vocab_lines.append(raw.strip())
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

        # 场景分隔符
        if line == "---":
            if current_scene:
                scenes.append(current_scene)
                current_scene = []
            continue

        # 尝试匹配角色台词
        m = SPEAKER_PATTERN.match(line)
        if m:
            found_first_dialogue = True
            speaker = m.group(1).upper()
            full_text = STAGE_DIRECTION.sub('', m.group(2)).strip()
            # 解析双语分隔符 |
            if '|' in full_text:
                parts = full_text.split('|', 1)
                text = parts[0].strip()
                text_cn = parts[1].strip()
            else:
                text = full_text
                text_cn = ""
            if text:
                current_scene.append({
                    "speaker": speaker,
                    "text": text,
                    "text_cn": text_cn
                })
                speakers.add(speaker)
        else:
            # 第一个 --- 之前、第一句台词之前的非空行视为标题
            if not found_first_dialogue and title is None:
                title = line

    # 最后一个场景
    if current_scene:
        scenes.append(current_scene)

    return title, scenes, speakers, vocab_lines


def assign_voices(speakers):
    """
    根据角色编号自动分配声音
    M1→男声池[0], M2→男声池[1], ...
    F1→女声池[0], F2→女声池[1], ...
    """
    voices = {}
    for s in sorted(speakers):
        gender = s[0]       # 'M' or 'F'
        num = int(s[1:])    # 编号，从 1 开始
        if gender == 'M':
            voices[s] = MALE_VOICES[(num - 1) % len(MALE_VOICES)]
        else:
            voices[s] = FEMALE_VOICES[(num - 1) % len(FEMALE_VOICES)]
    return voices


def calc_grid(scene_count):
    """根据场景数量自动计算网格布局 (rows, cols)"""
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
    """在 input/ 中查找图片文件"""
    for fname in os.listdir(INPUT_DIR):
        if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp')):
            return fname
    return None


# ============================================================
# 核心流程
# ============================================================

def step0_load_config():
    """自动从 input/文本 + 图片生成配置，或读取已有 config.json"""
    print("=" * 50)
    print("步骤 0: 加载配置")
    print("=" * 50)

    # 查找文本文件
    text_path = None
    for fname in os.listdir(INPUT_DIR):
        if fname.lower().endswith('.txt'):
            text_path = os.path.join(INPUT_DIR, fname)
            break

    if text_path:
        # 自动解析模式
        print(f"  发现文本: {os.path.basename(text_path)}")
        title, scenes_data, speakers, vocab_lines = parse_text_file(text_path)

        if not scenes_data:
            print("  [错误] 文本中未解析到任何台词！")
            print("  请使用 M1:/F1: 等格式标记角色")
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

        # 打印信息
        print(f"  场景数量: {len(config['scenes'])}")
        print(f"  网格布局: {grid[0]}×{grid[1]}")
        print(f"  角色配音:")
        for s in sorted(voices):
            print(f"    {s} → {voices[s]}")
        print(f"  源图片:   {source_image or '无'}")
        print(f"  标题:     {title or '无'}")
        print(f"  核心表达: {len(vocab_lines)} 条")
        print(f"  输出文件: {config['output']}\n")

    else:
        print("  [错误] input/ 中没有 .txt 文本文件！")
        sys.exit(1)

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    return config


def step1_cut_images(config):
    """如果配置了 source_image + grid，从 input/ 读取并切割到 output/"""
    print("=" * 50)
    print("步骤 1: 准备图片")
    print("=" * 50)

    if "source_image" in config and config["source_image"] and "grid" in config:
        src = os.path.join(INPUT_DIR, config["source_image"])
        if not os.path.exists(src):
            raise FileNotFoundError(f"图片不存在: {src}")

        rows, cols = config["grid"]
        img = Image.open(src)
        w, h = img.size
        cell_w, cell_h = w // cols, h // rows

        idx = 0
        for r in range(rows):
            for c in range(cols):
                if idx >= len(config["scenes"]):
                    break
                box = (c * cell_w, r * cell_h, (c + 1) * cell_w, (r + 1) * cell_h)
                cropped = img.crop(box)
                out_path = os.path.join(OUTPUT_DIR, config["scenes"][idx]["image"])
                cropped.save(out_path)
                print(f"  切割: {config['scenes'][idx]['image']}")
                idx += 1
        print(f"  从 input/{config['source_image']} 切出 {idx} 张图片 → output/\n")
    else:
        # 不切割，从 input/ 复制或直接引用
        for scene in config["scenes"]:
            src = os.path.join(INPUT_DIR, scene["image"])
            dst = os.path.join(OUTPUT_DIR, scene["image"])
            if os.path.exists(src) and not os.path.exists(dst):
                Image.open(src).save(dst)
                print(f"  复制: input/{scene['image']} → output/")
            elif os.path.exists(dst):
                print(f"  已有: output/{scene['image']}")
            else:
                raise FileNotFoundError(f"图片不存在: input/{scene['image']}")
        print()


async def step2_generate_audio(config, slow=False):
    """为每句台词生成语音到 output/audio_clips/"""
    rate = SLOW_RATE if slow else "+0%"
    suffix = "_slow" if slow else ""
    label = "慢速" if slow else "正常"

    print("=" * 50)
    print(f"步骤 2: 生成语音（{label}）")
    print("=" * 50)

    # 支持多角色配音 (voices dict) 或单一配音 (voice string)
    voices = config.get("voices", {})
    default_voice = config.get("voice", "en-US-GuyNeural")

    audio_dir = os.path.join(OUTPUT_DIR, f"audio_clips{suffix}")
    os.makedirs(audio_dir, exist_ok=True)
    all_lines = []
    line_index = 0

    for scene_idx, scene in enumerate(config["scenes"]):
        for line in scene["lines"]:
            line_index += 1
            # 支持新格式 {"speaker": "M1", "text": "..."} 和旧格式纯字符串
            if isinstance(line, dict):
                text = line["text"]
                speaker = line.get("speaker", "")
                voice = voices.get(speaker, default_voice)
            else:
                text = line
                speaker = ""
                voice = default_voice

            audio_file = os.path.join(audio_dir, f"line_{line_index:02d}.mp3")
            print(f"  [{line_index}] ({speaker or '旁白'}) {text[:50]}...")
            await generate_audio(text, audio_file, voice, rate=rate)
            duration = get_audio_duration(audio_file)
            all_lines.append({
                "scene_idx": scene_idx,
                "text": text,
                "text_cn": line.get("text_cn", "") if isinstance(line, dict) else "",
                "speaker": speaker,
                "audio_file": audio_file,
                "duration": duration
            })

    print(f"  共 {len(all_lines)} 条语音（{label}）\n")
    return all_lines


def step3_calc_durations(config, all_lines):
    """根据实际语音时长，计算每个场景的显示时长"""
    print("=" * 50)
    print("步骤 3: 计算时长")
    print("=" * 50)

    gap = config["gap"]
    scene_durations = []

    for scene_idx in range(len(config["scenes"])):
        lines = [l for l in all_lines if l["scene_idx"] == scene_idx]
        total = sum(l["duration"] + gap for l in lines)
        scene_durations.append(total)
        print(f"  场景 {scene_idx + 1}: {total:.2f}s ({len(lines)} 句)")

    print(f"  总时长: {sum(scene_durations):.2f}s\n")
    return scene_durations


def step4_generate_srt(config, all_lines, time_offset=0.0):
    """生成 SRT 字幕文件到 output/（支持双语）"""
    print("=" * 50)
    print("步骤 4: 生成字幕")
    print("=" * 50)

    gap = config["gap"]
    srt_content = []
    current_time = time_offset  # 标题卡之后才开始

    for i, line_info in enumerate(all_lines, 1):
        start = current_time
        end = current_time + line_info["duration"]
        srt_content.append(f"{i}")
        srt_content.append(f"{format_srt_time(start)} --> {format_srt_time(end)}")
        # 双语字幕：英文 \N 中文
        text_cn = line_info.get("text_cn", "")
        if text_cn:
            srt_content.append(f"{line_info['text']}\\N{text_cn}")
        else:
            srt_content.append(line_info["text"])
        srt_content.append("")
        current_time = end + gap

    srt_path = os.path.join(OUTPUT_DIR, "subtitles.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_content))

    print(f"  保存: output/subtitles.srt\n")
    return srt_path


def step5_merge_audio(config, all_lines):
    """顺序拼接所有语音片段到 output/"""
    print("=" * 50)
    print("步骤 5: 拼接音频")
    print("=" * 50)

    gap = config["gap"]

    # 生成静音文件
    silence = os.path.join(OUTPUT_DIR, "_silence.mp3")
    ffmpeg_run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono",
        "-t", str(gap), "-c:a", "libmp3lame", silence
    ], "生成静音文件")

    # 写拼接列表
    concat_list = os.path.join(OUTPUT_DIR, "_audio_concat.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for line_info in all_lines:
            f.write(f"file '{line_info['audio_file'].replace(chr(92), '/')}'\n")
            f.write(f"file '{silence.replace(chr(92), '/')}'\n")

    # 拼接
    merged = os.path.join(OUTPUT_DIR, "voiceover.mp3")
    ffmpeg_run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c:a", "libmp3lame", merged
    ], "拼接音频")

    # 清理
    os.remove(silence)
    os.remove(concat_list)

    print(f"  保存: output/voiceover.mp3\n")
    return merged


TITLE_DURATION = 3.0   # 标题卡显示秒数
VOCAB_DURATION = 6.0   # 每张核心表达卡片显示秒数
SLOW_RATE = "-30%"     # 慢速版本语速

# 支持中文的字体查找顺序
_CN_FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",     # 微软雅黑
    "C:/Windows/Fonts/simhei.ttf",   # 黑体
    "C:/Windows/Fonts/simsun.ttc",   # 宋体
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]


def _load_font(size, prefer_cn=False):
    """加载字体，prefer_cn=True 时优先加载中文字体"""
    from PIL import ImageFont
    if prefer_cn:
        for fp in _CN_FONT_CANDIDATES:
            if os.path.exists(fp):
                try:
                    return ImageFont.truetype(fp, size)
                except OSError:
                    continue
    # 回退到 Arial 或默认
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def generate_title_frame(title):
    """用 PIL 生成标题卡图片（1280x720 黑底白字）"""
    from PIL import ImageDraw
    img = Image.new("RGB", (1280, 720), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _load_font(48, prefer_cn=True)
    bbox = draw.textbbox((0, 0), title, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (1280 - tw) // 2
    y = (720 - th) // 2
    draw.text((x, y), title, fill=(255, 255, 255), font=font)
    out_path = os.path.join(OUTPUT_DIR, "_title_card.png")
    img.save(out_path)
    return out_path


def generate_vocab_cards(vocab_lines):
    """用 PIL 为每条核心表达生成卡片图片（1280x720，支持中文）"""
    from PIL import ImageDraw
    font_big = _load_font(36, prefer_cn=True)
    font_small = _load_font(28, prefer_cn=True)

    card_paths = []
    for i, line in enumerate(vocab_lines):
        img = Image.new("RGB", (1280, 720), color=(20, 20, 30))
        draw = ImageDraw.Draw(img)

        # 标题 "Core Expressions" 在顶部
        if i == 0:
            header = "Core Expressions"
            hbox = draw.textbbox((0, 0), header, font=font_big)
            hx = (1280 - (hbox[2] - hbox[0])) // 2
            draw.text((hx, 40), header, fill=(255, 200, 80), font=font_big)

        # 解析：短语 — 释义 — 例句（用 — 分隔）
        parts = [p.strip() for p in line.split("—")]
        y = 200
        colors = [(255, 255, 255), (180, 220, 255), (200, 200, 200)]
        fonts = [font_big, font_small, font_small]
        for j, part in enumerate(parts):
            if not part:
                continue
            f = fonts[min(j, len(fonts) - 1)]
            c = colors[min(j, len(colors) - 1)]
            bbox = draw.textbbox((0, 0), part, font=f)
            tx = (1280 - (bbox[2] - bbox[0])) // 2
            draw.text((tx, y), part, fill=c, font=f)
            y += (bbox[3] - bbox[1]) + 30

        card_path = os.path.join(OUTPUT_DIR, f"_vocab_{i + 1:02d}.png")
        img.save(card_path)
        card_paths.append(card_path)

    return card_paths


def step6_make_video(config, scene_durations, merged_audio, srt_path):
    """图片转视频 → 合并音频 → 烧录字幕，输出到 output/"""
    print("=" * 50)
    print("步骤 6: 合成视频")
    print("=" * 50)

    output = os.path.join(OUTPUT_DIR, config["output"])
    title = config.get("title")
    vocab = config.get("vocab", [])
    temp_files = []  # 收集所有临时文件，最后统一清理

    # 6a. 图片序列 → 无声视频（场景正文部分）
    img_list = os.path.join(OUTPUT_DIR, "_img_concat.txt")
    temp_files.append(img_list)
    with open(img_list, "w", encoding="utf-8") as f:
        # 开头标题卡
        if title:
            title_img = generate_title_frame(title)
            temp_files.append(title_img)
            f.write(f"file '{title_img.replace(chr(92), '/')}'\n")
            f.write(f"duration {TITLE_DURATION}\n")

        # 正文场景
        for i, scene in enumerate(config["scenes"]):
            img_path = os.path.join(OUTPUT_DIR, scene["image"]).replace("\\", "/")
            f.write(f"file '{img_path}'\n")
            f.write(f"duration {scene_durations[i]}\n")

        # 片尾核心表达卡片
        if vocab:
            card_paths = generate_vocab_cards(vocab)
            for cp in card_paths:
                temp_files.append(cp)
                f.write(f"file '{cp.replace(chr(92), '/')}'\n")
                f.write(f"duration {VOCAB_DURATION}\n")

        # concat 格式要求最后一帧重复（否则最后一张会闪过）
        if vocab:
            f.write(f"file '{card_paths[-1].replace(chr(92), '/')}'\n")
        else:
            last_img = os.path.join(OUTPUT_DIR, config["scenes"][-1]["image"]).replace("\\", "/")
            f.write(f"file '{last_img}'\n")

    temp1 = os.path.join(OUTPUT_DIR, "_temp_video.mp4")
    temp_files.append(temp1)
    print("  [6a] 图片 → 视频...")
    # 图片缩放到 1280x660，底部留 60px 黑条用于字幕，总高度 720
    ffmpeg_run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", img_list,
        "-vf", "scale=1280:660:force_original_aspect_ratio=decrease,"
               "pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", temp1
    ], "图片转视频")

    # 6b. 合并音频（标题卡期间静音 + 正文配音 + 片尾静音）
    temp_audio = os.path.join(OUTPUT_DIR, "_temp_full_audio.mp3")
    temp_files.append(temp_audio)
    print("  [6b] 合并音频...")

    # 生成静音段
    audio_parts_list = os.path.join(OUTPUT_DIR, "_audio_full_concat.txt")
    temp_files.append(audio_parts_list)

    with open(audio_parts_list, "w", encoding="utf-8") as f:
        # 标题卡静音
        if title:
            title_silence = os.path.join(OUTPUT_DIR, "_title_silence.mp3")
            temp_files.append(title_silence)
            ffmpeg_run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                "-t", str(TITLE_DURATION), "-c:a", "libmp3lame", title_silence
            ], "标题静音")
            f.write(f"file '{title_silence.replace(chr(92), '/')}'\n")

        # 正文配音
        f.write(f"file '{merged_audio.replace(chr(92), '/')}'\n")

        # 片尾静音
        if vocab:
            vocab_silence = os.path.join(OUTPUT_DIR, "_vocab_silence.mp3")
            temp_files.append(vocab_silence)
            total_vocab_dur = VOCAB_DURATION * len(vocab)
            ffmpeg_run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                "-t", str(total_vocab_dur), "-c:a", "libmp3lame", vocab_silence
            ], "片尾静音")
            f.write(f"file '{vocab_silence.replace(chr(92), '/')}'\n")

    ffmpeg_run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", audio_parts_list, "-c:a", "libmp3lame", temp_audio
    ], "拼接完整音频")

    # 6c. 合并音视频
    temp2 = os.path.join(OUTPUT_DIR, "_temp_with_audio.mp4")
    temp_files.append(temp2)
    print("  [6c] 合并音视频...")
    ffmpeg_run([
        "ffmpeg", "-y", "-i", temp1, "-i", temp_audio,
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0", "-shortest", temp2
    ], "合并音视频")

    # 6d. 烧录字幕（字幕显示在底部黑色区域，不遮挡画面）
    srt_escaped = srt_path.replace("\\", "/").replace(":", "\\:")
    print("  [6d] 烧录字幕...")
    ffmpeg_run([
        "ffmpeg", "-y", "-i", temp2,
        "-vf", f"subtitles='{srt_escaped}':force_style='FontSize=20,FontName=Microsoft YaHei,"
               f"PrimaryColour=&Hffffff,OutlineColour=&H000000,BorderStyle=1,"
               f"Outline=1,Shadow=0,MarginV=5,Alignment=2'",
        "-c:v", "libx264", "-c:a", "copy", output
    ], "烧录字幕")

    # 清理临时文件
    for f in temp_files:
        if os.path.exists(f):
            os.remove(f)

    print(f"\n  输出: output/{config['output']}\n")
    return output


# ============================================================
# 主流程
# ============================================================

async def build_video(config, slow=False):
    """生成单个版本的视频（正常或慢速）"""
    label = "慢速版" if slow else "正常版"

    print("\n" + "#" * 50)
    print(f"  生成{label}")
    print("#" * 50 + "\n")

    all_lines = await step2_generate_audio(config, slow=slow)
    scene_durations = step3_calc_durations(config, all_lines)

    srt_offset = TITLE_DURATION if config.get("title") else 0.0
    srt_path = step4_generate_srt(config, all_lines, time_offset=srt_offset)

    merged_audio = step5_merge_audio(config, all_lines)

    # 慢速版输出文件名加 _slow
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
        print("例如: python make_video.py 3地铁搭讪")
        sys.exit(1)

    project_name = sys.argv[1]
    init_paths(project_name)

    print(f"项目: {project_name}")
    print(f"路径: {PROJECT_DIR}\n")

    config = step0_load_config()
    step1_cut_images(config)

    # 生成正常版
    output_normal = await build_video(config, slow=False)

    # 生成慢速版
    output_slow = await build_video(config, slow=True)

    print("=" * 50)
    print(f"完成！")
    print(f"  正常版: {output_normal}")
    print(f"  慢速版: {output_slow}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
