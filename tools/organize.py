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


# 绝对不允许移动的扩展名（代码 / 配置 / 项目定义文件）
# 无论 LLM 建议什么，这些文件在执行层强制跳过
PROTECTED_EXTS = {
    # 代码
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
    ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".sh", ".bat", ".ps1",
    # 配置 / 项目文件
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env",
    ".json",   # 包含 settings.json、package.json 等
    # Web 结构
    ".html", ".htm", ".css",
    # 项目元数据
    ".gitignore", ".gitattributes", ".editorconfig",
    # 文档（README 类通常与代码同级，移走会断链）
    ".md", ".rst",
}

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

        # ── 硬拦截：代码/配置文件无论 LLM 说什么都不动 ──────────────
        if src.suffix.lower() in PROTECTED_EXTS or src.name.startswith("."):
            print(RED(f"  [🛡️ 拦截] {a['path']}"))
            print(DIM(f"       扩展名 {src.suffix!r} 在保护名单中，跳过（LLM 建议已被忽略）"))
            blocked += 1; continue
        # ────────────────────────────────────────────────────────────

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
        print(RED(f"  🛡️ 拦截: {blocked} 项（代码/配置文件，已保护）"))
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
# 6. Agent 模式（ReAct 循环）
# ══════════════════════════════════════════════

AGENT_SYSTEM = textwrap.dedent("""
你是一个仔细、保守的文件夹整理 Agent。你可以使用工具反复研究目录中的文件，
充分了解后再给出整理建议。你的工作流程是：

1. 先用 list_dir 全面了解目录结构
2. 对可疑文件用 read_file 阅读内容，判断它是临时产物还是有用文件
3. 研究充分后，用 propose_move / propose_delete 提交建议
4. 最后调用 finish 结束，给出总结

【安全规则（强制）】
- 绝对不要对 .py .js .html .bat .sh .yaml .yaml .json .md 等代码/配置文件提出 move 或 delete
- 只整理：视频音频(.mp4 .mov .wav .mp3)、图片(.png .jpg)、PDF讲义、UUID临时文件、明显冗余的副本
- 不确定的文件宁可不动

每次只输出一个 JSON 动作，格式如下：
{"thought": "当前思考", "action": "工具名", "args": {参数}}

可用工具：
- list_dir: {"path": "相对路径或."}
- read_file: {"path": "文件相对路径", "lines": 30}
- propose_move: {"src": "原路径", "dst": "目标路径", "reason": "理由"}
- propose_delete: {"path": "路径", "reason": "理由"}
- finish: {"summary": "整理总结"}
""").strip()

MAX_AGENT_STEPS = 30   # 最多循环次数，防止无限运转
MAX_READ_BYTES  = 8000 # read_file 最多读取字节数


def _agent_list_dir(root: Path, rel: str) -> str:
    target = (root / rel).resolve()
    # 安全：不允许跑到 root 外面
    try:
        target.relative_to(root)
    except ValueError:
        return "[错误] 路径超出目标目录范围"
    if not target.exists():
        return f"[错误] 路径不存在: {rel}"
    if not target.is_dir():
        return f"[错误] 不是目录: {rel}"
    lines = []
    for entry in sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name)):
        if entry.name in SKIP_DIRS:
            continue
        tag = "[DIR] " if entry.is_dir() else f"[{fmt_size(entry.stat().st_size):>8}]"
        lines.append(f"  {tag} {entry.name}")
    return "\n".join(lines) if lines else "(空目录)"


def _agent_read_file(root: Path, rel: str, lines: int = 30) -> str:
    target = (root / rel).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return "[错误] 路径超出目标目录范围"
    if not target.exists():
        return f"[错误] 文件不存在: {rel}"
    if target.is_dir():
        return f"[错误] 这是目录，请用 list_dir: {rel}"
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
        head = "\n".join(text.splitlines()[:lines])
        if len(text.splitlines()) > lines:
            head += f"\n... ({len(text.splitlines()) - lines} more lines)"
        return head[:MAX_READ_BYTES]
    except Exception as e:
        return f"[读取失败] {e}"


