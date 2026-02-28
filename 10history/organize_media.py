#!/usr/bin/env python3
"""
organize_media.py - 照片/视频去重整理工具

从多个源文件夹扫描照片和视频，去重后按拍摄日期（年/月）整理到指定输出目录。
支持从 EXIF、视频元数据、文件名时间戳中提取拍摄日期。

用法:
    python organize_media.py 源文件夹1 源文件夹2 ... -o 输出目录 [--dry-run] [--verbose]
"""
from typing import Optional

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import warnings
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# 压制 exifread 和 Pillow 的警告输出
logging.getLogger('exifread').setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore', message='.*DecompressionBomb.*')

try:
    from tqdm import tqdm
except ImportError:
    # tqdm 不可用时用简单的替代
    class tqdm:
        def __init__(self, iterable=None, total=None, desc="", unit="", **kwargs):
            self.iterable = iterable
            self.total = total
            self.desc = desc
            self.n = 0
        def __iter__(self):
            for item in self.iterable:
                yield item
                self.n += 1
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def update(self, n=1):
            self.n += n
        def set_postfix_str(self, s):
            pass

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

PHOTO_EXTENSIONS = frozenset({
    '.jpg', '.jpeg', '.png', '.heic', '.heif',
    '.tiff', '.tif', '.bmp', '.webp', '.gif',
})

VIDEO_EXTENSIONS = frozenset({
    '.mp4', '.mov', '.avi', '.mkv', '.wmv',
    '.flv', '.m4v', '.3gp', '.mts', '.m2ts',
})

SUPPORTED_EXTENSIONS = PHOTO_EXTENSIONS | VIDEO_EXTENSIONS

QUICK_HASH_SIZE = 4096          # 快速哈希：读前 4KB
FULL_HASH_CHUNK = 8 * 1024 * 1024  # 完整哈希：8MB 分块

# Unix 毫秒时间戳的合理范围（2000-01-01 ~ 2030-01-01）
_TS_MIN = 946684800000
_TS_MAX = 1893456000000

# 日期格式文件名的正则
_RE_DATE_FILENAME = re.compile(r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2})(\d{2})(\d{2})')
# Unix 毫秒时间戳（文件名中的第一段连续数字，10-13 位）
_RE_TIMESTAMP = re.compile(r'^(\d{10,13})')

# ---------------------------------------------------------------------------
# 模块级状态
# ---------------------------------------------------------------------------

_ffprobe_available: bool = False
_exifread_available: bool = False
_heif_available: bool = False


def check_ffprobe() -> bool:
    global _ffprobe_available
    try:
        subprocess.run(
            ['ffprobe', '-version'],
            capture_output=True, timeout=10,
        )
        _ffprobe_available = True
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        _ffprobe_available = False
    return _ffprobe_available


def check_exifread() -> bool:
    global _exifread_available
    try:
        import exifread  # noqa: F401
        _exifread_available = True
    except ImportError:
        _exifread_available = False
    return _exifread_available


def check_heif() -> bool:
    global _heif_available
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
        _heif_available = True
    except ImportError:
        _heif_available = False
    return _heif_available


# ---------------------------------------------------------------------------
# 扫描
# ---------------------------------------------------------------------------

def scan_sources(source_dirs: list[Path]) -> list[tuple[Path, int]]:
    """递归扫描源文件夹，返回 (路径, 文件大小) 列表。"""
    files = []
    for src in source_dirs:
        if not src.is_dir():
            print(f"  警告: 跳过不存在的目录 {src}")
            continue
        for entry in src.rglob('*'):
            if entry.is_file() and entry.suffix.lower() in SUPPORTED_EXTENSIONS:
                try:
                    size = entry.stat().st_size
                    files.append((entry, size))
                except OSError:
                    pass
    return files


# ---------------------------------------------------------------------------
# 去重
# ---------------------------------------------------------------------------

def compute_quick_hash(filepath: Path) -> str:
    """读取前 4KB 计算快速哈希。"""
    h = hashlib.md5(usedforsecurity=False)
    try:
        with open(filepath, 'rb') as f:
            h.update(f.read(QUICK_HASH_SIZE))
    except OSError:
        return ''
    return h.hexdigest()


def compute_full_hash(filepath: Path) -> str:
    """8MB 分块计算完整 MD5 哈希。"""
    h = hashlib.md5(usedforsecurity=False)
    try:
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(FULL_HASH_CHUNK)
                if not chunk:
                    break
                h.update(chunk)
    except OSError:
        return ''
    return h.hexdigest()


