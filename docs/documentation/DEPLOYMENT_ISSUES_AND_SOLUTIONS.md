# Integrity Lab 部署问题与解决方案

**文档更新时间：2026-03-13**

---

## 📋 当前状态总结

### ✅ 已完成的工作

1. **代码统一**
   - 本地、GitHub、服务器三端代码已完全同步
   - 最新提交：`2c5d075` - 前端错误处理和 SSE 优化

2. **服务器部署**
   - 后端 API：运行在 `127.0.0.1:5000`（Gunicorn + Flask）
   - Nginx：运行在端口 80/443/8000
   - 前端文件：部署在 `/var/www/integrity`
   - 代码仓库：`/root/integrity-github`

3. **Nginx 配置优化**
   - 端口 8000：统一提供前端静态文件 + API 反向代理
   - 端口 443：HTTPS 配置（域名被劫持，暂时无法使用）
   - 配置文件：`/etc/nginx/conf.d/integrity-web.conf`

4. **前端优化**
   - AI 辩论赛：修复 SSE 事件处理，避免 undefined
   - 台词学习：增强错误处理和空数据防护
   - 视频生成：改进轮询错误处理
   - 图文互转：删除模拟函数，连接真实 API

---

## 🚨 核心问题：域名被劫持

### 问题描述

域名 `api.liangyiren.top` 在外网访问时被劫持或被墙：

```bash
# 现象 1：HTTPS 连接被重置
$ curl https://api.liangyiren.top/
curl: (35) Recv failure: Connection reset by peer

# 现象 2：HTTP 返回 403，Server 是 "Beaver"（不是 nginx）
$ curl -I http://api.liangyiren.top/
HTTP/1.1 403 Forbidden
Server: Beaver

# 现象 3：直接用 IP 访问正常
$ curl -k -I https://8.138.164.133/
HTTP/2 200 
server: nginx/1.23.1

# 现象 4：服务器内部访问正常
$ ssh root@8.138.164.133
$ curl https://api.liangyiren.top/
{"service":"Integrity Lab API","status":"ok"}
```

### 技术分析

1. **DNS 解析正常**：`api.liangyiren.top` → `8.138.164.133`
2. **SSL 证书有效**：Let's Encrypt 签发，有效期至 2026-06-10
3. **端口开放正常**：443 端口可以连接（`nc -zv 8.138.164.133 443` 成功）
4. **TLS 握手失败**：在 Client Hello 之后连接被重置
5. **HTTP 被劫持**：返回的 Server 头是 "Beaver"，不是 nginx

**结论**：域名在 GFW 或运营商层面被劫持，HTTP/HTTPS 请求被重定向到其他服务器。

---

## 💡 解决方案

### 方案 1：开放端口 8000（推荐，最快）

**优点**：
- 无需更换域名
- 配置已完成，只需开放端口
- 前后端同源，无跨域问题

**步骤**：

1. 登录阿里云控制台
2. 进入 ECS 实例管理
3. 安全组 → 配置规则 → 添加入方向规则
   - 端口范围：`8000/8000`
   - 授权对象：`0.0.0.0/0`
   - 协议：TCP
4. 保存后立即生效

**访问地址**：
```
http://8.138.164.133:8000/
http://8.138.164.133:8000/demos/ai-debate.html
http://8.138.164.133:8000/tools.html
```

**API 调用**：
```javascript
// 前端代码无需修改，自动使用同源 API
const API_BASE = window.location.origin; // http://8.138.164.133:8000
fetch(`${API_BASE}/api/tools/ai-compare/providers`)
```

---

### 方案 2：注册新域名

**优点**：
- 更专业的访问方式
- 可以使用 HTTPS

**步骤**：

1. 注册新域名（建议使用国外域名商，如 Namecheap、Cloudflare）
2. 配置 DNS A 记录指向 `8.138.164.133`
3. 申请 SSL 证书：
   ```bash
   certbot certonly --nginx -d newdomain.com
   ```
4. 更新 Nginx 配置：
   ```nginx
   server {
       listen 443 ssl http2;
       server_name newdomain.com;
       ssl_certificate /etc/letsencrypt/live/newdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/newdomain.com/privkey.pem;
       # ... 其他配置
   }
   ```

---

