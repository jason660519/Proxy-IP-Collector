"""
監控配置模塊
配置Prometheus指標收集和結構化日誌
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class MonitoringConfig:
    """監控配置類"""
    
    # Prometheus配置
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    prometheus_metrics_path: str = "/metrics"
    
    # 日誌配置
    log_level: str = "INFO"
    log_format: str = "json"  # json 或 text
    log_file: Optional[str] = None
    log_max_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    
    # 性能監控
    enable_performance_monitoring: bool = True
    performance_metrics_interval: int = 60  # 秒
    
    # 健康檢查
    health_check_interval: int = 30  # 秒
    health_check_timeout: int = 10  # 秒
    
    # 告警配置
    alerting_enabled: bool = True
    alert_thresholds: Dict[str, float] = None
    
    def __post_init__(self):
        """初始化後處理"""
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                "cpu_usage": 80.0,
                "memory_usage": 85.0,
                "disk_usage": 90.0,
                "response_time": 5.0,
                "error_rate": 5.0,
                "proxy_failure_rate": 20.0
            }
    
    @classmethod
    def from_env(cls) -> 'MonitoringConfig':
        """從環境變量加載配置"""
        return cls(
            prometheus_enabled=os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true",
            prometheus_port=int(os.getenv("PROMETHEUS_PORT", "9090")),
            prometheus_metrics_path=os.getenv("PROMETHEUS_METRICS_PATH", "/metrics"),
            
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_format=os.getenv("LOG_FORMAT", "json"),
            log_file=os.getenv("LOG_FILE"),
            log_max_size=int(os.getenv("LOG_MAX_SIZE", str(10 * 1024 * 1024))),
            log_backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5")),
            
            enable_performance_monitoring=os.getenv("ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true",
            performance_metrics_interval=int(os.getenv("PERFORMANCE_METRICS_INTERVAL", "60")),
            
            health_check_interval=int(os.getenv("HEALTH_CHECK_INTERVAL", "30")),
            health_check_timeout=int(os.getenv("HEALTH_CHECK_TIMEOUT", "10")),
            
            alerting_enabled=os.getenv("ALERTING_ENABLED", "true").lower() == "true"
        )


# 預定義配置實例
DEFAULT_CONFIG = MonitoringConfig()
DEVELOPMENT_CONFIG = MonitoringConfig(
    log_level="DEBUG",
    prometheus_enabled=True,
    enable_performance_monitoring=True,
    alerting_enabled=False  # 開發環境禁用告警
)

PRODUCTION_CONFIG = MonitoringConfig(
    log_level="INFO",
    prometheus_enabled=True,
    enable_performance_monitoring=True,
    alerting_enabled=True,
    log_file="logs/app.log"
)