# 📚 What We Learn - 技术实现与心得

本文档记录了 **AI 每日热点情报 Agent** 项目的核心技术实现和开发过程中的关键经验。

---

## 💡 核心技术特性

### 1. Serverless 定时任务架构

利用 GitHub Actions 的 `cron` 调度实现零服务器运维：

- **触发方式**：`schedule` 定时 + `workflow_dispatch` 手动
- **运行环境**：GitHub 提供的 `ubuntu-latest` Runner，免费额度每月 2000 分钟
- **关键点**：GitHub Actions 的 cron 使用 UTC 时区，`0 1 * * *` = 北京时间 09:00

```yaml
on:
  schedule:
    - cron: '0 1 * * *'
```

### 2. RSS 多源聚合策略

选择 RSS 作为主要数据获取方式的原因：
- **稳定性**：RSS 是标准协议，不存在反爬问题
- **统一接口**：`feedparser` 一个库解决所有源的解析
- **RSSHub 中转**：对于没有原生 RSS 的站点（HuggingFace Papers、GitHub Trending），通过 RSSHub 公共节点转换

信源分三层设计：
| 层级 | 信源 | 定位 |
|------|------|------|
| 国际硬核 | ArXiv、HF Papers、GitHub Trending | 论文 + 代码，技术源头 |
| 国际社区 | Hacker News、Reddit、OpenAI/Google Blog | 趋势 + 讨论 |
| 国内权威 | 机器之心、量子位 | 中文视角 + 落地信息 |

### 3. LLM 评级 Prompt Engineering

核心挑战：让 LLM 稳定输出结构化 JSON，同时对内容做出有价值的判断。

**解决方案**：
- 明确要求「只输出 JSON，不要 Markdown 代码块」
- 解析时做三层防护：去除 ````json` 标记 → 查找 `{` `}` 边界 → `json.loads`
- 中文媒体源加入「去营销化」指令，避免标题党干扰评分

```python
clean = text.replace("```json", "").replace("```", "").strip()
start = clean.find("{")
end = clean.rfind("}") + 1
return json.loads(clean[start:end])
```

### 4. 智能筛选机制

不硬性只推 S/A 级，而是采用「弹性补位」策略：
- 优先选 S 和 A 级内容
- 若不满 6 条，从 B 级中按分数补位
- 同标题去重（多源可能报道同一新闻）

这样保证每天有内容推送，又不会降低整体质量。

### 5. GitHub Pages 自动部署

脚本生成 `docs/index.html` 静态网页，workflow 自动 commit 回仓库：

```yaml
- name: Commit and push docs
  run: |
    git add docs/
    git diff --cached --quiet || git commit -m "Update daily AI news page"
    git push
```

关键点：
- `git diff --cached --quiet ||` 确保无变化时不会空 commit
- 需要 `permissions: contents: write` 授权 Actions 写入仓库
- Pages 设置为从 `main` 分支 `/docs` 目录部署

### 6. Telegram 消息分段

Telegram 单条消息限 4096 字符。处理方式：
- 按空行 (`\n\n`) 切分段落
- 累积拼接，接近 3800 字符时断开为新消息
- 这样每条新闻不会被从中间截断

### 7. 前后端解耦与静态化

v2.1.0 进行了架构重构，从「Python 生成 HTML」转向「Python 生成数据 + 前端动态渲染」：

- **旧方案**：Python 使用 f-string 拼接 HTML，每次运行全量覆盖 `news.html`。
    - *缺点*：无法查看历史日期，样式调整需改 Python 代码，耦合度高。
- **新方案**：
    - Python 只负责生成 `data/YYYY-MM-DD.json` 和 `data/index.json`。
    - 前端 HTML/JS 为纯静态文件，运行时 `fetch` 请求 JSON 数据渲染。
    - *优点*：支持历史回溯，支持客户端搜索，前后端开发独立，更符合 JAMStack 架构。

---

## 🔧 踩坑记录

### Qwen API 选型

- `dashscope` SDK 和 OpenAI 兼容接口都能用，选择 OpenAI 兼容接口 (`openai` 库)，原因是生态更通用，换模型只需改 `base_url` 和 `model`
- `base_url` 为 `https://dashscope.aliyuncs.com/compatible-mode/v1`

### RSS 源的坑

- Reddit RSS 在 GitHub Actions 的 IP 上可能被限流，返回 429。`feedparser` 不会报异常，只是 `feed.entries` 为空
- ArXiv RSS 噪音极大（每天几百篇），必须限制 `count` 并依赖 LLM 过滤
- RSSHub 公共节点不稳定，生产环境建议自建

### HTML 转义

Telegram HTML 模式和网页 HTML 都需要转义特殊字符（`<>&`），用 `html.escape()` 统一处理，避免标题中含 `<` 导致解析错误。
