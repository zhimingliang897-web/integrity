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
- tools.html 补充项目：
  - 20AIer-xhs 小红书图片自动化生成器
  - tools(不好用)/organize 智能文件夹整理助手

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

---

## 云服务器在线演示部署计划

### 架构设计

```
GitHub Pages (静态网页)
       ↓ fetch API
阿里云服务器 (Flask 后端)
       ↓ 调用
各 AI 模型 API (Qwen/DeepSeek/GPT)
```

### 部署步骤

#### 1. 服务器环境准备
```bash
# SSH 连接
ssh root@8.138.164.133

# 安装 Docker（如未安装）
dnf install -y docker
systemctl start docker
systemctl enable docker

# 安装 Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

#### 2. 项目目录结构
```
/root/integrity-api/
├── docker-compose.yml
├── Dockerfile
├── app/
│   ├── main.py          # Flask 主程序
│   ├── auth.py          # 用户认证
│   ├── tools/           # 各工具 API
│   │   ├── pdf.py       # PDF 工具
│   │   ├── vision.py    # 图文互转
│   │   ├── compare.py   # 多模型对比
│   │   └── debate.py    # AI 辩论
│   └── requirements.txt
├── config/
│   └── config.yaml      # API Keys 配置
└── data/
    └── users.db         # SQLite 用户数据库
```

#### 3. 核心功能 API 设计

| 功能 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 用户登录 | `/api/auth/login` | POST | 用户名+密码 |
| 用户注册 | `/api/auth/register` | POST | 需邀请码 |
| PDF 合并 | `/api/tools/pdf/merge` | POST | 上传多文件 |
| PDF 转图片 | `/api/tools/pdf/to-images` | POST | 上传 PDF |
| 图文互转 | `/api/tools/vision` | POST | 图片→提示词 |
| 多模型对比 | `/api/tools/compare` | POST | 问题→多模型回答 |
| AI 辩论 | `/api/tools/debate` | POST | SSE 流式输出 |

#### 4. 前端对接修改

在 `tools.html` 中，将模拟数据替换为真实 API 调用：

```javascript
// 示例：多模型对比
const API_BASE = 'http://8.138.164.133:5000';

async function callCompareAPI(question) {
    const response = await fetch(`${API_BASE}/api/tools/compare`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ question })
    });
    return response.json();
}
```

#### 5. 安全措施

- [x] 用户登录验证（JWT Token）
- [x] 邀请码注册机制
- [x] API 请求频率限制
- [x] CORS 配置（仅允许 GitHub Pages 域名）
- [x] API Key 环境变量注入

#### 6. Nginx 反向代理（可选）

```nginx
server {
    listen 80;
    server_name api.integrity-lab.com;  # 如有域名

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 待完成
- [x] 搭建 Flask 后端框架
- [x] 实现用户认证系统
- [x] 前端对接真实 API（Token 计算、用户登录）
- [ ] 开发更多工具 API（PDF、图文互转、多模型对比）
- [ ] 配置 HTTPS（如有域名）
- [ ] 设置进程守护（systemd/supervisor）

---

## 2026-03-12 部署完成

### 已完成
- [x] SSH 密钥配置（免密登录）
- [x] 安装 podman-compose / pip 依赖
- [x] 上传代码到 /root/integrity-api/
- [x] 配置 DASHSCOPE_API_KEY
- [x] 启动 gunicorn 服务（端口 5000）
- [x] 用户注册/登录 API 测试通过
- [x] 外部访问测试通过
- [x] 前端添加登录功能

### API 测试命令
```bash
# 健康检查
curl http://8.138.164.133:5000/

# 注册用户（需要邀请码）
curl -X POST http://8.138.164.133:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"123456","invite_code":"demo2026"}'

# 登录
curl -X POST http://8.138.164.133:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"123456"}'

# Token 计算
curl -X POST http://8.138.164.133:5000/api/tools/token-calc \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-plus","lang":"zh","chars":100}'
```

### 服务器管理命令
```bash
# SSH 登录
ssh root@8.138.164.133

# 查看服务状态
ps aux | grep gunicorn

# 重启服务
cd /root/integrity-api && pkill gunicorn && gunicorn -w 2 -b 0.0.0.0:5000 app.main:app --daemon

# 查看日志
cat /root/integrity-api/gunicorn.error.log
```

### 邀请码
- demo2026
- friend2026
- test2026