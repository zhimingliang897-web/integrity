"""utils.py — 共享常量、颜色输出、路径工具"""
import sys
from pathlib import Path

# ── 常量 ──────────────────────────────────────────────────
REPORT_FILE             = "organize_report.json"
CONTENT_PREVIEW_LINES   = 30
MAX_FILE_SIZE_FOR_PREVIEW = 500_000   # bytes，超过不读内容

SKIP_DIRS = {
    ".git", "__pycache__", ".minimax", "node_modules",
    ".venv", "venv", ".claude", ".github",
}
SKIP_EXTS = {".pyc", ".pyo"}

# 无论 LLM 建议什么，这些扩展名的文件在执行层绝对不动
PROTECTED_EXTS = {
    # 代码
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
    ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".sh", ".bat", ".ps1",
    # 配置 / 项目文件
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env", ".json",
    # Web 结构
    ".html", ".htm", ".css",
    # 项目元数据
    ".gitignore", ".gitattributes", ".editorconfig",
    # 文档（README 通常与代码同级，移走会断链）
    ".md", ".rst",
}

# ── 颜色输出（Windows CMD 兼容）─────────────────────────
def _c(text: str, code: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"

RED    = lambda t: _c(t, "91")
GREEN  = lambda t: _c(t, "92")
YELLOW = lambda t: _c(t, "93")
CYAN   = lambda t: _c(t, "96")
BOLD   = lambda t: _c(t, "1")
DIM    = lambda t: _c(t, "2")

# ── 工具函数 ──────────────────────────────────────────────
def fmt_size(size_bytes: int) -> str:
    """人类可读的文件大小。"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
