# Integrity Lab 部署日志

## 时间线

### 2026-03-11

**目标：** 完善 docs 文档 + 规划云服务器部署

**完成内容：**
1. 检查 docs 目录，发现缺少项目：
   - 20AIer-xhs（小红书图片自动化）
   - tools(不好用)/organize（智能文件夹整理）
2. 更新 tools.html，添加缺失项目
3. 修正 index.html 项目统计数字（18→14）
4. 更新 DEPLOYMENT.md 添加详细部署计划

### 2026-03-12

**目标：** 部署云服务器后端 API

**完成内容：**

#### 1. SSH 密钥配置
- 本地生成 Ed25519 密钥
- 上传公钥到服务器，实现免密登录

#### 2. 创建 server 目录（本地）
```
server/
├── app/main.py         # Flask 主程序（用户认证 + API）
├── requirements.txt    # Python 依赖
├── Dockerfile         # Docker 配置
├── docker-compose.yml # 编排配置
├── .env.example        # 环境变量示例
├── deploy.sh           # 部署脚本
└── README.md           # 部署说明
```

#### 3. 服务器部署
- 服务器：8.138.164.133（阿里云）
- 目录：/root/integrity-api/
- 安装依赖：podman-compose, flask, flask-cors, flask-sqlalchemy, flask-login, pyjwt, dashscope, gunicorn
- 启动服务：gunicorn -w 2 -b 0.0.0.0:5000

#### 4. API 功能
| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 健康检查 |
| `/api/auth/register` | POST | 用户注册（需邀请码）|
| `/api/auth/login` | POST | 用户登录 |
| `/api/tools/token-calc` | POST | Token 计算器 |

#### 5. 前端更新
- index.html：添加登录弹窗
- tools.html：添加登录弹窗 + Token 计算器调用真实 API

#### 6. 推送到 GitHub
- commit: "docs" (92 files changed)
- push 到 origin/main

### 2026-03-12 下午

**问题排查：**
- 用户无法从网页注册/登录
- 测试确认：服务器 API 正常（curl 测试成功）
- CORS 配置正确
- 数据库中已创建用户：test, lzm, test3, user999

**待解决：**
- 阿里云安全组开放 5000 端口（用户已操作）
- 浏览器访问测试

---

## 当前状态

| 项目 | 状态 |
|------|------|
| GitHub Pages | ✅ 部署完成 |
| API 服务器 | ✅ 运行中 (8.138.164.133:5000) |
| 用户注册 | ✅ API 正常 |
| 用户登录 | ✅ API 正常 |
| 前端对接 | ⚠️ 待验证 |

## 账号信息

- 测试用户：test / 123456
- 邀请码：demo2026, friend2026, test2026

## 服务器命令

```bash
# SSH 登录
ssh root@8.138.164.133

# 查看服务状态
ps aux | grep gunicorn

# 重启服务
cd /root/integrity-api
pkill gunicorn
export DASHSCOPE_API_KEY='sk-0ef56d1b3ba54a188ce28a46c54e2a24'
export SECRET_KEY='integrity-lab-2026'
gunicorn -w 2 -b 0.0.0.0:5000 app.main:app --daemon
```

## 未完成事项

- [ ] 前端登录功能测试通过
- [ ] 添加更多工具 API（PDF、多模型对比等）
- [ ] 配置进程守护（systemd）