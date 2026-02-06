# -*- coding: utf-8 -*-
"""
分镜视频生成器（适配多图版）
用法: python make_video.py <项目文件夹名>

适配 gen_text.py 生成的独立分镜图片 (1.png, 2.png...)
"""

import asyncio
import edge_tts
import os
import re
import subprocess
import sys
import math
from PIL import Image, ImageDraw, ImageOps

# ============================================================
# 路径定义
# ============================================================

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def init_paths(project_name: str):
    global PROJECT_DIR, INPUT_DIR, OUTPUT_DIR
    PROJECT_DIR = os.path.join(ROOT_DIR, project_name)
    INPUT_DIR = os.path.join(PROJECT_DIR, "input")
    OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")

    if not os.path.isdir(INPUT_DIR):
        print(f"[错误] 项目文件夹不存在: {INPUT_DIR}")
        sys.exit(1)

# ============================================================
# 声音配置
# ============================================================

MALE_VOICES = ["en-US-GuyNeural", "en-US-ChristopherNeural", "en-US-EricNeural"]
FEMALE_VOICES = ["en-US-JennyNeural", "en-US-AriaNeural", "en-US-MichelleNeural"]

# ============================================================
# 视觉参数（统一画布风格）
# ============================================================

PANEL_OUT_SIZE = (1280, 660)       # 视频画面尺寸（略小于720p，留给字幕空间）
PANEL_PAPER_COLOR = (248, 246, 240) # 暖白纸色背景
PANEL_PAPER_BORDER = 0              # 图片距离画布边缘的距离 (0表示铺满高度)
PANEL_INNER_PAD = 10                # 给图片加一个小衬底边框

TITLE_DURATION = 3.0
SLOW_RATE = "-30%"

# ============================================================
# 工具函数
# ============================================================

def _bytes_to_text(b: bytes) -> str:
    if not b: return ""
    try: return b.decode("utf-8", errors="ignore")
    except: return b.decode(errors="ignore")

def run_cmd(args, desc=""):
    result = subprocess.run(args, capture_output=True, text=False)
    if result.returncode != 0:
        print(f"  [错误] {desc}")
        print(_bytes_to_text(result.stderr)[-500:])
        raise RuntimeError(f"命令失败: {desc}")
    return result

def ffmpeg_run(args, desc=""):
    return run_cmd(args, desc=desc)

def get_audio_duration(file_path: str) -> float:
    try:
        res = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            capture_output=True, text=False
        )
        s = _bytes_to_text(res.stdout).strip()
        return float(s) if s else 0.0
    except:
        return 0.0

def format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

async def generate_audio(text: str, output_file: str, voice: str, rate="+0%"):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_file)

# ============================================================
# 文本解析
# ============================================================

SPEAKER_PATTERN = re.compile(r'^([MF]\d+)\s*[:：]\s*(.+)$')
STAGE_DIRECTION = re.compile(r'\([^)]*\)\s*')

def parse_text_file(text_path: str):
    with open(text_path, "r", encoding="utf-8") as f:
        raw_lines = f.read().splitlines()

    main_lines = []
    vocab_lines = []
    in_vocab = False

    for raw in raw_lines:
        s = raw.strip()
        if s == "===":
            in_vocab = not in_vocab # 简单翻转，处理可能的多个分隔符
            continue
        
        if in_vocab:
            # 简单过滤 Panel 说明，只留词汇
            if "Panel" in s or "分镜" in s: continue
            if s.count("—") >= 1: # 只要有分隔符就算词汇
                vocab_lines.append(s)
        else:
            if s: main_lines.append(s)

    scenes = []
    current_scene = []
    speakers = set()
    title = None
    
    for line in main_lines:
        line = line.strip()
        if not line: continue
        
        if line == "---":
            if current_scene:
                scenes.append(current_scene)
                current_scene = []
            continue

        m = SPEAKER_PATTERN.match(line)
        if m:
            speaker = m.group(1).upper()
            full_text = STAGE_DIRECTION.sub('', m.group(2)).strip()
            if '|' in full_text:
                parts = full_text.split('|', 1)
                text, text_cn = parts[0].strip(), parts[1].strip()
            else:
                text, text_cn = full_text, ""
            
            current_scene.append({"speaker": speaker, "text": text, "text_cn": text_cn})
            speakers.add(speaker)
        elif not title and not line.startswith("Panel"):
            title = line

    if current_scene: scenes.append(current_scene)
    return title, scenes, speakers, vocab_lines

def assign_voices(speakers):
    voices = {}
    for s in sorted(speakers):
        gender = s[0]
        num = int(s[1:])
        pool = MALE_VOICES if gender == 'M' else FEMALE_VOICES
        voices[s] = pool[(num - 1) % len(pool)]
    return voices

