# Integrity Lab

**一个人的 AI 实验室 —— 用 AI 造工具，用工具学 AI**

---

## 🌐 在线访问

- **前端界面**: https://zhimingliang897-web.github.io/integrity/
- **后端 API**: https://api.liangyiren.top/

---

## 📚 项目说明

这是一个 AI 工具集合项目，包含：

- **14+ 开源 AI 工具**：从视频生成到 PDF 处理，从辩论赛到文件助手
- **在线工具平台**：登录后可在浏览器直接使用工具，无需本地环境
- **AI 每日热点**：自动聚合全球 12+ 技术信源，LLM 智能评级与摘要

---

## 📂 目录结构

```
integrity/
├── docs/                    # 前端（GitHub Pages）
│   ├── index.html          # 首页
│   ├── news.html           # AI 热点
│   ├── tools.html          # 工具库
│   ├── style.css           # 样式
│   ├── server/             # 后端代码（本地备份）
│   └── README.md           # 前端文档
├── 1分镜/                   # 分镜视频生成器
├── 2台词/                   # 台词学习工具
├── 5AI辩论赛/               # AI 辩论赛
├── 6AI热点/                 # AI 每日情报 Agent
├── 9图生文文生图/           # 图文互转工具
├── 11easyapply/            # EasyApply 浏览器插件
├── 12pdffun/               # PDF 工具集
├── 13course_digest/        # CourseDigest 智能助考
├── 14file-agent/           # 个人文件助手 Agent
├── 15redbook/              # 小红书内容生成器
├── 17ai-compare/           # 多模型对比平台
├── 18tokens/               # Token 消耗对比工具
└── 20AIer-xhs/             # 小红书图片自动化生成器
```

---

## 🚀 快速开始

### 访问在线平台

1. 打开 https://zhimingliang897-web.github.io/integrity/
2. 浏览工具库和 AI 热点
3. 注册/登录后使用在线工具（需要邀请码）

### 本地运行工具

每个工具目录都有独立的 README，按照说明安装依赖并运行。

**示例（PDF 工具）：**
```bash
cd 12pdffun
pip install -r requirements.txt
python app.py
```

---

## 🔐 获取邀请码

在线工具需要邀请码注册。如需邀请码，请：
- 提交 GitHub Issue
- 或通过其他方式联系作者

---

## 📖 文档

- **前端文档**: [docs/README.md](docs/README.md)
- **后端文档**: [docs/server/README.md](docs/server/README.md)
- **各工具文档**: 查看对应目录的 README

---

## 🛠️ 技术栈

- **前端**: HTML + CSS + Vanilla JavaScript
- **后端**: Flask + SQLAlchemy + JWT
- **AI**: Qwen, DeepSeek, GPT-4o, Qwen-VL
- **部署**: GitHub Pages + 阿里云 ECS + Gunicorn

---

## 📝 学习理念

- **拒绝黑盒**：深入理解 Prompt 构建、数据流转、模型微调
- **造轮子**：通过构建真实工具来掌握 AI 全栈开发
- **持续迭代**：记录从 V1 到 Vn 的演进过程

---

## 📞 联系方式

- **GitHub**: https://github.com/zhimingliang897-web/integrity
- **问题反馈**: 提交 GitHub Issue

---

## 📄 许可证

本项目开源，仅供学习使用。