### 方案 3：使用 Cloudflare CDN

**优点**：
- 可以绕过 GFW
- 免费 SSL 证书
- CDN 加速

**步骤**：

1. 注册 Cloudflare 账号
2. 添加域名 `liangyiren.top`
3. 修改域名 NS 记录到 Cloudflare
4. 在 Cloudflare 添加 A 记录：
   - 名称：`api`
   - 内容：`8.138.164.133`
   - 代理状态：已代理（橙色云朵）
5. SSL/TLS 设置：完全（严格）

---

### 方案 4：修改 hosts 文件（仅本地测试）

**仅用于本地开发测试**，不适合生产环境。

```bash
# macOS/Linux
sudo echo "8.138.164.133 api.liangyiren.top" >> /etc/hosts

# Windows (管理员权限)
echo 8.138.164.133 api.liangyiren.top >> C:\Windows\System32\drivers\etc\hosts
```

然后访问：`https://api.liangyiren.top/`（需要忽略证书警告）

---

## 📝 待完成任务清单

### P0 - 紧急（阻塞功能）

- [ ] **开放端口 8000**（阿里云安全组配置）
- [ ] 或者：注册新域名并配置
- [ ] 或者：配置 Cloudflare CDN

### P1 - 核心功能

- [ ] **测试登录认证流程**
  - 注册新用户（需要邀请码）
  - 登录已有用户
  - Token 验证和刷新
  
- [ ] **测试在线工具功能**
  - AI 多模型对比
  - AI 辩论赛（SSE 流式）
  - 图文互转
  - 台词学习（PDF 上传）
  - 视频生成

- [ ] **删除 AI 辩论赛模拟函数**
  - 当前保留作为 API 失败时的降级方案
  - 确认 API 稳定后可删除

- [ ] **完善登录状态同步**
  - Token 过期自动跳转登录
  - 刷新 Token 机制
  - 登出功能

### P2 - 优化

- [ ] 添加加载动画/骨架屏
- [ ] 优化错误提示信息
- [ ] 添加 Toast 提示
- [ ] 实现请求超时重试
- [ ] 更新 README 文档

---

## 🔧 服务器维护命令

### 检查服务状态

```bash
# SSH 登录
ssh root@8.138.164.133

# 检查 Nginx
systemctl status nginx
nginx -t
nginx -s reload

# 检查后端 API
ps aux | grep gunicorn
curl http://localhost:5000/

# 检查端口监听
netstat -tlnp | grep -E '80|443|5000|8000'

# 查看日志
tail -f /root/integrity-api/server/gunicorn.error.log
tail -f /var/log/nginx/error.log
```

### 更新代码

```bash
# 拉取最新代码
cd /root/integrity-github
git pull origin main

# 同步到部署目录
cp -rf /root/integrity-github/docs/* /var/www/integrity/

# 重启后端（如果有更新）
cd /root/integrity-api
pkill gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 --timeout 120 app.main:app --daemon \
  --error-logfile server/gunicorn.error.log \
  --access-logfile server/gunicorn.access.log
```

### 重启服务

```bash
# 重启 Nginx
nginx -s reload

# 重启后端 API
pkill gunicorn
cd /root/integrity-api
gunicorn -w 2 -b 0.0.0.0:5000 --timeout 120 app.main:app --daemon \
  --error-logfile server/gunicorn.error.log \
  --access-logfile server/gunicorn.access.log
```

---

## 📊 当前架构图

```
外网用户
    ↓
[阿里云安全组] ← 需要开放端口 8000
    ↓
[Nginx :8000]
    ├─ /          → /var/www/integrity (前端静态文件)
    ├─ /api/      → http://127.0.0.1:5000 (后端 API)
    └─ /pdf/      → http://127.0.0.1:5000 (PDF 工具)
         ↓
[Gunicorn :5000]
    └─ Flask App (integrity-api)
         └─ DashScope API (qwen3.5-plus)
```

---

## 🎯 下一步行动

1. **立即执行**：开放阿里云安全组端口 8000
2. **测试访问**：`http://8.138.164.133:8000/`
3. **测试功能**：登录 → 使用在线工具
4. **长期方案**：注册新域名或使用 Cloudflare CDN

---

*文档最后更新：2026-03-13*
