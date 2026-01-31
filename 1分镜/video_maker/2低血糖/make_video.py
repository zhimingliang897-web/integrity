# -*- coding: utf-8 -*-
"""
分镜视频生成器
用法: python make_video.py [config.json路径]
默认读取同目录下的 config.json
"""
import asyncio
import edge_tts
import json
import os
import subprocess
import sys
from PIL import Image


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


async def generate_audio(text, output_file, voice):
    """调用 Edge TTS 生成单句语音"""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)


# ============================================================
# 核心流程
# ============================================================

def step0_load_config(config_path):
    """加载配置文件"""
    print("=" * 50)
    print("步骤 0: 加载配置")
    print("=" * 50)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    work_dir = os.path.dirname(os.path.abspath(config_path))
    config["_work_dir"] = work_dir
    config["_audio_dir"] = os.path.join(work_dir, "audio_clips")
    os.makedirs(config["_audio_dir"], exist_ok=True)

    print(f"  工作目录: {work_dir}")
    print(f"  场景数量: {len(config['scenes'])}")
    print(f"  配音声音: {config['voice']}")
    print(f"  输出文件: {config['output']}\n")
    return config


def step1_cut_images(config):
    """如果配置了 source_image + grid，自动切割图片"""
    print("=" * 50)
    print("步骤 1: 准备图片")
    print("=" * 50)

    work_dir = config["_work_dir"]

    if "source_image" in config and "grid" in config:
        src = os.path.join(work_dir, config["source_image"])
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
                out_path = os.path.join(work_dir, config["scenes"][idx]["image"])
                cropped.save(out_path)
                print(f"  切割: {config['scenes'][idx]['image']}")
                idx += 1
        print(f"  从 {config['source_image']} 切出 {idx} 张图片\n")
    else:
        # 不需要切割，检查图片是否存在
        for scene in config["scenes"]:
            img_path = os.path.join(work_dir, scene["image"])
            if not os.path.exists(img_path):
                raise FileNotFoundError(f"图片不存在: {img_path}")
            print(f"  已有: {scene['image']}")
        print()


async def step2_generate_audio(config):
    """为每句台词生成语音，并记录实际时长"""
    print("=" * 50)
    print("步骤 2: 生成语音")
    print("=" * 50)

    voice = config["voice"]
    audio_dir = config["_audio_dir"]
    all_lines = []
    line_index = 0

    for scene_idx, scene in enumerate(config["scenes"]):
        for line in scene["lines"]:
            line_index += 1
            audio_file = os.path.join(audio_dir, f"line_{line_index:02d}.mp3")
            print(f"  [{line_index}] {line[:50]}...")
            await generate_audio(line, audio_file, voice)
            duration = get_audio_duration(audio_file)
            all_lines.append({
                "scene_idx": scene_idx,
                "text": line,
                "audio_file": audio_file,
                "duration": duration
            })

    print(f"  共 {len(all_lines)} 条语音\n")
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


def step4_generate_srt(config, all_lines):
    """生成 SRT 字幕文件，时间与语音对齐"""
    print("=" * 50)
    print("步骤 4: 生成字幕")
    print("=" * 50)

    gap = config["gap"]
    work_dir = config["_work_dir"]
    srt_content = []
    current_time = 0.0

    for i, line_info in enumerate(all_lines, 1):
        start = current_time
        end = current_time + line_info["duration"]
        srt_content.append(f"{i}")
        srt_content.append(f"{format_srt_time(start)} --> {format_srt_time(end)}")
        srt_content.append(line_info["text"])
        srt_content.append("")
        current_time = end + gap

    srt_path = os.path.join(work_dir, "subtitles.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_content))

    print(f"  保存: subtitles.srt\n")
    return srt_path


def step5_merge_audio(config, all_lines):
    """顺序拼接所有语音片段，中间插入静音间隔"""
    print("=" * 50)
    print("步骤 5: 拼接音频")
    print("=" * 50)

    gap = config["gap"]
    work_dir = config["_work_dir"]

    # 生成静音文件
    silence = os.path.join(work_dir, "_silence.mp3")
    ffmpeg_run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono",
        "-t", str(gap), "-c:a", "libmp3lame", silence
    ], "生成静音文件")

    # 写拼接列表
    concat_list = os.path.join(work_dir, "_audio_concat.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for line_info in all_lines:
            f.write(f"file '{line_info['audio_file'].replace(chr(92), '/')}'\n")
            f.write(f"file '{silence.replace(chr(92), '/')}'\n")

    # 拼接
    merged = os.path.join(work_dir, "voiceover.mp3")
    ffmpeg_run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c:a", "libmp3lame", merged
    ], "拼接音频")

    # 清理
    os.remove(silence)
    os.remove(concat_list)

    print(f"  保存: voiceover.mp3\n")
    return merged


def step6_make_video(config, scene_durations, merged_audio, srt_path):
    """图片转视频 → 合并音频 → 烧录字幕"""
    print("=" * 50)
    print("步骤 6: 合成视频")
    print("=" * 50)

    work_dir = config["_work_dir"]
    output = os.path.join(work_dir, config["output"])

    # 6a. 图片 → 无声视频
    img_list = os.path.join(work_dir, "_img_concat.txt")
    with open(img_list, "w", encoding="utf-8") as f:
        for i, scene in enumerate(config["scenes"]):
            img_path = os.path.join(work_dir, scene["image"]).replace("\\", "/")
            f.write(f"file '{img_path}'\n")
            f.write(f"duration {scene_durations[i]}\n")
        last_img = os.path.join(work_dir, config["scenes"][-1]["image"]).replace("\\", "/")
        f.write(f"file '{last_img}'\n")

    temp1 = os.path.join(work_dir, "_temp_video.mp4")
    print("  [6a] 图片 → 视频...")
    ffmpeg_run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", img_list,
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", temp1
    ], "图片转视频")

    # 6b. 合并音频
    temp2 = os.path.join(work_dir, "_temp_with_audio.mp4")
    print("  [6b] 合并音频...")
    ffmpeg_run([
        "ffmpeg", "-y", "-i", temp1, "-i", merged_audio,
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0", "-shortest", temp2
    ], "合并音视频")

    # 6c. 烧录字幕
    srt_escaped = srt_path.replace("\\", "/").replace(":", "\\:")
    print("  [6c] 烧录字幕...")
    ffmpeg_run([
        "ffmpeg", "-y", "-i", temp2,
        "-vf", f"subtitles='{srt_escaped}':force_style='FontSize=24,FontName=Arial,"
               f"PrimaryColour=&Hffffff,OutlineColour=&H000000,BorderStyle=1,"
               f"Outline=2,Shadow=1,MarginV=30'",
        "-c:v", "libx264", "-c:a", "copy", output
    ], "烧录字幕")

    # 清理临时文件
    for f in [temp1, temp2, img_list]:
        if os.path.exists(f):
            os.remove(f)

    print(f"\n  输出: {config['output']}\n")
    return output


# ============================================================
# 主流程
# ============================================================

async def main():
    # 读取配置文件路径（默认同目录下的 config.json）
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

    config = step0_load_config(config_path)
    step1_cut_images(config)
    all_lines = await step2_generate_audio(config)
    scene_durations = step3_calc_durations(config, all_lines)
    srt_path = step4_generate_srt(config, all_lines)
    merged_audio = step5_merge_audio(config, all_lines)
    output = step6_make_video(config, scene_durations, merged_audio, srt_path)

    print("=" * 50)
    print(f"完成！{output}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
