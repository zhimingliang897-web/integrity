"""
视频导出模块 — 将辩论记录转为带配音+字幕的完整视频

复用 1分镜/video_maker/make_video.py 的 FFmpeg 管线模式：
  PIL 生成辩论卡片 → FFmpeg 图转视频 → 拼接音频 → 烧录字幕
"""

import os
from PIL import Image, ImageDraw, ImageFont
from config import OUTPUT_DIR, SPEECH_GAP
from tts_engine import get_audio_duration, ffmpeg_run, merge_all_audio


# ===== 常量 =====
VIDEO_W, VIDEO_H = 1280, 720
TITLE_DURATION = 4.0
PHASE_CARD_DURATION = 2.0

# 中文字体查找
_CN_FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]


def _load_font(size):
    """加载中文字体"""
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


def _wrap_text(text, font, max_width, draw):
    """中文文本自动换行"""
    lines = []
    current_line = ""
    for char in text:
        test_line = current_line + char
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] > max_width:
            if current_line:
                lines.append(current_line)
            current_line = char
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)
    return lines


def generate_title_card(topic: str, pro_position: str, con_position: str) -> str:
    """生成标题卡：辩题 + 正反方立场"""
    img = Image.new("RGB", (VIDEO_W, VIDEO_H), color=(10, 10, 30))
    draw = ImageDraw.Draw(img)

    font_big = _load_font(40)
    font_small = _load_font(24)

    # 辩题
    bbox = draw.textbbox((0, 0), topic, font=font_big)
    tw = bbox[2] - bbox[0]
    draw.text(((VIDEO_W - tw) // 2, 200), topic, fill=(255, 255, 255), font=font_big)

    # 分割线
    draw.line([(VIDEO_W // 2 - 200, 280), (VIDEO_W // 2 + 200, 280)], fill=(100, 100, 200), width=2)

    # 正方立场
    pro_text = f"正方：{pro_position}"
    bbox = draw.textbbox((0, 0), pro_text, font=font_small)
    draw.text(((VIDEO_W - (bbox[2] - bbox[0])) // 2, 320), pro_text, fill=(79, 172, 254), font=font_small)

    # 反方立场
    con_text = f"反方：{con_position}"
    bbox = draw.textbbox((0, 0), con_text, font=font_small)
    draw.text(((VIDEO_W - (bbox[2] - bbox[0])) // 2, 370), con_text, fill=(254, 100, 100), font=font_small)

    path = os.path.join(OUTPUT_DIR, "_title_card.png")
    img.save(path)
    return path


def generate_phase_card(phase_name: str) -> str:
    """生成阶段过渡卡"""
    img = Image.new("RGB", (VIDEO_W, VIDEO_H), color=(15, 15, 40))
    draw = ImageDraw.Draw(img)
    font = _load_font(48)

    bbox = draw.textbbox((0, 0), phase_name, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((VIDEO_W - tw) // 2, (VIDEO_H - th) // 2), phase_name, fill=(192, 144, 255), font=font)

    path = os.path.join(OUTPUT_DIR, f"_phase_{phase_name}.png")
    img.save(path)
    return path


def generate_speaker_card(name: str, side: str, role: str, text: str, index: int) -> str:
    """生成辩手发言卡片"""
    bg_color = (13, 27, 58) if side == "pro" else (42, 13, 13)
    accent = (79, 172, 254) if side == "pro" else (254, 100, 100)
    side_label = "正方" if side == "pro" else "反方"

    img = Image.new("RGB", (VIDEO_W, VIDEO_H), color=bg_color)
    draw = ImageDraw.Draw(img)

    font_name = _load_font(32)
    font_tag = _load_font(20)
    font_body = _load_font(26)

    # 顶部：辩手名 + 标签
    draw.text((60, 40), name, fill=accent, font=font_name)
    draw.text((60, 80), f"{side_label}{role}", fill=(150, 150, 150), font=font_tag)

    # 分割线
    draw.line([(60, 115), (VIDEO_W - 60, 115)], fill=(60, 60, 100), width=1)

    # 正文（自动换行）
    lines = _wrap_text(text, font_body, VIDEO_W - 120, draw)
    y = 140
    for line in lines[:18]:  # 最多显示18行
        draw.text((60, y), line, fill=(224, 224, 224), font=font_body)
        y += 36
    if len(lines) > 18:
        draw.text((60, y), "...", fill=(150, 150, 150), font=font_body)

    path = os.path.join(OUTPUT_DIR, f"_card_{index:03d}.png")
    img.save(path)
    return path


def generate_judge_card(text: str) -> str:
    """生成裁判评判卡片"""
    img = Image.new("RGB", (VIDEO_W, VIDEO_H), color=(15, 30, 15))
    draw = ImageDraw.Draw(img)

    font_title = _load_font(36)
    font_body = _load_font(22)

    draw.text((60, 40), "裁判评判", fill=(106, 254, 106), font=font_title)
    draw.line([(60, 90), (VIDEO_W - 60, 90)], fill=(40, 100, 40), width=1)

    lines = _wrap_text(text, font_body, VIDEO_W - 120, draw)
    y = 110
    for line in lines[:22]:
        draw.text((60, y), line, fill=(200, 200, 200), font=font_body)
        y += 28
    if len(lines) > 22:
        draw.text((60, y), "...", fill=(150, 150, 150), font=font_body)

    path = os.path.join(OUTPUT_DIR, "_judge_card.png")
    img.save(path)
    return path


def format_srt_time(seconds: float) -> str:
    """秒数 → SRT 时间格式"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def export_debate_video(history: list[dict], topic: str, pro_position: str = "", con_position: str = "") -> str:
    """
    将辩论记录导出为完整视频。

    Args:
        history: debate_engine.history 列表
        topic: 辩题
        pro_position: 正方立场
        con_position: 反方立场

    Returns:
        输出视频文件路径
    """
    print("=" * 50)
    print("  开始导出辩论视频")
    print("=" * 50)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    temp_files = []

    pro_pos = pro_position
    con_pos = con_position

    # 1. 收集已有的音频文件信息
    audio_dir = os.path.join(OUTPUT_DIR, "audio")
    audio_infos = []
    card_entries = []  # (image_path, duration, subtitle_text, speaker_name)

    # 标题卡
    title_img = generate_title_card(topic, pro_pos, con_pos)
    temp_files.append(title_img)
    card_entries.append((title_img, TITLE_DURATION, None, None))

    current_phase = None
    card_index = 0

    for i, entry in enumerate(history):
        if entry["id"] == "judge":
            continue  # 裁判单独处理

        # 阶段变化时插入阶段卡
        if entry["phase"] != current_phase:
            current_phase = entry["phase"]
            phase_names = {
                "opening": "开篇立论",
                "question": "攻辩质询",
                "answer": "攻辩质询",
                "summary": "攻辩小结",
                "free": "自由辩论",
                "closing": "总结陈词",
            }
            phase_display = phase_names.get(current_phase, current_phase)
            phase_img = generate_phase_card(phase_display)
            temp_files.append(phase_img)
            card_entries.append((phase_img, PHASE_CARD_DURATION, None, None))

        # 辩手发言卡
        speaker_img = generate_speaker_card(
            entry["name"], entry["side"], entry["role"], entry["content"], card_index,
        )
        temp_files.append(speaker_img)

        # 查找对应的音频文件
        audio_file = os.path.join(audio_dir, f"turn_{card_index:03d}_{entry['id']}.mp3")
        if os.path.exists(audio_file):
            duration = get_audio_duration(audio_file)
            audio_infos.append({"audio_file": audio_file, "duration": duration})
            card_entries.append((speaker_img, duration + SPEECH_GAP, entry["content"], entry["name"]))
        else:
            card_entries.append((speaker_img, 5.0, entry["content"], entry["name"]))

        card_index += 1

    # 裁判卡
    judge_entries = [e for e in history if e["id"] == "judge"]
    if judge_entries:
        judge_img = generate_judge_card(judge_entries[0]["content"])
        temp_files.append(judge_img)

        judge_audio = os.path.join(audio_dir, f"turn_{card_index:03d}_judge.mp3")
        if os.path.exists(judge_audio):
            duration = get_audio_duration(judge_audio)
            audio_infos.append({"audio_file": judge_audio, "duration": duration})
            card_entries.append((judge_img, duration + SPEECH_GAP, None, None))
        else:
            card_entries.append((judge_img, 10.0, None, None))

    # 2. 生成 SRT 字幕
    print("  [1/4] 生成字幕...")
    srt_content = []
    current_time = TITLE_DURATION + PHASE_CARD_DURATION  # 跳过标题卡和第一个阶段卡
    sub_index = 1
    for img_path, duration, text, speaker in card_entries:
        if text and speaker:
            side_label = ""
            start = current_time
            end = current_time + duration - SPEECH_GAP
            srt_content.append(f"{sub_index}")
            srt_content.append(f"{format_srt_time(start)} --> {format_srt_time(end)}")
            srt_content.append(f"【{speaker}】{text[:80]}")
            srt_content.append("")
            sub_index += 1
        current_time += duration

    srt_path = os.path.join(OUTPUT_DIR, "debate.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_content))
    temp_files.append(srt_path)

    # 3. 图片序列 → 无声视频
    print("  [2/4] 图片 → 视频...")
    img_list = os.path.join(OUTPUT_DIR, "_img_list.txt")
    temp_files.append(img_list)
    with open(img_list, "w", encoding="utf-8") as f:
        for img_path, duration, _, _ in card_entries:
            f.write(f"file '{img_path.replace(chr(92), '/')}'\n")
            f.write(f"duration {duration}\n")
        # 最后一帧重复
        f.write(f"file '{card_entries[-1][0].replace(chr(92), '/')}'\n")

    temp_video = os.path.join(OUTPUT_DIR, "_temp_video.mp4")
    temp_files.append(temp_video)
    ffmpeg_run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", img_list,
        "-vf", f"scale={VIDEO_W}:{VIDEO_H}:force_original_aspect_ratio=decrease,"
               f"pad={VIDEO_W}:{VIDEO_H}:(ow-iw)/2:(oh-ih)/2:color=black",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", temp_video,
    ], "图片转视频")

    # 4. 合并音频
    print("  [3/4] 合并音频...")
    if audio_infos:
        merged_audio = os.path.join(OUTPUT_DIR, "_merged_audio.mp3")
        temp_files.append(merged_audio)

        # 标题卡+阶段卡期间的静音
        title_silence = os.path.join(OUTPUT_DIR, "_title_silence.mp3")
        temp_files.append(title_silence)
        silence_dur = TITLE_DURATION + PHASE_CARD_DURATION
        ffmpeg_run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
            "-t", str(silence_dur), "-c:a", "libmp3lame", title_silence,
        ], "标题静音")

        # 阶段间静音
        phase_silence = os.path.join(OUTPUT_DIR, "_phase_silence.mp3")
        temp_files.append(phase_silence)
        ffmpeg_run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
            "-t", str(PHASE_CARD_DURATION), "-c:a", "libmp3lame", phase_silence,
        ], "阶段静音")

        # 拼接所有音频
        voiceover = os.path.join(OUTPUT_DIR, "_voiceover.mp3")
        temp_files.append(voiceover)
        merge_all_audio(audio_infos, voiceover)

        # 前面加静音
        full_audio_list = os.path.join(OUTPUT_DIR, "_full_audio.txt")
        temp_files.append(full_audio_list)
        with open(full_audio_list, "w", encoding="utf-8") as f:
            f.write(f"file '{title_silence.replace(chr(92), '/')}'\n")
            f.write(f"file '{voiceover.replace(chr(92), '/')}'\n")

        ffmpeg_run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", full_audio_list, "-c:a", "libmp3lame", merged_audio,
        ], "拼接完整音频")

        # 合并音视频
        temp_av = os.path.join(OUTPUT_DIR, "_temp_av.mp4")
        temp_files.append(temp_av)
        ffmpeg_run([
            "ffmpeg", "-y", "-i", temp_video, "-i", merged_audio,
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v:0", "-map", "1:a:0", "-shortest", temp_av,
        ], "合并音视频")
    else:
        temp_av = temp_video

    # 5. 烧录字幕
    print("  [4/4] 烧录字幕...")
    output_path = os.path.join(OUTPUT_DIR, "debate_video.mp4")
    srt_escaped = srt_path.replace("\\", "/").replace(":", "\\:")
    ffmpeg_run([
        "ffmpeg", "-y", "-i", temp_av,
        "-vf", f"subtitles='{srt_escaped}':force_style='FontSize=18,FontName=Microsoft YaHei,"
               f"PrimaryColour=&Hffffff,OutlineColour=&H000000,BorderStyle=1,"
               f"Outline=1,Shadow=0,MarginV=10,Alignment=2'",
        "-c:v", "libx264", "-c:a", "copy", output_path,
    ], "烧录字幕")

    # 清理临时文件
    for f in temp_files:
        if os.path.exists(f):
            try:
                os.remove(f)
            except OSError:
                pass

    print(f"\n  视频已导出: {output_path}")
    return output_path
