# Integrity Lab 工具库需求文档

**版本**: 1.0  
**创建日期**: 2026-03-13  
**最后更新**: 2026-03-13

---

## 一、项目概述

### 1.1 项目定位

Integrity Lab 是一个 AI 工具集合平台，包含多个自研 AI 工具。项目分为两个核心模块：

1. **演示体验** - 静态展示，给用户初步印象
2. **在线工具** - 真实可用的后端服务

### 1.2 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                        用户访问                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  GitHub Pages (HTTPS)                        │
│           https://zhimingliang897-web.github.io/integrity/   │
│                                                              │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │    首页展示     │    │   演示体验区    │                 │
│  │  (项目介绍)     │    │  (静态JS模拟)   │                 │
│  └─────────────────┘    └─────────────────┘                 │
│                                                              │
│                    点击"在线工具"                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 跳转
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               云服务器 (8.138.164.133:5000)                  │
│                   http://8.138.164.133:5000/app/             │
│                                                              │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │   在线工具库    │    │   Flask 后端    │                 │
│  │  (需登录使用)   │◄──►│   API 服务      │                 │
│  └─────────────────┘    └─────────────────┘                 │
│                               │                              │
│                               ▼                              │
│                    ┌─────────────────────┐                   │
│                    │   AI 服务 (Qwen)    │                   │
│                    │   PDF 处理          │                   │
│                    │   TTS 语音合成      │                   │
│                    │   视频生成          │                   │
│                    └─────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 为什么这样设计？

| 问题 | 解决方案 |
|------|----------|
| 域名未备案，80/443 端口被拦截 | GitHub Pages 做展示，服务器用非标准端口 |
| HTTPS 页面无法调用 HTTP API | 演示用静态模拟，在线工具部署在服务器上 |
| 需要给用户初步印象 | 演示体验区用 JS 模拟效果 |
| 需要真实可用功能 | 在线工具连接真实后端服务 |

---

## 二、模块详细需求

### 2.1 演示体验模块

#### 2.1.1 目的

- 展示工具的核心功能效果
- 给用户直观的初步印象
- 吸引用户登录使用完整功能

#### 2.1.2 技术要求

| 项目 | 要求 |
|------|------|
| 托管平台 | GitHub Pages |
| 技术栈 | HTML + CSS + Vanilla JavaScript |
| 数据来源 | **静态模拟数据**，不调用后端 API |
| 用户交互 | 纯前端动画效果 |

#### 2.1.3 功能列表

| # | 工具名称 | 展示效果 | 实现方式 |
|---|----------|----------|----------|
| 1 | 🎨 图文互转 | 点击按钮，模拟生成提示词的过程 | JS 打字机效果 |
| 2 | ⚖️ 多模型对比 | 点击按钮，三个模型依次返回模拟回答 | JS 延时 + 打字效果 |
| 3 | 🎭 AI 辩论赛 | 点击按钮，模拟双方辩论对话 | JS 逐步显示 |
| 4 | 🪙 Token 计算 | 点击按钮，显示计算结果 | 调用后端 API（无需登录） |
| 5 | 📝 台词学习 | 展示功能介绍 + 跳转链接 | 静态卡片 |
| 6 | 🎬 视频生成 | 展示功能介绍 + 跳转链接 | 静态卡片 |

#### 2.1.4 实现示例

```javascript
// 演示体验 - 多模型对比示例
const modelResponses = {
    'qwen-plus': '大语言模型（LLM）是...',
    'qwen-turbo': 'LLM 本质是文本预测...',
    'qwen-max': 'Large Language Model is...'
};

document.getElementById('start-compare-btn').addEventListener('click', async () => {
    // 1. 显示"思考中..."
    // 2. 逐字显示模拟回答
    // 3. 完成后按钮变为"重新对比"
});
```

#### 2.1.5 文件位置

```
docs/
├── tools.html              # 工具库主页面
└── assets/js/
    └── tools-demo.js       # 演示体验 JS 逻辑
```

---

### 2.2 在线工具模块

#### 2.2.1 目的

- 提供真实可用的 AI 工具服务
- 用户登录后可以使用完整功能
- 后端处理实际业务逻辑

#### 2.2.2 访问流程

