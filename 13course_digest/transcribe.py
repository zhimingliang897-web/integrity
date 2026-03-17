"""
transcribe.py - 视频语音转文字模块

支持两种引擎：
- faster-whisper：稳定，内存友好
- insanely-fast-whisper：快 10 倍，需更多显存

依赖：ffmpeg（conda install -c conda-forge ffmpeg）
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
    """根据视频路径生成缓存文件路径。"""
    return Path(config.CACHE_DIR) / f"{Path(video_path).stem}.json"


def _format_timestamp(seconds: float) -> str:
    """将秒数转换为 HH:MM:SS 格式。"""
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _get_duration(video_path: str) -> float:
    """用 ffprobe 获取视频总时长（秒）。"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", video_path],
            capture_output=True, text=True, check=True,
        )
        return float(json.loads(result.stdout)["format"]["duration"])
    except FileNotFoundError:
        raise RuntimeError("未找到 ffprobe，请安装 ffmpeg：conda install -c conda-forge ffmpeg")


def _extract_wav(video_path: str, start: float, duration: float, out_path: str) -> None:
    """用 ffmpeg 从视频中截取音频并转为 16kHz 单声道 WAV。"""
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


def _transcribe_fast(video_path: str) -> list[dict]:
    """使用 insanely-fast-whisper 转录（快 10 倍）。"""
    from insanely_fast_whisper import AudioLoader, Transcriber

    print(f"[FastWhisper] 开始转录: {video_path}")

    # 初始化转录器
    transcriber = Transcriber(
        model_name=f"openai/whisper-{config.WHISPER_MODEL}",
        device="cuda" if config.WHISPER_DEVICE == "cuda" else "cpu",
    )

    # 加载音频
    loader = AudioLoader(video_path)
    audio = loader.load()

    # 转录
    result = transcriber.transcribe(audio, language=config.WHISPER_LANGUAGE)

    # 转换格式
    segments = []
    for chunk in result.get("chunks", []):
        start = chunk.get("timestamp", [0, 0])[0]
        end = chunk.get("timestamp", [0, 0])[1]
        text = chunk.get("text", "").strip()
        if text:
            segments.append({
                "start": start,
                "end": end,
                "timestamp": f"[{_format_timestamp(start)}-{_format_timestamp(end)}]",
                "text": text,
            })

    return segments


def _transcribe_faster(video_path: str) -> list[dict]:
    """使用 faster-whisper 转录（稳定，内存友好）。"""
    print(f"[Whisper] 开始转录: {video_path}")

    from faster_whisper import WhisperModel
    import ctranslate2

    device = config.WHISPER_DEVICE
    if device == "auto":
        device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"

    compute_type = config.WHISPER_COMPUTE_TYPE
    if compute_type == "int8":
        cuda_try_order = ["int8", "float16", "int8_float16"]
    else:
        cuda_try_order = ["float16", "int8_float16", "int8"]

    model = None
    if device == "cuda":
        for ct in cuda_try_order:
            try:
                model = WhisperModel(config.WHISPER_MODEL, device="cuda", compute_type=ct)
                compute_type = ct
                print(f"[Whisper] 模型: {config.WHISPER_MODEL}，设备: cuda，精度: {ct}")
                break
            except Exception as e:
                print(f"[Whisper] cuda/{ct} 不可用，尝试下一个...")
        if model is None:
            print("[Whisper] GPU 不可用，降级为 CPU...")
            device, compute_type = "cpu", "int8"

    if model is None:
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

                raw_segs = list(segs_iter)

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

    return all_segments


def transcribe(video_path: str) -> list[dict]:
    """
    转录视频音频，返回带时间戳的片段列表。
    优先读取缓存；缓存不存在时根据配置选择引擎转录。

    Args:
        video_path: 视频文件路径

    Returns:
        list[dict]: 片段列表
    """
    cache_file = _cache_path(video_path)
    if cache_file.exists():
        print(f"[缓存] 读取转录缓存: {cache_file}")
        with open(cache_file, encoding="utf-8") as f:
            return json.load(f)

    # 选择引擎
    engine = getattr(config, "WHISPER_ENGINE", "faster")
    if engine == "fast":
        try:
            segments = _transcribe_fast(video_path)
        except ImportError:
            print("[警告] insanely-fast-whisper 未安装，回退到 faster-whisper")
            print("安装命令: pip install insanely-fast-whisper")
            segments = _transcribe_faster(video_path)
    else:
        segments = _transcribe_faster(video_path)

    # 保存缓存
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)
    print(f"[缓存] 已保存: {cache_file}")

    return segments


def segments_to_chunks(segments: list[dict]) -> list[str]:
    """将转录片段按时间分块，供 LLM 分批分析。"""
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