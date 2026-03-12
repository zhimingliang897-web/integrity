# Demo 项目部署状态分析

**更新时间：2026-03-13**

---

## 一、tools.html 列出的所有项目

| # | 项目名称 | 后端需求 | 部署状态 | 说明 |
|---|----------|----------|----------|------|
| 1 | PDF 工具集 | ✅ 需要 | ✅ 已部署 | `pdf.py` |
| 2 | 分镜视频生成器 | ✅ 需要 | ✅ 已部署 | `video_maker.py` |
| 3 | 台词学习工具 | ✅ 需要 | ✅ 已部署 | `dialogue_learning.py` |
| 4 | AI 辩论赛 | ✅ 需要 | ✅ 已部署 | `ai_debate.py` |
| 5 | AI 每日情报 Agent | ⚠️ 特殊 | ❌ 未部署 | GitHub Actions 定时任务 |
| 6 | 图文互转工具 | ✅ 需要 | ✅ 已部署 | `image_prompt.py` |
| 7 | EasyApply 浏览器插件 | ❌ 不需要 | - | 纯前端浏览器扩展 |
| 8 | CourseDigest 智能助考 | ⚠️ 本地 | ❌ 不适合 | 需要本地 Whisper + 本地文件 |
| 9 | 个人文件助手 Agent | ⚠️ 本地 | ❌ 不适合 | 操作本地文件系统 |
| 10 | 小红书内容生成器 | ⚠️ 特殊 | ❌ 未部署 | 需要 Playwright 浏览器自动化 |
| 11 | 多模型对比平台 | ✅ 需要 | ✅ 已部署 | `ai_compare.py` |
| 12 | Token 消耗对比工具 | ❌ 不需要 | - | 纯前端计算 |
| 13 | 小红书图片生成器 | ⚠️ 本地 | ❌ 不适合 | 本地 PIL 渲染图片 |
| 14 | 大麦抢票助手 | ⚠️ 本地 | ❌ 私有 | 需要连接手机 ADB |

---

## 二、服务器已部署的 API

```
/root/integrity-api/server/app/tools/
├── pdf.py              ✅ PDF 工具集
├── ai_compare.py       ✅ 多模型对比
├── image_prompt.py     ✅ 图文互转
├── ai_debate.py        ✅ AI 辩论赛
├── dialogue_learning.py ✅ 台词学习
├── video_maker.py      ✅ 视频生成
└── __init__.py
```

---

## 三、部署状态总结

### ✅ 已部署（6个）

| 项目 | API 路径 | 功能 |
|------|----------|------|
| PDF 工具集 | `/api/tools/pdf/*` | 图片转PDF、合并、删除页面等 |
| 多模型对比 | `/api/tools/ai-compare/*` | 多模型并发对比 |
| 图文互转 | `/api/tools/image-prompt/*` | 图片分析、提示词优化 |
| AI 辩论赛 | `/api/tools/ai-debate/*` | SSE 流式辩论 |
| 台词学习 | `/api/tools/dialogue-learning/*` | PDF解析、台词检索、TTS |
| 视频生成 | `/api/tools/video-maker/*` | AI剧本、分镜图、配音合成 |

### ⚠️ 需要特殊部署（2个）

| 项目 | 部署方式 | 难度 |
|------|----------|------|
| AI 每日情报 Agent | GitHub Actions 定时任务 | 中等 |
| 小红书内容生成器 | 需要 Playwright + 桌面环境 | 较难 |

### ❌ 不适合服务器部署（6个）

| 项目 | 原因 |
|------|------|
| EasyApply 浏览器插件 | 纯前端，用户自行安装 |
| CourseDigest 智能助考 | 需要本地 Whisper 模型处理视频 |
| 个人文件助手 Agent | 操作用户本地文件系统 |
| Token 消耗对比工具 | 纯前端计算即可 |
| 小红书图片生成器 | 本地 PIL 渲染，无需服务端 |
| 大麦抢票助手 | 需要连接用户手机 ADB |

---

## 四、新部署计划

### P1 - 可部署项目

#### 1. AI 每日情报 Agent

**部署方式**：GitHub Actions 定时任务

**需要准备**：
- Telegram Bot Token
- RSS 源配置
- DashScope API Key（已有）

**部署步骤**：
```yaml
# .github/workflows/daily-news.yml
name: AI Daily News
on:
  schedule:
    - cron: '0 2 * * *'  # 每天 2:00 UTC
  workflow_dispatch:

jobs:
  fetch-news:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r 6AI热点/requirements.txt
      - run: python 6AI热点/main.py
        env:
          DASHSCOPE_API_KEY: ${{ secrets.DASHSCOPE_API_KEY }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

#### 2. 小红书内容生成器

**部署方式**：服务器 + Playwright

**需要准备**：
- 安装 Playwright
- 配置无头浏览器环境

**部署步骤**：
```bash
# 服务器上执行
pip install playwright
playwright install chromium
playwright install-deps
```

**后端 API Blueprint**：
```python
# app/tools/redbook.py
# 提供 /api/tools/redbook/generate 端点
```

### P2 - 前端优化

#### 1. Token 消耗对比工具

当前是纯前端演示，需要连接真实 API 计算 Token：

```javascript
// 可以添加一个后端接口
// /api/tools/token/calculate
// 调用 tiktoken 计算真实 Token 数
```

---

## 五、立即执行计划

### 任务 1：部署 AI 每日情报 Agent（推荐）

**优先级**：高  
**工作量**：2-3 小时  
**步骤**：
1. 创建 GitHub Actions workflow 文件
2. 配置 Secrets（Telegram Token）
3. 测试定时任务

### 任务 2：修复外网访问（紧急）

**优先级**：最高  
**步骤**：
```bash
ssh root@8.138.164.133
# 检查 Nginx
systemctl status nginx
nginx -t
cat /etc/nginx/sites-enabled/default

# 检查 SSL
certbot certificates

# 检查端口
netstat -tlnp | grep -E '80|443'
```

### 任务 3：部署小红书内容生成器 API

**优先级**：中  
**工作量**：4-6 小时  
**步骤**：
1. 创建 `redbook.py` Blueprint
2. 安装 Playwright 依赖
3. 测试无头浏览器
4. 添加到 main.py 注册

---

## 六、建议执行顺序

1. **立即**：修复外网 HTTPS 访问问题
2. **本周**：部署 AI 每日情报 Agent（GitHub Actions）
3. **下周**：考虑小红书内容生成器服务器部署

---

*文档更新：2026-03-13*