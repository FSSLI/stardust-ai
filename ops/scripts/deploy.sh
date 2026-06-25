#!/bin/bash
星尘 AI 部署脚本
用法：./deploy.sh [dev|prod]
ENV=${1:-dev}
SERVER="123.56.146.118"
REMOTE_PATH="/opt/stardust-backend"
echo "===== 星尘 AI 部署脚本 ====="
echo "环境: 
ENV"echo"服务器:
 
SERVER"
echo ""
1. 构建前端
echo "[1/5] 构建前端..."
cd frontend/web
npm run build
cd ../..
2. 同步代码到服务器
echo "[2/5] 同步代码到服务器..."
rsync -avz --exclude=node_modules --exclude=venv --exclude=pycache 
--exclude=.git --exclude=*.db 
./ root@SERVER: REMOTE_PATH/
3. 重启后端服务
echo "[3/5] 重启后端服务..."
ssh root@SERVER"cd REMOTE_PATH && docker-compose restart backend"
4. 重启 Nginx
echo "[4/5] 重启 Nginx..."
ssh root@$SERVER "docker-compose restart nginx"
5. 健康检查
echo "[5/5] 健康检查..."
sleep 3
curl -s https://myxingchen.xyz/api/health || echo "健康检查失败，请手动检查"
echo ""
echo "===== 部署完成 ====="