def _has_date_info(filepath: Path) -> int:
    """评估文件的日期信息质量，分数越高越好。用于去重时决定保留哪个。"""
    name = filepath.stem
    # 文件名包含日期格式 "2018-02-11 184617" → 最好
    if _RE_DATE_FILENAME.search(name):
        return 2
    # 文件名包含合理的时间戳 → 次好
    m = _RE_TIMESTAMP.match(name)
    if m:
        ts = int(m.group(1))
        if len(m.group(1)) == 10:
            ts *= 1000
        if _TS_MIN <= ts <= _TS_MAX:
            return 1
    # 无法从文件名获取日期 → 最差
    return 0


def _pick_best_file(group: list[Path]) -> Path:
    """从一组内容相同的文件中，选出日期信息最丰富的保留。"""
    return max(group, key=_has_date_info)


def deduplicate(files: list[tuple[Path, int]], verbose: bool = False) -> tuple[list[Path], list[tuple[Path, Path]]]:
    """
    三级过滤去重：
    1. 按文件大小分组，大小唯一的直接通过
    2. 大小相同的算快速哈希（前 4KB）
    3. 快速哈希也相同的算完整 MD5
    返回 (唯一文件列表, 重复文件列表[(重复文件, 保留的原件)])。
    """
    # 第一级：按大小分组
    size_groups: dict[int, list[Path]] = defaultdict(list)
    for path, size in files:
        size_groups[size].append(path)

    unique: list[Path] = []
    duplicates: list[tuple[Path, Path]] = []
    need_quick_hash: list[Path] = []

    for size, group in size_groups.items():
        if len(group) == 1:
            unique.append(group[0])
        else:
            need_quick_hash.extend(group)

    if verbose:
        print(f"  第一级过滤: {len(unique)} 个大小唯一, {len(need_quick_hash)} 个需要进一步检查")

    # 第二级：快速哈希
    quick_groups: dict[str, list[Path]] = defaultdict(list)
    for path in tqdm(need_quick_hash, desc="  快速哈希", unit="个", leave=False):
        qh = compute_quick_hash(path)
        quick_groups[qh].append(path)

    need_full_hash: list[Path] = []
    for qh, group in quick_groups.items():
        if len(group) == 1:
            unique.append(group[0])
        else:
            need_full_hash.extend(group)

    if verbose:
        print(f"  第二级过滤: 还需完整哈希的文件 {len(need_full_hash)} 个")

    # 第三级：完整哈希
    # 收集所有哈希相同的文件组
    hash_groups: dict[str, list[Path]] = defaultdict(list)
    for path in tqdm(need_full_hash, desc="  完整哈希", unit="个", leave=False):
        fh = compute_full_hash(path)
        hash_groups[fh].append(path)

    for fh, group in hash_groups.items():
        if len(group) == 1:
            unique.append(group[0])
        else:
            # 优先保留能从文件名/EXIF解析出日期的文件
            best = _pick_best_file(group)
            unique.append(best)
            for p in group:
                if p != best:
                    duplicates.append((p, best))
                    if verbose:
                        print(f"    重复: {p} == {best}")

    return unique, duplicates


# ---------------------------------------------------------------------------
# 日期提取
# ---------------------------------------------------------------------------

def get_photo_date(filepath: Path) -> Optional[datetime]:

    """用 exifread 读取照片 EXIF 日期（仅读头部）。HEIC 用 Pillow。"""
    ext = filepath.suffix.lower()

    # HEIC/HEIF: 用 Pillow + pillow-heif
    if ext in ('.heic', '.heif'):
        if not _heif_available:
            return None
        try:
            from PIL import Image
            with Image.open(filepath) as img:
                exif = img.getexif()
                if not exif:
                    return None
                # 尝试 Exif sub-IFD
                exif_ifd = exif.get_ifd(0x8769)
                date_str = None
                if exif_ifd:
                    date_str = exif_ifd.get(36867) or exif_ifd.get(36868)
                if not date_str:
                    date_str = exif.get(306)
                if date_str:
                    return datetime.strptime(str(date_str), "%Y:%m:%d %H:%M:%S")
        except Exception:
            pass
        return None

    # 只对 JPEG/TIFF 尝试读 EXIF，其他格式几乎没有
    _EXIF_FORMATS = ('.jpg', '.jpeg', '.tiff', '.tif')
    if ext not in _EXIF_FORMATS:
        return None

    # 用 exifread（轻量，只读头部），压制它的 stderr 输出
    if _exifread_available:
        try:
            import exifread
            with open(filepath, 'rb') as f:
                # exifread 会直接 print 警告到 stderr，用 devnull 压制
                _real_stderr = sys.stderr
                sys.stderr = open(os.devnull, 'w')
                try:
                    tags = exifread.process_file(
                        f, stop_tag='DateTimeOriginal', details=False,
                    )
                finally:
                    sys.stderr.close()
                    sys.stderr = _real_stderr
            for tag_name in ('EXIF DateTimeOriginal', 'EXIF DateTimeDigitized', 'Image DateTime'):
                if tag_name in tags:
                    date_str = str(tags[tag_name])
                    return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
        except Exception:
            pass

    # exifread 不可用时，用 Pillow 作为后备
    try:
        from PIL import Image
        with Image.open(filepath) as img:
            exif = img.getexif()
            if not exif:
                return None
            exif_ifd = exif.get_ifd(0x8769)
            date_str = None
            if exif_ifd:
                date_str = exif_ifd.get(36867) or exif_ifd.get(36868)
            if not date_str:
                date_str = exif.get(306)
            if date_str:
                return datetime.strptime(str(date_str), "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass

    return None


def get_video_date(filepath: Path) -> Optional[datetime]:

    """用 ffprobe 读取视频元数据中的 creation_time。"""
    if not _ffprobe_available:
        return None
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json',
             '-show_format', '-show_streams', str(filepath)],
            capture_output=True, text=True, timeout=30,
            encoding='utf-8', errors='replace',
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)

        creation_time = None
        # 先看 format 级别
        fmt_tags = data.get('format', {}).get('tags', {})
        creation_time = fmt_tags.get('creation_time') or fmt_tags.get('com.apple.quicktime.creationdate')
        # 再看 streams
        if not creation_time:
            for stream in data.get('streams', []):
                ct = stream.get('tags', {}).get('creation_time')
                if ct:
                    creation_time = ct
                    break

        if creation_time:
            # 处理 ISO 8601 格式
            ct = creation_time.replace('Z', '+00:00')
            dt = datetime.fromisoformat(ct)
            return dt.astimezone().replace(tzinfo=None)
    except Exception:
        pass
    return None


