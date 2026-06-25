from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# SQLite 异步引擎
async_engine = create_async_engine(
    settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///"),
    echo=settings.debug
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


async def get_db():
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库"""
    # 确保所有模型被导入（触发 Base.metadata 注册）
    import app.models.models  # noqa: F401
    import app.models.memory  # noqa: F401
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)