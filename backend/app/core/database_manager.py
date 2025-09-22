"""
統一的數據庫管理器

這個模塊提供統一的數據庫接口，支持SQLite和PostgreSQL
整合了新的數據庫配置管理模塊
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Union, AsyncGenerator, Generator
from pathlib import Path
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime

# 導入新的配置模塊
from .database_config import DatabaseConfig, DatabaseType, DatabaseManager as ConfigManager
from .exceptions import DatabaseConnectionException, DatabaseQueryException

# 導入SQLite適配器（保留兼容性）
try:
    from .sqlite_adapter import SQLiteAdapter, AsyncSQLiteAdapter, ProxyDatabase, TaskDatabase
    SQLITE_ADAPTER_AVAILABLE = True
except ImportError:
    SQLITE_ADAPTER_AVAILABLE = False
    logging.warning("SQLite適配器未安裝，將使用SQLAlchemy替代")

# 嘗試導入PostgreSQL依賴
try:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    from sqlalchemy.pool import QueuePool
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False
    logging.warning("PostgreSQL依賴未安裝，PostgreSQL功能將被禁用")

# 嘗試導入Redis依賴
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis依賴未安裝，Redis功能將被禁用")

try:
    from .config_improved import get_settings
    LEGACY_CONFIG_AVAILABLE = True
except ImportError:
    LEGACY_CONFIG_AVAILABLE = False

logger = logging.getLogger(__name__)


class DatabaseManager:
    """統一的數據庫管理器
    
    整合 PostgreSQL、SQLite 和 Redis 的連接管理，提供統一的接口。
    支持新的配置系統和遺留的配置系統。
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """初始化數據庫管理器
        
        Args:
            config: 數據庫配置，如果為 None 則使用環境變量加載
        """
        # 優先使用新的配置系統
        if config:
            self.config = config
            self.legacy_settings = None
        elif LEGACY_CONFIG_AVAILABLE:
            # 使用遺留配置系統
            self.legacy_settings = get_settings()
            self.config = self._convert_legacy_config()
        else:
            # 使用默認配置
            self.config = DatabaseConfig.from_env()
            self.legacy_settings = None
        
        self.engine: Optional[Union[AsyncEngine, AsyncSQLiteAdapter]] = None
        self.session_maker = None
        self.redis_client = None
        self.proxy_db = None
        self.task_db = None
        self._initialized = False
        
        # 連接池統計
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'idle_connections': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'connection_errors': 0
        }
        
        self.connection_string = self._build_connection_string()
        
    def _build_connection_string(self) -> str:
        """構建連接字符串
        
        Returns:
            str: 數據庫連接字符串
        """
        if self.config.database_type == DatabaseType.SQLITE:
            return f"sqlite:///{self.config.database}"
        elif self.config.database_type == DatabaseType.POSTGRESQL:
            return f"postgresql://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}"
        else:
            return "unknown"
    
    def _convert_legacy_config(self) -> DatabaseConfig:
        """將遺留配置轉換為新配置格式"""
        if not self.legacy_settings:
            return DatabaseConfig.from_env()
        
        # 根據遺留設置創建新配置
        if self.legacy_settings.is_sqlite:
            return DatabaseConfig.sqlite_config(
                database=self.legacy_settings.database_path,
                echo=self.legacy_settings.DEBUG
            )
        elif self.legacy_settings.is_postgresql:
            return DatabaseConfig.postgresql_config(
                host=self.legacy_settings.POSTGRES_HOST,
                port=self.legacy_settings.POSTGRES_PORT,
                database=self.legacy_settings.POSTGRES_DB,
                username=self.legacy_settings.POSTGRES_USER,
                password=self.legacy_settings.POSTGRES_PASSWORD,
                echo=self.legacy_settings.DEBUG
            )
        else:
            return DatabaseConfig.from_env()
    
    async def initialize(self) -> bool:
        """初始化數據庫連接
        
        Returns:
            bool: 初始化是否成功
        """
        if self._initialized:
            return True
        
        try:
            logger.info(f"正在初始化數據庫連接，類型: {self.config.database_type.value}")
            
            # 驗證配置
            if not self.config.validate():
                logger.error("數據庫配置驗證失敗")
                return False
            
            if self.config.database_type == DatabaseType.SQLITE:
                success = await self._init_sqlite()
            elif self.config.database_type == DatabaseType.POSTGRESQL:
                success = await self._init_postgresql()
            else:
                logger.error(f"不支持的數據庫類型: {self.config.database_type.value}")
                return False
            
            if success:
                # 初始化數據庫操作類（保留兼容性）
                if self.config.database_type == DatabaseType.SQLITE and SQLITE_ADAPTER_AVAILABLE:
                    self.proxy_db = ProxyDatabase(self.engine)
                    self.task_db = TaskDatabase(self.engine)
                
                # 初始化Redis（如果可用）
                if REDIS_AVAILABLE:
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
        """初始化SQLite連接
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 驗�SQLite配置
            if not hasattr(self.config, 'database'):
                logger.error("配置缺少 database 屬性")
                return False
            
            # 創建數據庫目錄
            db_path = Path(self.config.database)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 創建SQLite引擎（使用新的配置）
            self.engine = AsyncSQLiteAdapter(db_path, echo=self.config.echo)
            
            # 創建會話工廠（SQLite不需要SQLAlchemy會話，但為了統一接口）
            self.session_maker = None
            
            # 創建數據表
            await self._create_sqlite_tables()
            
            # 更新連接統計
            self.connection_stats['total_connections'] += 1
            self.connection_stats['active_connections'] += 1
            
            logger.info(f"SQLite數據庫初始化成功: {db_path}")
            return True
            
        except Exception as e:
            self.connection_stats['connection_errors'] += 1
            logger.error(f"SQLite初始化失敗: {str(e)}")
            logger.exception(e)
            return False
    
    async def _init_postgresql(self) -> bool:
        """初始化PostgreSQL連接
        
        Returns:
            bool: 初始化是否成功
        """
        if not POSTGRESQL_AVAILABLE:
            logger.error("PostgreSQL依賴未安裝，無法初始化")
            return False
        
        try:
            # 驗證PostgreSQL配置
            if not hasattr(self.config, 'host') or not hasattr(self.config, 'database'):
                logger.error("配置缺少必要的 PostgreSQL 參數")
                return False
            
            # 構建連接字符串
            database_url = (
                f"postgresql+asyncpg://{self.config.username}:{self.config.password}@"
                f"{self.config.host}:{self.config.port}/{self.config.database}"
            )
            
            # 創建異步引擎
            self.engine = create_async_engine(
                database_url,
                echo=self.config.echo,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                poolclass=QueuePool
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
            
            # 更新連接統計
            self.connection_stats['total_connections'] += self.config.pool_size
            self.connection_stats['active_connections'] += 1
            
            logger.info(f"PostgreSQL數據庫初始化成功: {self.config.host}:{self.config.port}")
            return True
            
        except Exception as e:
            self.connection_stats['connection_errors'] += 1
            logger.error(f"PostgreSQL初始化失敗: {str(e)}")
            logger.exception(e)
            return False
    
    async def _init_redis(self) -> bool:
        """初始化Redis連接
        
        Returns:
            bool: 初始化是否成功
        """
        if not REDIS_AVAILABLE:
            logger.warning("Redis依賴未安裝，跳過Redis初始化")
            return False
        
        try:
            # 獲取Redis配置
            redis_config = getattr(self.config, 'redis_config', None)
            if not redis_config or not redis_config.url:
                logger.info("Redis未配置，跳過初始化")
                return False
            
            # 創建Redis連接
            self.redis_client = redis.from_url(
                redis_config.url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=redis_config.socket_timeout,
                socket_connect_timeout=redis_config.socket_connect_timeout,
                socket_keepalive=redis_config.socket_keepalive,
                socket_keepalive_options=redis_config.socket_keepalive_options,
                max_connections=redis_config.max_connections,
                retry_on_timeout=redis_config.retry_on_timeout,
                retry_on_error=redis_config.retry_on_error
            )
            
            # 測試連接
            await self.redis_client.ping()
            
            # 更新連接統計
            self.connection_stats['total_connections'] += 1
            self.connection_stats['active_connections'] += 1
            
            logger.info("Redis連接初始化成功")
            return True
            
        except Exception as e:
            self.connection_stats['connection_errors'] += 1
            logger.error(f"Redis初始化失敗: {str(e)}")
            logger.exception(e)
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
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """獲取數據庫會話

        Yields:
            AsyncSession: 數據庫會話
            
        Raises:
            DatabaseConnectionException: 如果數據庫未初始化或會話工廠未創建
        """
        if not self._initialized:
            raise DatabaseConnectionException(
                connection_string=self.connection_string,
                original_exception=Exception("數據庫尚未初始化"),
                details={'error': 'database_not_initialized'}
            )
        
        # SQLite使用自定義適配器，不需要SQLAlchemy會話
        if self.config.database_type == DatabaseType.SQLITE:
            # 創建一個模擬的會話對象來兼容接口
            class SQLiteSession:
                def __init__(self, engine):
                    self.engine = engine
                    self._transaction_active = False
                
                async def execute(self, query, params=None):
                    if hasattr(query, 'text'):
                        # SQLAlchemy text對象
                        sql = query.text
                    else:
                        # 字符串查詢
                        sql = str(query)
                    
                    if params:
                        return await self.engine.execute(sql, params)
                    else:
                        return await self.engine.execute(sql)
                
                async def commit(self):
                    # SQLite自動提交模式
                    pass
                
                async def rollback(self):
                    # SQLite不支持事務回滾
                    pass
                
                async def close(self):
                    pass
            
            session = SQLiteSession(self.engine)
            try:
                self.connection_stats['active_connections'] += 1
                self.connection_stats['pool_hits'] += 1
                yield session
            except Exception as e:
                self.connection_stats['connection_errors'] += 1
                raise e
            finally:
                self.connection_stats['active_connections'] -= 1
                self.connection_stats['idle_connections'] += 1
        
        elif self.config.database_type == DatabaseType.POSTGRESQL:
            if not self.session_maker:
                raise DatabaseConnectionException(
                    connection_string=self.connection_string,
                    original_exception=Exception("PostgreSQL會話工廠未創建"),
                    details={'error': 'session_factory_not_created'}
                )
            
            async with self.session_maker() as session:
                try:
                    # 更新連接統計
                    self.connection_stats['active_connections'] += 1
                    self.connection_stats['pool_hits'] += 1
                    yield session
                except Exception as e:
                    await session.rollback()
                    self.connection_stats['connection_errors'] += 1
                    raise e
                finally:
                    await session.close()
                    self.connection_stats['active_connections'] -= 1
                    self.connection_stats['idle_connections'] += 1
        else:
            raise DatabaseConnectionException(
                connection_string=self.connection_string,
                original_exception=Exception(f"不支持的數據庫類型: {self.config.database_type.value}"),
                details={'error': 'unsupported_database_type', 'database_type': self.config.database_type.value}
            )
    
    def get_redis_client(self) -> Optional[redis.Redis]:
        """獲取Redis客戶端
        
        Returns:
            Optional[redis.Redis]: Redis客戶端實例，如果未配置則返回None
        """
        return self.redis_client
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查
        
        Returns:
            Dict[str, Any]: 包含數據庫和Redis連接狀態的字典
        """
        result = {
            'status': 'healthy',
            'database': 'unknown',
            'redis': 'unknown',
            'timestamp': datetime.now().isoformat(),
            'connection_stats': self.connection_stats.copy(),
            'config_type': self.config.database_type.value
        }
        
        try:
            # 檢查數據庫連接
            if self.engine:
                if self.config.database_type == DatabaseType.SQLITE:
                    result['database'] = 'connected'
                    result['database_type'] = 'sqlite'
                elif self.config.database_type == DatabaseType.POSTGRESQL:
                    async with self.engine.connect() as conn:
                        await conn.execute(text("SELECT 1"))
                        result['database'] = 'connected'
                        result['database_type'] = 'postgresql'
            else:
                result['database'] = 'disconnected'
                result['status'] = 'unhealthy'
                
        except Exception as e:
            result['database'] = f'error: {str(e)}'
            result['status'] = 'unhealthy'
        
        try:
            # 檢查Redis連接
            if self.redis_client:
                await self.redis_client.ping()
                result['redis'] = 'connected'
            else:
                result['redis'] = 'not_configured'
                
        except Exception as e:
            result['redis'] = f'error: {str(e)}'
            result['status'] = 'unhealthy'
        
        return result
    
    async def get_stats(self) -> Dict[str, Any]:
        """獲取數據庫統計信息"""
        stats = {}
        
        if self.config.database_type == DatabaseType.SQLITE:
            # SQLite統計
            try:
                # 執行簡單的統計查詢
                result = await self.engine.fetch_one("SELECT COUNT(*) as count FROM proxies")
                proxy_count = result['count'] if result else 0
                
                result = await self.engine.fetch_one("SELECT COUNT(*) as count FROM tasks")
                task_count = result['count'] if result else 0
                
                stats = {
                    'proxies': {'total': proxy_count},
                    'tasks': {'total': task_count},
                    'database_type': 'sqlite'
                }
            except Exception as e:
                logger.error(f"獲取SQLite統計失敗: {str(e)}")
                stats = {'error': str(e)}
        
        elif self.config.database_type == DatabaseType.POSTGRESQL:
            # PostgreSQL統計（需要實現）
            stats = {'database_type': 'postgresql', 'status': 'not_implemented'}
        
        return stats
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """獲取連接統計信息
        
        Returns:
            Dict[str, Any]: 包含連接池統計信息的字典
        """
        stats = self.connection_stats.copy()
        stats['initialized'] = self._initialized
        stats['config_type'] = self.config.database_type.value
        stats['timestamp'] = datetime.now().isoformat()
        
        # 計算連接池效率
        if stats['pool_hits'] + stats['pool_misses'] > 0:
            stats['pool_efficiency'] = round(
                stats['pool_hits'] / (stats['pool_hits'] + stats['pool_misses']) * 100, 2
            )
        else:
            stats['pool_efficiency'] = 0.0
        
        return stats
    
    async def get_database_info(self) -> Dict[str, Any]:
        """獲取數據庫信息
        
        Returns:
            Dict[str, Any]: 包含數據庫詳細信息的字典
        """
        info = {
            'config': self.config.to_dict(),
            'initialized': self._initialized,
            'connection_stats': self.get_connection_stats(),
            'timestamp': datetime.now().isoformat()
        }
        
        # 添加數據庫特定信息
        if self.config.database_type == DatabaseType.SQLITE and hasattr(self.config, 'database'):
            info['database_file'] = str(Path(self.config.database).resolve())
            info['file_exists'] = Path(self.config.database).exists()
            if info['file_exists']:
                info['file_size'] = Path(self.config.database).stat().st_size
        
        elif self.config.database_type == DatabaseType.POSTGRESQL:
            info['connection_string'] = (
                f"postgresql://{self.config.username}@{self.config.host}:"
                f"{self.config.port}/{self.config.database}"
            )
        
        return info
    
    async def close(self):
        """關閉所有連接
        
        關閉數據庫引擎和Redis客戶端連接，清理資源。
        """
        try:
            if self.engine:
                await self.engine.dispose()
                logger.info("數據庫連接已關閉")
                self.connection_stats['active_connections'] = 0
                self.connection_stats['idle_connections'] = 0
            
            if self.redis_client:
                await self.redis_client.close()
                logger.info("Redis連接已關閉")
            
            self._initialized = False
            
        except Exception as e:
            logger.error(f"關閉連接時出錯: {str(e)}")
            logger.exception(e)
    
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
_db_manager: Optional[DatabaseManager] = None


