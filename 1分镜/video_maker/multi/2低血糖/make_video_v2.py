# -*- coding: utf-8 -*-
import asyncio
import edge_tts
import os
import subprocess
from PIL import Image

work_dir = r"e:\分镜\2低血糖"
audio_dir = os.path.join(work_dir, "audio_clips")
os.makedirs(audio_dir, exist_ok=True)

VOICE = "en-US-GuyNeural"
GAP = 0.3  # 每句之间的间隔（秒）

# 场景和台词定义
scenes = [
    {
        "image": "scene_1.png",
        "lines": [
            "It was a busy morning on the MRT.",
            "Suddenly, I felt strange.",
            "My head grew light, and my hands turned cold.",
            "I sat down and curled up on the seat.",
        ]
    },
    {
        "image": "scene_2.png",
        "lines": [
            "A stranger noticed me.",
            '"Are you all right?" he asked.',
            '"I feel dizzy. I think my blood sugar is low."',
            '"Have you eaten today?"',
            '"Not much. I skipped breakfast."',
        ]
    },
    {
        "image": "scene_3.png",
        "lines": [
            "He looked worried.",
            "He took out some candy and handed it to me.",
            '"Here," he said.',
            "My hands were shaking.",
            '"Sit still. Take your time."',
        ]
    },
    {
        "image": "scene_4.png",
        "lines": [
            "After a few minutes, I began to feel better.",
            '"Thank you," I said quietly.',
            '"If you feel worse, we can get off at the next station."',
            "I was still weak, but I was no longer alone.",
        ]
    },
]

def get_audio_duration(file_path):
    """获取音频文件时长"""
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", file_path
    ], capture_output=True, text=True)
    return float(result.stdout.strip())

async def generate_audio(text, output_file):
    """生成单句语音"""
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_file)

def format_srt_time(seconds):
    """格式化为 SRT 时间"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

async def main():
    print("=" * 50)
    print("步骤 1: 生成所有语音片段")
    print("=" * 50)

    line_index = 0
    all_lines = []

    for scene_idx, scene in enumerate(scenes):
        for line in scene["lines"]:
            line_index += 1
            audio_file = os.path.join(audio_dir, f"line_{line_index:02d}.mp3")
            print(f"  [{line_index}] {line[:50]}...")
            await generate_audio(line, audio_file)
            duration = get_audio_duration(audio_file)
            all_lines.append({
                "scene_idx": scene_idx,
                "text": line,
                "audio_file": audio_file,
                "duration": duration
            })

    print(f"\n共生成 {len(all_lines)} 条语音\n")

    print("=" * 50)
    print("步骤 2: 计算每个场景的时长")
    print("=" * 50)

    # 计算每个场景的时长（该场景所有台词时长 + 间隔）
    scene_durations = []
    for scene_idx in range(len(scenes)):
        scene_lines = [l for l in all_lines if l["scene_idx"] == scene_idx]
        total = sum(l["duration"] + GAP for l in scene_lines)
        scene_durations.append(total)
        print(f"  场景 {scene_idx + 1}: {total:.2f} 秒 ({len(scene_lines)} 句)")

    total_duration = sum(scene_durations)
    print(f"\n总时长: {total_duration:.2f} 秒\n")

    print("=" * 50)
    print("步骤 3: 生成字幕文件")
    print("=" * 50)

    srt_content = []
    current_time = 0.0
    sub_index = 0

    for line_info in all_lines:
        sub_index += 1
        start = current_time
        end = current_time + line_info["duration"]
        srt_content.append(f"{sub_index}")
        srt_content.append(f"{format_srt_time(start)} --> {format_srt_time(end)}")
        srt_content.append(line_info["text"])
        srt_content.append("")
        current_time = end + GAP

    srt_path = os.path.join(work_dir, "subtitles_v2.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_content))
    print(f"  保存: subtitles_v2.srt\n")

    print("=" * 50)
    print("步骤 4: 拼接所有语音（顺序播放，不重叠）")
    print("=" * 50)

    # 创建一个文件列表，每个音频后面加静音间隔
    concat_list = os.path.join(work_dir, "audio_concat.txt")
    silence_file = os.path.join(work_dir, "silence.mp3")

    # 生成短静音文件
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono",
        "-t", str(GAP), "-c:a", "libmp3lame", silence_file
    ], capture_output=True)

    with open(concat_list, "w", encoding="utf-8") as f:
        for line_info in all_lines:
            f.write(f"file '{line_info['audio_file'].replace(chr(92), '/')}'\n")
            f.write(f"file '{silence_file.replace(chr(92), '/')}'\n")

    # 拼接音频
    merged_audio = os.path.join(work_dir, "voiceover_v2.mp3")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c:a", "libmp3lame", merged_audio
    ], capture_output=True, check=True)
    print(f"  保存: voiceover_v2.mp3\n")

    print("=" * 50)
    print("步骤 5: 生成视频（图片时长与语音对齐）")
    print("=" * 50)

    # 创建图片序列文件
    img_concat = os.path.join(work_dir, "img_concat.txt")
    with open(img_concat, "w", encoding="utf-8") as f:
        for scene_idx, scene in enumerate(scenes):
            img_path = os.path.join(work_dir, scene["image"]).replace("\\", "/")
            f.write(f"file '{img_path}'\n")
            f.write(f"duration {scene_durations[scene_idx]}\n")
        # 最后一帧
        last_img = os.path.join(work_dir, scenes[-1]["image"]).replace("\\", "/")
        f.write(f"file '{last_img}'\n")

    # 生成无声视频
    temp_video = os.path.join(work_dir, "temp_video_v2.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", img_concat,
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
        temp_video
    ], capture_output=True, check=True)
    print("  基础视频生成完成")

    print("=" * 50)
    print("步骤 6: 合并音频和视频")
    print("=" * 50)

    temp_with_audio = os.path.join(work_dir, "temp_with_audio.mp4")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", temp_video,
        "-i", merged_audio,
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        temp_with_audio
    ], capture_output=True, check=True)
    print("  音视频合并完成")

    print("=" * 50)
    print("步骤 7: 添加字幕")
    print("=" * 50)

    output_video = os.path.join(work_dir, "低血糖_完整版.mp4")
    srt_escaped = srt_path.replace("\\", "/").replace(":", "\\:")

    subprocess.run([
        "ffmpeg", "-y",
        "-i", temp_with_audio,
        "-vf", f"subtitles='{srt_escaped}':force_style='FontSize=24,FontName=Arial,PrimaryColour=&Hffffff,OutlineColour=&H000000,BorderStyle=1,Outline=2,Shadow=1,MarginV=30'",
        "-c:v", "libx264", "-c:a", "copy",
        output_video
    ], capture_output=True, check=True)

    # 清理临时文件
    for f in [temp_video, temp_with_audio, concat_list, img_concat, silence_file]:
        if os.path.exists(f):
            os.remove(f)

    print(f"\n{'=' * 50}")
    print(f"完成！视频已保存为: {output_video}")
    print(f"总时长: {total_duration:.1f} 秒")
    print(f"{'=' * 50}")

if __name__ == "__main__":
    asyncio.run(main())
