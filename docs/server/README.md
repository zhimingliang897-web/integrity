# Integrity Lab API Server

**本地备份 | 云端部署方案**

这是 Integrity Lab 的后端 API 服务器，为 GitHub Pages 托管的前端提供认证和工具功能。

> **重要说明**：本目录是代码备份，实际运行在云端服务器 `8.138.164.133:5000`

---

## 📋 目录结构

```
docs/server/
├── app/
│   ├── main.py              # Flask 主入口
│   ├── tools/
│   │   ├── __init__.py
│   │   └── pdf.py           # PDF 工具集 Blueprint
├── data/
│   └── users.db             # SQLite 用户数据库（自动创建）
├── requirements.txt         # Python 依赖
├── deploy.sh                # 部署脚本
├── docker-compose.yml       # Docker 部署配置
├── Dockerfile               # Docker 镜像
├── .env.example             # 环境变量示例
├── SETUP_HTTPS.md           # HTTPS 配置指南
└── README.md                # 本文档
```

---

## 🚀 快速开始

### 本地开发

1. **安装依赖**
```bash
cd docs/server
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，设置必要的环境变量
```

3. **运行服务器**
```bash
python -m app.main
# 或
gunicorn -w 2 -b 0.0.0.0:5000 app.main:app
```

4. **测试 API**
```bash
curl http://localhost:5000/
# 应返回: {"status":"ok","service":"Integrity Lab API","version":"2.0.0"}
```

---

## ☁️ 云端部署（当前生产环境）

### 服务器信息
- **主机**: 8.138.164.133
- **端口**: 5000
- **域名**: api.liangyiren.top
- **运行方式**: Gunicorn + Systemd
- **部署路径**: `/root/integrity-api/server`

### 部署步骤

#### 1. 连接服务器
```bash
ssh root@8.138.164.133
```

#### 2. 更新代码
```bash
cd ~/integrity-api/server

# 方式一：使用 Git（推荐）
git pull origin main

# 方式二：手动上传
# 在本地执行：
scp -r docs/server/* root@8.138.164.133:/root/integrity-api/server/
```

#### 3. 安装/更新依赖
```bash
cd ~/integrity-api/server
pip install -r requirements.txt
```

#### 4. 配置环境变量

**必需的环境变量：**
- `SECRET_KEY`: JWT 密钥（默认: integrity-lab-secret-key-2026）
- `INVITE_CODES`: 注册邀请码，逗号分隔（默认: demo2026,test2026,friend2026）
- `DASHSCOPE_API_KEY`: 阿里云 DashScope API 密钥（可选，用于 AI 功能）

#### 5. 重启服务
```bash
# 查看当前运行的进程
ps aux | grep gunicorn

# 停止旧进程
pkill gunicorn

# 启动新进程
gunicorn -w 2 -b 0.0.0.0:5000 app.main:app --daemon \
  --chdir /root/integrity-api/server \
  --error-logfile /root/integrity-api/server/gunicorn.error.log \
  --access-logfile /root/integrity-api/server/gunicorn.access.log \
  --env SECRET_KEY=integrity-lab-secret-2026 \
  --env DASHSCOPE_API_KEY=sk-0ef56d1b3ba54a188ce28a46c54e2a24 \
  --env INVITE_CODES=demo2026,friend2026,test2026
```

#### 6. 验证部署
```bash
# 测试健康检查
curl http://localhost:5000/
# 应返回: {"status":"ok","service":"Integrity Lab API","version":"2.0.0","tools":["pdf","token-calc"]}

# 测试外网访问
curl https://api.liangyiren.top/
```

#### 7. 查看日志
```bash
# Gunicorn 日志
tail -f ~/integrity-api/server/gunicorn.error.log
tail -f ~/integrity-api/server/gunicorn.access.log
```

---

## 🔧 API 端点

