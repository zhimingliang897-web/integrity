"""modes.py — scan / classify / clean 三种传统模式"""
import json
import shutil
import sys
import textwrap
from pathlib import Path

from .utils import (
    REPORT_FILE, PROTECTED_EXTS,
    RED, GREEN, YELLOW, CYAN, BOLD, DIM, fmt_size,
)
from .llm import call_llm, extract_json
from .scanner import scan_directory, build_user_prompt


# ── Prompt ───────────────────────────────────────────────
def _system_prompt() -> str:
    return textwrap.dedent("""
    你是一个保守且安全的项目资产文件整理助手。主要整理【数据资产】和【临时副产物】，绝对不要打乱代码和配置。

    【安全原则】
    项目中已预定义很多路径依赖。所有 *.py .js .html .bat .sh .yaml .json .ini 等代码/配置文件，
    无论看起来像什么，一律 action=keep。

    整理范围：
    1. 原始输入素材（视频 .mp4、音频、PDF讲义、图片）→ 移至 input/ 或 media/
    2. 缓存/中间数据（大模型分析 JSON、转录残留）→ 移至 cache/ 或 temp/
    3. 最终输出文档（学习指南 .md、报告 .docx）→ 移至 output/ 或 docs/
    4. UUID 临时文件、空文件 → delete，risk=low
    5. 拼写错误且有替代品的文件 → delete，risk=low
    6. 其他不确定的 → keep

    严格输出 JSON，不要有多余文字：
    {
      "summary": "一句话总结",
      "issues": ["混乱点1"],
      "actions": [
        {
          "action": "move" | "delete" | "rename" | "keep",
          "path": "相对路径",
          "target": "目标路径（delete/keep 时为 null）",
          "reason": "理由",
          "risk": "low" | "medium" | "high",
          "category": "input" | "output" | "cache" | "temp" | "core" | "config" | "doc"
        }
      ],
      "new_dirs": ["建议新建的目录"],
      "notes": "备注"
    }
    """).strip()


# ── 辅助函数 ─────────────────────────────────────────────
def _load_report(report_path: Path) -> dict:
    if not report_path.exists():
        print(RED(f"  [错误] 报告文件不存在: {report_path}"))
        print("  请先运行 scan 模式")
        sys.exit(1)
    with open(report_path, encoding="utf-8") as f:
        return json.load(f)


def _confirm(prompt: str, default_yes: bool = False) -> bool:
    hint = "[Y/n]" if default_yes else "[y/N]"
    ans = input(f"{prompt} {hint}: ").strip().lower()
    return (ans in ("y", "yes", "是")) if ans else default_yes


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


# ── 三种模式主函数 ────────────────────────────────────────
def mode_scan(root: Path, api_cfg: dict, report_path: Path):
    print(BOLD(f"\n🔍 扫描目录: {root}"))
    files = scan_directory(root)
    print(f"   发现 {len(files)} 个文件\n")
    print(CYAN("📡 调用 LLM 分析中，请稍候..."))

    raw = call_llm(api_cfg, [
        {"role": "system", "content": _system_prompt()},
        {"role": "user",   "content": build_user_prompt(root, files)},
    ])

    try:
        report = extract_json(raw)
    except Exception:
        print(RED("  [错误] LLM 返回内容无法解析为 JSON："))
        print(DIM(raw[:1000]))
        sys.exit(1)

    report["_root"] = str(root)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    _print_report(report)
    print(f"\n💾 报告已保存: {report_path}")
    print(f"\n下一步:")
    print(f"  python organize.py {root} --mode classify --dry-run")
    print(f"  python organize.py {root} --mode clean")


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

    moved = skipped = blocked = 0
    for a in actions:
        src = report_root / a["path"]
        dst = report_root / a["target"]

        # 硬拦截：代码/配置文件无论 LLM 说什么都不动
        if src.suffix.lower() in PROTECTED_EXTS or src.name.startswith("."):
            print(RED(f"  [🛡️ 拦截] {a['path']}"))
            print(DIM(f"       扩展名 {src.suffix!r} 受保护，已忽略 LLM 建议"))
            blocked += 1; continue

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
    if blocked:
        print(RED(f"  🛡️ 拦截: {blocked} 项（受保护文件）"))
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

        if path.suffix.lower() in {".txt", ".log", ".csv"}:
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[:6]
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
