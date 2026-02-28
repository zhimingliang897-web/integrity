"""
organize.py — 智能目录整理助手（LLM 驱动）
存放位置：e:/integrity/tools/organize.py

每次运行时指定要整理的目录路径，支持相对路径或绝对路径。

用法：
    # 在任意位置运行，通过路径指定目标
    python e:/integrity/tools/organize.py e:/integrity/13course_digest
    python e:/integrity/tools/organize.py e:/integrity/2台词
    python e:/integrity/tools/organize.py e:/integrity/8评论 --mode classify --dry-run
    python e:/integrity/tools/organize.py e:/integrity/7爬虫 --mode clean

模式：
    scan      扫描 + LLM 分析，生成 organize_report.json（默认）
    classify  按报告执行文件移动（--dry-run 仅预演）
    clean     逐一审核建议删除的文件，手动输入 y 才删

API 配置查找优先级（从低到高）：
    organize_config.yaml（与本脚本同目录）→ 目标目录 config.yaml → 环境变量 → --api-key
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
# 常量
# ──────────────────────────────────────────────
REPORT_FILE = "organize_report.json"
CONTENT_PREVIEW_LINES = 30
MAX_FILE_SIZE_FOR_PREVIEW = 500_000
SKIP_DIRS = {".git", "__pycache__", ".minimax", "node_modules", ".venv", "venv", ".claude", ".github"}
SKIP_EXTS = {".pyc", ".pyo"}

# 脚本所在目录（全局配置读取用）
SCRIPT_DIR = Path(__file__).parent

# ──────────────────────────────────────────────
# 颜色输出
# ──────────────────────────────────────────────
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


# ══════════════════════════════════════════════
# 1. 目录扫描
# ══════════════════════════════════════════════

def scan_directory(root: Path, max_depth: int = 3) -> list[dict]:
    """递归扫描目录，收集文件元信息和内容预览。"""
    results = []
    text_exts = {
        ".py", ".js", ".ts", ".md", ".txt", ".yaml", ".yml",
        ".json", ".toml", ".cfg", ".ini", ".bat", ".sh",
        ".html", ".css", ".rst", ".csv", ".log",
    }

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
                if ext in SKIP_EXTS:
                    continue
                try:
                    size = entry.stat().st_size
                except OSError:
                    size = 0
                content_preview = ""
                is_text = False
                if ext in text_exts and size < MAX_FILE_SIZE_FOR_PREVIEW:
                    try:
                        raw = entry.read_text(encoding="utf-8", errors="replace")
                        lines = raw.splitlines()
                        content_preview = "\n".join(lines[:CONTENT_PREVIEW_LINES])
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


def fmt_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# ══════════════════════════════════════════════
# 2. API 配置加载
# ══════════════════════════════════════════════

def _read_yaml_api(yaml_path: Path, cfg: dict) -> bool:
    """从 yaml 读取 api 配置块，读取到 key 返回 True。"""
    if not yaml_path.exists():
        return False
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
        return bool(cfg["api_key"])
    except Exception:
        return False


def _load_api_config(target_dir: Path, cli_key: str) -> dict:
    """
    优先级（低→高，后者覆盖前者）：
      organize_config.yaml（脚本同目录）
      → config.yaml（目标目录）
      → 环境变量 DASHSCOPE_API_KEY / OPENAI_API_KEY
      → --api-key 参数
    """
    cfg = {
        "api_key": "",
        "model": "qwen-plus",
        "provider": "dashscope",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    }
    # 全局配置
    for name in ["organize_config.yaml", "organize_config.yml"]:
        if _read_yaml_api(SCRIPT_DIR / name, cfg):
            break
    # 项目专属配置
    for name in ["config.yaml", "config.yml"]:
        if _read_yaml_api(target_dir / name, cfg):
            break
    # 环境变量
    env_key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if env_key:
        cfg["api_key"] = env_key
    # CLI
    if cli_key:
        cfg["api_key"] = cli_key

    provider_urls = {
        "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "openai":    "https://api.openai.com/v1",
        "groq":      "https://api.groq.com/openai/v1",
    }
    cfg["base_url"] = provider_urls.get(cfg["provider"], cfg["base_url"])
    return cfg


# ══════════════════════════════════════════════
# 3. LLM 调用
# ══════════════════════════════════════════════

def _call_llm(cfg: dict, system_prompt: str, user_prompt: str) -> str:
    try:
        from openai import OpenAI
    except ImportError:
        print(RED("  [LLM] 未安装 openai 包：pip install openai"))
        sys.exit(1)
    if not cfg["api_key"]:
        print(RED("  [错误] 未找到 API Key！"))
        print(f"  请在 {SCRIPT_DIR / 'organize_config.yaml'} 中配置，或使用 --api-key 参数")
        sys.exit(1)
    client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])
    resp = client.chat.completions.create(
        model=cfg["model"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=4096,
    )
    return resp.choices[0].message.content.strip()


def _extract_json(text: str) -> Any:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1).strip()
    start = next((i for i, c in enumerate(text) if c in "{["), 0)
    return json.loads(text[start:])


def build_system_prompt() -> str:
    return textwrap.dedent("""
    你是一个保守且安全的项目资产文件整理助手。你的主要目标是整理【数据资产】和【中间副产物】，而【绝对不要打乱代码和配置】。

    【极其重要的安全原则】
    项目中已经预先定义了很多路径相互依赖。如果你随意移动代码或配置文件，会导致项目彻底崩溃。
    因此，对于所有核心逻辑代码（如 *.py, *.js, *.html, *.bat, *.sh 等）和项目配置文件（如 *.yaml, *.json, *.ini, config.* 等），你 **绝对不要建议移动或重命名**。不管它们长得多么像工具脚本，请统一把它们的 action 设为 keep。

    你的整理范围仅限于：
    1. 原始输入素材（如视频 .mp4、音频、PDF讲义、图片等）→ 可移至 input/、media/ 等适当的资源子目录
    2. 缓存和中间数据（如大模型分析缓存的 .json、转录残留文件等）→ 移至 cache/ 或 temp/
    3. 最终输出成品文档（如用户需要的最终版 .md, .docx 报告）→ 移至 output/ 或 docs/
    4. 无用垃圾文件（如毫无意义的 UUID 临时文件、大小极小的空残留文件）→ 建议 delete（设置 risk="low"）
    5. 重复的错别字垃圾文件（如果有明显替代品）→ 建议 delete（设置 risk="low"）
    6. 其他不确定、不敢动的文件 → 必须 keep

    严格输出以下 JSON，不要有多余文字：
    {
      "summary": "对整个目录的整理总结",
      "issues": ["发现的混乱点1", "发现的混乱点2"],
      "actions": [
        {
          "action": "move" | "delete" | "rename" | "keep",
          "path": "相对路径（原路径）",
          "target": "目标相对路径（delete/keep 时为 null）",
          "reason": "理由（中文一句话）",
          "risk": "low" | "medium" | "high",
          "category": "core" | "tool" | "script" | "input" | "output" | "cache" | "temp" | "config" | "doc"
        }
      ],
      "new_dirs": ["建议新建的纯资源/数据存放目录"],
      "notes": "额外备注"
    }
    """).strip()


def build_user_prompt(root: Path, files: list[dict]) -> str:
    lines = [f"项目根目录: {root}", "", "文件列表（格式：[大小] 路径 | 内容预览）：", "=" * 60]
    for f in files:
        lines.append(f"\n[{fmt_size(f['size_bytes'])}] {f['rel_path']}")
        if f["content_preview"]:
            for line in f["content_preview"][:800].splitlines()[:15]:
                lines.append(f"    | {line}")
    lines += ["\n" + "=" * 60, "请根据以上信息，输出整理建议 JSON。"]
    return "\n".join(lines)


# ══════════════════════════════════════════════
# 4. 三种模式
# ══════════════════════════════════════════════

def mode_scan(root: Path, api_cfg: dict, report_path: Path):
    print(BOLD(f"\n🔍 扫描目录: {root}"))
    files = scan_directory(root)
    print(f"   发现 {len(files)} 个文件\n")
    print(CYAN("📡 调用 LLM 分析中，请稍候..."))
    raw = _call_llm(api_cfg, build_system_prompt(), build_user_prompt(root, files))
    try:
        report = _extract_json(raw)
    except json.JSONDecodeError:
        print(RED("  [错误] LLM 返回内容无法解析为 JSON："))
        print(DIM(raw[:1000]))
        sys.exit(1)
    report["_root"] = str(root)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    _print_report(report)
    script = Path(__file__).resolve()
    print(f"\n💾 报告已保存: {report_path}")
    print(f"\n下一步:")
    print(f"  python {script} {root} --mode classify --dry-run")
    print(f"  python {script} {root} --mode classify")
    print(f"  python {script} {root} --mode clean")


def _print_report(report: dict):
    print(f"\n{'═'*60}")
    print(BOLD("📋 整理分析报告"))
    print(f"{'═'*60}")
    print(f"📌 {report.get('summary', '')}\n")
    for issue in report.get("issues", []):
        print(f"  • {issue}")
    if report.get("issues"):
        print()

    by_action: dict[str, list] = {}
    for a in report.get("actions", []):
        by_action.setdefault(a["action"], []).append(a)

    icons  = {"move": "📦", "delete": "🗑️ ", "rename": "✏️ ", "fix_content": "🔧", "keep": "✅"}
    labels = {"move": "移动", "delete": "删除", "rename": "重命名", "fix_content": "修正内容", "keep": "保留"}
    rfn    = {"low": GREEN, "medium": YELLOW, "high": RED}

    for action, items in by_action.items():
        if action == "keep":
            continue
        print(BOLD(f"{icons.get(action,'?')} {labels.get(action, action)}（{len(items)} 项）"))
        for item in items:
            risk = item.get("risk", "low")
            tag  = rfn.get(risk, CYAN)(f"[{risk}]")
            tgt  = f" -> {item['target']}" if item.get("target") else ""
            print(f"  {tag} {item['path']}{tgt}")
            print(DIM(f"       {item['reason']}"))
        print()

    if report.get("new_dirs"):
        print(BOLD("📁 建议新建目录："))
        for d in report["new_dirs"]:
            print(f"  {d}/")
        print()
    if report.get("notes"):
        print(BOLD("📝 备注："))
        print(f"  {report['notes']}")


def _load_report(report_path: Path) -> dict:
    if not report_path.exists():
        print(RED(f"  [错误] 未找到报告文件: {report_path}"))
        print("  请先运行 scan 模式生成报告")
        sys.exit(1)
    with open(report_path, encoding="utf-8") as f:
        return json.load(f)


def _confirm(prompt: str, default_yes: bool = False) -> bool:
    hint = "[Y/n]" if default_yes else "[y/N]"
    ans = input(f"{prompt} {hint}: ").strip().lower()
    return (ans in ("y", "yes", "是")) if ans else default_yes


def mode_classify(root: Path, report_path: Path, dry_run: bool):
    report = _load_report(report_path)
    report_root = Path(report.get("_root", root))
    actions  = [a for a in report.get("actions", []) if a["action"] in ("move", "rename")]
    new_dirs = report.get("new_dirs", [])
    if not actions:
        print(YELLOW("  没有需要移动/重命名的文件。"))
        return

    print(BOLD(f"\n📦 文件分类{'（预演）' if dry_run else ''}  共 {len(actions)} 项\n"))
    rfn = {"low": GREEN, "medium": YELLOW, "high": RED}

    for d in new_dirs:
        dp = report_root / d
        if not dp.exists():
            print(f"  {'[DRY] ' if dry_run else ''}创建目录: {d}/")
            if not dry_run:
                dp.mkdir(parents=True, exist_ok=True)

    moved = skipped = 0
    for a in actions:
        src = report_root / a["path"]
        dst = report_root / a["target"]
        if not src.exists():
            print(YELLOW(f"  [跳过] 源不存在: {a['path']}"))
            skipped += 1; continue
        if dst.exists():
            print(YELLOW(f"  [跳过] 目标已存在: {a['target']}"))
            skipped += 1; continue
        risk = a.get("risk", "low")
        tag  = rfn.get(risk, CYAN)(f"[{risk}]")
        print(f"  {tag} {a['path']}\n       -> {a['target']}")
        print(DIM(f"       {a['reason']}"))
        if dry_run:
            moved += 1; continue
        if risk == "high" and not _confirm("  ⚠️  高风险，确认执行？"):
            skipped += 1; continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        print(GREEN("       ✓ 完成"))
        moved += 1

    print(f"\n{'─'*40}")
    print(f"  {'预演' if dry_run else '完成'}: 移动 {moved} 项，跳过 {skipped} 项")
    if dry_run:
        print("  去掉 --dry-run 即可实际执行")


def mode_clean(root: Path, report_path: Path):
    report = _load_report(report_path)
    report_root = Path(report.get("_root", root))
    actions = [a for a in report.get("actions", []) if a["action"] == "delete"]
    if not actions:
        print(YELLOW("  没有建议删除的文件。"))
        return

    print(BOLD(f"\n🗑️  待审核删除列表（共 {len(actions)} 项）"))
    print(RED("  ⚠️  每项均需手动输入 y 确认，其他任何输入均跳过"))
    print(f"{'─'*50}\n")

    rfn = {"low": GREEN, "medium": YELLOW, "high": RED}
    deleted = skipped = 0

    for i, a in enumerate(actions, 1):
        path = report_root / a["path"]
        risk = a.get("risk", "low")
        tag  = rfn.get(risk, CYAN)(f"[{risk}]")
        size_str = fmt_size(path.stat().st_size) if path.exists() else "不存在"
        print(f"[{i}/{len(actions)}] {tag} {a['path']} ({size_str})")
        print(f"   理由: {a['reason']}")
        if not path.exists():
            print(DIM("   （文件不存在，跳过）"))
            skipped += 1; print(); continue
        if path.suffix.lower() in {".py", ".md", ".txt", ".json", ".yaml", ".bat", ".sh"}:
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[:8]
                print(DIM("   预览:"))
                for line in lines:
                    print(DIM(f"   | {line[:80]}"))
            except Exception:
                pass
        ans = input("\n   确认删除？[y/N]: ").strip().lower()
        if ans == "y":
            try:
                path.unlink()
                print(GREEN("   ✓ 已删除"))
                deleted += 1
            except Exception as e:
                print(RED(f"   ✗ 失败: {e}"))
                skipped += 1
        else:
            print(DIM("   → 跳过"))
            skipped += 1
        print()

    print(f"{'─'*40}")
    print(f"  完成: 删除 {deleted} 个，跳过 {skipped} 个")


# ══════════════════════════════════════════════
# 5. 主入口
# ══════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="🗂️  智能目录整理助手（LLM 驱动）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        示例:
          python organize.py e:/integrity/13course_digest
          python organize.py e:/integrity/2台词 --mode classify --dry-run
          python organize.py e:/integrity/8评论 --mode classify
          python organize.py e:/integrity/7爬虫 --mode clean
        """),
    )
    parser.add_argument("target", help="要整理的目录路径（相对或绝对）")
    parser.add_argument(
        "--mode", choices=["scan", "classify", "clean"],
        default="scan", help="运行模式（默认: scan）",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="classify 模式下仅预演，不实际执行",
    )
    parser.add_argument(
        "--api-key", default="",
        help="LLM API Key（最高优先级）",
    )
    parser.add_argument(
        "--report", default="",
        help=f"报告文件路径（默认: <目标目录>/{REPORT_FILE}）",
    )
    args = parser.parse_args()

    root = Path(args.target).resolve()
    if not root.exists() or not root.is_dir():
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
