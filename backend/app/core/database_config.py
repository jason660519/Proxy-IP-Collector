"""
數據庫配置管理模塊
支持 PostgreSQL 和 SQLite 數據庫連接配置
"""

import os
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

class DatabaseType(Enum):
    """數據庫類型枚舉"""
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"

@dataclass
class RedisConfig:
    """Redis配置類"""
    url: str = "redis://localhost:6379/0"
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    socket_keepalive: bool = True
    socket_keepalive_options: Optional[Dict[str, Any]] = None
    max_connections: int = 50
    retry_on_timeout: bool = True
    retry_on_error: Optional[list] = None

@dataclass
class DatabaseConfig:
    """數據庫配置基類"""
    
    # 基本配置
    database_type: DatabaseType
    host: str = "localhost"
    port: int = 5432
    database: str = "proxy_collector"
    username: str = "postgres"
    password: str = ""
    
    # 連接池配置
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    # SSL 配置
    ssl_mode: str = "prefer"
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_root_cert: Optional[str] = None
    
    # 其他配置
    echo: bool = False
    echo_pool: bool = False
    pool_pre_ping: bool = True
    
    # Redis配置
    redis_config: Optional[RedisConfig] = None
    
    # 連接字符串緩存
    _connection_string: Optional[str] = field(default=None, init=False)
    
    @property
    def connection_string(self) -> str:
        """生成數據庫連接字符串"""
        if self._connection_string is None:
            self._connection_string = self._build_connection_string()
        return self._connection_string
    
    def _build_connection_string(self) -> str:
        """構建連接字符串"""
        if self.database_type == DatabaseType.POSTGRESQL:
            return self._build_postgresql_connection_string()
        elif self.database_type == DatabaseType.SQLITE:
            return self._build_sqlite_connection_string()
        else:
            raise ValueError(f"不支持的數據庫類型: {self.database_type}")
    
    def _build_postgresql_connection_string(self) -> str:
        """構建 PostgreSQL 連接字符串"""
        # 編碼特殊字符
        encoded_username = quote_plus(self.username)
        encoded_password = quote_plus(self.password)
        encoded_host = quote_plus(self.host)
        encoded_database = quote_plus(self.database)
        
        # 基本連接字符串
        conn_str = f"postgresql://{encoded_username}:{encoded_password}@{encoded_host}:{self.port}/{encoded_database}"
        
        # 添加連接參數
        params = []
        
        # SSL 配置
        if self.ssl_mode:
            params.append(f"sslmode={self.ssl_mode}")
        if self.ssl_cert:
            params.append(f"sslcert={self.ssl_cert}")
        if self.ssl_key:
            params.append(f"sslkey={self.ssl_key}")
        if self.ssl_root_cert:
            params.append(f"sslrootcert={self.ssl_root_cert}")
        
        # 連接池配置
        params.extend([
            f"pool_size={self.pool_size}",
            f"max_overflow={self.max_overflow}",
            f"pool_timeout={self.pool_timeout}",
            f"pool_recycle={self.pool_recycle}",
            f"echo={'true' if self.echo else 'false'}",
            f"echo_pool={'true' if self.echo_pool else 'false'}",
            f"pool_pre_ping={'true' if self.pool_pre_ping else 'false'}"
        ])
        
        if params:
            conn_str += "?" + "&".join(params)
        
        return conn_str
    
    def _build_sqlite_connection_string(self) -> str:
        """構建 SQLite 連接字符串"""
        # 確保數據庫目錄存在
        db_path = self.database
        if not os.path.isabs(db_path):
            # 如果是相對路徑，轉換為絕對路徑
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            db_path = os.path.join(base_dir, "data", self.database)
        
        # 確保目錄存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 基本連接字符串
        conn_str = f"sqlite:///{db_path}"
        
        # SQLite 特定參數
        params = []
        
        if self.echo:
            params.append("echo=true")
        
        if params:
            conn_str += "?" + "&".join(params)
        
        return conn_str
    
    def validate(self) -> bool:
        """驗證配置"""
        try:
            if self.database_type == DatabaseType.POSTGRESQL:
                return self._validate_postgresql_config()
            elif self.database_type == DatabaseType.SQLITE:
                return self._validate_sqlite_config()
            else:
                logger.error(f"不支持的數據庫類型: {self.database_type}")
                return False
        except Exception as e:
            logger.error(f"配置驗證失敗: {e}")
            return False
    
    def _validate_postgresql_config(self) -> bool:
        """驗證 PostgreSQL 配置"""
        if not self.host:
            logger.error("PostgreSQL 主機地址不能為空")
            return False
        
        if not self.database:
            logger.error("PostgreSQL 數據庫名不能為空")
            return False
        
        if not self.username:
            logger.error("PostgreSQL 用戶名不能為空")
            return False
        
        if self.port <= 0 or self.port > 65535:
            logger.error(f"PostgreSQL 端口無效: {self.port}")
            return False
        
        if self.pool_size <= 0:
            logger.error(f"連接池大小無效: {self.pool_size}")
            return False
        
        if self.max_overflow < 0:
            logger.error(f"最大溢出連接數無效: {self.max_overflow}")
            return False
        
        return True
    
    def _validate_sqlite_config(self) -> bool:
        """驗證 SQLite 配置"""
        if not self.database:
            logger.error("SQLite 數據庫路徑不能為空")
            return False
        
        # 檢查數據庫路徑是否有效
        try:
            db_dir = os.path.dirname(self.database)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"SQLite 數據庫路徑無效: {e}")
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典（用於日誌和調試）"""
        return {
            'database_type': self.database_type.value,
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'username': self.username,
            'password': '***' if self.password else '',  # 隱藏密碼
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'ssl_mode': self.ssl_mode,
            'echo': self.echo,
            'connection_string': self.connection_string.replace(self.password, '***') if self.password else self.connection_string
        }
    
    @classmethod
    def from_env(cls, prefix: str = "DB_") -> 'DatabaseConfig':
        """從環境變量加載配置"""
        
        # 確定數據庫類型
        db_type_str = os.getenv(f"{prefix}TYPE", "sqlite").lower()
        if db_type_str == "postgresql":
            database_type = DatabaseType.POSTGRESQL
        elif db_type_str == "sqlite":
            database_type = DatabaseType.SQLITE
        else:
            logger.warning(f"未知的數據庫類型 '{db_type_str}'，使用默認的 SQLite")
            database_type = DatabaseType.SQLITE
        
        # 基本配置
        config = cls(
            database_type=database_type,
            host=os.getenv(f"{prefix}HOST", "localhost"),
            port=int(os.getenv(f"{prefix}PORT", "5432")),
            database=os.getenv(f"{prefix}DATABASE", "proxy_collector.db"),
            username=os.getenv(f"{prefix}USERNAME", "postgres"),
            password=os.getenv(f"{prefix}PASSWORD", ""),
            
            # 連接池配置
            pool_size=int(os.getenv(f"{prefix}POOL_SIZE", "10")),
            max_overflow=int(os.getenv(f"{prefix}MAX_OVERFLOW", "20")),
            pool_timeout=int(os.getenv(f"{prefix}POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv(f"{prefix}POOL_RECYCLE", "3600")),
            
            # SSL 配置
            ssl_mode=os.getenv(f"{prefix}SSL_MODE", "prefer"),
            ssl_cert=os.getenv(f"{prefix}SSL_CERT"),
            ssl_key=os.getenv(f"{prefix}SSL_KEY"),
            ssl_root_cert=os.getenv(f"{prefix}SSL_ROOT_CERT"),
            
            # 其他配置
            echo=os.getenv(f"{prefix}ECHO", "false").lower() == "true",
            echo_pool=os.getenv(f"{prefix}ECHO_POOL", "false").lower() == "true",
            pool_pre_ping=os.getenv(f"{prefix}POOL_PRE_PING", "true").lower() == "true"
        )
        
        logger.info(f"從環境變量加載數據庫配置: {config.to_dict()}")
        return config
    
    @classmethod
    def postgresql_config(
        cls,
        host: str = "localhost",
        port: int = 5432,
        database: str = "proxy_collector",
        username: str = "postgres",
        password: str = "",
        **kwargs
    ) -> 'DatabaseConfig':
        """創建 PostgreSQL 配置"""
        return cls(
            database_type=DatabaseType.POSTGRESQL,
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
            **kwargs
        )
    
    @classmethod
    def sqlite_config(
        cls,
        database: str = "proxy_collector.db",
        **kwargs
    ) -> 'DatabaseConfig':
        """創建 SQLite 配置"""
        return cls(
            database_type=DatabaseType.SQLITE,
            database=database,
            **kwargs
        )

class DatabaseManager:
    """數據庫管理器"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._engine = None
        self._session_factory = None
    
    @property
    def engine(self):
        """獲取數據庫引擎"""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine
    
    @property
    def session_factory(self):
        """獲取會話工廠"""
        if self._session_factory is None:
            self._session_factory = self._create_session_factory()
        return self._session_factory
    
    def _create_engine(self):
        """創建數據庫引擎"""
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.pool import QueuePool
            
            # 創建引擎
            if self.config.database_type == DatabaseType.POSTGRESQL:
                engine = create_engine(
                    self.config.connection_string,
                    poolclass=QueuePool,
                    pool_size=self.config.pool_size,
                    max_overflow=self.config.max_overflow,
                    pool_timeout=self.config.pool_timeout,
                    pool_recycle=self.config.pool_recycle,
                    echo=self.config.echo,
                    echo_pool=self.config.echo_pool,
                    pool_pre_ping=self.config.pool_pre_ping
                )
            elif self.config.database_type == DatabaseType.SQLITE:
                engine = create_engine(
                    self.config.connection_string,
                    echo=self.config.echo,
                    pool_pre_ping=self.config.pool_pre_ping
                )
            else:
                raise ValueError(f"不支持的數據庫類型: {self.config.database_type}")
            
            logger.info(f"成功創建數據庫引擎: {self.config.database_type.value}")
            return engine
            
        except Exception as e:
            logger.error(f"創建數據庫引擎失敗: {e}")
            raise
    
    def _create_session_factory(self):
        """創建會話工廠"""
        try:
            from sqlalchemy.orm import sessionmaker
            
            Session = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )
            
            logger.info("成功創建會話工廠")
            return Session
            
        except Exception as e:
            logger.error(f"創建會話工廠失敗: {e}")
            raise
    
    def test_connection(self) -> bool:
        """測試數據庫連接"""
        try:
            # 測試連接
            with self.engine.connect() as conn:
                result = conn.execute("SELECT 1")
                result.fetchone()
            
            logger.info("數據庫連接測試成功")
            return True
            
        except Exception as e:
            logger.error(f"數據庫連接測試失敗: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """獲取數據庫信息"""
        try:
            with self.engine.connect() as conn:
                if self.config.database_type == DatabaseType.POSTGRESQL:
                    # PostgreSQL 特定查詢
                    result = conn.execute("SELECT version()")
                    version = result.fetchone()[0]
                    
                    result = conn.execute("SELECT current_database(), current_user")
                    db_info = result.fetchone()
                    
                    return {
                        'type': 'PostgreSQL',
                        'version': version,
                        'database': db_info[0],
                        'user': db_info[1],
                        'host': self.config.host,
                        'port': self.config.port
                    }
                
                elif self.config.database_type == DatabaseType.SQLITE:
                    # SQLite 特定查詢
                    result = conn.execute("SELECT sqlite_version()")
                    version = result.fetchone()[0]
                    
                    return {
                        'type': 'SQLite',
                        'version': version,
                        'database': self.config.database,
                        'path': os.path.abspath(self.config.database)
                    }
                
        except Exception as e:
            logger.error(f"獲取數據庫信息失敗: {e}")
            return {'error': str(e)}
    
    def close(self):
        """關閉數據庫連接"""
        try:
            if self._engine:
                self._engine.dispose()
                logger.info("數據庫連接已關閉")
        except Exception as e:
            logger.error(f"關閉數據庫連接失敗: {e}")

# 全局數據庫管理器實例
_database_manager: Optional[DatabaseManager] = None

def get_database_manager(config: Optional[DatabaseConfig] = None) -> DatabaseManager:
    """獲取全局數據庫管理器實例"""
    global _database_manager
    
    if _database_manager is None:
        if config is None:
            config = DatabaseConfig.from_env()
        
        _database_manager = DatabaseManager(config)
        logger.info("創建全局數據庫管理器實例")
    
    return _database_manager

def init_database(config: Optional[DatabaseConfig] = None) -> bool:
    """初始化數據庫連接"""
    try:
        manager = get_database_manager(config)
        
        # 驗證配置
        if not manager.config.validate():
            logger.error("數據庫配置驗證失敗")
            return False
        
        # 測試連接
        if not manager.test_connection():
            logger.error("數據庫連接測試失敗")
            return False
        
        # 獲取數據庫信息
        db_info = manager.get_database_info()
        logger.info(f"數據庫初始化成功: {db_info}")
        
        return True
        
    except Exception as e:
        logger.error(f"數據庫初始化失敗: {e}")
        return False

def close_database():
    """關閉數據庫連接"""
    global _database_manager
    
    if _database_manager:
        _database_manager.close()
        _database_manager = None
        logger.info("全局數據庫管理器已關閉")