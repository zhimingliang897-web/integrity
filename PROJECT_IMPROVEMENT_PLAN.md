# Integrity Lab 项目改进任务文档

**文档版本**: v1.0  
**创建日期**: 2026-03-13  
**状态**: 待执行  
**优先级**: P0 (紧急安全修复)

---

## 📋 执行摘要

本文档记录了 Integrity Lab 项目当前存在的问题和完整的改进方案。项目是一个AI工具集合平台，包含前端（GitHub Pages）和后端（Flask API）。经过全面代码审查，发现了**20类主要问题**，其中包括**6个严重安全隐患**需要立即处理。

**关键发现**:
- 🚨 服务器SSH密码和API Key在代码中明文暴露
- 🚨 敏感信息已提交到Git历史记录
- ⚠️ 代码中存在大量重复和配置混乱
- ⚠️ 缺少测试、文档和监控机制

---

## 📊 当前项目状况

### 项目概况

```
项目名称: Integrity Lab
项目类型: AI工具集合平台
技术栈:
  - 前端: HTML + CSS + Vanilla JavaScript
  - 后端: Flask + SQLAlchemy + JWT
  - AI: Qwen, DeepSeek, GPT-4o
  - 部署: GitHub Pages + 阿里云ECS + Gunicorn
  
代码规模:
  - 14+ 独立AI工具
  - 前端页面: 20+ HTML文件
  - 后端API: 7个Blueprint模块
  - 总代码量: ~15,000+ 行
```

### 部署架构

```
┌─────────────────────────────────────────────────────────┐
│  GitHub Pages (前端)                                     │
│  https://zhimingliang897-web.github.io/integrity/       │
└────────────────────┬────────────────────────────────────┘
                     │ AJAX/Fetch
                     ↓
┌─────────────────────────────────────────────────────────┐
│  阿里云ECS (后端API)                                     │
│  IP: 8.138.164.133:5000                                 │
│  Gunicorn (2 workers, 120s timeout)                     │
│  Flask + SQLAlchemy + JWT                               │
└─────────────────────────────────────────────────────────┘
```

### 最近修复记录

**2026-03-13 已完成**:
- ✅ 修复AI辩论赛按钮点击失败问题
- ✅ 添加fetch请求超时控制(60秒)
- ✅ 改进错误处理和提示信息
- ✅ 增加gunicorn超时时间到120秒

---

## 🔍 问题清单

### 🚨 P0 - 严重安全问题（立即修复）

#### 1. 硬编码的服务器密码

**问题描述**:
- 文件: `docs/server/deploy_ssh.py:8`
- 内容: `PASSWORD = '15232735822Aa'`
- 影响: 服务器完全暴露，任何人都可以SSH登录

**修复优先级**: 🔴 P0 - 立即修复

---

#### 2. 硬编码的API Key

**问题描述**:
多个文件中硬编码了通义千问API Key:
- `docs/server/app/tools/video_maker.py:43`
- `docs/server/app/tools/image_prompt.py:32`
- `docs/server/app/tools/ai_compare.py:21`
- `docs/server/app/tools/dialogue_learning.py:52`
- `docs/server/deploy_ssh.py:73`

**影响范围**:
- API Key泄露可能导致额外费用
- 恶意使用可能导致账号被封禁

**修复优先级**: 🔴 P0 - 立即修复

---

#### 3. Git历史中的敏感信息

**问题描述**:
虽然`.gitignore`配置了忽略`.env`文件，但硬编码的密码和API Key已经提交到Git历史中。

**影响范围**:
- 即使删除当前代码中的敏感信息，历史记录仍然可访问
- 公开仓库意味着任何人都可以查看历史

**修复优先级**: 🔴 P0 - 立即修复

---

#### 4. 服务器IP地址广泛暴露

**问题描述**:
在67个文件中硬编码了服务器IP `8.138.164.133`

**影响范围**:
- 服务器IP暴露，容易成为攻击目标
- 更换服务器需要修改大量文件

**修复优先级**: 🔴 P0 - 立即修复

---

#### 5. JWT Secret Key管理不当

