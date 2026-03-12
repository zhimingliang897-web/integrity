# Integrity Lab API Server

部署在阿里云服务器的 Flask 后端，为 GitHub Pages 提供真实 API 服务。

## 快速部署指南

### 第一步：上传文件到服务器

在本地执行：
```bash
scp -r server root@8.138.164.133:/root/integrity-api/
```

或者手动创建目录结构：
```
/root/integrity-api/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── app/
│   └── main.py
└── data/
```

### 第二步：安装 Docker

```bash
# 更新系统
dnf update -y

# 安装 Docker
dnf install -y docker

# 启动 Docker
systemctl start docker
systemctl enable docker

# 安装 Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

### 第三步：配置环境变量

```bash
cd /root/integrity-api

# 创建 .env 文件
cat > .env << 'EOF'
SECRET_KEY=your-random-secret-key-here-change-this
DASHSCOPE_API_KEY=your-dashscope-api-key
INVITE_CODES=demo2026,friend2026,test2026
EOF

# 编辑填入你的真实 API Key
nano .env
```

### 第四步：构建并启动

```bash
cd /root/integrity-api

# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 第五步：验证服务

```bash
# 测试健康检查
curl http://localhost:5000/

# 应该返回 {"status": "ok", "service": "Integrity Lab API", "version": "1.0.0"}
```

### 第六步：配置防火墙

```bash
# 开放 5000 端口
firewall-cmd --permanent --add-port=5000/tcp
firewall-cmd --reload

# 或者使用阿里云控制台 -> 安全组 -> 添加规则
# 端口: 5000, 协议: TCP, 来源: 0.0.0.0/0
```

## API 接口说明

| 接口 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/` | GET | 健康检查 | 否 |
| `/api/auth/register` | POST | 用户注册（需邀请码） | 否 |
| `/api/auth/login` | POST | 用户登录 | 否 |
| `/api/auth/verify` | GET | 验证 Token | 是 |
| `/api/tools/token-calc` | POST | Token 计算器 | 否 |
| `/api/tools/chat` | POST | AI 对话 | 是 |

### 注册示例

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "123456", "invite_code": "demo2026"}'
```

### 登录示例

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "123456"}'
```

## 常用命令

```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 重新构建
docker-compose up -d --build
```

## 更新代码

```bash
# 1. 上传新代码
scp -r server/* root@8.138.164.133:/root/integrity-api/

# 2. 重新构建
cd /root/integrity-api
docker-compose up -d --build
```

## 故障排查

### 端口被占用
```bash
# 查看 5000 端口占用
netstat -tlnp | grep 5000

# 杀掉占用进程
kill -9 <PID>
```

### 容器无法启动
```bash
# 查看详细错误
docker-compose logs

# 进入容器调试
docker-compose exec api bash
```

### 数据库问题
```bash
# 删除数据库重建
rm -f data/users.db
docker-compose restart
```