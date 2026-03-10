"""agent.py — ReAct Agent 循环模式"""
import json
import shutil
import textwrap
import sys
from pathlib import Path

from .utils import SKIP_DIRS, PROTECTED_EXTS, RED, GREEN, YELLOW, CYAN, BOLD, DIM, fmt_size
from .llm import extract_json

MAX_STEPS    = 30     # 最多循环次数
MAX_READ_BYTES = 8000  # read_file 单次最多读取字节


AGENT_SYSTEM = textwrap.dedent("""
你是一个仔细、保守的文件夹整理 Agent，可以用工具反复研究目录后再给出整理建议。

工作流程：
1. list_dir — 了解目录结构
2. read_file — 阅读可疑文件内容，判断是临时产物还是有用文件
3. propose_move / propose_delete — 提交建议（不立即执行）
4. finish — 结束探索，给出总结

【安全规则（强制）】
绝对不要对 .py .js .html .bat .sh .yaml .json .md 等代码/配置文件提出 move 或 delete。
只整理：视频音频 .mp4 .mov .wav .mp3、图片 .png .jpg、PDF讲义、UUID临时文件、明显冗余副本。
不确定的宁可不动。

每次只输出一个 JSON 动作：
{"thought": "当前思考", "action": "工具名", "args": {参数}}

可用工具：
- list_dir:      {"path": "相对路径或."}
- read_file:     {"path": "文件相对路径", "lines": 30}
- propose_move:  {"src": "原路径", "dst": "目标路径", "reason": "理由"}
- propose_delete:{"path": "路径", "reason": "理由"}
- finish:        {"summary": "整理总结"}
""").strip()


# ── 工具实现 ──────────────────────────────────────────────

def _list_dir(root: Path, rel: str) -> str:
    target = (root / rel).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return "[错误] 路径超出目标目录范围"
    if not target.exists():
        return f"[错误] 路径不存在: {rel}"
    if not target.is_dir():
        return f"[错误] 不是目录，请使用 read_file: {rel}"
    lines = []
    for entry in sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name)):
        if entry.name in SKIP_DIRS:
            continue
        tag = "[DIR] " if entry.is_dir() else f"[{fmt_size(entry.stat().st_size):>8}]"
        lines.append(f"  {tag} {entry.name}")
    return "\n".join(lines) if lines else "(空目录)"


def _read_file(root: Path, rel: str, n_lines: int = 30) -> str:
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
        all_lines = text.splitlines()
        head = "\n".join(all_lines[:n_lines])
        if len(all_lines) > n_lines:
            head += f"\n... ({len(all_lines) - n_lines} more lines)"
        return head[:MAX_READ_BYTES]
    except Exception as e:
        return f"[读取失败] {e}"


def _execute(root: Path, action: str, args: dict, proposals: list) -> str:
    """执行单步工具调用。探索类立即返回，变更类只入队列。"""
    if action == "list_dir":
        return _list_dir(root, args.get("path", "."))
    if action == "read_file":
        return _read_file(root, args.get("path", ""), int(args.get("lines", 30)))
    if action == "propose_move":
        proposals.append({"action": "move",
                           "src": args.get("src", ""),
                           "dst": args.get("dst", ""),
                           "reason": args.get("reason", "")})
        return f"[已记录] 将来移动: {args.get('src')} -> {args.get('dst')}"
    if action == "propose_delete":
        proposals.append({"action": "delete",
                           "path": args.get("path", ""),
                           "reason": args.get("reason", "")})
        return f"[已记录] 将来删除: {args.get('path')}"
    if action == "finish":
        return "__FINISH__"
    return f"[错误] 未知工具: {action}"


# ── 审核建议并执行 ────────────────────────────────────────