async def get_db_session_manager() -> AsyncGenerator[AsyncSession, None]:
    """獲取數據庫會話的依賴注入函數
    
    這個函數用於FastAPI的Depends，提供數據庫會話。
    使用新的數據庫管理器而不是舊的get_db_session。
    
    Yields:
        AsyncSession: 數據庫會話
    """
    manager = get_db_manager()
    async with manager.get_session() as session:
        yield session


# 為了向後兼容，提供別名
get_db = get_db_session_manager


def get_db_manager(config: Optional[DatabaseConfig] = None) -> DatabaseManager:
    """獲取全局數據庫管理器實例
    
    Args:
        config: 可選的數據庫配置，如果不提供則使用默認配置
        
    Returns:
        DatabaseManager: 數據庫管理器實例
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(config=config)
    return _db_manager


def reset_db_manager():
    """重置全局數據庫管理器實例"""
    global _db_manager
    _db_manager = None


async def init_db_manager(config: Optional[DatabaseConfig] = None) -> bool:
    """初始化全局數據庫管理器
    
    Args:
        config: 可選的數據庫配置，如果不提供則使用默認配置
        
    Returns:
        bool: 初始化是否成功
    """
    manager = get_db_manager(config)
    return await manager.initialize()


async def close_db_manager():
    """關閉全局數據庫管理器"""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None


# 測試函數
async def test_connection():
    """測試數據庫連接
    
    Returns:
        bool: 測試是否通過
    """
    manager = get_db_manager()
    
    if not await manager.initialize():
        logger.error("數據庫初始化失敗")
        return False
    
    # 健康檢查
    health = await manager.health_check()
    logger.info(f"健康檢查結果: {health}")
    
    # 測試會話
    if manager.config.database_type == DatabaseType.POSTGRESQL:
        try:
            async for session in manager.get_session():
                result = await session.execute(text("SELECT 1"))
                logger.info(f"會話測試成功: {result.scalar()}")
                break
        except Exception as e:
            logger.error(f"會話測試失敗: {str(e)}")
            return False
    
    # 測試Redis
    if manager.redis_client:
        try:
            await manager.redis_client.set("test_key", "test_value", ex=10)
            value = await manager.redis_client.get("test_key")
            logger.info(f"Redis測試成功: {value}")
        except Exception as e:
            logger.error(f"Redis測試失敗: {str(e)}")
    
    # 顯示連接統計
    stats = manager.get_connection_stats()
    logger.info(f"連接統計: {stats}")
    
    # 顯示數據庫信息
    db_info = await manager.get_database_info()
    logger.info(f"數據庫信息: {db_info}")
    
    await manager.close()
    return True


if __name__ == "__main__":
    asyncio.run(test_connection())