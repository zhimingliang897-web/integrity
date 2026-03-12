# Changelog

All notable changes to this project will be documented in this file.

## [2026-03-13]

### Added
- **AI 多模型对比** - 新增在线工具，支持 Qwen-Turbo/Plus/Max 并发查询对比
- **图文互转工具** - 图片分析生成 AI 绘图提示词
- **AI 辩论赛** - SSE 流式辩论，支持自定义辩题和轮数
- **台词学习工具** - PDF 解析、台词检索、AI 整理、TTS 发音
- **分镜视频生成** - AI 剧本生成、分镜插图、Edge TTS 配音
- **演示体验区** - 新增 6 个可交互 Demo 卡片
- **在线工具区** - 新增 6 个在线工具（需登录）
- **tools-online.js** - 在线工具功能模块

### Changed
- **架构调整** - 前后端部署到同一服务器，解决 HTTPS/HTTP Mixed Content 问题
- **GitHub Pages** - 首页移除登录功能，改为跳转到服务器
- **API_BASE** - 改用 `window.location.origin` 实现同源访问
- **README.md** - 全面更新项目文档

### Fixed
- 修复 GitHub Pages HTTPS 无法调用 HTTP API 的问题
- 修复 80/443 端口被阿里云安全组拦截的问题
- 修复 Nginx 配置域名未备案无法访问的问题

### Deployment
- 服务器 IP: `8.138.164.133:5000`
- 前端地址: `http://8.138.164.133:5000/app/`
- 后端 API: `http://8.138.164.133:5000/`

---

## [2026-03-12]

### Added
- **后端 API Blueprint**
  - `ai_compare.py` - 多模型对比
  - `image_prompt.py` - 图文互转
  - `ai_debate.py` - AI 辩论赛
  - `dialogue_learning.py` - 台词学习
  - `video_maker.py` - 视频生成
- **统一 DashScope API** - 所有 AI 功能使用 qwen3.5-plus
- **后端实现指南** - `BACKEND_IMPLEMENTATION_GUIDE.md`

### Changed
- 更新 `requirements.txt` 添加新依赖
- 更新 `main.py` 注册所有 Blueprint

---

## [2026-03-11]

### Added
- **PDF 工具集** - 7 种 PDF 操作功能
- **认证系统** - JWT Token 登录注册
- **Token 计算器** - Token 消耗预估

---

## 项目概述

Integrity Lab 是一个 AI 工具集平台，包含 14 个开源 AI 工具：

1. PDF 工具集
2. 分镜视频生成器
3. 台词学习工具
4. AI 辩论赛
5. AI 每日情报 Agent
6. 图文互转工具
7. EasyApply 浏览器插件
8. CourseDigest 智能助考
9. 个人文件助手 Agent
10. 小红书内容生成器
11. 多模型对比平台
12. Token 消耗对比工具
13. 小红书图片生成器
14. 大麦抢票助手

---

**维护者**: Integrity Lab Team