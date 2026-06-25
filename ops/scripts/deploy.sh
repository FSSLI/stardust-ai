#!/bin/bash
# 星尘 AI 一键部署脚本
set -e

SERVER="123.56.146.118"
REMOTE_PATH="/opt/stardust-ai"

echo "===== 星尘 AI 部署 ====="

# 1. 同步代码（排除 node_modules / venv / .git / 数据库）
echo "[1/4] 同步代码..."
rsync -avz \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.db' \
    --exclude='.env' \
    ../.. root@${SERVER}:${REMOTE_PATH}/

# 2. 上传 .env（单独处理，避免覆盖服务器配置）
echo "[2/4] 构建 + 启动..."
ssh root@${SERVER} "cd ${REMOTE_PATH} && docker-compose up -d --build"

# 3. 等待启动
sleep 5

# 4. 健康检查
echo "[3/4] 健康检查..."
curl -s http://${SERVER}/api/health || echo "请等待容器启动..."

echo ""
echo "===== 部署完成 ====="
echo "访问地址: http://${SERVER}"
