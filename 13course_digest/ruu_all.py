import os
from pathlib import Path

cache_dir = Path("cache/3d")
for file in cache_dir.iterdir():
    if file.is_file() and file.suffix.lower() == ".mp4":
        os.system(f"python main.py \"{file}\"")