### 认证相关
| 接口 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/auth/register` | POST | 用户注册（需要邀请码） | 否 |
| `/api/auth/login` | POST | 用户登录 | 否 |
| `/api/auth/verify` | GET | 验证 Token | 是 |

### 工具相关
| 接口 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/tools/token-calc` | POST | Token 消耗计算器 | 否 |
| `/api/tools/pdf/info` | POST | 获取 PDF 信息 | 是 |
| `/api/tools/pdf/images_to_pdf` | POST | 图片转 PDF | 是 |
| `/api/tools/pdf/merge` | POST | 合并 PDF | 是 |
| `/api/tools/pdf/remove_pages` | POST | 删除页面 | 是 |
| `/api/tools/pdf/insert` | POST | 插入 PDF | 是 |
| `/api/tools/pdf/reorder` | POST | 页面重排 | 是 |
| `/api/tools/pdf/normalize` | POST | 统一尺寸 | 是 |
| `/api/tools/pdf/to_images` | POST | PDF 转图片 | 是 |
| `/api/tools/pdf/download/<filename>` | GET | 下载文件 | 否 |

### 使用示例

**注册：**
```bash
curl -X POST https://api.liangyiren.top/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "123456", "invite_code": "demo2026"}'
```

**登录：**
```bash
curl -X POST https://api.liangyiren.top/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "123456"}'
```

**使用 PDF 工具（需要 Token）：**
```bash
curl -X POST https://api.liangyiren.top/api/tools/pdf/info \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "pdf=@test.pdf"
```

---

## 📦 依赖说明

```txt
Flask==3.0.0              # Web 框架
Flask-CORS==4.0.0         # 跨域支持
Flask-SQLAlchemy==3.1.1   # ORM
PyJWT==2.8.0              # JWT 认证
pypdf==3.17.0             # PDF 处理
Pillow==10.1.0            # 图片处理
PyMuPDF==1.23.8           # PDF 转图片
gunicorn==21.2.0          # 生产服务器
```

---

## 🔐 安全注意事项

1. **密钥管理**
   - 生产环境必须修改 `SECRET_KEY`
   - 不要将密钥提交到 Git

2. **邀请码**
   - 定期更换邀请码
   - 通过环境变量配置

3. **文件上传**
   - 限制文件大小：100MB
   - 临时文件自动清理

4. **HTTPS**
   - 生产环境必须使用 HTTPS
   - 参考 `SETUP_HTTPS.md` 配置 SSL 证书

---

## 🐛 故障排查

### 服务无法启动
```bash
# 检查端口占用
lsof -i:5000
netstat -tulpn | grep 5000

# 检查进程
ps aux | grep gunicorn
ps aux | grep python

# 杀掉占用进程
pkill gunicorn
```

### 数据库问题
```bash
# 重新初始化数据库
cd ~/integrity-api/server
python -c "from app.main import app, db; app.app_context().push(); db.create_all()"

# 或删除数据库重建
rm -f data/users.db
# 重启服务后会自动创建
```

### 依赖问题
```bash
# 重新安装依赖
pip install --upgrade -r requirements.txt

# 检查 Python 版本（需要 3.8+）
python --version
```

### 防火墙问题
```bash
# 检查防火墙状态
firewall-cmd --list-all

# 开放 5000 端口
firewall-cmd --permanent --add-port=5000/tcp
firewall-cmd --reload

# 或在阿里云控制台配置安全组
```

---

## 📝 开发说明

### 添加新工具

1. 在 `app/tools/` 下创建新的 Blueprint 文件
2. 在 `app/main.py` 中注册 Blueprint
3. 使用 `@require_token` 装饰器保护需要认证的路由

**示例：**
```python
# app/tools/my_tool.py
from flask import Blueprint, request, jsonify
from app.tools.pdf import require_token  # 复用认证装饰器

my_tool_bp = Blueprint('my_tool', __name__, url_prefix='/api/tools/my_tool')

@my_tool_bp.route('/process', methods=['POST'])
@require_token
def process():
    # 你的逻辑
    return jsonify({'success': True})
```

```python
# app/main.py
from app.tools.my_tool import my_tool_bp
app.register_blueprint(my_tool_bp)
```

### 代码同步流程

1. **本地修改代码** → `docs/server/`
2. **测试本地运行** → `python -m app.main`
3. **上传到服务器** → `scp` 或 `git push`
4. **服务器拉取代码** → `git pull`
5. **重启服务** → `pkill gunicorn && gunicorn ...`

---

## 📞 联系方式

- **GitHub**: https://github.com/zhimingliang897-web/integrity
- **问题反馈**: 提交 GitHub Issue

---

## 📄 许可证

本项目开源，仅供学习使用。
