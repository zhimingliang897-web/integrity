
#!/usr/bin/env python3
"""
verify_dup.py - 验证重复文件是否确实在整理结果中有对应原件

用法:
    python verify_dup.py <整理后的根目录>

它会：
1. 读取 _重复文件/ 中每个文件的 MD5
2. 在日期文件夹中搜索相同 MD5 的文件
3. 报告哪些找到了对应原件，哪些没找到
"""
import hashlib
import sys
from pathlib import Path


def md5(filepath: Path) -> str:
    h = hashlib.md5(usedforsecurity=False)
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(8 * 1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def main():
    if len(sys.argv) < 2:
        print("用法: python verify_dup.py <整理后的根目录>")
        sys.exit(1)

    root = Path(sys.argv[1])
    dup_dir = root / "_重复文件"
    unknown_dir = root / "_未知日期"

    if not dup_dir.is_dir():
        print(f"未找到重复文件夹: {dup_dir}")
        sys.exit(1)

    # 收集日期文件夹中所有文件的哈希
    print("正在扫描日期文件夹中的文件...")
    date_hashes: dict[str, Path] = {}
    date_files = [
        f for f in root.rglob('*')
        if f.is_file()
        and not str(f).startswith(str(dup_dir))
        and f.name != '_重复对照清单.txt'
    ]
    for i, f in enumerate(date_files):
        if i % 500 == 0:
            print(f"  已扫描 {i}/{len(date_files)}...")
        try:
            h = md5(f)
            date_hashes[h] = f
        except OSError:
            pass
    print(f"  日期文件夹共 {len(date_hashes)} 个文件")

    # 检查每个重复文件
    print("\n正在验证重复文件...")
    dup_files = [f for f in dup_dir.iterdir() if f.is_file() and f.name != '_重复对照清单.txt']
    found = 0
    not_found = 0
    not_found_list = []

    for f in dup_files:
        try:
            h = md5(f)
            if h in date_hashes:
                found += 1
            else:
                not_found += 1
                not_found_list.append(f.name)
        except OSError:
            not_found += 1
            not_found_list.append(f.name)

    print(f"\n验证结果:")
    print(f"  重复文件总数:   {len(dup_files)}")
    print(f"  找到对应原件:   {found}")
    print(f"  未找到原件:     {not_found}")

    if not_found_list:
        print(f"\n以下重复文件在日期文件夹中没有找到对应原件:")
        for name in not_found_list[:20]:
            print(f"  {name}")
        if len(not_found_list) > 20:
            print(f"  ... 还有 {len(not_found_list) - 20} 个")


if __name__ == '__main__':
    main()
