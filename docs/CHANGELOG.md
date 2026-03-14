# Changelog

All notable changes to this project will be documented in this file.

## [2026-03-14] - Image Prompt Tool & Server Sync

### Added
- **Image Prompt Tool (图文互转)**
  - New API endpoints:
    - `POST /api/tools/image-prompt/analyze` - 分析图片生成提示词
    - `POST /api/tools/image-prompt/generate` - 根据提示词生成图片
    - `GET /api/tools/image-prompt/health` - 健康检查
  - Supports DALL-E 3 and Stable Diffusion style prompts
  - Uses Qwen3-VL for image analysis
  - Uses DALL-E 3 for image generation
  - Requires DASHSCOPE_API_KEY

### Sync
- **Local → Server sync completed**
  - Copied `image_prompt/` module to server
  - Updated server `__init__.py` with blueprint registration
  - Restarted service - running successfully

---

## [2026-03-14] - Server Bug Fixes & API Path Unification

### Fixed
- **[Server] debate.html JavaScript syntax error** (`integrity-tools/app/templates/debate.html`)
  - Removed orphaned `catch` block at line 168-173 that caused `startDebate is not defined` error
- **[Server] PDF module 404 error** (`integrity-tools/app/__init__.py`)
  - Added missing PDF blueprint registration: `app.register_blueprint(pdf_bp, url_prefix='/api/pdf')`
- **[Frontend] API path unification** (docs project)
  - Fixed all API paths to match integrity-tools backend:
    - `/api/tools/ai-compare/*` → `/api/compare/*`
    - `/api/tools/ai-debate/*` → `/api/debate/*`
    - `/api/tools/token-compare/*` → `/api/tokens/*`
    - `/api/tools/token-calc` → `/api/tokens/calc`
    - `/api/tools/pdf/*` → `/api/pdf/*`
    - `/api/tools/dialogue-learning/*` → `/api/lines/*`
  - Marked video-maker and image-prompt as "功能暂未上线" (backend not implemented)

### Changed
- Local `integrity-tools/app/__init__.py` synced with server

## [2026-03-13] - Bug Fixes & Security Hardening

### Fixed
- **[Critical] JS 全局变量重复声明导致页面崩溃** (`tools-demo.js`, `tools-online.js`)
  - `const API_BASE`、`const SERVER_URL`、`const IS_GITHUB_PAGES`、`function showToast` 在多个脚本中重复声明，引发 `SyntaxError`，导致 `tools.html` 所有 JS 功能（tab 切换、演示按钮、登录、PDF 工具）完全失效
  - 修复方案：将共享常量统一由 `tools-auth.js` 提供，其他文件删除重复声明
- **密码哈希算法升级** (`server/app/main.py`)
  - 原始 SHA256 无盐值哈希替换为 `werkzeug.security.generate_password_hash`（PBKDF2-HMAC-SHA256，自动加盐）
  - 登录验证改用 `check_password_hash`，兼容新哈希格式
- **SECRET_KEY 安全加固** (`server/app/main.py`)
  - 移除硬编码备用值 `'integrity-lab-secret-key-2026'`；环境变量未设置时直接抛出 `RuntimeError`，防止以已知明文 key 运行
- **CORS 通配符端口修复** (`server/app/main.py`)
  - `http://localhost:*` / `http://127.0.0.1:*` 通配符在 CORS 规范中无效，替换为明确端口列表（3000, 5000, 5500, 8080）
- **SQLAlchemy 弃用 API 替换** (`server/app/main.py`)
  - `User.query.get(user_id)` → `db.session.get(User, user_id)`（兼容 SQLAlchemy 2.0）

### Added
- **工具库演示体验区补全** (`docs/tools.html`)
  - 新增 6 个缺失的演示卡片：EasyApply 浏览器插件、CourseDigest 智能助考、个人文件助手 Agent、小红书内容生成器、小红书图片生成器、大麦抢票助手
  - 演示体验区现完整展示全部 12 个项目

### Changed
- **Demo 链接改为相对路径** (`docs/tools.html`)
  - Demo 5（台词学习）、Demo 6（分镜视频生成）从硬编码服务器地址（`http://8.138.164.133:5000/demos/...`）改为相对路径（`demos/...`），GitHub Pages 和服务器均可直接访问

---

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