# ============================================================
# 核心步骤
# ============================================================

def _load_font(size, prefer_cn=False):
    # 简单的字体加载兜底
    from PIL import ImageFont
    fonts = [
        "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf", 
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/PingFang.ttc"
    ]
    if prefer_cn:
        for f in fonts:
            if os.path.exists(f):
                try: return ImageFont.truetype(f, size)
                except: continue
    try: return ImageFont.truetype("arial.ttf", size)
    except: return ImageFont.load_default()

def _wrap_text(draw, text, font, max_width):
    # 简易换行
    lines = []
    if draw.textlength(text, font=font) <= max_width:
        return [text]
    # 暴力按字符拆分（简单处理中英文）
    curr = ""
    for char in text:
        if draw.textlength(curr + char, font=font) <= max_width:
            curr += char
        else:
            lines.append(curr)
            curr = char
    if curr: lines.append(curr)
    return lines

# ------------------------------------------------------------
# 步骤 0: 加载配置
# ------------------------------------------------------------

def step0_load_config():
    print("=" * 50)
    print("步骤 0: 加载配置")
    print("=" * 50)

    text_path = os.path.join(INPUT_DIR, "文本.txt")
    if not os.path.exists(text_path):
        # 尝试找其他 txt
        txts = [f for f in os.listdir(INPUT_DIR) if f.endswith(".txt")]
        if not txts:
            print("[错误] input/ 中没有文本.txt")
            sys.exit(1)
        text_path = os.path.join(INPUT_DIR, txts[0])

    print(f"  文本: {os.path.basename(text_path)}")
    title, scenes_data, speakers, vocab_lines = parse_text_file(text_path)

    if not scenes_data:
        print("[错误] 文本中未解析到台词！")
        sys.exit(1)

    # 寻找图片序列 (1.png, 2.png ...)
    image_files = {}
    for f in os.listdir(INPUT_DIR):
        if f.lower().endswith(('.png', '.jpg', '.jpeg')):
            name = os.path.splitext(f)[0]
            if name.isdigit():
                image_files[int(name)] = f
    
    # 按数字排序
    sorted_indices = sorted(image_files.keys())
    if not sorted_indices:
        print("[错误] input/ 中没有找到数字命名的分镜图片 (如 1.png)！")
        sys.exit(1)

    print(f"  找到 {len(sorted_indices)} 张分镜图片: {sorted_indices}")

    config = {
        "voices": assign_voices(speakers),
        "gap": 0.5,
        "output": os.path.basename(PROJECT_DIR) + ".mp4",
        "title": title,
        "vocab": vocab_lines,
        "scenes": []
    }

    # 匹配场景和图片
    # 如果图片比场景少，这就尴尬了；如果图片多，没关系
    for i, scene_lines in enumerate(scenes_data):
        img_idx = i + 1
        # 如果对应的图片不存在，就用最后一张兜底，或者报错
        if img_idx not in image_files:
            if img_idx > max(sorted_indices):
                actual_img = image_files[max(sorted_indices)] # 用最后一张
            else:
                actual_img = image_files[sorted_indices[0]] # 随便找一张
        else:
            actual_img = image_files[img_idx]

        config["scenes"].append({
            "source_image": actual_img,
            "processed_image": f"scene_{img_idx:02d}.png",
            "lines": scene_lines
        })

    print(f"  已规划 {len(config['scenes'])} 个视频场景")
    print(f"  输出: {config['output']}\n")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return config

# ------------------------------------------------------------
# 步骤 1: 图片标准化
# ------------------------------------------------------------

