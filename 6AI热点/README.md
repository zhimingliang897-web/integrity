# 📡 AI 每日热点情报 Agent

> 💡 **技术解密**: 关于本项目的技术实现与踩坑记录，请参阅 [👉 WHAT_WE_LEARN.md](WHAT_WE_LEARN.md)。

---

## 🏎️ 极速运行

### 1. 设置环境变量
```bash
set QWEN_API_KEY=sk-你的阿里云百炼密钥
set TELEGRAM_BOT_TOKEN=你的BotFather令牌
set TELEGRAM_CHAT_ID=-100xxxxxxxxxx
```

### 2. 启动
```bash
pip install -r requirements.txt
python main.py
```

### 3. 查看结果
- **Telegram 频道**：收到精选推送
- **网页**：`docs/index.html` 自动生成，部署到 GitHub Pages 后可公开访问

---

## 📐 系统架构

```
GitHub Actions (每日 09:00 北京时间)
       │
       ▼
  Python 脚本
       │
       ├── 1. 抓取 12 个 RSS/API 信源
       │       Hacker News · HF Papers · GitHub Trending
       │       ArXiv cs.AI · ArXiv cs.CL · Reddit LocalLLaMA
       │       Reddit ML · OpenAI Blog · Google AI
       │       MIT Tech Review · 机器之心 · 量子位
       │
       ├── 2. Qwen LLM 逐条评级 (S/A/B/C)
       │
       ├── 3. 筛选 Top + LLM 生成今日概览
       │
       ├── 4. Telegram 频道推送
       │
       └── 5. 数据归档
               Python保存 -> docs/data/202x-xx-xx.json
               GitHub Actions 自动 commit
               ▼
               Web 前端 (GitHub Pages)
               动态加载 JSON 渲染页面 (无需重构 HTML)
```

---

## 🔑 GitHub Secrets 配置

在仓库 **Settings → Secrets → Actions** 中添加：

| Name | 说明 |
|------|------|
| `QWEN_API_KEY` | 阿里云百炼 API Key |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | Telegram 频道/群组 ID |

---

## 🌐 GitHub Pages 部署

1. 进入仓库 **Settings → Pages**
2. Source 选择 **Deploy from a branch**
3. Branch 选择 `main`，文件夹选择 `/docs`
4. 保存后访问 `https://<username>.github.io/integrity/news.html`

---

## 📁 文件结构

```
6AI热点/
├── main.py              # 核心逻辑：采集 -> 分析 -> 推送 -> 存JSON
├── requirements.txt     # Python依赖
├── README.md            # 项目说明
├── WHAT_WE_LEARN.md     # 技术复盘
└── CHANGELOG.md         # 版本记录

docs/
├── news.html            # 主页：单页应用，动态加载数据
├── style.css            # 样式表
├── data/                # [自动生成] 数据归档目录
│   ├── index.json       # 日期索引
│   └── 202x-xx-xx.json  # 每日数据
└── index.html           # 首页导航
```
