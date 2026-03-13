# AI 辩论赛部署指南

## 部署架构

```
GitHub Pages (docs/)
  ├── demos/ai-debate.html (前端页面)
  └── assets/js/ (前端脚本)
           ↓ API调用
服务器 8.138.164.133:5000
  └── docs/server/
      ├── app/main.py (主应用)
      ├── app/tools/ai_debate.py (完整辩论引擎)
      ├── app/tools/debate_engine.py (辩论流程引擎)
      ├── app/tools/llm_client.py (LLM客户端)
      ├── Dockerfile
      └── docker-compose.yml
```

## 部署步骤

### 1. 准备 API Keys

AI 辩论赛需要多个 AI 服务商的 API Key：

- **必需**：通义千问 (QWEN_API_KEY 或 DASHSCOPE_API_KEY)
- **可选**：豆包 (DOUBAO_API_KEY)
- **可选**：Kimi (KIMI_API_KEY)
- **可选**：DeepSeek (DEEPSEEK_API_KEY)

如果只有通义千问的 API Key，系统会自动使用千问的不同模型来模拟多个辩手。

### 2. 上传代码到服务器

在本地执行（macOS/Linux）：

```bash
# 使用 rsync 上传整个 server 目录
rsync -avz --exclude='__pycache__' --exclude='*.pyc' --exclude='.env' \
  /Users/lzm/macbook_space/integrity/docs/server/ \
  root@8.138.164.133:/root/integrity-api/
```

或使用 scp：

```bash
cd /Users/lzm/macbook_space/integrity/docs/server
tar czf - . | ssh root@8.138.164.133 "cd /root/integrity-api && tar xzf -"
```

### 3. 在服务器上配置环境变量

SSH 登录服务器：

```bash
ssh root@8.138.164.133
```

创建 .env 文件：

```bash
cd /root/integrity-api
nano .env
```

填入以下内容（替换为你的实际 API Key）：

```env
SECRET_KEY=integrity-lab-secret-2026-$(date +%s)
QWEN_API_KEY=sk-your-qwen-api-key-here
DASHSCOPE_API_KEY=sk-your-dashscope-api-key-here
DOUBAO_API_KEY=your-doubao-api-key-here
KIMI_API_KEY=your-kimi-api-key-here
DEEPSEEK_API_KEY=your-deepseek-api-key-here
INVITE_CODES=demo2026,friend2026
```

保存并退出（Ctrl+X, Y, Enter）

### 4. 停止旧容器并重新构建

```bash
cd /root/integrity-api

# 停止并删除旧容器
docker-compose down

# 重新构建镜像
docker-compose build --no-cache

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 5. 验证部署

测试 API 是否正常：

```bash
# 健康检查
curl http://localhost:5000/

# 测试辩手列表
curl http://localhost:5000/api/tools/ai-debate/debaters

# 测试配置
curl http://localhost:5000/api/tools/ai-debate/config
```

### 6. 测试前端

访问：https://zhimingliang897-web.github.io/integrity/demos/ai-debate.html

1. 使用账号 `lzm` / `123456` 登录
2. 选择辩题或输入自定义辩题
3. 点击"开始辩论"
4. 观察辩论过程是否正常流式输出

## 故障排查

### 问题1：容器无法启动

```bash
# 查看容器日志
docker-compose logs api

# 检查端口占用
netstat -tlnp | grep 5000

# 如果端口被占用，停止占用进程
kill -9 $(lsof -t -i:5000)
```

### 问题2：API Key 未配置

检查 .env 文件是否正确：

```bash
cat /root/integrity-api/.env
```

确保至少配置了 QWEN_API_KEY 或 DASHSCOPE_API_KEY。

### 问题3：前端无法连接

1. 检查服务器防火墙是否开放 5000 端口
2. 检查 CORS 配置是否包含 GitHub Pages 域名
3. 在浏览器控制台查看具体错误信息

### 问题4：辩论过程中断

1. 检查 API Key 是否有效且有足够余额
2. 查看服务器日志：`docker-compose logs -f api`
3. 检查网络连接是否稳定

## 更新代码

当需要更新代码时：

```bash
# 1. 在本地上传新代码
rsync -avz --exclude='__pycache__' --exclude='*.pyc' --exclude='.env' \
  /Users/lzm/macbook_space/integrity/docs/server/ \
  root@8.138.164.133:/root/integrity-api/

# 2. 在服务器上重启服务
ssh root@8.138.164.133 "cd /root/integrity-api && docker-compose restart"
```

## 监控和维护

### 查看服务状态

```bash
docker-compose ps
```

### 查看实时日志

```bash
docker-compose logs -f api
```

### 重启服务

```bash
docker-compose restart
```

### 停止服务

```bash
docker-compose down
```

### 清理旧镜像

```bash
docker system prune -a
```

## 性能优化建议

1. **增加 Gunicorn workers**：在 Dockerfile 中修改 `-w 2` 为 `-w 4`（根据服务器CPU核心数）
2. **启用 Redis 缓存**：缓存辩手配置和常用响应
3. **配置 Nginx 反向代理**：提供 HTTPS 支持和负载均衡
4. **监控资源使用**：使用 `docker stats` 监控容器资源消耗

## 安全建议

1. **定期更新依赖**：`pip list --outdated`
2. **限制 API 调用频率**：添加 rate limiting
3. **日志审计**：定期检查访问日志
4. **备份数据库**：定期备份 `/root/integrity-api/data/users.db`

## 联系方式

如有问题，请联系：
- GitHub: https://github.com/zhimingliang897-web/integrity
- 邮箱: [你的邮箱]