**问题描述**:
多个工具文件中有fallback默认值: `'integrity-lab-secret-key-2026'`

**影响范围**:
- 弱密钥可能被暴力破解
- 默认值在代码中可见

**修复优先级**: 🔴 P0 - 立即修复

---

#### 6. 邀请码系统弱

**问题描述**:
邀请码简单且可预测: `demo2026`, `test2026`, `friend2026`

**影响范围**:
- 在代码中可见，任何人都可以注册

**修复优先级**: 🟠 P1 - 尽快修复

---

### ⚠️ P1 - 安全重要问题（尽快修复）

#### 7. CORS配置过于宽松
#### 8. 文件上传安全问题
#### 9. 错误信息泄露
#### 10. 缺少请求速率限制

---

### 🟡 P2 - 代码质量问题（计划修复）

#### 11. 大量重复代码
- `require_token`装饰器在7个文件中重复定义

#### 12. 配置管理混乱
- 环境变量、硬编码、默认值混用

#### 13. 缺少输入验证
#### 14. 错误处理不完善

---

### 🔧 P2 - 部署和运维问题

#### 15. 部署脚本问题
#### 16. 环境变量管理不当
#### 17. 日志管理不足
#### 18. 缺少监控和告警

---

### 🟢 P3 - 文档和测试问题

#### 19. API文档缺失
#### 20. 测试和CI/CD缺失

---

## 🎯 改进方案

### 阶段一：紧急安全修复（1-2天）

#### 任务1.1: 更改服务器密码 🔴

**步骤**:
1. SSH登录服务器
2. 执行 `passwd` 命令更改root密码
3. 使用强密码（建议使用密码管理器生成）
4. 更新本地记录（不要提交到Git）

**验证**:
```bash
ssh root@8.138.164.133  # 使用新密码登录
```

---

#### 任务1.2: 轮换API Key 🔴

**步骤**:
1. 登录阿里云控制台
2. 生成新的DASHSCOPE_API_KEY
3. 在服务器上更新环境变量
4. 删除旧的API Key

---

#### 任务1.3: 清理Git历史中的敏感信息 🔴

**步骤**:
1. 备份仓库
2. 使用BFG Repo-Cleaner清理

```bash
# 安装BFG
brew install bfg  # Mac

# 克隆镜像
git clone --mirror https://github.com/zhimingliang897-web/integrity.git

# 创建passwords.txt文件
cat > passwords.txt << EOF
15232735822Aa
sk-0ef56d1b3ba54a188ce28a46c54e2a24
integrity-lab-secret-key-2026
EOF

# 清理敏感信息
bfg --replace-text passwords.txt integrity.git
cd integrity.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 强制推送（需要团队确认）
git push --force
```

**⚠️ 警告**: 强制推送会改写历史，需要所有协作者重新克隆仓库

---

#### 任务1.4: 移除代码中的硬编码敏感信息 🔴

**需要修改的文件**:

1. **删除deploy_ssh.py中的密码**:
```python
# docs/server/deploy_ssh.py
PASSWORD = os.environ.get('SSH_PASSWORD')
if not PASSWORD:
    raise ValueError("请设置SSH_PASSWORD环境变量")
```

2. **移除所有API Key的默认值**:
```python
# 修改以下文件:
# - docs/server/app/tools/video_maker.py:43
# - docs/server/app/tools/image_prompt.py:32
# - docs/server/app/tools/ai_compare.py:21
# - docs/server/app/tools/dialogue_learning.py:52

DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY')
if not DASHSCOPE_API_KEY:
    raise ValueError("DASHSCOPE_API_KEY environment variable is required")
```

3. **移除JWT Secret的默认值**:
```python
# 修改所有工具文件中的:
secret = flask.current_app.config.get('SECRET_KEY')
if not secret:
    raise ValueError("SECRET_KEY not configured")
```

---

#### 任务1.5: 使用域名替代IP地址 🔴

**步骤**:

1. **配置域名解析**:
   - 将 `api.liangyiren.top` 解析到 `8.138.164.133`
   - 配置SSL证书（Let's Encrypt）

