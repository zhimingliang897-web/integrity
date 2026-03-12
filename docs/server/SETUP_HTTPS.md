# 阿里云服务器 HTTPS 配置指南

## 目标
为 `api.liangyiren.top` 配置 HTTPS，解决 GitHub Pages (HTTPS) 调用 HTTP API 的 Mixed Content 问题。

## 服务器信息
- IP: 8.138.164.133
- 系统: Alibaba Cloud Linux 8
- 当前服务: Flask API 运行在 5000 端口 (gunicorn)

## 操作步骤

### 步骤 1: SSH 登录服务器
```bash
ssh root@8.138.164.133
```

### 步骤 2: 安装 Nginx 和 Certbot
```bash
dnf install -y nginx certbot python3-certbot-nginx
```

### 步骤 3: 启动并设置 Nginx 开机自启
```bash
systemctl start nginx
systemctl enable nginx
```

### 步骤 4: 配置防火墙开放 80 和 443 端口
```bash
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

如果 firewall-cmd 命令不存在或未启用防火墙，跳过此步骤。

### 步骤 5: 创建 Nginx 反向代理配置
```bash
cat > /etc/nginx/conf.d/api.liangyiren.top.conf << 'EOF'
server {
    listen 80;
    server_name api.liangyiren.top;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
```

### 步骤 6: 测试并重载 Nginx 配置
```bash
nginx -t && systemctl reload nginx
```

预期输出:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 步骤 7: 申请 Let's Encrypt SSL 证书
```bash
certbot --nginx -d api.liangyiren.top --non-interactive --agree-tos -m your-email@example.com
```

**注意**: 将 `your-email@example.com` 替换为真实邮箱，用于接收证书到期提醒。

预期输出:
```
Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/api.liangyiren.top/fullchain.pem
Key is saved at: /etc/letsencrypt/live/api.liangyiren.top/privkey.pem
...
Deploying certificate
Successfully deployed certificate for api.liangyiren.top to /etc/nginx/conf.d/api.liangyiren.top.conf
```

### 步骤 8: 验证 HTTPS 是否生效
```bash
curl -I https://api.liangyiren.top/
```

预期输出应包含:
```
HTTP/2 200
```

### 步骤 9: 设置证书自动续期
```bash
systemctl enable certbot-renew.timer
systemctl start certbot-renew.timer
```

## 完成后需要修改的前端代码

SSL 配置成功后，需要修改以下文件:

### 1. 更新 docs/index.html 第 250 行
将:
```javascript
const API_BASE = 'http://8.138.164.133:5000';
```
改为:
```javascript
const API_BASE = 'https://api.liangyiren.top';
```

### 2. 更新 docs/tools.html (如果有 API 调用)
同样将所有 `http://8.138.164.133:5000` 替换为 `https://api.liangyiren.top`

### 3. 更新后端 CORS 配置 (server/app/main.py 第 15-19 行)
将:
```python
CORS(app, origins=[
    'https://zhimingliang897-web.github.io',
    'http://localhost:*',
    'http://127.0.0.1:*'
])
```
改为:
```python
CORS(app, origins=[
    'https://zhimingliang897-web.github.io',
    'https://liangyiren.top',
    'https://www.liangyiren.top',
    'http://localhost:*',
    'http://127.0.0.1:*'
])
```

然后在服务器上重启 gunicorn:
```bash
cd /root/integrity-api && pkill gunicorn && gunicorn -w 2 -b 0.0.0.0:5000 app.main:app --daemon
```

## 故障排查

### 如果 certbot 失败
1. 确认 DNS 解析生效: `nslookup api.liangyiren.top`
2. 确认 80 端口可访问: `curl http://api.liangyiren.top/`
3. 检查阿里云安全组是否开放 80 和 443 端口

### 如果 Nginx 无法启动
```bash
# 查看错误日志
cat /var/log/nginx/error.log

# 检查端口占用
ss -tlnp | grep -E '80|443'
```

### 检查阿里云安全组
确保安全组规则允许入站:
- TCP 80 (HTTP)
- TCP 443 (HTTPS)
