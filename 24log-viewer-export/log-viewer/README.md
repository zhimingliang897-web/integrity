# Claude CLI 日志查看器

在本地查看、复盘 Claude Code 的对话与工具调用日志。支持 **Node**（`server.js`）与 **Python**（`server.py`）两种后端，**行为与 API 一致**，任选其一启动即可。

---

## 1. 功能一览

- **顶部**：选择**项目** → 选择该项目下的**会话**
- **左侧时间线**：按事件类型、工具名、关键词筛选；支持键盘上下键切换选中
- **右侧详情**：规则摘要、模型解说（需配置 API）、对当前事件提问、原始 JSON（可折叠）
- **健康信息**：事件总数、pre/post/失败数、去重与缺失 post 统计

---

## 2. 快速启动

**二选一**执行：

```powershell
cd $env:USERPROFILE\.claude\log-viewer
node server.js
```

或：

```powershell
python server.py
```

浏览器打开终端打印的地址（默认 `http://127.0.0.1:3847`）。端口被占用时两后端都会自动尝试后续端口并提示实际端口。

---

## 3. 配置说明（双后端统一）

### 3.1 数据目录

| 项 | 默认值 | 环境变量 |
|----|--------|----------|
| 项目/会话数据源 | `%USERPROFILE%\.claude\projects` | `CLAUDE_PROJECTS_DIR` |

扫描该目录下所有 `.jsonl`（自动跳过路径中含 `subagents` 的文件）。两后端行为相同。

### 3.2 端口

| 项 | 默认值 | 环境变量 |
|----|--------|----------|
| 监听端口 | 3847 | `CLAUDE_LOG_VIEWER_PORT` |

端口占用时自动尝试 +1、+2…（约 20 次）。

### 3.3 解说 API（模型解说 / 提问）

用于「生成解说」和「提问」功能。可在页面右上角**设置**中填写，或直接编辑 `log-viewer/explain-config.json`：

```json
{
  "apiUrl": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
  "apiKey": "你的 API Key",
  "model": "qwen-turbo"
}
```

- `apiUrl` 可只填基础地址（如 `https://.../v1`），服务会自动补全 `/chat/completions`。
- 环境变量（优先于文件）：`EXPLAIN_API_URL`、`EXPLAIN_API_KEY`、`EXPLAIN_MODEL`。

### 3.4 项目显示名（可选）

在 log-viewer 目录下放置 `projects-display-names.json`，可为项目 ID 指定展示名称，**Node 与 Python 均支持**：

```json
{
  "e--integrity": "Integrity 项目",
  "E--Ip": "IP 相关"
}
```

API 返回的 `name` / `projectName` 会优先使用该映射。

---

## 4. API 列表（双后端一致）

以下接口 **Node 与 Python 行为一致**，前端无需区分后端。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/projects` | 项目列表（含会话数、事件数、最后活动时间） |
| GET | `/api/projects/:projectId/sessions` | 指定项目下的会话列表 |
| GET | `/api/timelines/:sessionId/events` | 会话事件流，支持 `limit`、`offset`、`eventType`、`toolName`、`q`（关键词） |
| GET | `/api/timelines/:sessionId/health` | 会话健康统计 |
| GET/POST | `/api/explain-config` | 读写解说 API 配置 |
| POST | `/api/explain` | 对单条事件生成解说 |
| POST | `/api/question` | 对单条事件提问（请求体：`question`、`logJson`） |

**仅 Node 额外支持**（与旧版 tool-logs 兼容）：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/sessions` | 从 `~/.claude/tool-logs` 列出的 .txt 会话（环境变量 `CLAUDE_TOOL_LOG_DIR`） |
| GET | `/api/sessions/:id/log` | 某会话的原始日志内容 |

---

## 5. 事件模型（统一 schema）

后端统一输出字段：`schemaVersion`、`eventId`、`sessionId`、`projectId`、`traceId`、`source`、`eventType`、`toolName`、`toolInput`、`toolOutput`、`error`、`content`、`timestamp`、`cwd`、`raw`。  
`eventType` 取值：`user_input`、`assistant_output`、`pre_tool`、`post_tool`、`tool_failure`、`system`。

---

## 6. 数据质量与缓存

- 事件去重、按 `traceId` 的 pre/post 对账、缺失 post 统计（`missingPostCount`、`missingPostTraceIds`）
- 文件签名缓存（约 2 秒 TTL）减少重复全量解析

建议自测：在某一 project 下跑一次对话并触发工具调用，在 UI 中确认时间线与健康统计是否符合预期。

---

## 7. 安全建议

- `explain-config.json` 可能含 API Key，勿提交到公开仓库（已加入 `.gitignore`）
- 本工具面向本机复盘，避免将含隐私/凭据的日志外传；共享前请脱敏（路径、用户名、密钥、业务数据）
