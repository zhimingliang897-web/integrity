# 更新日志

## v2.1.0 — UI 焕新 + 数据归档

### 新功能
- 🎨 **UI 全面升级**：`news.html` 采用极简暗黑风 + 玻璃拟态设计，增加卡片悬停光效与微交互动画，提升阅读体验
- 🗄️ **历史数据归档**：每日新闻自动保存为 `data/YYYY-MM-DD.json`，不再覆盖静态 HTML，支持前端动态加载任意历史日期
- 🔍 **全站搜索**：前端实现纯客户端全文搜索，可按标题、标签、来源快速检索所有历史归档内容

### 优化
- ⚡ **前端动态渲染**：将 HTML 生成逻辑从 Python 剥离，改为 Python 生成 JSON 数据 → 前端 JS 渲染，解耦前后端
- 📱 **移动端适配**：优化控制栏布局，适配手机端操作，增加日期切换手势按钮
- 🛠️ **代码质量**：修复 Git 合并冲突，统一项目结构

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