```
1. 用户访问 GitHub Pages
2. 点击"在线工具"或"工具库"
3. 跳转到 http://8.138.164.133:5000/app/tools.html
4. 未登录显示"请先登录"
5. 登录后解锁所有在线工具
6. 使用真实后端 API 处理请求
```

#### 2.2.3 技术要求

| 项目 | 要求 |
|------|------|
| 服务器 | 阿里云服务器 8.138.164.133 |
| 后端框架 | Python Flask |
| 数据库 | SQLite (用户数据) |
| 认证 | JWT Token |
| AI 服务 | 通义千问 (Qwen) API |

#### 2.2.4 功能列表

| # | 工具名称 | 后端 API | 功能描述 |
|---|----------|----------|----------|
| 1 | ⚖️ AI 多模型对比 | `/api/tools/ai-compare/query` | 同时查询多个模型 |
| 2 | 🎨 图文互转 | `/api/tools/image-prompt/analyze` | 图片分析生成提示词 |
| 3 | 🎭 AI 辩论赛 | `/api/tools/ai-debate/start` | SSE 流式辩论 |
| 4 | 📝 台词学习 | `/api/tools/dialogue-learning/process` | PDF 解析 + 台词检索 |
| 5 | 🎬 视频生成 | `/api/tools/video-maker/generate` | AI 剧本 + 配音 |
| 6 | 📄 PDF 工具集 | `/api/tools/pdf/*` | 7 种 PDF 操作 |

#### 2.2.5 后端服务架构

```
server/
├── app/
│   ├── main.py                 # Flask 主入口
│   ├── models.py               # 数据模型
│   └── tools/
│       ├── pdf.py              # PDF 工具集
│       ├── ai_compare.py       # AI 对比
│       ├── image_prompt.py     # 图文互转
│       ├── ai_debate.py        # AI 辩论赛
│       ├── dialogue_learning.py # 台词学习
│       └── video_maker.py      # 视频生成
├── requirements.txt            # 依赖
└── data/
    └── users.db               # 用户数据库
```

#### 2.2.6 API 认证

```bash
# 登录获取 Token
POST /api/auth/login
{
    "username": "test",
    "password": "123456"
}

# 响应
{
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "username": "test"
}

# 使用 Token 调用 API
POST /api/tools/ai-compare/query
Header: Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

---

## 三、开发任务清单

### 3.1 已完成

| 任务 | 状态 | 说明 |
|------|------|------|
| 后端 API 部署 | ✅ | 服务器运行正常 |
| 前后端同源部署 | ✅ | 解决 Mixed Content 问题 |
| 登录认证系统 | ✅ | JWT Token 认证 |
| 演示体验 UI | ✅ | 6 个 Demo 卡片 |
| 在线工具 UI | ✅ | 6 个工具卡片 |
| PDF 工具集 | ✅ | 7 种功能 |

### 3.2 待完成

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | 完善演示体验 JS 动画 | 让静态展示更生动 |
| P0 | 测试所有在线工具功能 | 确保真实可用 |
| P1 | 添加错误处理和提示 | 用户体验优化 |
| P1 | 添加 loading 动画 | 用户体验优化 |
| P2 | 添加更多演示 Demo | 持续迭代 |

### 3.3 后续维护

| 任务 | 频率 | 说明 |
|------|------|------|
| 检查服务器状态 | 每周 | 确保服务正常运行 |
| 更新依赖包 | 每月 | 安全更新 |
| 备份数据库 | 每周 | 防止数据丢失 |
| 监控 API 调用 | 持续 | 关注使用情况 |

---

## 四、部署指南

### 4.1 GitHub Pages 部署

```bash
# 1. 修改代码后提交
git add docs/
git commit -m "update"
git push origin main

# 2. GitHub 自动部署
# 访问 https://zhimingliang897-web.github.io/integrity/
```

### 4.2 服务器部署

```bash
# 1. SSH 连接服务器
ssh root@8.138.164.133
# 密码: 15232735822Aa

# 2. 进入项目目录
cd /root/integrity-api/server

# 3. 拉取最新代码
git pull origin main

# 4. 重启服务
pkill gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 app.main:app --daemon \
  --chdir /root/integrity-api/server \
  --env SECRET_KEY=integrity-lab-secret-2026 \
  --env DASHSCOPE_API_KEY=sk-0ef56d1b3ba54a188ce28a46c54e2a24 \
  --env INVITE_CODES=demo2026,friend2026,test2026

