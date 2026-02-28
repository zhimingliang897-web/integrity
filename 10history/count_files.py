#!/usr/bin/env python3
"""
count_files.py - 统计目录下所有文件数量，按扩展名分类。

用法:
    python count_files.py 路径1 [路径2 ...]
"""
import argparse
import os
from collections import defaultdict
from pathlib import Path


def count_dir(root: Path) -> tuple[int, dict[str, int]]:
    """统计目录下所有文件，返回 (总数, {扩展名: 数量})。"""
    total = 0
    by_ext: dict[str, int] = defaultdict(int)
    for dirpath, dirnames, filenames in os.walk(root):
        # 跳过隐藏目录
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        for f in filenames:
            ext = Path(f).suffix.lower() or '(无扩展名)'
            by_ext[ext] += 1
            total += 1
    return total, dict(by_ext)


def main():
    parser = argparse.ArgumentParser(description='统计目录下所有文件数量')
    parser.add_argument('paths', nargs='+', type=Path, help='要统计的目录路径')
    args = parser.parse_args()

    grand_total = 0
    grand_ext: dict[str, int] = defaultdict(int)

    for p in args.paths:
        if not p.is_dir():
            print(f"  跳过: {p} (不是目录)")
            continue

        total, by_ext = count_dir(p)
        grand_total += total

        print(f"\n{p}  ({total} 个文件)")
        print("-" * 40)
        for ext, cnt in sorted(by_ext.items(), key=lambda x: -x[1]):
            grand_ext[ext] += cnt
            print(f"  {ext:12s}  {cnt:>8,}")

    if len(args.paths) > 1:
        print(f"\n{'=' * 40}")
        print(f"总计: {grand_total:,} 个文件")
        print("=" * 40)
        for ext, cnt in sorted(grand_ext.items(), key=lambda x: -x[1]):
            print(f"  {ext:12s}  {cnt:>8,}")

    print()


if __name__ == '__main__':
    main()
