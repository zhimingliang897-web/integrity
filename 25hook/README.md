# 25hook — Claude Code Hooks 快速迁移

本目录存放 Claude Code 的 hooks 配置与示例，便于在新项目中复用。

## 目录结构

```
25hook/
├── README.md           # 本说明
└── hooks/
    └── posttool_example.py   # PostToolUse 示例：工具调用后写审计日志并回传摘要
```

## 使用方式

1. **放置到项目根目录**
   - 将本仓库中的 `hooks/` 复制到你的项目下，或把 `posttool_example.py` 放到项目的 `.claude/hooks/` 中。
   - 确保 `.claude` 在项目根目录，Claude 会以项目根为工作目录执行 hook。

2. **路径与跨平台**
   - `settings.json` 里使用**相对项目根**的路径，一律用正斜杠 `/`。
   - 示例：`python3 .claude/hooks/posttool_example.py`（Windows/macOS/Linux 通用）。

3. **一次性准备**
   ```bash
   chmod +x .claude/hooks/posttool_example.py
   ```

4. **settings.json 示例**
   ```json
   {
     "hooks": {
       "PostToolUse": [
         {
           "matcher": "*",
           "hooks": [
             {
               "type": "command",
               "command": "python3 .claude/hooks/posttool_example.py"
             }
           ]
         }
       ],
       "PostToolUseFailure": [
         {
           "matcher": "*",
           "hooks": [
             {
               "type": "command",
               "command": "python3 .claude/hooks/posttool_example.py"
             }
           ]
         }
       ]
     }
   }
   ```

5. **运行**
   - 在项目根执行 `claude`，hook 会在项目根生成 `hook_audit.log`。

## 说明

- 本仓库仅提交示例脚本与说明；本地完整配置（如 `.claude(2)/`）由 `.gitignore` 排除，不提交。
