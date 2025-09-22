"""
環境配置管理器
提供統一的配置管理接口，支持多種數據庫類型和環境切換
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class DatabaseConfig:
    """數據庫配置數據類"""
    type: str = "sqlite"
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = "proxy_collector.db"
    username: Optional[str] = None
    password: Optional[str] = None
    url: Optional[str] = None
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    echo: bool = False


@dataclass
class RedisConfig:
    """Redis配置數據類"""
    host: str = "localhost"
    port: int = 6379
    database: int = 0
    password: Optional[str] = None
    decode_responses: bool = True
    socket_timeout: int = 5
    connection_pool_size: int = 50


@dataclass
class MonitoringConfig:
    """監控配置數據類"""
    enabled: bool = True
    prometheus_enabled: bool = True
    metrics_endpoint: str = "/metrics"
    health_check_endpoint: str = "/monitoring/health"
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    max_log_size: int = 10485760  # 10MB
    backup_count: int = 5


@dataclass
class SecurityConfig:
    """安全配置數據類"""
    secret_key: str = "your-secret-key-change-this"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"
    cors_origins: list = None
    rate_limit: str = "100/minute"

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["http://localhost:3000", "http://localhost:3001"]


@dataclass
class AppConfig:
    """應用配置數據類"""
    environment: str = "development"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    database: DatabaseConfig = None
    redis: RedisConfig = None
    monitoring: MonitoringConfig = None
    security: SecurityConfig = None

    def __post_init__(self):
        if self.database is None:
            self.database = DatabaseConfig()
        if self.redis is None:
            self.redis = RedisConfig()
        if self.monitoring is None:
            self.monitoring = MonitoringConfig()
        if self.security is None:
            self.security = SecurityConfig()


class ConfigManager:
    """配置管理器主類"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "app_config.json"
        self.env_file = Path(".env")
        self._config_cache = None
        
    def load_config(self, environment: str = None) -> AppConfig:
        """
        加載配置
        
        Args:
            environment: 環境名稱，如果為None則從環境變量讀取
            
        Returns:
            AppConfig: 應用配置對象
        """
        if environment is None:
            environment = os.getenv("ENVIRONMENT", "development")
            
        # 首先嘗試從緩存讀取
        if self._config_cache and self._config_cache.environment == environment:
            return self._config_cache
            
        # 嘗試從配置文件讀取
        config = self._load_from_file(environment)
        if config is None:
            # 創建默認配置
            config = self._create_default_config(environment)
            self.save_config(config)
            
        # 應用環境變量覆蓋
        config = self._apply_env_overrides(config)
        
        # 緩存配置
        self._config_cache = config
        return config
    
    def save_config(self, config: AppConfig) -> None:
        """保存配置到文件"""
        config_data = asdict(config)
        
        # 確保目錄存在
        self.config_dir.mkdir(exist_ok=True)
        
        # 保存到文件
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
            
    def create_environment_config(self, environment: str, database_type: str = "sqlite") -> AppConfig:
        """
        創建特定環境的配置
        
        Args:
            environment: 環境名稱 (development, testing, staging, production)
            database_type: 數據庫類型 (sqlite, postgresql)
            
        Returns:
            AppConfig: 環境配置對象
        """
        config = AppConfig(environment=environment)
        
        # 根據環境設置通用配置
        if environment == "production":
            config.debug = False
            config.workers = 4
            config.monitoring.log_level = "WARNING"
            config.monitoring.echo = False
        elif environment == "testing":
            config.debug = True
            config.workers = 2
            config.monitoring.log_level = "DEBUG"
        else:  # development
            config.debug = True
            config.workers = 1
            config.reload = True
            config.monitoring.log_level = "INFO"
            config.monitoring.echo = True
            
        # 根據數據庫類型設置數據庫配置
        if database_type == "sqlite":
            config.database = DatabaseConfig(
                type="sqlite",
                database=f"data/proxy_collector_{environment}.db",
                echo=config.debug
            )
        elif database_type == "postgresql":
            config.database = DatabaseConfig(
                type="postgresql",
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
                database=os.getenv("DB_NAME", f"proxy_collector_{environment}"),
                username=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "postgres"),
                pool_size=20 if environment == "production" else 10,
                echo=config.debug
            )
            
        # 設置Redis配置
        config.redis = RedisConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            database=int(os.getenv("REDIS_DB", "0"))
        )
        
        return config
    
    def _load_from_file(self, environment: str) -> Optional[AppConfig]:
        """從配置文件加載"""
        if not self.config_file.exists():
            return None
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # 檢查環境匹配
            if config_data.get("environment") != environment:
                return None
                
            # 反序列化配置
            return self._deserialize_config(config_data)
        except Exception as e:
            print(f"警告：加載配置文件失敗: {e}")
            return None
    
    def _create_default_config(self, environment: str) -> AppConfig:
        """創建默認配置"""
        # 檢測數據庫類型
        database_type = os.getenv("DATABASE_TYPE", "sqlite").lower()
        return self.create_environment_config(environment, database_type)
    
    def _apply_env_overrides(self, config: AppConfig) -> AppConfig:
        """應用環境變量覆蓋"""
        # 數據庫配置覆蓋
        if os.getenv("DATABASE_URL"):
            config.database.url = os.getenv("DATABASE_URL")
            
        if os.getenv("DATABASE_TYPE"):
            config.database.type = os.getenv("DATABASE_TYPE").lower()
            
        if os.getenv("DB_HOST"):
            config.database.host = os.getenv("DB_HOST")
            
        if os.getenv("DB_PORT"):
            config.database.port = int(os.getenv("DB_PORT"))
            
        if os.getenv("DB_NAME"):
            config.database.database = os.getenv("DB_NAME")
            
        if os.getenv("DB_USER"):
            config.database.username = os.getenv("DB_USER")
            
        if os.getenv("DB_PASSWORD"):
            config.database.password = os.getenv("DB_PASSWORD")
            
        # Redis配置覆蓋
        if os.getenv("REDIS_URL"):
            # 解析Redis URL
            redis_url = os.getenv("REDIS_URL")
            if "redis://" in redis_url:
                config.redis.host = redis_url.split("://")[1].split(":")[0]
                if ":" in redis_url:
                    config.redis.port = int(redis_url.split(":")[-1].split("/")[0])
                    
        # 監控配置覆蓋
        if os.getenv("MONITORING_ENABLED"):
            config.monitoring.enabled = os.getenv("MONITORING_ENABLED").lower() == "true"
            
        if os.getenv("LOG_LEVEL"):
            config.monitoring.log_level = os.getenv("LOG_LEVEL").upper()
            
        if os.getenv("PROMETHEUS_ENABLED"):
            config.monitoring.prometheus_enabled = os.getenv("PROMETHEUS_ENABLED").lower() == "true"
            
        return config
    
    def _deserialize_config(self, config_data: Dict[str, Any]) -> AppConfig:
        """反序列化配置數據"""
        # 反序列化嵌套對象
        if "database" in config_data:
            config_data["database"] = DatabaseConfig(**config_data["database"])
        if "redis" in config_data:
            config_data["redis"] = RedisConfig(**config_data["redis"])
        if "monitoring" in config_data:
            config_data["monitoring"] = MonitoringConfig(**config_data["monitoring"])
        if "security" in config_data:
            config_data["security"] = SecurityConfig(**config_data["security"])
            
        return AppConfig(**config_data)
    
    def get_database_url(self, config: AppConfig) -> str:
        """
        生成數據庫連接URL
        
        Args:
            config: 應用配置
            
        Returns:
            str: 數據庫連接URL
        """
        if config.database.url:
            return config.database.url
            
        if config.database.type == "sqlite":
            return f"sqlite:///{config.database.database}"
        elif config.database.type == "postgresql":
            return (
                f"postgresql://{config.database.username}:{config.database.password}"
                f"@{config.database.host}:{config.database.port}/{config.database.database}"
            )
        else:
            raise ValueError(f"不支持的數據庫類型: {config.database.type}")
    
    def create_env_file(self, config: AppConfig) -> None:
        """創建環境變量文件"""
        env_content = f"""
# 應用配置
ENVIRONMENT={config.environment}
DEBUG={str(config.debug).lower()}
HOST={config.host}
PORT={config.port}
WORKERS={config.workers}

# 數據庫配置
DATABASE_TYPE={config.database.type}
DATABASE_URL={self.get_database_url(config)}
"""
        
        if config.database.type == "postgresql":
            env_content += f"""
DB_HOST={config.database.host}
DB_PORT={config.database.port}
DB_NAME={config.database.database}
DB_USER={config.database.username}
DB_PASSWORD={config.database.password}
"""
        
        env_content += f"""
# Redis配置
REDIS_URL=redis://{config.redis.host}:{config.redis.port}/{config.redis.database}

# 監控配置
MONITORING_ENABLED={str(config.monitoring.enabled).lower()}
PROMETHEUS_ENABLED={str(config.monitoring.prometheus_enabled).lower()}
LOG_LEVEL={config.monitoring.log_level}
"""
        
        with open(self.env_file, 'w', encoding='utf-8') as f:
            f.write(env_content.strip())


# 全局配置管理器實例
config_manager = ConfigManager()


def get_config(environment: str = None) -> AppConfig:
    """
    獲取應用配置的便捷函數
    
    Args:
        environment: 環境名稱
        
    Returns:
        AppConfig: 應用配置對象
    """
    return config_manager.load_config(environment)


def setup_environment(database_type: str = "sqlite", environment: str = None) -> AppConfig:
    """
    設置運行環境
    
    Args:
        database_type: 數據庫類型
        environment: 環境名稱
        
    Returns:
        AppConfig: 環境配置對象
    """
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")
        
    config = config_manager.create_environment_config(environment, database_type)
    config_manager.save_config(config)
    config_manager.create_env_file(config)
    
    return config


if __name__ == "__main__":
    # 測試配置管理器
    print("測試配置管理器...")
    
    # 創建開發環境配置
    dev_config = setup_environment("sqlite", "development")
    print(f"開發環境配置: {dev_config}")
    
    # 創建生產環境配置
    prod_config = setup_environment("postgresql", "production")
    print(f"生產環境配置: {prod_config}")
    
    # 測試配置加載
    loaded_config = get_config("development")
    print(f"加載的配置: {loaded_config}")
    
    print("配置管理器測試完成！")