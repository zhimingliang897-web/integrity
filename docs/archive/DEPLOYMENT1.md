# Integrity Lab 部署说明

## GitHub Pages (前端网页)

访问地址：https://zhimingliang897-web.github.io/integrity/

源码提交后自动部署，约 1-3 分钟生效。

## 阿里云服务器 (后端 API)

**服务器：** 8.138.164.133

### SSH 登录
```bash
ssh root@8.138.164.133
```

### 服务管理
```bash
# 查看状态
ps aux | grep gunicorn

# 重启服务
cd /root/integrity-api
pkill gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 app.main:app --daemon --error-logfile gunicorn.error.log --capture-output

# 查看日志
cat /root/integrity-api/gunicorn.error.log
```

### API 端点
| 接口 | 地址 |
|------|------|
| 健康检查 | http://8.138.164.133:5000/ |
| 用户注册 | http://8.138.164.133:5000/api/auth/register |
| 用户登录 | http://8.138.164.133:5000/api/auth/login |
| Token 计算 | http://8.138.164.133:5000/api/tools/token-calc |

### 邀请码
- demo2026
- friend2026
- test2026

## ⚠️ 注意

- **不要** 将 `.env` 文件推送到 GitHub（已添加 .gitignore）
- API Key 存储在服务器 `/root/integrity-api/.env` 中
- 服务器密码：`15232735822Aa`（已配置 SSH 密钥，可免密登录）