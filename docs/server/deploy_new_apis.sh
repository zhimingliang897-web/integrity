#!/bin/bash
# 部署新的 API Blueprint 到服务器
# 服务器: 8.138.164.133
# 路径: /root/integrity-api/server

set -e

echo "=== 开始部署新的 API Blueprint ==="

# 1. 进入项目目录
cd /root/integrity-api/server
echo "当前目录: $(pwd)"

# 2. 拉取最新代码
echo "正在拉取最新代码..."
git pull origin main

# 3. 检查新文件
echo "检查新文件..."
ls -la app/tools/

# 4. 安装新依赖
echo "正在安装新依赖..."
pip install openai pdfplumber beautifulsoup4 edge-tts pillow pypdf requests -q

# 5. 检查依赖安装
echo "检查依赖..."
python -c "import openai; print(f'openai: {openai.__version__}')"
python -c "import pdfplumber; print('pdfplumber: OK')"
python -c "import bs4; print('beautifulsoup4: OK')"
python -c "import edge_tts; print('edge-tts: OK')"

# 6. 停止旧服务
echo "停止旧的 Gunicorn 进程..."
pkill gunicorn || true

# 7. 启动新服务
echo "启动新的 Gunicorn 服务..."
gunicorn -w 2 -b 0.0.0.0:5000 app.main:app --daemon \
  --chdir /root/integrity-api/server \
  --error-logfile /root/integrity-api/server/gunicorn.error.log \
  --access-logfile /root/integrity-api/server/gunicorn.access.log \
  --env SECRET_KEY=integrity-lab-secret-2026 \
  --env DASHSCOPE_API_KEY=sk-0ef56d1b3ba54a188ce28a46c54e2a24 \
  --env INVITE_CODES=demo2026,friend2026,test2026

# 8. 等待服务启动
sleep 3

# 9. 验证服务
echo "验证服务..."
curl -s http://localhost:5000/ | python -m json.tool

# 10. 检查新 API 端点
echo "检查新的 API 端点..."
echo "AI Compare:"
curl -s http://localhost:5000/api/tools/ai-compare/providers | python -m json.tool

echo "AI Debate:"
curl -s http://localhost:5000/api/tools/ai-debate/debaters | python -m json.tool

echo "=== 部署完成 ==="