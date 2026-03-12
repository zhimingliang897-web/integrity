#!/bin/bash
# Integrity Lab API 部署脚本
# 直接复制到服务器执行：bash deploy.sh

set -e

echo "=== Integrity Lab API 部署脚本 ==="

# 1. 安装 Docker
echo "[1/5] 检查 Docker..."
if ! command -v docker &> /dev/null; then
    echo "安装 Docker..."
    dnf install -y docker
    systemctl start docker
    systemctl enable docker
fi
docker --version

# 2. 安装 Docker Compose
echo "[2/5] 检查 Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "安装 Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi
docker-compose --version

# 3. 创建项目目录
echo "[3/5] 创建项目目录..."
mkdir -p /root/integrity-api/app
mkdir -p /root/integrity-api/data
cd /root/integrity-api

# 4. 创建环境变量文件
echo "[4/5] 创建配置文件..."
cat > .env << 'ENVEOF'
SECRET_KEY=integrity-lab-secret-$(date +%s)
DASHSCOPE_API_KEY=请替换为你的API_KEY
INVITE_CODES=demo2026,friend2026
ENVEOF

echo ""
echo "============================================"
echo "请编辑 .env 文件，填入你的 DASHSCOPE_API_KEY"
echo "执行: nano /root/integrity-api/.env"
echo "============================================"
echo ""

# 5. 提示后续步骤
echo "[5/5] 后续步骤..."
echo ""
echo "现在需要上传代码文件，在本地执行："
echo "  scp -r E:\\integrity\\server\\* root@8.138.164.133:/root/integrity-api/"
echo ""
echo "然后回到服务器执行："
echo "  cd /root/integrity-api"
echo "  nano .env  # 填入 API Key"
echo "  docker-compose up -d"
echo ""
echo "验证服务："
echo "  curl http://localhost:5000/"
echo ""

echo "=== 脚本执行完成 ==="