"""
統一的數據庫管理器

這個模塊提供統一的數據庫接口，支持SQLite和PostgreSQL
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Union
from pathlib import Path

# 導入SQLite適配器
from .sqlite_adapter import SQLiteAdapter, AsyncSQLiteAdapter, ProxyDatabase, TaskDatabase

# 嘗試導入PostgreSQL依賴
try:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False
    logging.warning("PostgreSQL依賴未安裝，PostgreSQL功能將被禁用")

# 嘗試導入Redis依賴
try:
    import aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis依賴未安裝，Redis功能將被禁用")

from .config_improved import get_settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """統一的數據庫管理器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.engine: Optional[Union[AsyncEngine, AsyncSQLiteAdapter]] = None
        self.session_maker = None
        self.redis_client = None
        self.proxy_db = None
        self.task_db = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """初始化數據庫連接"""
        if self._initialized:
            return True
        
        try:
            logger.info(f"正在初始化數據庫連接，類型: {self.settings.database_type}")
            
            if self.settings.is_sqlite:
                success = await self._init_sqlite()
            elif self.settings.is_postgresql:
                success = await self._init_postgresql()
            else:
                logger.error(f"不支持的數據庫類型: {self.settings.database_type}")
                return False
            
            if success:
                # 初始化數據庫操作類
                if self.settings.is_sqlite:
                    self.proxy_db = ProxyDatabase(self.engine)
                    self.task_db = TaskDatabase(self.engine)
                
                # 初始化Redis（如果可用）
                if self.settings.REDIS_URL and REDIS_AVAILABLE:
                    await self._init_redis()
                
                self._initialized = True
                logger.info("數據庫管理器初始化成功")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"數據庫管理器初始化失敗: {str(e)}")
            logger.exception(e)
            return False
    
    async def _init_sqlite(self) -> bool:
        """初始化SQLite連接"""
        try:
            # 創建SQLite適配器
            self.engine = AsyncSQLiteAdapter(self.settings.database_path)
            
            # 創建數據表
            await self._create_sqlite_tables()
            
            logger.info(f"SQLite數據庫初始化成功: {self.settings.database_path}")
            return True
            
        except Exception as e:
            logger.error(f"SQLite初始化失敗: {str(e)}")
            return False
    
    async def _init_postgresql(self) -> bool:
        """初始化PostgreSQL連接"""
        if not POSTGRESQL_AVAILABLE:
            logger.error("PostgreSQL依賴未安裝，無法初始化")
            return False
        
        try:
            # 創建異步引擎
            self.engine = create_async_engine(
                self.settings.DATABASE_URL,
                echo=self.settings.DEBUG,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600,
            )
            
            # 創建會話工廠
            self.session_maker = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # 測試連接
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            logger.info("PostgreSQL數據庫初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL初始化失敗: {str(e)}")
            return False
    
    async def _init_redis(self) -> bool:
        """初始化Redis連接"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis不可用，跳過初始化")
            return False
        
        try:
            self.redis_client = aioredis.from_url(
                self.settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            
            # 測試連接
            await self.redis_client.ping()
            
            logger.info("Redis連接初始化成功")
            return True
            
        except Exception as e:
            logger.warning(f"Redis連接失敗: {str(e)}")
            return False
    
    async def _create_sqlite_tables(self):
        """創建SQLite數據表"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS proxies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                port INTEGER NOT NULL,
                protocol TEXT NOT NULL,
                country TEXT,
                anonymity_level TEXT,
                is_active BOOLEAN DEFAULT 1,
                success_rate REAL DEFAULT 0.0,
                response_time REAL,
                last_checked TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                config TEXT,
                result TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                worker_id TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS proxy_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                source_type TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                last_fetched TIMESTAMP,
                fetch_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_proxies_ip_port ON proxies(ip, port);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_proxies_protocol ON proxies(protocol);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_proxies_is_active ON proxies(is_active);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(task_type);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_proxy_sources_active ON proxy_sources(is_active);
            """
        ]
        
        for table_sql in tables:
            await self.engine.execute(table_sql)
        
        logger.info("SQLite數據表創建完成")
    
    async def get_session(self) -> AsyncSession:
        """獲取數據庫會話"""
        if self.settings.is_postgresql and self.session_maker:
            return self.session_maker()
        else:
            raise NotImplementedError("PostgreSQL會話管理尚未實現")
    
    async def get_redis_client(self):
        """獲取Redis客戶端"""
        if not self.redis_client:
            logger.warning("Redis客戶端未初始化")
        return self.redis_client
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        results = {}
        
        # 數據庫健康檢查
        try:
            if self.settings.is_sqlite:
                # SQLite健康檢查
                result = await self.engine.fetch_one("SELECT 1 as health")
                results['database'] = {
                    'status': 'healthy' if result else 'unhealthy',
                    'type': 'sqlite',
                    'path': self.settings.database_path
                }
            elif self.settings.is_postgresql:
                # PostgreSQL健康檢查
                async with self.engine.begin() as conn:
                    result = await conn.execute(text("SELECT 1"))
                    results['database'] = {
                        'status': 'healthy' if result else 'unhealthy',
                        'type': 'postgresql'
                    }
        except Exception as e:
            results['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Redis健康檢查
        if self.redis_client:
            try:
                await self.redis_client.ping()
                results['redis'] = {'status': 'healthy'}
            except Exception as e:
                results['redis'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        else:
            results['redis'] = {'status': 'disabled'}
        
        return results
    
    async def get_stats(self) -> Dict[str, Any]:
        """獲取數據庫統計信息"""
        stats = {}
        
        if self.settings.is_sqlite:
            # SQLite統計
            try:
                proxy_stats = await self.proxy_db.get_proxy_stats()
                task_stats = await self.task_db.get_task_stats()
                
                stats = {
                    'proxies': proxy_stats,
                    'tasks': task_stats,
                    'database_type': 'sqlite'
                }
            except Exception as e:
                logger.error(f"獲取SQLite統計失敗: {str(e)}")
                stats = {'error': str(e)}
        
        elif self.settings.is_postgresql:
            # PostgreSQL統計（需要實現）
            stats = {'database_type': 'postgresql', 'status': 'not_implemented'}
        
        return stats
    
    async def close(self):
        """關閉數據庫連接"""
        try:
            if self.settings.is_sqlite and self.engine:
                await self.engine.close()
            elif self.settings.is_postgresql and self.engine:
                await self.engine.dispose()
            
            if self.redis_client:
                await self.redis_client.close()
            
            self._initialized = False
            logger.info("數據庫管理器已關閉")
            
        except Exception as e:
            logger.error(f"關閉數據庫管理器失敗: {str(e)}")
    
    def __del__(self):
        """析構函數"""
        if hasattr(self, '_initialized') and self._initialized:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
            except Exception:
                pass


# 全局數據庫管理器實例
db_manager = DatabaseManager()


async def get_db_manager() -> DatabaseManager:
    """獲取數據庫管理器實例"""
    if not db_manager._initialized:
        await db_manager.initialize()
    return db_manager


# 測試函數
async def test_database_manager():
    """測試數據庫管理器"""
    print("🚀 測試數據庫管理器...")
    
    try:
        # 獲取管理器
        manager = await get_db_manager()
        
        # 健康檢查
        health = await manager.health_check()
        print(f"✅ 健康檢查: {health}")
        
        # 獲取統計信息
        stats = await manager.get_stats()
        print(f"✅ 統計信息: {stats}")
        
        # 測試代理操作（SQLite）
        if manager.settings.is_sqlite:
            # 創建測試代理
            proxy_id = await manager.proxy_db.create_proxy({
                'ip': '192.168.1.100',
                'port': 8080,
                'protocol': 'http',
                'country': 'US',
                'anonymity_level': 'elite',
                'response_time': 0.5
            })
            print(f"✅ 創建代理成功，ID: {proxy_id}")
            
            # 獲取代理統計
            proxy_stats = await manager.proxy_db.get_proxy_stats()
            print(f"✅ 代理統計: {proxy_stats}")
        
        # 關閉連接
        await manager.close()
        print("✅ 數據庫管理器測試完成！")
        
    except Exception as e:
        print(f"❌ 數據庫管理器測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_database_manager())