"""
organize.py — 智能目录整理助手（LLM 驱动）

功能：
    scan      扫描目录，调用 LLM 分析文件用途，生成整理报告（JSON + 可读版）
    classify  按报告将文件移动到推荐位置（逐项确认，支持 --dry-run）
    clean     对建议删除的文件逐一审核，手动输入 y 才删除

设计原则：
    - 通用：不绑定任何具体项目，任意目录均可运行
    - 安全：删除前必须人工确认，绝不静默批量删除
    - 透明：每一步操作前都打印计划，--dry-run 只预演不执行

用法：
    python organize.py                        # 快速扫描当前目录
    python organize.py --mode scan            # 扫描并生成完整报告
    python organize.py --mode classify        # 执行文件移动（有提示）
    python organize.py --mode classify --dry-run  # 预演移动，不实际执行
    python organize.py --mode clean           # 审核并删除建议删除的文件
    python organize.py --dir /path/to/project # 指定目录
    python organize.py --api-key sk-xxx       # 临时指定 API Key

报告文件：organize_report.json（与脚本同目录）
"""

import argparse
import json
import os
import re
import shutil
import sys
import textwrap
import yaml
from pathlib import Path
from typing import Any

# ──────────────────────────────────────────────
# 配置常量
# ──────────────────────────────────────────────
REPORT_FILE = "organize_report.json"   # 报告输出文件名
CONTENT_PREVIEW_LINES = 30             # 读取文件内容的预览行数
MAX_FILE_SIZE_FOR_PREVIEW = 500_000    # 超过 500KB 的文件不读内容（字节）
SKIP_DIRS = {".git", "__pycache__", ".minimax", "node_modules", ".venv", "venv"}
SKIP_EXTENSIONS = {".pyc", ".pyo"}

# ──────────────────────────────────────────────
# 颜色输出（Windows CMD 兼容）
# ──────────────────────────────────────────────
def _c(text: str, code: str) -> str:
    """ANSI 颜色，非 TTY 时降级为无色。"""
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"

RED    = lambda t: _c(t, "91")
GREEN  = lambda t: _c(t, "92")
YELLOW = lambda t: _c(t, "93")
CYAN   = lambda t: _c(t, "96")
BOLD   = lambda t: _c(t, "1")
DIM    = lambda t: _c(t, "2")


# ══════════════════════════════════════════════
# 1. 目录扫描
# ══════════════════════════════════════════════

def scan_directory(root: Path, max_depth: int = 3) -> list[dict]:
    """
    递归扫描目录，收集每个文件的元信息和内容预览。

    Returns:
        list of dicts，每项包含：
            rel_path, abs_path, size_bytes, extension,
            is_text, content_preview, depth
    """
    results = []

    def _walk(dir_path: Path, depth: int):
        if depth > max_depth:
            return
        try:
            entries = sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name))
        except PermissionError:
            return

        for entry in entries:
            if entry.name in SKIP_DIRS:
                continue
            if entry.is_dir():
                _walk(entry, depth + 1)
            elif entry.is_file():
                ext = entry.suffix.lower()
                if ext in SKIP_EXTENSIONS:
                    continue
                try:
                    size = entry.stat().st_size
                except OSError:
                    size = 0

                # 尝试读取文本内容
                content_preview = ""
                is_text = False
                text_extensions = {
                    ".py", ".js", ".ts", ".md", ".txt", ".yaml", ".yml",
                    ".json", ".toml", ".cfg", ".ini", ".bat", ".sh",
                    ".html", ".css", ".rst", ".csv", ".log",
                }
                if ext in text_extensions and size < MAX_FILE_SIZE_FOR_PREVIEW:
                    try:
                        raw = entry.read_text(encoding="utf-8", errors="replace")
                        lines = raw.splitlines()
                        preview_lines = lines[:CONTENT_PREVIEW_LINES]
                        content_preview = "\n".join(preview_lines)
                        if len(lines) > CONTENT_PREVIEW_LINES:
                            content_preview += f"\n... ({len(lines) - CONTENT_PREVIEW_LINES} more lines)"
                        is_text = True
                    except Exception:
                        pass

                results.append({
                    "rel_path": str(entry.relative_to(root)),
                    "abs_path": str(entry.resolve()),
                    "size_bytes": size,
                    "extension": ext,
                    "is_text": is_text,
                    "content_preview": content_preview,
                    "depth": depth,
                })

    _walk(root, 0)
    return results


