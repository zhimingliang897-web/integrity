"""
compress_video.py - MP4 视频压缩工具

使用 ffmpeg 将视频重新编码为更小体积，不影响转录质量。
压缩后的视频转录速度更快，占用磁盘空间更少。

用法：
    python compress_video.py input.mp4                  # 默认压缩（CRF=28，720p）
    python compress_video.py input.mp4 --crf 24         # 更高质量（文件更大）
    python compress_video.py input.mp4 --crf 32         # 更小体积（质量略低）
    python compress_video.py input.mp4 --no-scale       # 保持原始分辨率
    python compress_video.py input.mp4 --out small.mp4  # 指定输出文件名

CRF 参数说明（H.264）：
    18-23 = 高质量（文件大）
    24-28 = 均衡（推荐转录用）
    29-35 = 小体积（音频质量不受影响，转录效果基本不变）
"""

import argparse
import subprocess
import sys
from pathlib import Path


def compress(input_path: str, output_path: str, crf: int, scale_720p: bool) -> None:
    """
    使用 ffmpeg 压缩视频文件。

    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        crf: H.264 质量参数（18-35，越大越小越模糊）
        scale_720p: 是否将分辨率缩放到 720p

    Raises:
        RuntimeError: ffmpeg 未安装或压缩失败
    """
    vf = "scale=-2:720" if scale_720p else "scale=trunc(iw/2)*2:trunc(ih/2)*2"

    cmd = [
        "ffmpeg", "-i", input_path,
        "-vcodec", "libx264",
        "-crf", str(crf),
        "-preset", "fast",        # fast=速度优先；slow=压缩率更高
        "-vf", vf,
        "-acodec", "aac",         # 音频重编码为 AAC（保证转录质量）
        "-ab", "128k",            # 音频码率 128kbps（足够转录用）
        output_path, "-y",
    ]

    input_size = Path(input_path).stat().st_size / (1024 ** 2)
    print(f"[compress] 输入: {input_path}（{input_size:.1f} MB）")
    print(f"[compress] CRF={crf}，{'720p' if scale_720p else '原始分辨率'}，开始压缩...")

    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        raise RuntimeError("未找到 ffmpeg，请安装：conda install -c conda-forge ffmpeg")

    output_size = Path(output_path).stat().st_size / (1024 ** 2)
    ratio = (1 - output_size / input_size) * 100
    print(f"[compress] 完成: {output_path}（{output_size:.1f} MB，压缩了 {ratio:.0f}%）")


def main() -> None:
    """解析命令行参数并执行压缩。"""
    parser = argparse.ArgumentParser(description="MP4 视频压缩工具（基于 ffmpeg）")
    parser.add_argument("input", help="输入视频文件路径")
    parser.add_argument("--out", default="", help="输出文件路径（默认：原名_compressed.mp4）")
    parser.add_argument("--crf", type=int, default=28, help="质量参数 18-35（默认 28）")
    parser.add_argument("--no-scale", action="store_true", help="保持原始分辨率（不缩到 720p）")
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"[error] 文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)

    output = args.out or Path(args.input).stem + "_compressed.mp4"
    compress(args.input, output, args.crf, not args.no_scale)


if __name__ == "__main__":
    main()