def parse_date_from_filename(filepath: Path) -> Optional[datetime]:
    """从文件名解析日期。支持日期格式和 Unix 毫秒时间戳。"""
    name = filepath.stem  # 不含扩展名

    # 尝试日期格式: "2018-02-11 184617"
    m = _RE_DATE_FILENAME.search(name)
    if m:
        try:
            return datetime(
                int(m.group(1)), int(m.group(2)), int(m.group(3)),
                int(m.group(4)), int(m.group(5)), int(m.group(6)),
            )
        except ValueError:
            pass

    # 尝试 Unix 毫秒时间戳: "1464689880000"
    m = _RE_TIMESTAMP.match(name)
    if m:
        ts_str = m.group(1)
        ts = int(ts_str)
        # 如果是 10 位，认为是秒
        if len(ts_str) == 10:
            ts *= 1000
        if _TS_MIN <= ts <= _TS_MAX:
            try:
                return datetime.fromtimestamp(ts / 1000)
            except (OSError, ValueError):
                pass

    return None


def get_capture_date(filepath: Path) -> tuple[Optional[datetime], str]:
    """
    获取拍摄日期，两级回退:
    1. EXIF/视频元数据
    2. 文件名解析
    无法确定时返回 (None, "unknown")，不再用 mtime 冒充拍摄时间。
    """
    ext = filepath.suffix.lower()

    # 第一级: 元数据
    if ext in PHOTO_EXTENSIONS:
        dt = get_photo_date(filepath)
        if dt is not None:
            return dt, "exif"
    elif ext in VIDEO_EXTENSIONS:
        dt = get_video_date(filepath)
        if dt is not None:
            return dt, "ffprobe"

    # 第二级: 文件名
    dt = parse_date_from_filename(filepath)
    if dt is not None:
        return dt, "filename"

    # 无法确定日期
    return None, "unknown"


# ---------------------------------------------------------------------------
# 文件操作
# ---------------------------------------------------------------------------

def build_dest_path(output_dir: Path, filepath: Path, capture_date: Optional[datetime]) -> Path:
    """构建目标路径。有日期的放 YYYY/YYYY-MM/，无日期的放 _未知日期/。"""
    if capture_date is not None:
        year = capture_date.strftime("%Y")
        year_month = capture_date.strftime("%Y-%m")
        dest_dir = output_dir / year / year_month
    else:
        dest_dir = output_dir / "_未知日期"
    dest_path = dest_dir / filepath.name

    # 重名冲突处理
    counter = 1
    while dest_path.exists():
        dest_path = dest_dir / f"{filepath.stem}_{counter}{filepath.suffix}"
        counter += 1

    return dest_path


def copy_file(src: Path, dest: Path, dry_run: bool = False) -> bool:
    """复制文件，保留元数据。"""
    try:
        if dry_run:
            return True
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return True
    except (OSError, shutil.Error) as e:
        print(f"  错误: 复制失败 {src} -> {dest}: {e}")
        return False


