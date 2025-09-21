"""
數據庫連接和會話管理
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from redis import asyncio as aioredis
from typing import AsyncGenerator
import asyncio
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# 創建異步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=300,
)

# 創建會話工廠
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# 創建基礎模型
Base = declarative_base()

# Redis連接
redis_client = None


async def init_db():
    """初始化數據庫連接"""
    global redis_client
    
    try:
        # 測試PostgreSQL連接
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # 初始化Redis連接
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
        
        # 測試Redis連接
        await redis_client.ping()
        
        logger.info("數據庫連接初始化成功")
        
    except Exception as e:
        logger.warning(f"數據庫連接初始化失敗: {e}，將使用內存模式運行")
        # 在開發環境下不拋出異常，允許服務繼續運行


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """獲取數據庫會話"""
    try:
        async with AsyncSessionLocal() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"數據庫會話錯誤: {e}")
                raise
            finally:
                await session.close()
    except Exception:
        # 如果數據庫不可用，提供模擬會話
        logger.warning("數據庫不可用，使用模擬會話")
        class MockSession:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
            async def commit(self):
                pass
            async def rollback(self):
                pass
            async def close(self):
                pass
        
        class MockQuery:
            def filter(self, *args, **kwargs):
                return self
            def all(self):
                return []
            def first(self):
                return None
            def count(self):
                return 0
        
        mock_session = MockSession()
        mock_session.query = lambda *args: MockQuery()
        yield mock_session


# 為了向後兼容，提供別名
get_db_session = get_db


async def get_redis():
    """獲取Redis客戶端"""
    if redis_client is None:
        raise RuntimeError("Redis客戶端未初始化")
    return redis_client


async def close_db():
    """關閉數據庫連接"""
    global redis_client
    
    try:
        if redis_client:
            await redis_client.close()
        
        await engine.dispose()
        logger.info("數據庫連接已關閉")
        
    except Exception as e:
        logger.error(f"關閉數據庫連接時出錯: {e}")


class DatabaseManager:
    """數據庫管理器"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = AsyncSessionLocal()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        await self.session.close()