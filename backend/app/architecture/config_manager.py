"""
統一配置管理器
提供標準化的配置管理機制
"""
import os
import json
import yaml
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from pydantic import BaseModel, Field, validator
from datetime import datetime
import logging
from app.core.logging import get_logger

logger = get_logger(__name__)


class ConfigValidationError(Exception):
    """配置驗證錯誤"""
    pass


class ConfigSource(BaseModel):
    """配置源信息"""
    name: str
    source_type: str  # file, env, database, remote
    path: Optional[str] = None
    priority: int = 0
    last_loaded: Optional[datetime] = None
    enabled: bool = True


class ConfigSchema(BaseModel):
    """配置架構定義"""
    app_name: str = Field(default="proxy-collector", description="應用名稱")
    debug: bool = Field(default=False, description="調試模式")
    
    # 服務器配置
    host: str = Field(default="0.0.0.0", description="服務器主機")
    port: int = Field(default=8000, ge=1, le=65535, description="服務器端口")
    
    # 數據庫配置
    database_url: str = Field(description="數據庫連接URL")
    
    # Redis配置
    redis_url: str = Field(default="redis://localhost:6379", description="Redis連接URL")
    
    # 日誌配置
    log_level: str = Field(default="INFO", description="日誌級別")
    log_format: str = Field(default="json", description="日誌格式")
    
    # 爬蟲配置
    max_concurrent_requests: int = Field(default=10, ge=1, description="最大並發請求數")
    request_timeout: int = Field(default=30, ge=1, description="請求超時時間（秒）")
    retry_attempts: int = Field(default=3, ge=0, description="重試次數")
    
    # 代理驗證配置
    proxy_test_timeout: int = Field(default=10, ge=1, description="代理測試超時時間（秒）")
    proxy_test_urls: List[str] = Field(
        default=["http://httpbin.org/ip"],
        description="代理測試URL列表"
    )
    
    # 速率限制配置
    rate_limit_enabled: bool = Field(default=True, description="是否啟用速率限制")
    rate_limit_requests_per_minute: int = Field(default=60, ge=1, description="每分鐘請求數限制")
    
    # 安全配置
    secret_key: str = Field(description="應用密鑰")
    cors_origins: List[str] = Field(default=["*"], description="CORS允許的源")
    
    @validator('secret_key', pre=True, always=True)
    def validate_secret_key(cls, v):
        """驗證密鑰"""
        if not v:
            # 生成隨機密鑰
            import secrets
            return secrets.token_urlsafe(32)
        return v
    
    @validator('database_url', pre=True, always=True)
    def validate_database_url(cls, v):
        """驗證數據庫URL"""
        if not v:
            # 默認SQLite數據庫
            return "sqlite:///./proxy_collector.db"
        return v


