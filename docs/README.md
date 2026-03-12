# Integrity Lab - 项目文档

**GitHub Pages 托管的 AI 工具集合平台**

这是 Integrity Lab 的前端界面，展示 14 个 AI 工具项目，并提供在线使用功能。

---

## 🌐 访问地址

- **生产环境**：https://zhimingliang897-web.github.io/integrity/
- **后端 API**：https://api.liangyiren.top/
- **演示页面**：https://zhimingliang897-web.github.io/integrity/demos/

---

## 📁 目录结构

```
docs/
├── assets/                    # 静态资源
│   ├── css/                  # 样式文件
│   │   ├── style.css        # 全局样式
│   │   └── tools-styles.css # 工具页面样式
│   ├── js/                   # JavaScript 文件
│   │   ├── demos-common.js  # 演示页面通用脚本
│   │   ├── tools-auth.js    # 认证模块
│   │   ├── tools-demo.js    # 工具演示脚本
│   │   └── tools-pdf.js     # PDF 工具脚本
│   └── images/              # 图片资源
│
├── demos/                     # 演示页面
│   ├── _template.html       # 页面模板
│   ├── index.html           # 演示页面索引
│   ├── ai-compare.html      # 多模型对比平台
│   ├── ai-debate.html       # AI 辩论赛
│   ├── course-digest.html   # CourseDigest 智能助考
│   ├── dialogue-learning.html # 台词学习工具
│   ├── easyapply.html       # EasyApply 浏览器插件
│   ├── file-agent.html      # 个人文件助手 Agent
│   ├── image-prompt.html    # 图文互转工具
│   ├── redbook-generator.html # 小红书内容生成器
│   ├── ticket-helper.html   # 大麦抢票助手
│   ├── token-compare.html   # Token 消耗对比工具
│   ├── video-maker.html     # 分镜视频生成器
│   └── xhs-image-generator.html # 小红书图片生成器
│
├── documentation/             # 文档中心
│   ├── guides/              # 使用指南
│   │   ├── AUTH_SYSTEM.md
│   │   ├── AUTHENTICATION_SUMMARY.md
│   │   └── DEMO_QUICK_START.md
│   ├── reference/           # 技术参考
│   │   ├── DIRECTORY_STRUCTURE.md
│   │   └── ONLINE_TOOLS_ROADMAP.md
│   ├── NEXT_SESSION_TODO.md # 项目完成报告
│   ├── PROJECT_STATUS.md    # 项目状态报告
│   ├── FILES_SUMMARY.md
│   ├── INDEX.md
│   ├── QUICK_GUIDE.md
│   ├── README_TOOLS.md
│   ├── SKILL_FRONTEND_REFACTOR.md
│   ├── SKILL_QUICK_GUIDE.md
│   ├── TOOLS_REFACTOR_PROGRESS.md
│   └── skill-frontend-refactor.json
│
├── data/                      # 数据文件
│   └── *.json              # 新闻数据
│
├── server/                    # 后端代码
│   └── app/
│       └── tools/
│           └── pdf.py
│
├── archive/                   # 归档文件
│
├── index.html                 # 首页
├── news.html                  # AI 每日情报
├── tools.html                 # 工具库主页面
├── DEPLOYMENT.md             # 部署文档
├── DEPLOY_LOG.md             # 部署日志
└── README.md                 # 本文件
```

---

## 🎯 项目状态

**✅ 所有 14 个演示页面已完成（100%）**

| 优先级 | 项目 | 状态 |
|--------|------|------|
| 高 | 分镜视频生成器 | ✅ |
| 高 | 台词学习工具 | ✅ |
| 高 | AI 辩论赛 | ✅ |
| 高 | 图文互转工具 | ✅ |
| 高 | 多模型对比平台 | ✅ |
| 中 | EasyApply 浏览器插件 | ✅ |
| 中 | CourseDigest 智能助考 | ✅ |
| 中 | 个人文件助手 Agent | ✅ |
| 中 | 小红书内容生成器 | ✅ |
| 中 | 小红书图片生成器 | ✅ |
| 低 | Token 消耗对比工具 | ✅ |
| 低 | 大麦抢票助手 | ✅ |
| 低 | AI 每日情报 Agent | ✅ |
| 低 | PDF 工具集 | ✅ |

---

## 🔐 认证系统

### 测试账号
```
用户名：test
密码：123456
```

### 注册邀请码
```
demo2026      # 演示账号专用
test2026      # 测试账号专用
friend2026    # 朋友分享专用
```

> **详细说明**：查看 `documentation/guides/AUTH_SYSTEM.md`

---

## 🚀 本地开发

### 1. 启动本地服务器

```bash
# Python
cd docs
python3 -m http.server 8000

# Node.js
npx http-server docs -p 8000
```

### 2. 访问页面

- http://localhost:8000/index.html - 首页
- http://localhost:8000/tools.html - 工具库
- http://localhost:8000/demos/index.html - 演示页面

---

## 🛠️ API 配置

```javascript
const API_BASE = 'https://api.liangyiren.top';
```

### 主要端点
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `POST /api/tools/pdf/*` - PDF 工具（需登录）

---

## 📝 开发指南

### 添加新的演示页面

```bash
# 1. 复制模板
cp docs/demos/_template.html docs/demos/your-demo.html

# 2. 修改内容
# 3. 测试
```

### 通用工具函数

```javascript
// 检查登录
const { token, isLoggedIn } = DemoUtils.checkAuth();

// 显示消息
DemoUtils.showMessage('操作成功', 'success');

// 上传文件
const result = await DemoUtils.uploadFile(file, '/api/endpoint');
```

> **详细指南**：查看 `documentation/guides/DEMO_QUICK_START.md`

---

## 📚 相关文档

- `documentation/NEXT_SESSION_TODO.md` - 项目完成报告
- `documentation/PROJECT_STATUS.md` - 项目状态报告
- `documentation/guides/DEMO_QUICK_START.md` - 演示页面开发指南
- `documentation/guides/AUTH_SYSTEM.md` - 认证系统说明

---

## 📞 联系方式

- **GitHub**：https://github.com/zhimingliang897-web/integrity
- **问题反馈**：提交 GitHub Issue

---

**文档版本**：v3.0  
**最后更新**：2026-03-13  
**维护者**：Integrity Lab Team
