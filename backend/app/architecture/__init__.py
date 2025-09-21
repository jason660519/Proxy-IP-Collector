"""
統一架構模塊
提供標準化的服務架構實現
"""
from .unified_server import UnifiedServer
from .api_standard import (
    ApiStatus, HealthStatus, BaseResponse, HealthResponse,
    ProxyStatsResponse, ScrapingTaskResponse, ScrapingStatusResponse,
    create_success_response, create_error_response, create_health_response
)
from .health_check import (
    HealthCheckResult, BaseHealthCheck, DatabaseHealthCheck,
    RedisHealthCheck, APIHealthCheck, MemoryHealthCheck,
    DiskHealthCheck, UnifiedHealthChecker, health_checker, get_health_status
)
from .config_manager import (
    ConfigManager, ConfigSchema, ConfigSource, ConfigValidationError,
    config_manager, setup_config
)
from .service_launcher import (
    ServiceLauncher, service_launcher, create_app, run_service, run_service_sync
)

__all__ = [
    # 統一服務器
    'UnifiedServer',
    
    # API標準化
    'ApiStatus', 'HealthStatus', 'BaseResponse', 'HealthResponse',
    'ProxyStatsResponse', 'ScrapingTaskResponse', 'ScrapingStatusResponse',
    'create_success_response', 'create_error_response', 'create_health_response',
    
    # 健康檢查
    'HealthCheckResult', 'BaseHealthCheck', 'DatabaseHealthCheck',
    'RedisHealthCheck', 'APIHealthCheck', 'MemoryHealthCheck',
    'DiskHealthCheck', 'UnifiedHealthChecker', 'health_checker', 'get_health_status',
    
    # 配置管理
    'ConfigManager', 'ConfigSchema', 'ConfigSource', 'ConfigValidationError',
    'config_manager', 'setup_config',
    
    # 服務啟動器
    'ServiceLauncher', 'service_launcher', 'create_app', 'run_service', 'run_service_sync'
]