# ---------------------------------------------------------------------------
# CLI & Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='照片/视频去重整理工具 - 从多个文件夹去重并按拍摄日期整理',
    )
    parser.add_argument(
        'sources', nargs='+', type=Path, metavar='SOURCE',
        help='源文件夹路径（可指定多个）',
    )
    parser.add_argument(
        '-o', '--output', required=True, type=Path,
        help='输出目录路径',
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='只显示将要执行的操作，不实际复制文件',
    )
    parser.add_argument(
        '--verbose', action='store_true',
        help='显示每个文件的处理详情',
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("=" * 50)
    print("  照片/视频去重整理工具")
    print("=" * 50)

    if args.dry_run:
        print("  [DRY-RUN 模式 - 不会实际复制文件]")
    print()

    # 启动检查
    print("检查依赖...")
    check_exifread()
    if _exifread_available:
        print("  exifread: 可用")
    else:
        print("  exifread: 不可用 (将用 Pillow 读取 EXIF，内存占用稍高)")

    check_heif()
    if _heif_available:
        print("  pillow-heif: 可用")
    else:
        print("  pillow-heif: 不可用 (HEIC/HEIF 文件将使用文件名/mtime 获取日期)")

    check_ffprobe()
    if _ffprobe_available:
        print("  ffprobe: 可用")
    else:
        print("  ffprobe: 不可用 (视频文件将使用文件名/mtime 获取日期)")
    print()

    # 验证源目录
    valid_sources = [s for s in args.sources if s.is_dir()]
    if not valid_sources:
        print("错误: 没有有效的源文件夹！")
        sys.exit(1)

    # 1. 扫描
    print(f"[1/3] 扫描 {len(valid_sources)} 个源文件夹...")
    all_files = scan_sources(valid_sources)
    total_found = len(all_files)
    print(f"  找到 {total_found} 个媒体文件")
    if total_found == 0:
        print("没有找到任何媒体文件，退出。")
        return
    print()

    # 2. 去重
    print("[2/3] 去重...")
    unique_files, duplicate_pairs = deduplicate(all_files, verbose=args.verbose)
    dup_count = len(duplicate_pairs)
    print(f"  去重结果: {len(unique_files)} 个唯一文件, {dup_count} 个重复")
    print()

    # 3. 整理
    print(f"[3/3] 按日期整理到 {args.output} ...")
    organized = 0
    failed = 0
    date_sources = defaultdict(int)

    # 3a. 整理唯一文件
    for filepath in tqdm(unique_files, desc="  整理中", unit="个"):
        try:
            capture_date, source = get_capture_date(filepath)
            date_sources[source] += 1
            dest = build_dest_path(args.output, filepath, capture_date)

            if args.verbose:
                date_str = capture_date.strftime('%Y-%m-%d') if capture_date else "未知"
                tqdm.write(f"    {filepath.name} -> {dest.relative_to(args.output)} [{source}: {date_str}]")

            if copy_file(filepath, dest, dry_run=args.dry_run):
                organized += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            if args.verbose:
                tqdm.write(f"    错误: {filepath}: {e}")

    # 3b. 重复文件复制到 _重复文件/ 文件夹，并生成对照清单
    dup_copied = 0
    dup_log_lines: list[str] = []
    if duplicate_pairs:
        dup_dir = args.output / "_重复文件"
        print(f"\n  复制 {dup_count} 个重复文件到 {dup_dir} ...")
        for dup_file, original in tqdm(duplicate_pairs, desc="  重复文件", unit="个", leave=False):
            dest = dup_dir / dup_file.name
            counter = 1
            while dest.exists():
                dest = dup_dir / f"{dup_file.stem}_{counter}{dup_file.suffix}"
                counter += 1
            if copy_file(dup_file, dest, dry_run=args.dry_run):
                dup_copied += 1
            dup_log_lines.append(f"{dup_file}  <--重复于-->  {original}")
        # 写对照清单
        if not args.dry_run and dup_log_lines:
            dup_dir.mkdir(parents=True, exist_ok=True)
            log_path = dup_dir / "_重复对照清单.txt"
            log_path.write_text("\n".join(dup_log_lines), encoding="utf-8")

    # 汇总
    print()
    print("=" * 50)
    print("  整理完成")
    print("=" * 50)
    print(f"  源文件夹数量:        {len(valid_sources)}")
    print(f"  总文件数:           {total_found}")
    print(f"  重复文件:           {dup_count} (已复制到 _重复文件/)")
    print(f"  成功整理:           {organized}")
    print(f"  失败文件:           {failed}")
    print(f"  --- 日期来源 ---")
    print(f"  使用元数据日期:      {date_sources.get('exif', 0) + date_sources.get('ffprobe', 0)}")
    print(f"  使用文件名日期:      {date_sources.get('filename', 0)}")
    print(f"  无法确定日期:        {date_sources.get('unknown', 0)} (已放入 _未知日期/)")
    print(f"  输出目录:           {args.output}")
    print("=" * 50)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n已中断。")
        sys.exit(1)
