# 更新日志

## v2.0.0 — 网页部署 + 推送优化

### 新功能
- 🌐 **GitHub Pages 网页**：每日自动生成 `docs/index.html`，暗色主题卡片式排版，任何人可通过链接访问
- 🧭 **今日概览**：LLM 生成 2-3 句话的每日总结，置于推送和网页顶部
- 📊 **弹性筛选**：优先 S/A 级，不足时自动补 B 级，保证每日有内容

### 优化
- 📉 **推送精简**：每日推送从 10 条缩减为 6 条，总结从 3-5 句缩短为 2-3 句（80 字内）
- 💬 **点评更短**：单条点评从 50 字缩减为 20 字
- 🔤 **HTML 转义**：Telegram 和网页均使用 `html.escape()` 防止特殊字符导致解析失败
- 📡 **Telegram 格式重排**：总结在前 → 逐条列表在后，信息密度更高

### Workflow
- ✅ GitHub Actions 自动 commit `docs/` 并推送，支持 GitHub Pages 部署
- ✅ 添加 `permissions: contents: write` 授权

## v1.0.0 — 初始版本

### 功能
- 🤖 **12 源聚合**：Hacker News、HF Papers、GitHub Trending、ArXiv (cs.AI + cs.CL)、Reddit (LocalLLaMA + ML)、OpenAI Blog、Google AI、MIT Tech Review、机器之心、量子位
- 🧠 **Qwen LLM 评级**：S/A/B/C 四级评分，中文源含去营销化指令
- 📲 **Telegram 推送**：HTML 格式，自动分段（3800 字符安全阈值）
- 🔁 **GitHub Actions 定时**：每天北京时间 09:00 自动运行