2. **创建配置文件**:
```javascript
// docs/assets/js/config.js
const CONFIG = {
    API_BASE: window.location.hostname === 'localhost' 
        ? 'http://localhost:5000'
        : 'https://api.liangyiren.top',
    
    isDevelopment: window.location.hostname === 'localhost'
};

window.APP_CONFIG = CONFIG;
```

3. **批量替换硬编码IP**:
```bash
# 在所有HTML和JS文件中替换
find docs -type f \( -name "*.html" -o -name "*.js" \) -exec sed -i '' 's|http://8.138.164.133:5000|https://api.liangyiren.top|g' {} +
```

---

### 阶段二：代码重构和质量改进（3-5天）

#### 任务2.1: 提取公共代码

**创建公共认证模块**: `docs/server/app/auth.py`

**创建公共配置模块**: `docs/server/app/config.py`

**创建错误处理模块**: `docs/server/app/errors.py`

---

#### 任务2.2: 添加输入验证

**创建验证器模块**: `docs/server/app/validators.py`

---

#### 任务2.3: 添加请求速率限制

```bash
# 安装依赖
pip install Flask-Limiter

# 在main.py中配置
from flask_limiter import Limiter
limiter = Limiter(app=app, key_func=get_remote_address)
```

---

### 阶段三：部署和运维改进（2-3天）

#### 任务3.1: 配置systemd服务

**创建服务文件**: `/etc/systemd/system/integrity-api.service`

**创建.env文件**: `/root/integrity-api/server/.env`

```bash
SECRET_KEY=<生成的强密钥>
DASHSCOPE_API_KEY=<新的API Key>
INVITE_CODES=<新的邀请码>
```

**启动服务**:
```bash
systemctl daemon-reload
systemctl start integrity-api
systemctl enable integrity-api
```

---

#### 任务3.2: 配置Nginx反向代理和SSL

**安装Nginx和Certbot**:
```bash
apt install nginx certbot python3-certbot-nginx
```

**配置SSL证书**:
```bash
certbot --nginx -d api.liangyiren.top
```

---

#### 任务3.3: 配置日志和监控

**结构化日志**:
```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
```

---

### 阶段四：文档和测试（3-5天）

#### 任务4.1: 添加API文档

使用Flask-RESTX或Flask-Swagger生成API文档

#### 任务4.2: 添加单元测试

使用pytest编写测试用例

#### 任务4.3: 配置CI/CD

使用GitHub Actions自动化测试和部署

---

## 📅 实施时间表

| 阶段 | 任务 | 预计时间 | 优先级 |
|------|------|----------|--------|
| 阶段一 | 紧急安全修复 | 1-2天 | P0 🔴 |
| 阶段二 | 代码重构 | 3-5天 | P1-P2 🟠 |
| 阶段三 | 部署改进 | 2-3天 | P2 🟡 |
| 阶段四 | 文档测试 | 3-5天 | P3 🟢 |
| **总计** | **全部任务** | **9-15天** | - |

---

## ✅ 验收标准

### 阶段一完成标准:
- [ ] 服务器密码已更改
- [ ] API Key已轮换
- [ ] Git历史已清理
- [ ] 代码中无硬编码敏感信息
- [ ] 使用域名访问API
- [ ] 所有功能正常运行

### 阶段二完成标准:
- [ ] 公共代码已提取
- [ ] 错误处理统一
- [ ] 输入验证完善
- [ ] 速率限制已添加
- [ ] 代码审查通过

### 阶段三完成标准:
- [ ] systemd服务运行正常
- [ ] SSL证书配置成功
- [ ] 日志系统工作正常
- [ ] 监控告警已配置

### 阶段四完成标准:
- [ ] API文档完整
- [ ] 测试覆盖率>70%
- [ ] CI/CD流程正常

---

## 📞 联系和支持

如有问题，请：
- 提交GitHub Issue
- 查看项目文档
- 联系项目维护者

---

## 📝 变更日志

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-03-13 | v1.0 | 初始版本，完成项目审查和改进方案 |

---

**文档结束**