class ConfigManager:
    """統一配置管理器"""
    
    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置目錄路徑
        """
        self.config_dir = Path(config_dir or "config")
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_sources: List[ConfigSource] = []
        self.config_data: Dict[str, Any] = {}
        self.config_schema: ConfigSchema = ConfigSchema()
        self._setup_default_sources()
        
        logger.info(f"配置管理器初始化完成 - 配置目錄: {self.config_dir}")
    
    def _setup_default_sources(self):
        """設置默認配置源"""
        # 環境變量配置（最高優先級）
        self.add_source(ConfigSource(
            name="environment",
            source_type="env",
            priority=100
        ))
        
        # 本地配置文件
        self.add_source(ConfigSource(
            name="local_config",
            source_type="file",
            path=str(self.config_dir / "local.yaml"),
            priority=80
        ))
        
        # 環境特定配置
        env_config = os.getenv("ENVIRONMENT", "development")
        self.add_source(ConfigSource(
            name=f"{env_config}_config",
            source_type="file",
            path=str(self.config_dir / f"{env_config}.yaml"),
            priority=60
        ))
        
        # 默認配置
        self.add_source(ConfigSource(
            name="default_config",
            source_type="file",
            path=str(self.config_dir / "default.yaml"),
            priority=10
        ))
    
    def add_source(self, source: ConfigSource):
        """添加配置源"""
        self.config_sources.append(source)
        # 按優先級排序（高的在前）
        self.config_sources.sort(key=lambda x: x.priority, reverse=True)
        logger.info(f"添加配置源: {source.name} (優先級: {source.priority})")
    
    def remove_source(self, source_name: str):
        """移除配置源"""
        self.config_sources = [s for s in self.config_sources if s.name != source_name]
        logger.info(f"移除配置源: {source_name}")
    
    async def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        加載配置
        
        Args:
            force_reload: 是否強制重新加載
            
        Returns:
            合併後的配置數據
        """
        if self.config_data and not force_reload:
            return self.config_data
        
        logger.info("開始加載配置...")
        
        merged_config = {}
        loaded_sources = []
        
        # 按優先級加載配置源
        for source in self.config_sources:
            if not source.enabled:
                continue
            
            try:
                config_data = await self._load_source(source)
                if config_data:
                    # 合併配置（高優先級覆蓋低優先級）
                    merged_config.update(config_data)
                    loaded_sources.append(source.name)
                    source.last_loaded = datetime.now()
                    
                    logger.info(f"成功加載配置源: {source.name}")
                
            except Exception as e:
                logger.warning(f"加載配置源失敗: {source.name} - {e}")
        
        # 驗證配置
        try:
            validated_config = self._validate_config(merged_config)
            self.config_data = validated_config
            
            logger.info(f"配置加載完成 - 加載源: {loaded_sources}")
            return self.config_data
            
        except ConfigValidationError as e:
            logger.error(f"配置驗證失敗: {e}")
            raise
    
    async def _load_source(self, source: ConfigSource) -> Optional[Dict[str, Any]]:
        """加載單個配置源"""
        if source.source_type == "file":
            return await self._load_file_source(source)
        elif source.source_type == "env":
            return self._load_env_source()
        else:
            logger.warning(f"不支持的配置源類型: {source.source_type}")
            return None
    
    async def _load_file_source(self, source: ConfigSource) -> Optional[Dict[str, Any]]:
        """加載文件配置源"""
        if not source.path:
            return None
        
        file_path = Path(source.path)
        if not file_path.exists():
            logger.debug(f"配置文件不存在: {file_path}")
            return None
        
        try:
            if file_path.suffix.lower() == '.yaml':
                return await self._load_yaml_file(file_path)
            elif file_path.suffix.lower() == '.json':
                return await self._load_json_file(file_path)
            else:
                logger.warning(f"不支持的配置文件格式: {file_path.suffix}")
                return None
                
        except Exception as e:
            logger.error(f"加載配置文件失敗: {file_path} - {e}")
            return None
    
    async def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """加載YAML文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    async def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """加載JSON文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_env_source(self) -> Dict[str, Any]:
        """加載環境變量配置"""
        env_config = {}
        
        # 環境變量映射
        env_mappings = {
            'APP_NAME': 'app_name',
            'DEBUG': 'debug',
            'HOST': 'host',
            'PORT': 'port',
            'DATABASE_URL': 'database_url',
            'REDIS_URL': 'redis_url',
            'LOG_LEVEL': 'log_level',
            'LOG_FORMAT': 'log_format',
            'MAX_CONCURRENT_REQUESTS': 'max_concurrent_requests',
            'REQUEST_TIMEOUT': 'request_timeout',
            'RETRY_ATTEMPTS': 'retry_attempts',
            'PROXY_TEST_TIMEOUT': 'proxy_test_timeout',
            'RATE_LIMIT_ENABLED': 'rate_limit_enabled',
            'RATE_LIMIT_REQUESTS_PER_MINUTE': 'rate_limit_requests_per_minute',
            'SECRET_KEY': 'secret_key',
            'CORS_ORIGINS': 'cors_origins',
        }
        
        for env_key, config_key in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                # 類型轉換
                if config_key in ['debug', 'rate_limit_enabled']:
                    env_value = env_value.lower() in ('true', '1', 'yes', 'on')
                elif config_key in ['port', 'max_concurrent_requests', 'request_timeout', 
                                   'retry_attempts', 'proxy_test_timeout', 'rate_limit_requests_per_minute']:
                    try:
                        env_value = int(env_value)
                    except ValueError:
                        logger.warning(f"環境變量 {env_key} 轉換為整數失敗: {env_value}")
                        continue
                elif config_key == 'cors_origins':
                    env_value = [origin.strip() for origin in env_value.split(',')]
                
                env_config[config_key] = env_value
        
        if env_config:
            logger.info(f"從環境變量加載 {len(env_config)} 個配置項")
        
        return env_config
    
    def _validate_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證配置數據"""
        try:
            # 使用Pydantic模型驗證
            validated_config = ConfigSchema(**config_data)
            return validated_config.dict()
            
        except Exception as e:
            raise ConfigValidationError(f"配置驗證失敗: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        if not self.config_data:
            return default
        
        # 支持點號分隔的嵌套鍵
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any, save_to_file: bool = False):
        """設置配置值"""
        # 支持點號分隔的嵌套鍵
        keys = key.split('.')
        config = self.config_data
        
        # 遍歷到父級
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 設置值
        config[keys[-1]] = value
        
        logger.info(f"設置配置: {key} = {value}")
        
        if save_to_file:
            self.save_config()
    
    async def save_config(self, file_path: Optional[Union[str, Path]] = None):
        """保存配置到文件"""
        if not file_path:
            file_path = self.config_dir / "local.yaml"
        
        file_path = Path(file_path)
        
        try:
            # 創建備份
            if file_path.exists():
                backup_path = file_path.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml")
                file_path.rename(backup_path)
                logger.info(f"創建配置文件備份: {backup_path}")
            
            # 保存配置
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config_data, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"配置已保存到: {file_path}")
            
        except Exception as e:
            logger.error(f"保存配置失敗: {e}")
            raise
    
    def create_default_config(self):
        """創建默認配置文件"""
        default_config_file = self.config_dir / "default.yaml"
        
        if not default_config_file.exists():
            default_config = {
                "app_name": "proxy-collector",
                "debug": False,
                "host": "0.0.0.0",
                "port": 8000,
                "database_url": "sqlite:///./proxy_collector.db",
                "redis_url": "redis://localhost:6379",
                "log_level": "INFO",
                "log_format": "json",
                "max_concurrent_requests": 10,
                "request_timeout": 30,
                "retry_attempts": 3,
                "proxy_test_timeout": 10,
                "proxy_test_urls": ["http://httpbin.org/ip"],
                "rate_limit_enabled": True,
                "rate_limit_requests_per_minute": 60,
                "secret_key": "your-secret-key-here",
                "cors_origins": ["*"]
            }
            
            try:
                with open(default_config_file, 'w', encoding='utf-8') as f:
                    yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
                
                logger.info(f"創建默認配置文件: {default_config_file}")
                
            except Exception as e:
                logger.error(f"創建默認配置文件失敗: {e}")
    
    def get_config_info(self) -> Dict[str, Any]:
        """獲取配置信息"""
        return {
            "config_dir": str(self.config_dir),
            "loaded_sources": [
                {
                    "name": source.name,
                    "type": source.source_type,
                    "path": source.path,
                    "priority": source.priority,
                    "enabled": source.enabled,
                    "last_loaded": source.last_loaded.isoformat() if source.last_loaded else None
                }
                for source in self.config_sources
            ],
            "config_keys": list(self.config_data.keys()) if self.config_data else [],
            "total_config_items": len(self.config_data) if self.config_data else 0
        }


# 全局配置管理器實例
config_manager = ConfigManager()


async def setup_config() -> Dict[str, Any]:
    """設置配置（供應用啟動時使用）"""
    # 創建默認配置
    config_manager.create_default_config()
    
    # 加載配置
    config = await config_manager.load_config()
    
    # 設置日誌級別
    log_level = config.get("log_level", "INFO")
    logging.getLogger().setLevel(getattr(logging, log_level.upper()))
    
    logger.info("配置設置完成")
    return config