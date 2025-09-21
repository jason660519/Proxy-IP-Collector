"""
改進的應用配置模塊

這個模塊提供了靈活的配置管理，支持多種數據庫類型
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, validator
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """應用配置類"""
    
    # 應用基本信息
    APP_NAME: str = "Proxy Collector"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 數據庫配置
    DATABASE_URL: str = "sqlite:///./data/proxy_collector.db"
    REDIS_URL: Optional[str] = None
    
    # 服務器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False
    
    # 日誌配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # 爬蟲配置
    MAX_CONCURRENT_REQUESTS: int = 50
    REQUEST_TIMEOUT: int = 30
    RETRY_COUNT: int = 3
    
    # 代理驗證配置
    VALIDATOR_TIMEOUT: int = 10
    VALIDATOR_TARGET_URL: str = "http://httpbin.org/ip"
    
    # 速率限制配置
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # 任務隊列配置
    TASK_QUEUE_SIZE: int = 1000
    TASK_WORKER_COUNT: int = 4
    
    # 代理池配置
    MAX_POOL_SIZE: int = 1000
    MIN_POOL_SIZE: int = 100
    
    # 存儲配置
    DATA_DIR: str = "data"
    LOGS_DIR: str = "logs"
    
    # 環境變量文件
    env_file: str = ".env"
    env_file_encoding: str = "utf-8"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @validator('DATABASE_URL')
    def validate_database_url(cls, v):
        """驗證數據庫URL"""
        if not v:
            raise ValueError("DATABASE_URL不能為空")
        
        # 支持多種數據庫類型
        supported_schemes = ['sqlite', 'postgresql', 'mysql']
        scheme = v.split('://')[0] if '://' in v else ''
        
        if scheme not in supported_schemes:
            logger.warning(f"不支持的數據庫類型: {scheme}，支持的類型: {supported_schemes}")
        
        return v
    
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        """驗證日誌級別"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"無效的日誌級別: {v}，支持的級別: {valid_levels}")
        return v.upper()
    
    @validator('MAX_CONCURRENT_REQUESTS', 'TASK_QUEUE_SIZE', 'MAX_POOL_SIZE')
    def validate_positive_integers(cls, v):
        """驗證正整數"""
        if v <= 0:
            raise ValueError("必須為正整數")
        return v
    
    @property
    def is_sqlite(self) -> bool:
        """判斷是否使用SQLite"""
        return self.DATABASE_URL.startswith('sqlite')
    
    @property
    def is_postgresql(self) -> bool:
        """判斷是否使用PostgreSQL"""
        return self.DATABASE_URL.startswith('postgresql')
    
    @property
    def database_type(self) -> str:
        """獲取數據庫類型"""
        if self.is_sqlite:
            return 'sqlite'
        elif self.is_postgresql:
            return 'postgresql'
        else:
            return 'unknown'
    
    @property
    def database_path(self) -> str:
        """獲取數據庫文件路徑（僅限SQLite）"""
        if not self.is_sqlite:
            return None
        
        # 解析SQLite URL
        path = self.DATABASE_URL.replace('sqlite:///', '')
        if self.DATABASE_URL.startswith('sqlite:///./'):
            path = self.DATABASE_URL.replace('sqlite:///./', '')
        
        return path
    
    def get_database_config(self) -> Dict[str, Any]:
        """獲取數據庫配置"""
        config = {
            'url': self.DATABASE_URL,
            'type': 'sqlite' if self.is_sqlite else 'postgresql',
        }
        
        if self.is_sqlite:
            config['path'] = self.database_path
            config['options'] = {
                'check_same_thread': False,
                'timeout': 30.0,
                'isolation_level': None
            }
        elif self.is_postgresql:
            config['pool_size'] = 10
            config['max_overflow'] = 20
            config['pool_timeout'] = 30
        
        return config
    
    def ensure_directories(self):
        """確保必要的目錄存在"""
        directories = [self.DATA_DIR, self.LOGS_DIR]
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
            logger.info(f"確保目錄存在: {directory}")
    
    def setup_logging(self):
        """設置日誌配置"""
        # 確保日誌目錄存在
        Path(self.LOGS_DIR).mkdir(exist_ok=True)
        
        # 配置日誌格式
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # 設置根日誌器
        logging.basicConfig(
            level=getattr(logging, self.LOG_LEVEL),
            format=log_format,
            handlers=[
                logging.FileHandler(self.LOG_FILE, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        logger.info(f"日誌配置完成，級別: {self.LOG_LEVEL}")
    
    def validate_config(self) -> Dict[str, Any]:
        """驗證配置並返回診斷信息"""
        issues = []
        warnings = []
        
        # 檢查數據庫配置
        if self.is_sqlite:
            db_path = Path(self.database_path)
            if not db_path.parent.exists():
                warnings.append(f"數據庫目錄不存在，將自動創建: {db_path.parent}")
        
        # 檢查Redis配置
        if self.REDIS_URL and not self.REDIS_URL.startswith('redis://'):
            issues.append(f"Redis URL格式錯誤: {self.REDIS_URL}")
        
        # 檢查路徑配置
        data_path = Path(self.DATA_DIR)
        logs_path = Path(self.LOGS_DIR)
        
        if not data_path.is_absolute() and not data_path.exists():
            warnings.append(f"數據目錄不存在: {self.DATA_DIR}")
        
        if not logs_path.is_absolute() and not logs_path.exists():
            warnings.append(f"日誌目錄不存在: {self.LOGS_DIR}")
        
        return {
            'issues': issues,
            'warnings': warnings,
            'is_valid': len(issues) == 0,
            'database_type': 'sqlite' if self.is_sqlite else 'postgresql',
            'redis_enabled': bool(self.REDIS_URL)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """將配置轉換為字典"""
        return {
            'app_name': self.APP_NAME,
            'app_version': self.APP_VERSION,
            'debug': self.DEBUG,
            'database_url': self.DATABASE_URL,
            'database_type': 'sqlite' if self.is_sqlite else 'postgresql',
            'redis_url': self.REDIS_URL,
            'host': self.HOST,
            'port': self.PORT,
            'reload': self.RELOAD,
            'log_level': self.LOG_LEVEL,
            'log_file': self.LOG_FILE,
            'max_concurrent_requests': self.MAX_CONCURRENT_REQUESTS,
            'request_timeout': self.REQUEST_TIMEOUT,
            'retry_count': self.RETRY_COUNT,
            'validator_timeout': self.VALIDATOR_TIMEOUT,
            'validator_target_url': self.VALIDATOR_TARGET_URL,
            'rate_limit_per_minute': self.RATE_LIMIT_PER_MINUTE,
            'task_queue_size': self.TASK_QUEUE_SIZE,
            'task_worker_count': self.TASK_WORKER_COUNT,
            'max_pool_size': self.MAX_POOL_SIZE,
            'min_pool_size': self.MIN_POOL_SIZE,
            'data_dir': self.DATA_DIR,
            'logs_dir': self.LOGS_DIR
        }


# 全局配置實例
settings = Settings()


def get_settings() -> Settings:
    """獲取配置實例"""
    return settings


def init_config():
    """初始化配置"""
    # 確保目錄存在
    settings.ensure_directories()
    
    # 設置日誌
    settings.setup_logging()
    
    # 驗證配置
    validation = settings.validate_config()
    
    if not validation['is_valid']:
        logger.error(f"配置驗證失敗: {validation['issues']}")
        raise ValueError(f"配置錯誤: {validation['issues']}")
    
    if validation['warnings']:
        logger.warning(f"配置警告: {validation['warnings']}")
    
    logger.info(f"配置初始化完成，數據庫類型: {validation['database_type']}")
    logger.info(f"Redis狀態: {'啟用' if validation['redis_enabled'] else '禁用'}")
    
    return validation


# 配置測試函數
def test_config():
    """測試配置"""
    print("🚀 測試配置...")
    
    try:
        # 初始化配置
        validation = init_config()
        
        print(f"✅ 配置初始化成功")
        print(f"📊 配置信息:")
        print(f"   - 應用名稱: {settings.APP_NAME}")
        print(f"   - 應用版本: {settings.APP_VERSION}")
        print(f"   - 調試模式: {settings.DEBUG}")
        print(f"   - 數據庫類型: {validation['database_type']}")
        print(f"   - 數據庫URL: {settings.DATABASE_URL}")
        print(f"   - Redis狀態: {'啟用' if validation['redis_enabled'] else '禁用'}")
        print(f"   - 日誌級別: {settings.LOG_LEVEL}")
        print(f"   - 日誌文件: {settings.LOG_FILE}")
        
        if validation['warnings']:
            print(f"⚠️  配置警告: {validation['warnings']}")
        
        print("✅ 配置測試完成！")
        
    except Exception as e:
        print(f"❌ 配置測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_config()