def _agent_execute_tool(root: Path, action: str, args: dict,
                        proposals: list) -> str:
    """执行 Agent 工具调用，纯探索工具立即执行，变更类工具加入队列。"""
    if action == "list_dir":
        return _agent_list_dir(root, args.get("path", "."))

    elif action == "read_file":
        return _agent_read_file(root, args.get("path", ""),
                                int(args.get("lines", 30)))

    elif action == "propose_move":
        src = args.get("src", "")
        dst = args.get("dst", "")
        reason = args.get("reason", "")
        proposals.append({"action": "move", "src": src, "dst": dst, "reason": reason})
        return f"[已记录] 将来移动: {src} -> {dst}"

    elif action == "propose_delete":
        path = args.get("path", "")
        reason = args.get("reason", "")
        proposals.append({"action": "delete", "path": path, "reason": reason})
        return f"[已记录] 将来删除: {path}"

    elif action == "finish":
        return "__FINISH__"  # 特殊信号

    else:
        return f"[错误] 未知工具: {action}"


def mode_agent(root: Path, api_cfg: dict, dry_run: bool):
    """ReAct Agent 循环：LLM 反复研究文件夹后提出建议，最终人工审核。"""
    print(BOLD(f"\n🤖 Agent 模式启动: {root}"))
    print(DIM(f"   最多 {MAX_AGENT_STEPS} 步，大模型将自主探索后给出建议\n"))

    messages = [
        {"role": "system", "content": AGENT_SYSTEM},
        {"role": "user",   "content":
            f"请开始整理以下目录，先做充分调研再给出建议：\n目标目录根: {root}\n\n"
            f"首先用 list_dir 看一下根目录内容。"},
    ]

    proposals: list[dict] = []
    finished = False

    try:
        from openai import OpenAI
    except ImportError:
        print(RED("  [LLM] 未安装 openai 包：pip install openai"))
        sys.exit(1)
    if not api_cfg["api_key"]:
        print(RED("  [错误] 未找到 API Key"))
        sys.exit(1)
    client = OpenAI(api_key=api_cfg["api_key"], base_url=api_cfg["base_url"])

    for step in range(1, MAX_AGENT_STEPS + 1):
        print(CYAN(f"── Step {step}/{MAX_AGENT_STEPS} "), end="", flush=True)

        # 调用 LLM
        response = client.chat.completions.create(
            model=api_cfg["model"],
            messages=messages,
            temperature=0.1,
            max_tokens=1024,
        )
        raw = response.choices[0].message.content.strip()
        messages.append({"role": "assistant", "content": raw})

        # 解析 JSON 动作
        try:
            obj = _extract_json(raw)
            thought = obj.get("thought", "")
            action  = obj.get("action", "")
            args    = obj.get("args", {})
        except Exception:
            print(RED(f"[解析失败] 原始输出: {raw[:200]}"))
            tool_result = "[错误] 请输出合法 JSON 格式的动作"
            messages.append({"role": "user", "content": f"工具结果: {tool_result}"})
            continue

        # 打印思考过程
        print(BOLD(action))
        if thought:
            print(DIM(f"   💭 {thought[:120]}"))
        print(DIM(f"   🔧 {action}({json.dumps(args, ensure_ascii=False)})"))

        # 执行工具
        tool_result = _agent_execute_tool(root, action, args, proposals)

        if tool_result == "__FINISH__":
            summary = args.get("summary", "Agent 完成探索")
            print(GREEN(f"\n✅ Agent 完成: {summary}"))
            finished = True
            break

        # 打印工具结果摘要
        result_preview = tool_result[:300].replace("\n", "\n   ")
        print(DIM(f"   📋 结果:\n   {result_preview}"))

        messages.append({"role": "user", "content": f"工具结果:\n{tool_result}"})

    if not finished:
        print(YELLOW(f"\n⚠️  已达到最大步数 {MAX_AGENT_STEPS}，强制结束"))

    # ── 审核建议 ────────────────────────────────
    if not proposals:
        print(YELLOW("\n  Agent 没有提出任何整理建议。"))
        return

    print(f"\n{'═'*60}")
    print(BOLD(f"📋 Agent 建议汇总（共 {len(proposals)} 项）"))
    print(f"{'═'*60}")
    for i, p in enumerate(proposals, 1):
        if p["action"] == "move":
            print(f"  [{i}] 📦 移动  {p['src']} -> {p['dst']}")
        else:
            print(f"  [{i}] 🗑️  删除  {p['path']}")
        print(DIM(f"       理由: {p['reason']}"))
    print()

    if dry_run:
        print(YELLOW("  [预演模式] 以上是 Agent 的建议，去掉 --dry-run 才会逐项确认执行"))
        return

    print(RED("  ⚠️  以下每项操作均需你手动输入 y 确认，其余跳过\n"))
    done_count = skip_count = 0

    for p in proposals:
        if p["action"] == "move":
            src = root / p["src"]
            dst = root / p["dst"]

            # 硬拦截保护扩展名
            if src.suffix.lower() in PROTECTED_EXTS or src.name.startswith("."):
                print(RED(f"  [🛡️ 拦截] {p['src']} — 受保护文件类型，跳过"))
                skip_count += 1; continue

            print(f"  📦 移动: {p['src']}")
            print(f"       -> {p['dst']}")
            print(DIM(f"       {p['reason']}"))
            if not src.exists():
                print(DIM("       (源文件不存在，跳过)")); skip_count += 1; print(); continue
            ans = input("     确认？[y/N]: ").strip().lower()
            if ans == "y":
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                print(GREEN("     ✓ 完成"))
                done_count += 1
            else:
                print(DIM("     → 跳过")); skip_count += 1

        elif p["action"] == "delete":
            path = root / p["path"]
            if path.suffix.lower() in PROTECTED_EXTS or path.name.startswith("."):
                print(RED(f"  [🛡️ 拦截] {p['path']} — 受保护文件类型，跳过"))
                skip_count += 1; continue

            size_str = fmt_size(path.stat().st_size) if path.exists() else "不存在"
            print(f"  🗑️  删除: {p['path']} ({size_str})")
            print(DIM(f"       {p['reason']}"))
            if not path.exists():
                print(DIM("       (文件不存在，跳过)")); skip_count += 1; print(); continue
            # 预览
            if path.suffix.lower() in {".txt", ".log"}:
                try:
                    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[:5]
                    for ln in lines: print(DIM(f"       | {ln[:80]}"))
                except Exception: pass
            ans = input("     确认删除？[y/N]: ").strip().lower()
            if ans == "y":
                path.unlink()
                print(GREEN("     ✓ 已删除"))
                done_count += 1
            else:
                print(DIM("     → 跳过")); skip_count += 1
        print()

    print(f"{'─'*40}")
    print(f"  完成: 执行 {done_count} 项，跳过 {skip_count} 项")


