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
       ├── 3. 筛选 Top 6 + LLM 生成今日概览
       │
       ├── 4. Telegram 频道推送
       │
       └── 5. 生成 docs/index.html 网页
               GitHub Actions 自动 commit → GitHub Pages
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
4. 保存后访问 `https://<username>.github.io/integrity/`

---

## 📁 文件结构

```
6AI热点/
├── main.py              # 主脚本：抓取 + 评级 + 推送 + 生成网页
├── requirements.txt     # Python 依赖
├── README.md            # 本文件
├── WHAT_WE_LEARN.md     # 技术心得
└── CHANGELOG.md         # 更新日志

docs/
└── index.html           # 自动生成的每日热点网页 (GitHub Pages)

.github/workflows/
└── daily_news.yml       # 定时任务配置
```
