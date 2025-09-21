"""
後端核心配置文件
"""
from typing import List, Optional
from pydantic import validator
from pydantic_settings import BaseSettings
import os
from pathlib import Path

# 獲取項目根目錄
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """應用配置類"""
    
    # 應用基本信息
    APP_NAME: str = "Proxy IP Pool Collector"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # 服務器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    RELOAD: bool = False
    
    # 數據庫配置
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/proxy_collector"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 日誌配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE_PATH: str = str(BASE_DIR / "logs" / "app.log")
    
    # 爬取配置
    MAX_CONCURRENT_REQUESTS: int = 50
    REQUEST_TIMEOUT: int = 30
    RETRY_COUNT: int = 3
    RETRY_DELAY: int = 1
    
    # 代理驗證配置
    VALIDATOR_TIMEOUT: int = 10
    VALIDATOR_TARGET_URLS: str = "http://httpbin.org/ip,https://www.baidu.com"
    VALIDATOR_CONCURRENT_WORKERS: int = 20
    
    # 速率限制
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 10
    
    # 監控配置
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    SENTRY_DSN: Optional[str] = None
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # 代理來源配置
    PROXY_SOURCES_CONFIG_PATH: str = str(BASE_DIR / "config" / "proxy_sources.json")
    
    # CORS配置
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # 緩存配置
    CACHE_TTL: int = 300  # 5分鐘
    PROXY_POOL_CACHE_KEY: str = "proxy:pool:active"
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """驗證日誌級別"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"無效的日誌級別: {v}")
        return v.upper()
    
    @validator("VALIDATOR_TARGET_URLS")
    def validate_target_urls(cls, v):
        """驗證目標URL格式"""
        urls = v.split(",")
        for url in urls:
            if not url.strip().startswith(("http://", "https://")):
                raise ValueError(f"無效的URL格式: {url}")
        return v
    
    @property
    def validator_target_urls_list(self) -> List[str]:
        """獲取驗證目標URL列表"""
        return [url.strip() for url in self.VALIDATOR_TARGET_URLS.split(",")]
    
    class Config:
        """Pydantic配置"""
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 創建全局配置實例
settings = Settings()

# 確保日誌目錄存在
os.makedirs(os.path.dirname(settings.LOG_FILE_PATH), exist_ok=True)