def format_size(size_bytes: int) -> str:
    """人类可读的文件大小。"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# ══════════════════════════════════════════════
# 2. LLM 调用
# ══════════════════════════════════════════════

def _load_api_config(project_root: Path, cli_key: str) -> dict:
    """
    尝试从以下来源读取 API 配置（优先级从高到低）：
    1. CLI --api-key 参数
    2. 环境变量 DASHSCOPE_API_KEY / OPENAI_API_KEY
    3. 项目 config.yaml
    """
    cfg = {
        "api_key": "",
        "model": "qwen-plus",
        "provider": "dashscope",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    }

    # 从 config.yaml 读取
    for yaml_name in ["config.yaml", "config.yml"]:
        yaml_path = project_root / yaml_name
        if yaml_path.exists():
            try:
                with open(yaml_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                api = data.get("api", {})
                if api.get("api_key"):
                    cfg["api_key"] = api["api_key"]
                if api.get("model"):
                    cfg["model"] = api["model"]
                if api.get("provider"):
                    cfg["provider"] = api["provider"]
            except Exception:
                pass
            break

    # 环境变量覆盖
    cfg["api_key"] = (
        os.environ.get("DASHSCOPE_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or cfg["api_key"]
    )

    # CLI 最高优先级
    if cli_key:
        cfg["api_key"] = cli_key

    # provider → base_url 映射
    provider_urls = {
        "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "openai": "https://api.openai.com/v1",
        "groq": "https://api.groq.com/openai/v1",
    }
    cfg["base_url"] = provider_urls.get(cfg["provider"], cfg["base_url"])

    return cfg


def _call_llm(cfg: dict, system_prompt: str, user_prompt: str) -> str:
    """
    调用 OpenAI-compatible API（兼容 DashScope / OpenAI / Groq）。
    """
    try:
        from openai import OpenAI
    except ImportError:
        print(RED("  [LLM] 未安装 openai 包，请运行: pip install openai"))
        sys.exit(1)

    if not cfg["api_key"]:
        print(RED("  [LLM] 未找到 API Key，请通过 --api-key 或环境变量 DASHSCOPE_API_KEY 提供"))
        sys.exit(1)

    client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])
    response = client.chat.completions.create(
        model=cfg["model"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=4096,
    )
    return response.choices[0].message.content.strip()


def _extract_json(text: str) -> Any:
    """从 LLM 输出中提取 JSON（处理 markdown 代码块包裹的情况）。"""
    # 去除 ```json ... ``` 包裹
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1).strip()
    # 找到第一个 { 或 [
    start = next((i for i, c in enumerate(text) if c in "{["), 0)
    return json.loads(text[start:])


def build_system_prompt() -> str:
    return textwrap.dedent("""
    你是一个专业的项目文件整理助手。你的任务是分析给定目录中的文件列表，
    并以 JSON 格式输出整理建议。

    你必须严格输出以下格式的 JSON，不要有多余的文字：
    {
      "summary": "对整个目录的一句话总结",
      "issues": ["发现的混乱点1", "发现的混乱点2"],
      "actions": [
        {
          "action": "move" | "delete" | "rename" | "fix_content" | "keep",
          "path": "相对路径（原路径）",
          "target": "相对路径（移动/重命名目标，delete/keep/fix_content时为null）",
          "reason": "理由（中文，一句话）",
          "risk": "low" | "medium" | "high",
          "category": "core" | "tool" | "script" | "input" | "output" | "cache" | "temp" | "config" | "doc"
        }
      ],
      "new_dirs": ["建议新建的目录列表（相对路径）"],
      "notes": "额外备注（可选）"
    }

    整理原则：
    1. 核心逻辑/配置文件 → 保留在根目录或整齐的子目录
    2. 工具性脚本（与主流程无关） → tools/
    3. 一次性/批处理脚本 → scripts/
    4. 输入素材（视频、PDF） → input/ 下按课程分子目录
    5. 转录缓存（JSON） → cache/（仅存中间缓存，不存原始素材）
    6. 最终输出文档 → output/
    7. 中间产物（UUID命名、临时、空文件） → 建议 delete，risk=low
    8. 拼写错误且有替代品的文件 → 建议 delete，risk=low
    9. 硬编码绝对路径的文件 → 建议 fix_content，risk=medium
    10. 删除建议必须保守，不确定的文件宁可 keep
    """).strip()


def build_user_prompt(root: Path, files: list[dict]) -> str:
    """构建发送给 LLM 的用户 prompt。"""
    lines = [f"项目根目录: {root}", ""]
    lines.append("文件列表（格式：[大小] 路径 | 内容预览）：")
    lines.append("=" * 60)

    for f in files:
        size_str = format_size(f["size_bytes"])
        lines.append(f"\n[{size_str}] {f['rel_path']}")
        if f["content_preview"]:
            # 截断超长预览
            preview = f["content_preview"][:800]
            for line in preview.splitlines()[:15]:
                lines.append(f"    | {line}")

    lines.append("\n" + "=" * 60)
    lines.append("请根据以上文件信息，输出整理建议 JSON。")
    return "\n".join(lines)


# ══════════════════════════════════════════════
# 3. 三种模式的执行逻辑
# ══════════════════════════════════════════════

def mode_scan(root: Path, api_cfg: dict, report_path: Path):
    """扫描目录，调用 LLM，生成并保存报告。"""
    print(BOLD(f"\n🔍 扫描目录: {root}"))
    files = scan_directory(root)
    print(f"   发现 {len(files)} 个文件\n")

    print(CYAN("📡 调用 LLM 分析中，请稍候..."))
    system = build_system_prompt()
    user = build_user_prompt(root, files)

    raw = _call_llm(api_cfg, system, user)

    try:
        report = _extract_json(raw)
    except json.JSONDecodeError:
        print(RED("  [错误] LLM 返回内容无法解析为 JSON，原始内容："))
        print(DIM(raw[:1000]))
        sys.exit(1)

    # 注入根目录信息，方便后续 classify/clean 使用
    report["_root"] = str(root)

    # 保存报告
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 打印可读报告
    _print_report(report)
    print(f"\n💾 报告已保存: {report_path}")
    print(f"\n下一步:")
    print(f"  python organize.py --mode classify --dry-run  # 预演移动")
    print(f"  python organize.py --mode classify            # 执行移动")
    print(f"  python organize.py --mode clean               # 审核删除")


def _print_report(report: dict):
    """打印人类可读的报告。"""
    print(f"\n{'═'*60}")
    print(BOLD("📋 整理分析报告"))
    print(f"{'═'*60}")
    print(f"📌 {report.get('summary', '')}\n")

    issues = report.get("issues", [])
    if issues:
        print(BOLD("⚠️  发现的问题："))
        for issue in issues:
            print(f"  • {issue}")
        print()

    actions = report.get("actions", [])
    by_action = {}
    for a in actions:
        by_action.setdefault(a["action"], []).append(a)

    icons = {
        "move": "📦", "delete": "🗑️", "rename": "✏️",
        "fix_content": "🔧", "keep": "✅",
    }
    labels = {
        "move": "移动", "delete": "删除", "rename": "重命名",
        "fix_content": "修正内容", "keep": "保留",
    }
    risk_colors = {"low": GREEN, "medium": YELLOW, "high": RED}

    for action, items in by_action.items():
        if action == "keep":
            continue
        icon = icons.get(action, "?")
        label = labels.get(action, action)
        print(BOLD(f"{icon} {label}（{len(items)} 项）"))
        for item in items:
            risk = item.get("risk", "low")
            risk_fn = risk_colors.get(risk, CYAN)
            target = f" → {item['target']}" if item.get("target") else ""
            print(f"  {risk_fn(f'[{risk}]')} {item['path']}{target}")
            print(DIM(f"         {item['reason']}"))
        print()

    new_dirs = report.get("new_dirs", [])
    if new_dirs:
        print(BOLD("📁 建议新建目录："))
        for d in new_dirs:
            print(f"  {d}/")
        print()

    notes = report.get("notes", "")
    if notes:
        print(BOLD("📝 备注："))
        print(f"  {notes}")


def _load_report(report_path: Path) -> dict:
    """加载已有报告文件。"""
    if not report_path.exists():
        print(RED(f"  [错误] 未找到报告文件: {report_path}"))
        print(f"  请先运行: python organize.py --mode scan")
        sys.exit(1)
    with open(report_path, encoding="utf-8") as f:
        return json.load(f)


def _confirm(prompt: str, default_yes: bool = False) -> bool:
    """交互式确认，返回 True 表示用户同意。"""
    hint = "[Y/n]" if default_yes else "[y/N]"
    answer = input(f"{prompt} {hint}: ").strip().lower()
    if not answer:
        return default_yes
    return answer in ("y", "yes", "是")


def mode_classify(root: Path, report_path: Path, dry_run: bool):
    """按报告执行移动/重命名操作。"""
    report = _load_report(report_path)
    report_root = Path(report.get("_root", root))

    actions = [a for a in report.get("actions", []) if a["action"] in ("move", "rename")]
    new_dirs = report.get("new_dirs", [])

    if not actions:
        print(YELLOW("  没有需要移动/重命名的文件。"))
        return

    print(BOLD(f"\n📦 文件分类{'（预演模式）' if dry_run else ''}"))
    print(f"   共 {len(actions)} 项操作\n")

    # 先建目录
    for d in new_dirs:
        dir_path = report_root / d
        if not dir_path.exists():
            print(f"  {'[DRY]' if dry_run else ''} 创建目录: {d}/")
            if not dry_run:
                dir_path.mkdir(parents=True, exist_ok=True)

    moved = 0
    skipped = 0

    for a in actions:
        src = report_root / a["path"]
        dst = report_root / a["target"]

        if not src.exists():
            print(YELLOW(f"  [跳过] 源文件不存在: {a['path']}"))
            skipped += 1
            continue

        if dst.exists():
            print(YELLOW(f"  [跳过] 目标已存在: {a['target']}"))
            skipped += 1
            continue

        risk_fn = {
            "low": GREEN, "medium": YELLOW, "high": RED
        }.get(a.get("risk", "low"), CYAN)
        risk_tag = risk_fn(f"[{a['risk']}]")
        print(f"  {risk_tag} {a['path']}")
        print(f"       -> {a['target']}")
        print(DIM(f"       {a['reason']}"))

        if dry_run:
            moved += 1
            continue

        if a.get("risk") == "high":
            if not _confirm("  ⚠️  高风险操作，确认执行？"):
                skipped += 1
                continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        print(GREEN("       ✓ 完成"))
        moved += 1

    print(f"\n{'─'*40}")
    print(f"  {'预演' if dry_run else '完成'}: {moved} 项移动，{skipped} 项跳过")
    if dry_run:
        print(f"\n  去掉 --dry-run 参数即可实际执行。")


def mode_clean(root: Path, report_path: Path):
    """对建议删除的文件逐一审核。"""
    report = _load_report(report_path)
    report_root = Path(report.get("_root", root))

    actions = [a for a in report.get("actions", []) if a["action"] == "delete"]

    if not actions:
        print(YELLOW("  没有建议删除的文件。"))
        return

    print(BOLD(f"\n🗑️  待审核删除列表（共 {len(actions)} 项）"))
    print(RED("  ⚠️  每项均需手动输入 y 确认，输入其他任何内容则跳过"))
    print(f"{'─'*50}\n")

    deleted = 0
    skipped = 0

    for i, a in enumerate(actions, 1):
        path = report_root / a["path"]
        risk_fn = {
            "low": GREEN, "medium": YELLOW, "high": RED
        }.get(a.get("risk", "low"), CYAN)

        size_str = format_size(path.stat().st_size) if path.exists() else "不存在"
        risk_tag = risk_fn(f"[{a['risk']}]")
        print(f"[{i}/{len(actions)}] {risk_tag} {a['path']} ({size_str})")
        print(f"   理由: {a['reason']}")

        if not path.exists():
            print(DIM("   （文件不存在，跳过）"))
            skipped += 1
            continue

        # 显示内容预览（文本文件）
        if path.suffix.lower() in {".py", ".md", ".txt", ".json", ".yaml", ".bat", ".sh"}:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                lines = content.splitlines()[:8]
                print(DIM("   预览:"))
                for line in lines:
                    print(DIM(f"   | {line[:80]}"))
            except Exception:
                pass

        answer = input(f"\n   确认删除？[y/N]: ").strip().lower()
        if answer == "y":
            try:
                path.unlink()
                print(GREEN(f"   ✓ 已删除"))
                deleted += 1
            except Exception as e:
                print(RED(f"   ✗ 删除失败: {e}"))
                skipped += 1
        else:
            print(DIM("   → 跳过"))
            skipped += 1
        print()

    print(f"{'─'*40}")
    print(f"  完成: 删除 {deleted} 个，跳过 {skipped} 个")


# ══════════════════════════════════════════════
# 4. 主入口
# ══════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="🗂️  智能目录整理助手（LLM 驱动）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        示例:
          python organize.py                         快速扫描当前目录
          python organize.py --mode classify --dry-run  预演文件移动
          python organize.py --mode clean            审核删除建议
          python organize.py --dir e:/myproject      整理指定目录
        """),
    )
    parser.add_argument(
        "--mode", choices=["scan", "classify", "clean"],
        default="scan",
        help="运行模式（默认: scan）",
    )
    parser.add_argument(
        "--dir", default=".",
        help="要整理的目录（默认: 当前目录）",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="classify 模式下仅预演，不实际执行",
    )
    parser.add_argument(
        "--api-key", default="",
        help="LLM API Key（覆盖 config.yaml 和环境变量）",
    )
    parser.add_argument(
        "--report", default="",
        help=f"报告文件路径（默认: <dir>/{REPORT_FILE}）",
    )
    args = parser.parse_args()

    root = Path(args.dir).resolve()
    if not root.exists():
        print(RED(f"  [错误] 目录不存在: {root}"))
        sys.exit(1)

    report_path = Path(args.report) if args.report else root / REPORT_FILE

    if args.mode == "scan":
        api_cfg = _load_api_config(root, args.api_key)
        mode_scan(root, api_cfg, report_path)
    elif args.mode == "classify":
        mode_classify(root, report_path, args.dry_run)
    elif args.mode == "clean":
        mode_clean(root, report_path)


if __name__ == "__main__":
    main()
