# 🗂️ organize — 智能文件夹整理助手

> 基于 LLM 的项目目录整理工具。支持 Agent 自主探索循环，充分研究文件内容后再给出建议。  
> **代码和配置文件受到双重保护，绝对不会被误移动。**

---

## 目录结构

```
tools/
├── organize.py           # 入口脚本（~60 行）
├── organize_config.yaml  # 全局 API 配置
├── README.md
└── lib/                  # 功能模块
    ├── utils.py          # 常量、颜色输出、保护扩展名
    ├── llm.py            # API 配置加载、LLM 调用
    ├── scanner.py        # 目录扫描、文件内容预览
    ├── modes.py          # scan / classify / clean 模式
    └── agent.py          # ReAct Agent 循环模式
```

---

## 快速开始

```bash
# Agent 模式（默认）：大模型自主探索后给出建议
python e:\integrity\tools\organize.py e:\integrity\13course_digest

# 先预演，看看会做什么，不动任何文件
python e:\integrity\tools\organize.py e:\integrity\1分镜\video_maker --dry-run
```

---

## 四种模式

| 模式 | 参数 | 说明 |
|------|------|------|
| **agent** | `--mode agent` | 🌟 **默认**。LLM 循环探索，读文件内容后再提建议，最后统一人工确认 |
| **scan** | `--mode scan` | 一次性扫描，生成 `organize_report.json` |
| **classify** | `--mode classify` | 按 scan 报告执行移动（需先 scan）|
| **clean** | `--mode clean` | 按 scan 报告逐一审核删除（需先 scan）|

### 典型工作流

```bash
# 方式一：直接 Agent（推荐）
python organize.py <目录>
python organize.py <目录> --dry-run   # 预演

# 方式二：两步流程（scan → classify/clean）
python organize.py <目录> --mode scan
python organize.py <目录> --mode classify --dry-run
python organize.py <目录> --mode classify
python organize.py <目录> --mode clean
```

---

## 完整参数

```
positional:
  target              要整理的目录路径（相对或绝对）

options:
  --mode              agent | scan | classify | clean（默认: agent）
  --dry-run           仅预演，不执行任何文件操作
  --api-key KEY       临时指定 API Key（优先级最高）
  --report PATH       scan 报告文件路径（默认: <目标目录>/organize_report.json）
```

---

## API 配置

编辑 `organize_config.yaml`（填一次，所有目录均生效）：

```yaml
api:
  provider: "dashscope"        # dashscope / openai / groq
  api_key: "sk-你的key"
  model: "qwen-plus-2025-12-01"
```

**配置读取优先级（低 → 高）：**

```
organize_config.yaml（本目录）
  → <目标目录>/config.yaml（项目自带配置）
    → 环境变量 DASHSCOPE_API_KEY / OPENAI_API_KEY
      → --api-key 参数
```

---

## 🛡️ 安全机制

两道独立的防线，缺一不可：

**第一道：Prompt 层** — 系统提示明确告知大模型不要碰代码和配置文件

**第二道：代码层（强制）** — 无论 LLM 建议什么，执行时一旦检测到受保护扩展名，立即拦截并打印 `🛡️ 拦截`，绝不静默跳过

**受保护的文件类型（代码层强制，无法绕过）：**

| 类别 | 扩展名 |
|------|--------|
| 代码 | `.py .js .ts .html .bat .sh .go .java` 等 |
| 配置 | `.yaml .yml .json .toml .ini .cfg .env` |
| 文档 | `.md .rst`（通常与代码同级，移走会断链） |
| 隐藏 | 所有 `.` 开头的文件 |

**只能整理：** `.mp4 .mov .wav .mp3 .png .jpg .gif .pdf` 等纯资产，以及明确的临时垃圾文件。

---

## 🤖 Agent 工作原理

Agent 采用 **ReAct 循环**（Reasoning + Acting），完全手写，不依赖任何 Agent 框架：

```
while step < 30:
    LLM(对话历史) → {"thought": "...", "action": "工具名", "args": {...}}
    执行工具 → 返回结果
    结果追加到对话历史（LLM 下一步能看到）
    if action == "finish": break

↓ 汇总所有 propose 建议
↓ 逐项展示给用户 → 输入 y 才执行
```

**五个工具：**

| 工具 | 类型 | 作用 |
|------|------|------|
| `list_dir` | 探索 | 列出目录内容（立即执行，结果返回给 LLM）|
| `read_file` | 探索 | 读取文件内容（立即执行）|
| `propose_move` | 变更 | 提出移动建议（入队列，不立即执行）|
| `propose_delete` | 变更 | 提出删除建议（入队列，不立即执行）|
| `finish` | 终止 | 结束探索，触发建议汇总 |

探索类工具立即执行让大模型获取真实信息；变更类工具只入队列，保证所有文件操作都经过人工确认。
