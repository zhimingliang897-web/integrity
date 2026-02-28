"""
compress_pdf.py - PDF 压缩工具

优先使用 Ghostscript（效果最好），若未安装则使用 pypdf 压缩图片。
主要针对包含大量图片的 PDF（如扫描版讲义），纯文字 PDF 压缩效果有限。

用法：
    python compress_pdf.py input.pdf                  # 默认压缩（screen 模式）
    python compress_pdf.py input.pdf --quality ebook  # 中等质量
    python compress_pdf.py input.pdf --quality printer # 高质量（文件较大）
    python compress_pdf.py input.pdf --out small.pdf  # 指定输出文件名

Ghostscript quality 模式：
    screen  = 最小体积（72 dpi，适合屏幕阅读）
    ebook   = 中等（150 dpi，推荐）
    printer = 高质量（300 dpi）
    prepress= 最高质量

安装 Ghostscript（选一）：
    conda install -c conda-forge ghostscript
    或下载：https://www.ghostscript.com/releases/gsdnld.html
"""

import argparse
import subprocess
import sys
from pathlib import Path


def _compress_with_ghostscript(input_path: str, output_path: str, quality: str) -> bool:
    """
    使用 Ghostscript 压缩 PDF（效果最好）。

    Args:
        input_path: 输入 PDF 路径
        output_path: 输出 PDF 路径
        quality: 压缩质量（screen/ebook/printer/prepress）

    Returns:
        bool: True=成功，False=Ghostscript 未安装
    """
    gs_cmd = "gswin64c" if sys.platform == "win32" else "gs"  # Windows 用 gswin64c
    cmd = [
        gs_cmd, "-sDEVICE=pdfwrite",
        f"-dPDFSETTINGS=/{quality}",
        "-dCompatibilityLevel=1.4",
        "-dNOPAUSE", "-dQUIET", "-dBATCH",
        f"-sOutputFile={output_path}", input_path,
    ]
    try:
        subprocess.run(cmd, check=True)
        return True
    except FileNotFoundError:
        return False  # Ghostscript 未安装


def _compress_with_pypdf(input_path: str, output_path: str) -> None:
    """
    使用 pypdf 压缩 PDF（备选方案，效果一般）。

    Args:
        input_path: 输入 PDF 路径
        output_path: 输出 PDF 路径

    Raises:
        ImportError: pypdf 未安装（pip install pypdf）
    """
    try:
        from pypdf import PdfWriter, PdfReader
    except ImportError:
        raise ImportError("请安装 pypdf：pip install pypdf")

    reader = PdfReader(input_path)
    writer = PdfWriter()
    for page in reader.pages:
        page.compress_content_streams()  # 压缩页面内容流
        writer.add_page(page)
    with open(output_path, "wb") as f:
        writer.write(f)


def main() -> None:
    """解析命令行参数并执行 PDF 压缩。"""
    parser = argparse.ArgumentParser(description="PDF 压缩工具（Ghostscript 优先）")
    parser.add_argument("input", help="输入 PDF 文件路径")
    parser.add_argument("--out", default="", help="输出文件路径（默认：原名_compressed.pdf）")
    parser.add_argument(
        "--quality", default="ebook",
        choices=["screen", "ebook", "printer", "prepress"],
        help="Ghostscript 压缩质量（默认 ebook）"
    )
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"[error] 文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)

    output = args.out or Path(args.input).stem + "_compressed.pdf"
    input_size = Path(args.input).stat().st_size / (1024 ** 2)
    print(f"[compress] 输入: {args.input}（{input_size:.1f} MB）")

    # 优先用 Ghostscript
    if _compress_with_ghostscript(args.input, output, args.quality):
        print(f"[compress] 使用 Ghostscript（{args.quality} 模式）")
    else:
        print("[compress] Ghostscript 未找到，改用 pypdf（效果有限）...")
        print("  建议安装：conda install -c conda-forge ghostscript")
        _compress_with_pypdf(args.input, output)

    output_size = Path(output).stat().st_size / (1024 ** 2)
    ratio = (1 - output_size / input_size) * 100
    print(f"[compress] 完成: {output}（{output_size:.1f} MB，压缩了 {ratio:.0f}%）")


if __name__ == "__main__":
    main()
