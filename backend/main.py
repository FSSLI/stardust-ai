from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from app.core.database import init_db, async_engine
from app.core.config import settings
from app.routers import auth, chat, persona, journal, memory
from app.services.persona_service import persona_service
from app.services.user_service import user_service
from app.core.database import AsyncSessionLocal


async def cleanup_loop():
    """每小时清理一次超时匿名用户（24h 未活跃）"""
    while True:
        await asyncio.sleep(3600)  # 1 小时
        try:
            async with AsyncSessionLocal() as db:
                count = await user_service.cleanup_abandoned_anonymous(db, hours=24)
                if count > 0:
                    print(f"[清理] 已删除 {count} 个超时匿名用户及其数据")
        except Exception as e:
            print(f"[清理] 异常: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    print("正在初始化数据库...")
    await init_db()

    # 初始化默认人格
    async with AsyncSessionLocal() as db:
        await persona_service.init_default_personas(db)
        print("默认人格初始化完成")
        # 启动时也做一次清理
        count = await user_service.cleanup_abandoned_anonymous(db, hours=24)
        if count > 0:
            print(f"[清理] 启动时清理了 {count} 个超时匿名用户")

    # 启动定时清理任务
    cleanup_task = asyncio.create_task(cleanup_loop())

    print("星尘 AI 后端启动成功！")
    yield

    # 关闭时清理
    cleanup_task.cancel()
    await async_engine.dispose()
    print("星尘 AI 后端已关闭")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境请限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(persona.router, prefix="/api/v1")
app.include_router(journal.router, prefix="/api/v1")
app.include_router(memory.router, prefix="/api/v1")


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "service": settings.app_name}


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)