#!/usr/bin/env python3
import json
import sys
import datetime

# 强制使用 UTF-8 编码，确保 Emoji 在 Mac 终端完美显示
if sys.stdout.encoding != 'UTF-8':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass

def main():
    # 1. 从 stdin 读取 Claude 传入的工具执行数据
    raw = sys.stdin.read()
    log_file = "hook_audit.log"
    
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now()}] ⚠️ 无法解析传入的 JSON 数据\n\n")
        sys.exit(0)

    # 2. 提取核心字段
    tool_name = data.get("tool_name", "Unknown")
    tool_response = data.get("tool_response", {})
    
    # 动态判断事件名称 (重要：决定了反馈是否能成功挂载)
    is_error = bool(tool_response.get("error")) or (tool_response.get("exit_code", 0) != 0)
    event_name = "PostToolUseFailure" if is_error else "PostToolUse"
    status_text = "失败 ❌" if is_error else "成功 ✅"

    # 3. 提取输出摘要
    raw_output = tool_response.get("stdout") or tool_response.get("output") or tool_response.get("error") or ""
    output_preview = "无输出内容"
    if isinstance(raw_output, str) and raw_output.strip():
        preview = raw_output.strip().replace("\n", " ")[:150]
        output_preview = f"{preview}..." if len(raw_output.strip()) > 150 else preview

    # 4. 写入本地“黑匣子”日志 (Audit Log)
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now()}] {status_text} | 工具: {tool_name}\n")
            f.write(f" ▸ 摘要: {output_preview}\n")
            f.write("-" * 60 + "\n")
    except Exception:
        pass 

    # 5. 构造具有视觉冲击力的 UI 反馈 (additionalContext)
    # 我们使用特殊的 ASCII 边框和 Markdown 引用，让 Hook 的存在感拉满
    visual_report = (
        f"\n> ### 🔍 审计 Hook 自动播报\n"
        f"> ┌──────────────────────────────────────────────────┐\n"
        f">   **执行工具**：`{tool_name}`\n"
        f">   **执行状态**：{status_text}\n"
        f">   **输出预览**：{output_preview}\n"
        f"> └──────────────────────────────────────────────────┘\n\n"
        f"请你在回复的最开头展示上述审计框，并用一句话简评结果。"
    )

    # 6. 标准 JSON 输出返回给 Claude Code
    response_data = {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": visual_report
        }
    }
    
    sys.stdout.write(json.dumps(response_data, ensure_ascii=False))
    sys.stdout.flush()

if __name__ == "__main__":
    main()
