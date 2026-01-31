# -*- coding: utf-8 -*-
import asyncio
import edge_tts
import os
import subprocess
import re

work_dir = r"e:\分镜\2低血糖"
srt_path = os.path.join(work_dir, "subtitles.srt")
audio_dir = os.path.join(work_dir, "audio_clips")
os.makedirs(audio_dir, exist_ok=True)

# 英文男声，语速适中
VOICE = "en-US-GuyNeural"  # 可选: en-US-JennyNeural (女声)

def parse_srt(srt_file):
    """解析SRT字幕文件"""
    with open(srt_file, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.+?)(?=\n\n|\Z)"
    matches = re.findall(pattern, content, re.DOTALL)

    subtitles = []
    for match in matches:
        idx, start, end, text = match
        subtitles.append({
            "index": int(idx),
            "start": start,
            "end": end,
            "text": text.strip().replace("\n", " ")
        })
    return subtitles

def time_to_seconds(time_str):
    """将 SRT 时间格式转为秒"""
    h, m, rest = time_str.split(":")
    s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

async def generate_audio(text, output_file):
    """生成单句语音"""
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_file)

async def main():
    print("正在解析字幕文件...")
    subtitles = parse_srt(srt_path)
    print(f"  共 {len(subtitles)} 条字幕\n")

    # 1. 为每句台词生成语音
    print("正在生成语音...")
    audio_files = []
    for sub in subtitles:
        audio_file = os.path.join(audio_dir, f"line_{sub['index']:02d}.mp3")
        print(f"  [{sub['index']}/{len(subtitles)}] {sub['text'][:40]}...")
        await generate_audio(sub["text"], audio_file)
        audio_files.append({
            "file": audio_file,
            "start": time_to_seconds(sub["start"]),
            "end": time_to_seconds(sub["end"]),
            "duration": time_to_seconds(sub["end"]) - time_to_seconds(sub["start"])
        })
    print("语音生成完成！\n")

    # 2. 获取视频总时长
    video_path = os.path.join(work_dir, "低血糖_final.mp4")
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", video_path
    ], capture_output=True, text=True)
    total_duration = float(result.stdout.strip())
    print(f"视频总时长: {total_duration:.1f} 秒\n")

    # 3. 创建带时间偏移的音频合并命令
    print("正在合并音频轨道...")

    # 构建 FFmpeg 复杂滤镜
    filter_parts = []
    input_args = []

    for i, af in enumerate(audio_files):
        input_args.extend(["-i", af["file"]])
        # 调整每段音频的速度以适应字幕时长，并添加延迟
        # adelay 参数是毫秒
        delay_ms = int(af["start"] * 1000)
        filter_parts.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[a{i}]")

    # 混合所有音频
    mix_inputs = "".join(f"[a{i}]" for i in range(len(audio_files)))
    filter_parts.append(f"{mix_inputs}amix=inputs={len(audio_files)}:duration=longest[aout]")

    filter_complex = ";".join(filter_parts)

    # 生成混合音频
    mixed_audio = os.path.join(work_dir, "voiceover.mp3")
    cmd_mix = ["ffmpeg", "-y"] + input_args + [
        "-filter_complex", filter_complex,
        "-map", "[aout]",
        "-t", str(total_duration),
        mixed_audio
    ]
    subprocess.run(cmd_mix, capture_output=True, check=True)
    print(f"  音频轨道已保存: voiceover.mp3\n")

    # 4. 将音频合并到视频
    print("正在合并音视频...")
    output_video = os.path.join(work_dir, "低血糖_配音版.mp4")
    cmd_final = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", mixed_audio,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_video
    ]
    subprocess.run(cmd_final, capture_output=True, check=True)

    print(f"\n完成！配音版视频已保存为: {output_video}")

if __name__ == "__main__":
    asyncio.run(main())
