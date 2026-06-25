# 星尘 Stardust AI 陪伴系统

> 一个温暖、有记忆、可切换人格的 AI 陪伴应用。

## 项目简介

星尘（Stardust）是一个基于 DeepSeek API 的 AI 陪伴系统，支持：
- 💬 流式对话（打字机效果）
- 🧠 上下文记忆（SQLite 存储）
- 🎭 多人格切换
- 📔 手帐与记录

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue3 + Vite + TailwindCSS |
| 后端 | FastAPI + Python 3.11 |
| AI | DeepSeek API (SSE 流式) |
| 数据库 | SQLite (开发) → PostgreSQL (生产) |
| 缓存 | Redis |
| 部署 | Docker + Nginx + 阿里云 ECS |

## 快速开始

```bash
# 1. 克隆项目
git clone <repo-url>
cd stardust-ai

# 2. 启动后端
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# 3. 启动前端
cd ../frontend/web
npm install
npm run dev
项目结构
plain
stardust-ai/
├── frontend/          # 前端应用
├── backend/           # FastAPI 后端服务
├── ai-models/         # 提示词模板与人格配置
├── ops/               # 部署与运维配置
└── docs/              # 项目文档
文档索引
项目概述
功能清单
系统架构
数据库设计
API 设计规范
许可证
MIT License