# 5. 验证服务
curl http://localhost:5000/
```

### 4.3 文件上传（非 Git 方式）

```python
# 使用 Python SFTP 上传文件
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('8.138.164.133', port=22, username='root', password='15232735822Aa')

sftp = ssh.open_sftp()
sftp.put('本地文件路径', '/root/integrity-api/server/app/static/远程文件名')
sftp.close()
ssh.close()
```

---

## 五、环境配置

### 5.1 环境变量

| 变量名 | 值 | 用途 |
|--------|-----|------|
| SECRET_KEY | integrity-lab-secret-2026 | JWT 密钥 |
| DASHSCOPE_API_KEY | sk-0ef56d1b3ba54a188ce28a46c54e2a24 | 通义千问 API |
| INVITE_CODES | demo2026,friend2026,test2026 | 注册邀请码 |

### 5.2 服务器信息

| 项目 | 值 |
|------|-----|
| IP | 8.138.164.133 |
| SSH 端口 | 22 |
| SSH 用户 | root |
| SSH 密码 | 15232735822Aa |
| HTTP 端口 | 5000 |
| 项目路径 | /root/integrity-api/server |

### 5.3 依赖包

```
flask==3.0.0
flask-cors==4.0.0
flask-sqlalchemy==3.1.1
pyjwt==2.8.0
openai==1.12.0
pdfplumber==0.10.0
beautifulsoup4==4.12.0
edge-tts==6.1.0
pillow==10.1.0
pypdf==3.17.0
dashscope==1.14.0
gunicorn==21.2.0
```

---

## 六、测试用例

### 6.1 演示体验测试

```markdown
- [ ] 点击"提取提示词"按钮，显示模拟结果
- [ ] 点击"开始对比"按钮，三个模型依次返回
- [ ] 点击"开始辩论"按钮，显示模拟辩论
- [ ] 点击"计算消耗"按钮，显示计算结果
```

### 6.2 在线工具测试

```markdown
- [ ] 未登录时显示"请先登录"
- [ ] 使用邀请码注册新用户
- [ ] 登录成功获取 Token
- [ ] AI 对比：选择模型，提交问题，获取回答
- [ ] 图文互转：上传图片，获取提示词
- [ ] AI 辩论：输入辩题，观看实时辩论
- [ ] PDF 工具：测试 7 种功能
```

### 6.3 API 测试

```bash
# 健康检查
curl http://8.138.164.133:5000/

# 登录
curl -X POST http://8.138.164.133:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"123456"}'

# AI 对比
curl -X POST http://8.138.164.133:5000/api/tools/ai-compare/query \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question":"你好","provider":"qwen","model":"qwen-turbo"}'
```

---

## 七、常见问题

### Q1: 为什么演示体验不调用真实 API？

A: GitHub Pages 是 HTTPS，服务器是 HTTP，存在 Mixed Content 限制。演示体验只是给用户初步印象，真实功能在服务器上。

### Q2: 为什么不能用域名访问？

A: 域名未备案，80/443 端口被阿里云拦截。使用 IP:5000 端口可以绕过限制。

### Q3: 如何添加新的工具？

1. 创建后端 Blueprint: `docs/server/app/tools/xxx.py`
2. 在 `main.py` 中注册 Blueprint
3. 创建前端 Demo: `docs/demos/xxx.html`
4. 在 `tools.html` 中添加卡片
5. 部署到服务器

### Q4: Token 过期怎么办？

Token 有效期 7 天，过期后需要重新登录。

---

## 八、联系方式

- **GitHub**: https://github.com/zhimingliang897-web/integrity
- **问题反馈**: GitHub Issues
- **文档位置**: `docs/documentation/REQUIREMENTS.md`

---

**文档版本**: 1.0  
**适用对象**: 开发者、维护者、智能体

---

## 附录：快速参考

### 访问地址速查

| 名称 | 地址 |
|------|------|
| GitHub Pages | https://zhimingliang897-web.github.io/integrity/ |
| 服务器工具库 | http://8.138.164.133:5000/app/tools.html |
| API 端点 | http://8.138.164.133:5000/ |

### SSH 连接速查

```
ssh root@8.138.164.133
密码: 15232735822Aa
```

### 邀请码速查

```
demo2026
friend2026
test2026
```