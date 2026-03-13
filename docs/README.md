# Integrity Lab - AI 工具集

> 一个人的 AI 实验室 —— 用 AI 造工具，用工具学 AI

## 📢 重要提示

**当前状态**：代码已完成，需开放阿里云安全组端口 8000 才能访问。

详见：[项目总结文档](./documentation/PROJECT_SUMMARY.md) | [部署问题文档](./documentation/DEPLOYMENT_ISSUES_AND_SOLUTIONS.md)

## 🌐 访问地址与部署方式

| 平台 | 地址 | 说明 |
|------|------|------|
| **GitHub Pages** | https://zhimingliang897-web.github.io/integrity/ | 静态站点：首页、工具库页、演示体验区、源码浏览，均托管于此 |
| **云服务器（在线工具）** | http://8.138.164.133:5000/app/tools.html | 仅在线工具入口跳转至此，登录与全部 API 在服务器运行 |
| 后端 API | http://127.0.0.1:5000/ | 服务器内部 API |

**部署策略**：仅保留一个「在线工具」入口跳转到云服务器；其余内容（演示、源码、说明）均在本地通过 GitHub Pages 部署。

修改云服务器地址时，请同时更新：`assets/js/tools-auth.js` 中的 `SERVER_URL`、`tools.html` 中「在线工具」卡片的 `#online-tools-server-link` 的 `href`。

---

## ✨ 功能特性

### 演示体验区（6 个）

| 功能 | 说明 | 状态 |
|------|------|------|
| 🎨 图文互转 | 上传图片生成 AI 绘图提示词 | ✅ |
| ⚖️ 多模型对比 | 同时对比 Qwen-Turbo/Plus/Max 回答 | ✅ |
| 🎭 AI 辩论赛 | 输入辩题，观看两个 AI 激烈交锋 | ✅ |
| 🪙 Token 计算器 | 计算不同模型的 Token 成本 | ✅ |
| 📝 台词学习预览 | 展示单词学习功能 | ✅ |
| 🎬 视频生成预览 | 展示 AI 视频生成功能 | ✅ |

### 在线工具区（仅 1 个入口）

- **在线工具（云服务器）**：工具库页「在线工具」Tab 内仅保留一个入口，点击后跳转到云服务器，在服务器端登录后使用以下功能：
  - AI 多模型对比、图文互转、AI 辩论赛、台词学习、视频生成、PDF 工具集（7 种操作）
- 上述功能的 API 与登录均在云服务器运行，本仓库 `docs/` 仅提供跳转链接。

### 云服务器上的 PDF 工具集（7 种功能）

1. **图片转 PDF** - 多图合成
2. **合并 PDF** - 多文件合并
3. **删除页面** - 指定页码删除
4. **插入 PDF** - 在指定位置插入
5. **页面重排** - 竖版横版排序
6. **统一尺寸** - 横向页面统一
7. **PDF 转图片** - 导出图片/长图

---

## 🔧 技术栈

### 前端
- HTML5 + CSS3 + Vanilla JavaScript
- 响应式设计
- GitHub Pages 托管

### 后端
- Python Flask
- SQLite (用户数据)
- JWT 认证
- Gunicorn + Nginx

### AI 服务
- 通义千问 (Qwen) - 主要 LLM
- Qwen VL - 视觉理解
- Edge TTS - 语音合成

---

## 📁 项目结构

```
docs/
├── index.html              # 首页
├── tools.html              # 工具库主页
├── news.html               # AI 热点
│
├── demos/                  # 演示页面
│   ├── ai-compare.html     # 多模型对比
│   ├── ai-debate.html      # AI 辩论赛
│   ├── image-prompt.html   # 图文互转
│   ├── dialogue-learning.html
│   └── video-maker.html
│
├── assets/
│   ├── css/
│   │   ├── style.css
│   │   └── tools-styles.css
│   └── js/
│       ├── tools-auth.js       # 认证与跳转（GitHub 上仅跳转云服务器）
│       └── tools-demo.js       # 演示体验区
│
└── server/                 # 后端代码
    └── app/
        ├── main.py             # 主入口
        └── tools/
            ├── pdf.py          # PDF 工具
            ├── ai_compare.py   # AI 对比
            ├── image_prompt.py # 图文互转
            ├── ai_debate.py    # AI 辩论
            ├── dialogue_learning.py
            └── video_maker.py
```

---

## 🚀 快速开始

### 本地预览

```bash
# 进入 docs 目录
cd docs

# 启动本地服务器
python -m http.server 8000

# 访问
# http://localhost:8000
```

### 本地运行后端

```bash
cd docs/server

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export DASHSCOPE_API_KEY=your-api-key
export SECRET_KEY=your-secret-key
export INVITE_CODES=demo2026,test2026

# 启动服务
python -m app.main
```

---

## 🔐 认证系统

### 注册邀请码
```
demo2026
test2026
friend2026
```

### API 认证
```bash
# 登录获取 Token
curl -X POST http://8.138.164.133:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"123456"}'

# 使用 Token
curl http://8.138.164.133:5000/api/auth/verify \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📡 API 端点

### 认证
```
POST /api/auth/register  # 注册
POST /api/auth/login     # 登录
GET  /api/auth/verify    # 验证 Token
```

### AI 工具
```
POST /api/tools/ai-compare/query       # AI 对比
GET  /api/tools/ai-compare/providers   # 提供商列表
POST /api/tools/image-prompt/analyze   # 图片分析
POST /api/tools/image-prompt/generate  # 提示词优化
POST /api/tools/ai-debate/start        # 开始辩论 (SSE)
GET  /api/tools/ai-debate/debaters     # 辩手列表
```

### PDF 工具
```
POST /api/tools/pdf/info          # PDF 信息
POST /api/tools/pdf/images_to_pdf # 图片转 PDF
POST /api/tools/pdf/merge         # 合并 PDF
POST /api/tools/pdf/remove_pages  # 删除页面
POST /api/tools/pdf/insert        # 插入 PDF
POST /api/tools/pdf/reorder       # 页面重排
POST /api/tools/pdf/normalize     # 统一尺寸
POST /api/tools/pdf/to_images     # PDF 转图片
GET  /api/tools/pdf/download/:file # 下载文件
```

---

## 📚 相关文档

- [📋 项目总结](./documentation/PROJECT_SUMMARY.md) - **必读：做了什么，还要做什么**
- [🚨 部署问题与解决方案](./documentation/DEPLOYMENT_ISSUES_AND_SOLUTIONS.md) - **必读：HTTPS 问题分析**
- [✅ 任务清单](./documentation/TASK_TODO.md)
- [📝 变更日志](./CHANGELOG.md)
- [🚀 部署指南](./DEPLOYMENT.md)

---

## 📝 开源协议

MIT License

---

**维护者**: Integrity Lab Team  
**最后更新**: 2026-03-13