# ══════════════════════════════════════════════
# 7. 主入口
# ══════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="🗂️  智能目录整理助手（LLM 驱动）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        模式说明:
          scan     一次性扫描 + LLM 分析，生成 organize_report.json
          classify 按报告执行文件移动（需先 scan）
          clean    审核建议删除的文件（需先 scan）
          agent    LLM 自主探索循环，充分研究后再建议（推荐）

        示例:
          python organize.py e:/integrity/13course_digest --mode agent
          python organize.py e:/integrity/2台词 --mode agent --dry-run
          python organize.py e:/integrity/8评论 --mode scan
        """),
    )
    parser.add_argument("target", help="要整理的目录路径")
    parser.add_argument(
        "--mode", choices=["scan", "classify", "clean", "agent"],
        default="agent", help="运行模式（默认: agent）",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="仅预演，不实际执行任何文件操作")
    parser.add_argument("--api-key", default="", help="LLM API Key（最高优先级）")
    parser.add_argument("--report", default="",
                        help=f"报告路径（scan/classify/clean 模式用，默认: <dir>/{REPORT_FILE}）")
    args = parser.parse_args()

    root = Path(args.target).resolve()
    if not root.exists() or not root.is_dir():
        print(RED(f"  [错误] 目录不存在: {root}"))
        sys.exit(1)

    report_path = Path(args.report) if args.report else root / REPORT_FILE
    api_cfg = _load_api_config(root, args.api_key)

    if args.mode == "scan":
        mode_scan(root, api_cfg, report_path)
    elif args.mode == "classify":
        mode_classify(root, report_path, args.dry_run)
    elif args.mode == "clean":
        mode_clean(root, report_path)
    elif args.mode == "agent":
        mode_agent(root, api_cfg, args.dry_run)


if __name__ == "__main__":
    main()