def _process_single_image(src_path, dest_path):
    """
    把任意尺寸的图片，居中放到 1280x660 的暖白纸背景上
    保持原图比例
    """
    img = Image.open(src_path).convert("RGB")
    W, H = PANEL_OUT_SIZE
    
    # 目标内容区域大小
    target_w = W - 20
    target_h = H - 20 # 上下留一点白

    # 计算缩放
    iw, ih = img.size
    scale = min(target_w / iw, target_h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    
    img_resized = img.resize((nw, nh), Image.LANCZOS)
    
    # 创建画布
    canvas = Image.new("RGB", (W, H), PANEL_PAPER_COLOR)
    
    # 居中粘贴
    x = (W - nw) // 2
    y = (H - nh) // 2
    
    # 加一点阴影或边框（可选，这里简单加个黑边框）
    # ImageOps.expand(img_resized, border=1, fill="#333") 
    
    canvas.paste(img_resized, (x, y))
    canvas.save(dest_path)

def step1_prepare_images(config):
    print("=" * 50)
    print("步骤 1: 处理图片 (统一画幅)")
    print("=" * 50)

    for scene in config["scenes"]:
        src = os.path.join(INPUT_DIR, scene["source_image"])
        dst = os.path.join(OUTPUT_DIR, scene["processed_image"])
        
        _process_single_image(src, dst)
        print(f"  处理: {scene['source_image']} -> {scene['processed_image']}")
    print("")

# ------------------------------------------------------------
# 步骤 2-6: 音频、字幕、合成 (逻辑基本不变，仅适配新Config结构)
# ------------------------------------------------------------

async def step2_generate_audio(config, slow=False):
    rate = SLOW_RATE if slow else "+0%"
    suffix = "_slow" if slow else ""
    label = "慢速" if slow else "正常"
    
    print("=" * 50)
    print(f"步骤 2: 生成语音 ({label})")
    
    voices = config["voices"]
    audio_dir = os.path.join(OUTPUT_DIR, f"audio_clips{suffix}")
    os.makedirs(audio_dir, exist_ok=True)
    
    all_lines = []
    line_cnt = 0
    
    for s_idx, scene in enumerate(config["scenes"]):
        for line in scene["lines"]:
            line_cnt += 1
            spk = line["speaker"]
            txt = line["text"]
            voice = voices.get(spk, "en-US-GuyNeural")
            
            fname = f"line_{line_cnt:02d}.mp3"
            fpath = os.path.join(audio_dir, fname)
            
            if not os.path.exists(fpath):
                print(f"  [{line_cnt}] {spk}: {txt[:30]}...")
                await generate_audio(txt, fpath, voice, rate)
            
            dur = get_audio_duration(fpath)
            all_lines.append({
                "scene_idx": s_idx,
                "text": txt,
                "text_cn": line["text_cn"],
                "audio": fpath,
                "duration": dur
            })
            
    return all_lines

def step3_calc_durations(config, all_lines):
    print("\n步骤 3: 计算时长")
    gap = config["gap"]
    scene_durs = []
    for i in range(len(config["scenes"])):
        lines = [l for l in all_lines if l["scene_idx"] == i]
        total = sum(l["duration"] + gap for l in lines)
        # 如果场景没台词，至少给 2 秒展示
        if total < 0.1: total = 2.0 
        scene_durs.append(total)
        print(f"  Scene {i+1}: {total:.2f}s")
    return scene_durs

def step4_generate_srt(config, all_lines, offset=0.0):
    print("\n步骤 4: 生成字幕")
    gap = config["gap"]
    srt = []
    curr = offset
    
    for i, line in enumerate(all_lines, 1):
        start = curr
        end = curr + line["duration"]
        # 字幕格式：序号\n时间\n内容
        t_str = f"{format_srt_time(start)} --> {format_srt_time(end)}"
        content = f"{line['text']}\\N{line['text_cn']}" if line['text_cn'] else line['text']
        
        srt.append(f"{i}\n{t_str}\n{content}\n")
        curr = end + gap
        
    srt_path = os.path.join(OUTPUT_DIR, "subtitles.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt))
    return srt_path

def step5_merge_audio(config, all_lines):
    print("\n步骤 5: 拼接音频")
    gap = config["gap"]
    
    # 生成一个静音片段
    silence = os.path.join(OUTPUT_DIR, "_sil.mp3")
    if not os.path.exists(silence):
        ffmpeg_run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(gap), "-c:a", "libmp3lame", silence])
        
    list_txt = os.path.join(OUTPUT_DIR, "_audio_list.txt")
    with open(list_txt, "w", encoding="utf-8") as f:
        for line in all_lines:
            f.write(f"file '{line['audio'].replace(chr(92), '/')}'\n")
            f.write(f"file '{silence.replace(chr(92), '/')}'\n")
            
    out_mp3 = os.path.join(OUTPUT_DIR, "full_audio.mp3")
    ffmpeg_run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_txt, "-c:a", "libmp3lame", out_mp3])
    return out_mp3
