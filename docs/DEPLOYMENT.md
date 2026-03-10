# Integrity Lab 部署记录

## 2026-03-11

### 1. GitHub 安全问题修复
- 问题：代码中硬编码了 OpenAI API Key，推送被 GitHub 阻止
- 解决：
  - 创建 `18tokens/config_example.py` 示例文件
  - `config.py` 改为从环境变量读取 API Key
  - `.gitignore` 添加 `18tokens/config.py`
  - 使用 `git filter-branch` 重写历史移除密钥

### 2. 网页文档增强 (docs/)
- tools.html 新增交互 Demo：
  - 🎨 图文互转（模拟视觉识别效果）
  - ⚖️ 多模型对比（Qwen/DeepSeek/GPT 回答展示）
  - 🪙 Token 消耗计算器
- index.html 新增：项目统计卡片

### 3. 阿里云服务器部署后端
- 服务器：8.138.164.133 (2核2G, Alibaba Cloud Linux 8)
- 服务：Flask API 服务
- 端口：5000
- 功能：
  - `/` - 健康检查
  - `/api/login` - 用户登录/注册
  - `/api/chat` - AI 对话（调用阿里云百炼）
  - `/api/tools/token-calc` - Token 计算

### 访问地址
- 网页文档：https://zhimingliang897-web.github.io/integrity/
- API 服务：http://8.138.164.133:5000/

### 待完成
- [ ] 添加更多后端功能
- [ ] 用户认证系统完善
- [ ] 网页调用真实 API