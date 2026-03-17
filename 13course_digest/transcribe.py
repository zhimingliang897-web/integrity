"""
transcribe.py - 视频语音转文字模块

使用 faster-whisper 在本地将视频音频转录为带时间戳的文本。
通过 ffmpeg 将长视频切成 30 分钟小段逐段处理，解决大内存问题。
转录结果自动缓存为 JSON，避免对同一视频重复处理。

依赖：ffmpeg（系统工具，conda install -c conda-forge ffmpeg）
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

from tqdm import tqdm

import config

# 每次送给 Whisper 的音频段长度（秒），30 分钟 = 约 300MB 内存
_SEGMENT_SECS = 30 * 60


def _cache_path(video_path: str) -> Path:
    """
    根据视频路径生成对应的缓存文件路径。

    Args:
        video_path: 视频文件路径

    Returns:
        Path: 缓存 JSON 文件路径（位于 CACHE_DIR 下）
    """
    return Path(config.CACHE_DIR) / f"{Path(video_path).stem}.json"


def _format_timestamp(seconds: float) -> str:
    """
    将秒数转换为 HH:MM:SS 格式的时间戳字符串。

    Args:
        seconds: 秒数（浮点数）

    Returns:
        str: 格式化时间戳，如 "01:23:45"
    """
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _get_duration(video_path: str) -> float:
    """
    用 ffprobe 获取视频总时长（秒）。

    Args:
        video_path: 视频文件路径

    Returns:
        float: 时长（秒）

    Raises:
        RuntimeError: ffprobe 不在 PATH 中（未安装 ffmpeg）
    """
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", video_path],
            capture_output=True, text=True, check=True,
        )
        return float(json.loads(result.stdout)["format"]["duration"])
    except FileNotFoundError:
        raise RuntimeError("未找到 ffprobe，请安装 ffmpeg：conda install -c conda-forge ffmpeg")


def _extract_wav(video_path: str, start: float, duration: float, out_path: str) -> None:
    """
    用 ffmpeg 从视频中截取一段音频并转为 16kHz 单声道 WAV。

    Args:
        video_path: 输入视频路径
        start: 起始时间（秒）
        duration: 截取时长（秒）
        out_path: 输出 WAV 文件路径
    """
    subprocess.run(
        [
            "ffmpeg", "-v", "quiet",
            "-i", video_path,
            "-ss", str(start), "-t", str(duration),
            "-ar", "16000", "-ac", "1", "-vn",
            out_path, "-y",
        ],
        check=True,
    )


def transcribe(video_path: str) -> list[dict]:
    """
    转录视频音频，返回带时间戳的片段列表。
    优先读取缓存；缓存不存在时按 30 分钟分段处理，避免内存溢出。

    Args:
        video_path: 视频文件路径（mp4、mkv 等均可）

    Returns:
        list[dict]: 片段列表，每项包含:
            - start (float): 开始时间（秒，相对于视频开头）
            - end (float): 结束时间（秒）
            - timestamp (str): 格式化时间戳，如 "[00:05:30-00:05:42]"
            - text (str): 识别的文字内容
    """
    cache_file = _cache_path(video_path)
    if cache_file.exists():
        print(f"[缓存] 读取转录缓存: {cache_file}")
        with open(cache_file, encoding="utf-8") as f:
            return json.load(f)

    print(f"[Whisper] 开始转录: {video_path}")

    from faster_whisper import WhisperModel
    import ctranslate2

    device = config.WHISPER_DEVICE
    if device == "auto":
        device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"

    compute_type = config.WHISPER_COMPUTE_TYPE
    cuda_try_order = ["float16", "int8_float16", "int8"]  # GPU 精度依次尝试

    model = None
    if device == "cuda" and compute_type == "auto":
        for ct in cuda_try_order:
            try:
                model = WhisperModel(config.WHISPER_MODEL, device="cuda", compute_type=ct)
                compute_type = ct
                print(f"[Whisper] 模型: {config.WHISPER_MODEL}，设备: cuda，精度: {ct}")
                break
            except Exception as e:
                print(f"[Whisper] cuda/{ct} 不可用（{e}），尝试下一个...")
        if model is None:
            print("[Whisper] GPU 所有精度均不可用，降级为 CPU...")
            device, compute_type = "cpu", "float32"

    if model is None:
        if compute_type == "auto":
            # GPU 默认 float16，CPU 默认 int8 以换取更高速度
            compute_type = "float16" if device == "cuda" else "int8"
        print(f"[Whisper] 模型: {config.WHISPER_MODEL}，设备: {device}，精度: {compute_type}")
        model = WhisperModel(config.WHISPER_MODEL, device=device, compute_type=compute_type)

    total_secs = _get_duration(video_path)
    n_segments = int(total_secs / _SEGMENT_SECS) + 1
    print(f"[Whisper] 视频时长 {_format_timestamp(total_secs)}，分 {n_segments} 段处理...")

    all_segments: list[dict] = []
    offset = 0.0

    os.makedirs(config.CACHE_DIR, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=config.CACHE_DIR) as tmp:
        with tqdm(total=int(total_secs), unit="sec", desc="转录进度") as pbar:
            seg_idx = 0
            while offset < total_secs:
                seg_dur = min(_SEGMENT_SECS, total_secs - offset)
                wav_path = os.path.join(tmp, f"seg_{seg_idx:03d}.wav")

                _extract_wav(video_path, offset, seg_dur, wav_path)
                segs_iter, _ = model.transcribe(
                    wav_path,
                    language=config.WHISPER_LANGUAGE,
                    beam_size=getattr(config, "WHISPER_BEAM_SIZE", 1),
                )

                try:
                    raw_segs = list(segs_iter)  # 触发实际 GPU/CPU 计算
                except RuntimeError as e:
                    if "cuda" in device and ("cublas" in str(e).lower() or "cuda" in str(e).lower()):
                        print(f"\n[Whisper] GPU 运行失败（{e}），切换到 CPU 重试...")
                        device = "cpu"
                        if compute_type == "auto":
                            compute_type = "int8"
                        model = WhisperModel(
                            config.WHISPER_MODEL,
                            device=device,
                            compute_type=compute_type,
                        )
                        segs_iter, _ = model.transcribe(
                            wav_path,
                            language=config.WHISPER_LANGUAGE,
                            beam_size=getattr(config, "WHISPER_BEAM_SIZE", 1),
                        )
                        raw_segs = list(segs_iter)
                    else:
                        raise

                for seg in raw_segs:
                    abs_start = seg.start + offset
                    abs_end = seg.end + offset
                    all_segments.append({
                        "start": abs_start,
                        "end": abs_end,
                        "timestamp": f"[{_format_timestamp(abs_start)}-{_format_timestamp(abs_end)}]",
                        "text": seg.text.strip(),
                    })

                pbar.update(int(seg_dur))
                offset += seg_dur
                seg_idx += 1

    os.makedirs(config.CACHE_DIR, exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(all_segments, f, ensure_ascii=False, indent=2)
    print(f"[缓存] 已保存: {cache_file}")

    return all_segments


def segments_to_chunks(segments: list[dict]) -> list[str]:
    """
    将转录片段按时间分块（每块约 CHUNK_MINUTES 分钟），供 LLM 分批分析。

    Args:
        segments: transcribe() 返回的片段列表

    Returns:
        list[str]: 每块的文本，包含时间戳，如 "[00:05:30-00:05:42] Hello..."
    """
    chunk_seconds = config.CHUNK_MINUTES * 60
    chunks: list[str] = []
    current: list[str] = []
    chunk_start = 0.0

    for seg in segments:
        current.append(f"{seg['timestamp']} {seg['text']}")
        if seg["end"] - chunk_start >= chunk_seconds:
            chunks.append("\n".join(current))
            current = []
            chunk_start = seg["end"]

    if current:
        chunks.append("\n".join(current))

    return chunks
