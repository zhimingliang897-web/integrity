#!/bin/bash
# 部署脚本 - 在服务器上运行

set -e

echo "=== Integrity Tools 部署脚本 ==="

# 1. 停止旧服务
echo "[1/6] 停止旧服务..."
pkill -f gunicorn 2>/dev/null || true
systemctl stop integrity-tools 2>/dev/null || true

# 2. 安装依赖
echo "[2/6] 安装依赖..."
pip install -r requirements.txt -q

# 3. 初始化数据库
echo "[3/6] 初始化数据库..."
python init_db.py

# 4. 创建输出目录
echo "[4/6] 创建必要目录..."
mkdir -p app/tools/debate/output/audio
mkdir -p app/tools/lines/data

# 5. 安装systemd服务
echo "[5/6] 安装systemd服务..."
cp integrity-tools.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable integrity-tools

# 6. 启动服务
echo "[6/6] 启动服务..."
systemctl start integrity-tools

# 检查状态
sleep 3
systemctl status integrity-tools --no-pager

echo ""
echo "=== 部署完成 ==="
echo "访问地址: http://8.138.164.133:5000"
echo ""
echo "常用命令:"
echo "  查看状态: systemctl status integrity-tools"
echo "  查看日志: journalctl -u integrity-tools -f"
echo "  重启服务: systemctl restart integrity-tools"