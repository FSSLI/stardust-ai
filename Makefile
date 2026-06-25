.PHONY: help dev build test deploy clean
help:
@echo "星尘 AI 项目命令"
@echo "  make dev     - 启动本地开发环境"
@echo "  make build   - 构建 Docker 镜像"
@echo "  make test    - 运行测试"
@echo "  make deploy  - 部署到服务器"
@echo "  make clean   - 清理构建产物"
dev:
@echo "启动后端..."
cd backend && uvicorn main:app --reload --port 8000 &
@echo "启动前端..."
cd frontend/web && npm run dev
build:
docker-compose build
test:
cd backend && pytest
deploy:
./ops/scripts/deploy.sh prod
clean:
rm -rf frontend/web/dist
rm -rf backend/pycache
rm -rf backend/**/pycache