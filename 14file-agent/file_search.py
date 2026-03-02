import os
import fnmatch
import json
import time

# Try to import optional libraries for content search
try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# Cache config to avoid repeated file reads
_config_cache = None
_config_mtime = 0


def load_config():
    global _config_cache, _config_mtime
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        mtime = os.path.getmtime(config_path)
        if _config_cache is None or mtime > _config_mtime:
            with open(config_path, "r", encoding="utf-8") as f:
                _config_cache = json.load(f)
            _config_mtime = mtime
        return _config_cache
    except Exception:
        return {
            "search_roots": ["C:\\Users"],
            "excluded_dirs": ["Windows", "Program Files", "node_modules", ".git"],
            "max_results": 20
        }


def format_size(size_bytes):
    """Human-readable file size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024*1024):.1f} MB"
    else:
        return f"{size_bytes / (1024*1024*1024):.1f} GB"


def format_time(ts):
    """Human-readable modification time."""
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))


def should_skip_dir(dirpath, excluded_dirs, excluded_set=None):
    """Check if a directory should be skipped."""
    dirpath_lower = dirpath.lower()
    dirname = os.path.basename(dirpath)
    dirname_lower = dirname.lower()

    if excluded_set and dirname_lower in excluded_set:
        return True

    for excl in excluded_dirs:
        excl_lower = excl.lower()
        if excl_lower in dirpath_lower:
            return True
        if fnmatch.fnmatch(dirname_lower, excl_lower):
            return True
    return False


def read_text_content(filepath):
    """Read text content from a file for content search."""
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext in [".txt", ".md", ".py", ".js", ".html", ".css", ".csv", ".log", ".json", ".xml"]:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(50000)  # limit to 50KB
        elif ext == ".docx" and HAS_DOCX:
            doc = docx.Document(filepath)
            return "\n".join([p.text for p in doc.paragraphs])
        elif ext == ".pdf" and HAS_PDF:
            text = []
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages[:10]:  # first 10 pages
                    text.append(page.extract_text() or "")
            return "\n".join(text)
    except Exception:
        pass
    return ""


def get_all_drives():
    """获取所有可用的磁盘驱动器（Windows）。"""
    drives = []
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    return drives


def list_directory(path=None, show_hidden=False):
    """
    浏览目录内容。

    Args:
        path: 要浏览的目录路径。None 则列出所有可用磁盘。
        show_hidden: 是否显示隐藏文件/目录

    Returns:
        dict with 'path', 'dirs', 'files', 'error'
    """
    # 如果没有指定路径，列出所有磁盘
    if path is None or path.strip() in ("", "/", "\\"):
        drives = get_all_drives()
        return {
            "path": "计算机",
            "dirs": [{"name": d, "path": d, "is_drive": True} for d in drives],
            "files": [],
            "error": None
        }

    # 规范化路径
    path = os.path.normpath(path)

    if not os.path.exists(path):
        return {"path": path, "dirs": [], "files": [], "error": f"路径不存在: {path}"}

    if not os.path.isdir(path):
        return {"path": path, "dirs": [], "files": [], "error": f"不是目录: {path}"}

    dirs = []
    files = []

    try:
        entries = os.scandir(path)
        for entry in entries:
            try:
                # 跳过隐藏文件（以.开头或Windows隐藏属性）
                if not show_hidden and entry.name.startswith("."):
                    continue

                stat = entry.stat()
                if entry.is_dir(follow_symlinks=False):
                    dirs.append({
                        "name": entry.name,
                        "path": entry.path,
                        "modified": format_time(stat.st_mtime)
                    })
                else:
                    ext = os.path.splitext(entry.name)[1].lower()
                    files.append({
                        "name": entry.name,
                        "path": entry.path,
                        "size": stat.st_size,
                        "size_str": format_size(stat.st_size),
                        "modified": format_time(stat.st_mtime),
                        "ext": ext
                    })
            except (PermissionError, OSError):
                continue

        # 排序：目录按名称，文件按修改时间倒序
        dirs.sort(key=lambda x: x["name"].lower())
        files.sort(key=lambda x: x["modified"], reverse=True)

        return {
            "path": path,
            "dirs": dirs,
            "files": files,
            "error": None
        }

    except PermissionError:
        return {"path": path, "dirs": [], "files": [], "error": f"没有权限访问: {path}"}
    except Exception as e:
        return {"path": path, "dirs": [], "files": [], "error": str(e)}


def search_files(keywords, file_types=None, content_keyword=None, max_results=20,
                 timeout_seconds=300, search_roots=None, progress_callback=None):
    """
    搜索文件（按名称关键词，可选按内容）。

    Args:
        keywords: 关键词列表，匹配文件名或文件夹路径
        file_types: 扩展名列表如 ['.pdf', '.docx']，None 表示所有类型
        content_keyword: 搜索文件内容的关键词
        max_results: 最大返回结果数
        timeout_seconds: 最大搜索时间（秒），默认300秒（5分钟）
        search_roots: 覆盖 config 的搜索根目录
        progress_callback: fn(status_str, found_count) 进度回调，可为 None

    Returns:
        list of dicts with file info
    """
    config = load_config()

    if search_roots is None:
        search_roots = config.get("search_roots", ["C:\\Users"])

    if search_roots == ["all"] or search_roots == "all":
        search_roots = get_all_drives()

    excluded_dirs = config.get("excluded_dirs", [])

    file_types_lower = set(ft.lower() for ft in file_types) if file_types else None
    keywords_lower = [kw.lower() for kw in keywords] if keywords else []
    excluded_set = set(d.lower() for d in excluded_dirs if '\\' not in d and '/' not in d)

    results = []
    seen_paths = set()
    start_time = time.time()
    dirs_scanned = 0

    for root in search_roots:
        if not os.path.exists(root):
            continue

        try:
            for dirpath, dirnames, filenames in os.walk(root, topdown=True, onerror=lambda e: None):
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    if progress_callback:
                        progress_callback(f"搜索超时（{int(elapsed)}秒），返回已找到的结果", len(results))
                    break

                if len(results) >= max_results * 10:
                    break

                dirnames[:] = [
                    d for d in dirnames
                    if not should_skip_dir(os.path.join(dirpath, d), excluded_dirs, excluded_set)
                ]

                dirs_scanned += 1
                # 每扫描50个目录汇报一次进度
                if progress_callback and dirs_scanned % 50 == 0:
                    progress_callback(
                        f"正在扫描：{dirpath}",
                        len(results)
                    )

                dirpath_lower = dirpath.lower()

                for filename in filenames:
                    if len(results) >= max_results * 10:
                        break

                    filepath = os.path.join(dirpath, filename)
                    if filepath in seen_paths:
                        continue

                    ext = os.path.splitext(filename)[1].lower()
                    if file_types_lower and ext not in file_types_lower:
                        continue

                    if keywords_lower:
                        filename_lower = filename.lower()
                        matched = any(kw in filename_lower or kw in dirpath_lower
                                      for kw in keywords_lower)
                        if not matched:
                            continue

                    if content_keyword:
                        try:
                            content = read_text_content(filepath)
                            if content_keyword.lower() not in content.lower():
                                continue
                        except Exception:
                            continue

                    try:
                        stat = os.stat(filepath)
                        score = 0
                        filename_lower = filename.lower()
                        for kw in keywords_lower:
                            if kw in filename_lower:
                                score += 10
                            elif kw in dirpath_lower:
                                score += 3

                        results.append({
                            "name": filename,
                            "path": filepath,
                            "size": stat.st_size,
                            "size_str": format_size(stat.st_size),
                            "modified": stat.st_mtime,
                            "modified_str": format_time(stat.st_mtime),
                            "ext": ext,
                            "_score": score
                        })
                        seen_paths.add(filepath)
                    except (PermissionError, OSError, FileNotFoundError):
                        continue

        except (PermissionError, OSError):
            continue

        if time.time() - start_time > timeout_seconds:
            break

    results.sort(key=lambda x: (-x.get("_score", 0), -x["modified"]))
    for r in results:
        r.pop("_score", None)

    return results[:max_results]


def get_file_info(filepath):
    """Get info for a single file."""
    try:
        stat = os.stat(filepath)
        return {
            "name": os.path.basename(filepath),
            "path": filepath,
            "size": stat.st_size,
            "size_str": format_size(stat.st_size),
            "modified_str": format_time(stat.st_mtime),
            "ext": os.path.splitext(filepath)[1].lower()
        }
    except Exception:
        return None