def step6_make_video(config, scene_durs, audio_path, srt_path):
    print("\n步骤 6: 最终合成")
    
    # === 核心修改：使用 basename (文件名) 代替 绝对路径，避开中文路径乱码 ===
    
    # 6a. 制作图片流视频
    img_list = os.path.join(OUTPUT_DIR, "_vid_list.txt")
    title_dur = 0
    
    with open(img_list, "w", encoding="utf-8") as f:
        # 标题卡
        if config["title"]:
            title_img = os.path.join(OUTPUT_DIR, "_title.png")
            _generate_title_card(config["title"], title_img)
            # 修改点：只写入文件名
            f.write(f"file '{os.path.basename(title_img)}'\n")
            f.write(f"duration {TITLE_DURATION}\n")
            title_dur = TITLE_DURATION
            
        for i, scene in enumerate(config["scenes"]):
            ipath = os.path.join(OUTPUT_DIR, scene["processed_image"])
            # 修改点：只写入文件名
            f.write(f"file '{os.path.basename(ipath)}'\n")
            f.write(f"duration {scene_durs[i]}\n")
            
        # 重复最后一张图防止截断
        last = os.path.join(OUTPUT_DIR, config["scenes"][-1]["processed_image"])
        f.write(f"file '{os.path.basename(last)}'\n")
        
    video_silent = os.path.join(OUTPUT_DIR, "_silent.mp4")
    # 注意：FFmpeg 读取 list 时，如果 list 里是相对路径，它是相对于 list 文件所在目录寻找的
    # 因为 list 和图片都在 OUTPUT_DIR，所以这样写是安全的
    ffmpeg_run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", img_list,
        "-vf", "format=yuv420p", "-c:v", "libx264", "-r", "30", video_silent
    ], desc="图片合成视频")
    
    # 6b. 处理音频（加标题静音）
    final_audio = audio_path
    if title_dur > 0:
        title_sil = os.path.join(OUTPUT_DIR, "_title_sil.mp3")
        ffmpeg_run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(title_dur), "-c:a", "libmp3lame", title_sil])
        
        # 拼接音频 list
        concat_a = os.path.join(OUTPUT_DIR, "_audio_final_list.txt")
        with open(concat_a, "w", encoding="utf-8") as f:
            # 修改点：只写入文件名
            f.write(f"file '{os.path.basename(title_sil)}'\n")
            f.write(f"file '{os.path.basename(audio_path)}'\n")
            
        final_audio = os.path.join(OUTPUT_DIR, "_final_audio.mp3")
        ffmpeg_run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_a, "-c:a", "libmp3lame", final_audio], desc="音频拼接")

    # 6c. 合并+字幕
    output_file = os.path.join(OUTPUT_DIR, config["output"])
    
    # Windows下字体配置
    style = "FontSize=14,MarginV=15,Alignment=2,Outline=1"
    if os.name == 'nt': style = "FontName=Microsoft YaHei," + style
    
    # 处理字幕路径转义（解决之前的 SyntaxError）
    escaped_srt_path = srt_path.replace("\\", "/").replace(":", "\\:")
    
    ffmpeg_run([
        "ffmpeg", "-y", "-i", video_silent, "-i", final_audio,
        "-vf", f"subtitles='{escaped_srt_path}':force_style='{style}'",
        "-c:v", "libx264", "-c:a", "aac", "-shortest", output_file
    ], desc="最终合成")
    
    return output_file

# ------------------------------------------------------------
# 辅助绘图
# ------------------------------------------------------------

def _generate_title_card(text, out_path):
    img = Image.new("RGB", (1280, 720), (20, 20, 20))
    draw = ImageDraw.Draw(img)
    font = _load_font(50, True)
    
    # 简单居中
    bbox = draw.textbbox((0,0), text, font=font)
    w, h = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.text(((1280-w)//2, (720-h)//2), text, font=font, fill="white")
    img.save(out_path)

def generate_poster(vocab, out_path):
    # 简版海报
    if not vocab: return
    W, H = 1080, 1400
    img = Image.new("RGB", (W, H), (240, 235, 225))
    draw = ImageDraw.Draw(img)
    
    font_main = _load_font(40, True)
    y = 100
    draw.text((50, 50), "Core Expressions", font=_load_font(60), fill="#553311")
    
    for line in vocab:
        parts = line.split("—")
        txt = parts[0].strip()
        draw.text((60, y), f"• {txt}", font=font_main, fill="#333")
        y += 60
        if len(parts) > 1:
            draw.text((100, y), parts[1].strip(), font=_load_font(30, True), fill="#666")
            y += 50
        y += 30
        
    img.save(out_path)

# ============================================================
# Main
# ============================================================

async def main():
    if len(sys.argv) < 2:
        print("用法: python make_video.py <项目文件夹名>")
        sys.exit(1)
        
    project = sys.argv[1]
    init_paths(project)
    
    # 0. 加载配置
    config = step0_load_config()
    
    # 1. 图片处理
    step1_prepare_images(config)
    
    # 2-6. 视频生成
    all_lines = await step2_generate_audio(config, slow=False)
    durs = step3_calc_durations(config, all_lines)
    
    title_time = TITLE_DURATION if config["title"] else 0
    srt_path = step4_generate_srt(config, all_lines, offset=title_time)
    
    audio_path = step5_merge_audio(config, all_lines)
    
    final_video = step6_make_video(config, durs, audio_path, srt_path)
    
    # 海报
    if config["vocab"]:
        generate_poster(config["vocab"], os.path.join(OUTPUT_DIR, "poster.png"))
        
    print("\n" + "="*50)
    print(f"全部完成！视频已生成: {final_video}")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())