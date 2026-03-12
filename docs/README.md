# Integrity Lab - AI 工具集

> 一个人的 AI 实验室 —— 用 AI 造工具，用工具学 AI

## 🌐 访问地址

| 平台 | 地址 | 说明 |
|------|------|------|
| GitHub Pages | https://zhimingliang897-web.github.io/integrity/ | 项目展示页 |
| 在线工具库 | http://8.138.164.133:5000/app/tools.html | 可交互使用 |
| 后端 API | http://8.138.164.133:5000/ | RESTful API |

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

### 在线工具区（6 个，需登录）

| 工具 | API 端点 | 功能 |
|------|----------|------|
| AI 多模型对比 | `/api/tools/ai-compare/query` | 并发查询多个模型 |
| 图文互转 | `/api/tools/image-prompt/analyze` | 图片分析生成提示词 |
| AI 辩论赛 | `/api/tools/ai-debate/start` | SSE 流式辩论 |
| 台词学习 | `/api/tools/dialogue-learning/process` | PDF 解析 + 台词检索 |
| 视频生成 | `/api/tools/video-maker/generate` | AI 剧本 + 分镜 + 配音 |
| PDF 工具集 | `/api/tools/pdf/*` | 7 种 PDF 操作 |

### PDF 工具集（7 种功能）

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
│       ├── tools-auth.js       # 认证模块
│       ├── tools-demo.js       # 演示功能
│       ├── tools-online.js     # 在线工具
│       └── tools-pdf.js        # PDF 功能
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

- [后端实现指南](./BACKEND_IMPLEMENTATION_GUIDE.md)
- [部署状态](./documentation/DEPLOYMENT_STATUS.md)
- [任务清单](./documentation/TASK_TODO.md)
- [变更日志](./CHANGELOG.md)

---

## 📝 开源协议

MIT License

---

**维护者**: Integrity Lab Team  
**最后更新**: 2026-03-13