def _review_proposals(root: Path, proposals: list, dry_run: bool):
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
        print(YELLOW("  [预演模式] 去掉 --dry-run 才会逐项确认执行"))
        return

    print(RED("  ⚠️  以下每项均需手动输入 y 确认，其余跳过\n"))
    done = skip = 0

    for p in proposals:
        if p["action"] == "move":
            src = root / p["src"]
            dst = root / p["dst"]
            if src.suffix.lower() in PROTECTED_EXTS or src.name.startswith("."):
                print(RED(f"  [🛡️ 拦截] {p['src']} — 受保护文件类型"))
                skip += 1; continue
            print(f"  📦 {p['src']}\n       -> {p['dst']}")
            print(DIM(f"       {p['reason']}"))
            if not src.exists():
                print(DIM("       (源不存在，跳过)")); skip += 1; print(); continue
            if input("     确认？[y/N]: ").strip().lower() == "y":
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                print(GREEN("     ✓ 完成")); done += 1
            else:
                print(DIM("     → 跳过")); skip += 1

        elif p["action"] == "delete":
            path = root / p["path"]
            if path.suffix.lower() in PROTECTED_EXTS or path.name.startswith("."):
                print(RED(f"  [🛡️ 拦截] {p['path']} — 受保护文件类型"))
                skip += 1; continue
            size_str = fmt_size(path.stat().st_size) if path.exists() else "不存在"
            print(f"  🗑️  {p['path']} ({size_str})")
            print(DIM(f"       {p['reason']}"))
            if not path.exists():
                print(DIM("       (文件不存在，跳过)")); skip += 1; print(); continue
            if input("     确认删除？[y/N]: ").strip().lower() == "y":
                path.unlink()
                print(GREEN("     ✓ 已删除")); done += 1
            else:
                print(DIM("     → 跳过")); skip += 1
        print()

    print(f"{'─'*40}")
    print(f"  完成: 执行 {done} 项，跳过 {skip} 项")


# ── 主入口 ────────────────────────────────────────────────

def mode_agent(root: Path, api_cfg: dict, dry_run: bool):
    """ReAct Agent 循环：LLM 反复研究文件夹，提出建议后人工审核。"""
    print(BOLD(f"\n🤖 Agent 模式: {root}"))
    print(DIM(f"   最多 {MAX_STEPS} 步，大模型将自主探索后给出建议\n"))

    try:
        from openai import OpenAI
    except ImportError:
        print(RED("  pip install openai")); sys.exit(1)
    if not api_cfg["api_key"]:
        print(RED("  [错误] 未找到 API Key")); sys.exit(1)

    client = OpenAI(api_key=api_cfg["api_key"], base_url=api_cfg["base_url"])
    messages = [
        {"role": "system", "content": AGENT_SYSTEM},
        {"role": "user",   "content":
            f"请整理目录（根: {root}）。先用 list_dir 看一下根目录内容。"},
    ]

    proposals: list[dict] = []
    finished = False

    for step in range(1, MAX_STEPS + 1):
        print(CYAN(f"── Step {step}/{MAX_STEPS} "), end="", flush=True)

        resp = client.chat.completions.create(
            model=api_cfg["model"],
            messages=messages,
            temperature=0.1,
            max_tokens=1024,
        )
        raw = resp.choices[0].message.content.strip()
        messages.append({"role": "assistant", "content": raw})

        try:
            obj     = extract_json(raw)
            thought = obj.get("thought", "")
            action  = obj.get("action", "")
            args    = obj.get("args", {})
        except Exception:
            print(RED(f"[JSON解析失败] {raw[:120]}"))
            messages.append({"role": "user", "content": "[错误] 请输出合法 JSON 格式的动作"})
            continue

        print(BOLD(action))
        if thought:
            print(DIM(f"   💭 {thought[:120]}"))
        print(DIM(f"   🔧 {action}({json.dumps(args, ensure_ascii=False)})"))

        result = _execute(root, action, args, proposals)
        if result == "__FINISH__":
            print(GREEN(f"\n✅ {args.get('summary', 'Agent 完成')}"))
            finished = True
            break

        preview = result[:300].replace("\n", "\n   ")
        print(DIM(f"   📋 结果:\n   {preview}"))
        messages.append({"role": "user", "content": f"工具结果:\n{result}"})

    if not finished:
        print(YELLOW(f"\n⚠️  已达到最大步数 {MAX_STEPS}，强制结束"))

    _review_proposals(root, proposals, dry_run)
