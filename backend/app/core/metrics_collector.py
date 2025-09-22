"""
Prometheus指標收集模塊
提供系統指標的收集和導出功能
"""

import time
import psutil
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("警告: prometheus_client 未安裝，指標收集功能將被禁用")

from .monitoring_config import MonitoringConfig
from .structured_logging import get_logger


@dataclass
class SystemMetrics:
    """系統指標數據類"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    process_count: int
    load_average: tuple


@dataclass
class ApplicationMetrics:
    """應用程序指標數據類"""
    timestamp: datetime
    total_requests: int
    active_connections: int
    response_time_avg: float
    error_rate: float
    proxy_count: int
    validation_count: int
    validation_success_rate: float


class MetricsCollector:
    """指標收集器"""
    
    def __init__(self, config: MonitoringConfig):
        """初始化指標收集器"""
        self.config = config
        self.logger = get_logger("metrics")
        self.prometheus_available = PROMETHEUS_AVAILABLE and config.prometheus_enabled
        
        if self.prometheus_available:
            self._initialize_prometheus_metrics()
        
        # 內部指標存儲
        self._system_metrics: list[SystemMetrics] = []
        self._application_metrics: list[ApplicationMetrics] = []
        self._max_metrics_history = 1000
    
    def _initialize_prometheus_metrics(self):
        """初始化Prometheus指標"""
        if not self.prometheus_available:
            return
        
        try:
            # 系統指標
            self.cpu_usage_gauge = Gauge('proxy_collector_cpu_usage_percent', 'CPU使用率百分比')
            self.memory_usage_gauge = Gauge('proxy_collector_memory_usage_percent', '內存使用率百分比')
            self.disk_usage_gauge = Gauge('proxy_collector_disk_usage_percent', '磁盤使用率百分比')
            self.process_count_gauge = Gauge('proxy_collector_process_count', '進程數量')
            
            # 應用程序指標
            self.requests_total = Counter('proxy_collector_requests_total', '總請求數', ['method', 'endpoint'])
            self.request_duration = Histogram('proxy_collector_request_duration_seconds', '請求持續時間', ['method', 'endpoint'])
            self.active_connections_gauge = Gauge('proxy_collector_active_connections', '活動連接數')
            self.error_rate_gauge = Gauge('proxy_collector_error_rate', '錯誤率百分比')
            
            # 代理相關指標
            self.proxy_count_gauge = Gauge('proxy_collector_proxy_count', '代理數量', ['status'])
            self.validation_total = Counter('proxy_collector_validations_total', '代理驗證總數', ['result'])
            self.validation_duration = Histogram('proxy_collector_validation_duration_seconds', '代理驗證持續時間')
            self.validation_success_rate_gauge = Gauge('proxy_collector_validation_success_rate', '代理驗證成功率')
            
            # 應用信息
            self.app_info = Info('proxy_collector_app_info', '應用程序信息')
            self.app_info.info({
                'version': '1.0.0',
                'name': 'Proxy Collector',
                'description': '代理收集器系統'
            })
            
            self.logger.info("Prometheus指標初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化Prometheus指標失敗: {e}")
            self.prometheus_available = False
    
    def collect_system_metrics(self) -> SystemMetrics:
        """收集系統指標"""
        try:
            # 獲取系統信息
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            processes = len(psutil.pids())
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
            
            metrics = SystemMetrics(
                timestamp=datetime.utcnow(),
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_io={
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                process_count=processes,
                load_average=load_avg
            )
            
            # 更新Prometheus指標
            if self.prometheus_available:
                self.cpu_usage_gauge.set(cpu_usage)
                self.memory_usage_gauge.set(memory.percent)
                self.disk_usage_gauge.set(disk.percent)
                self.process_count_gauge.set(processes)
            
            # 存儲歷史數據
            self._system_metrics.append(metrics)
            if len(self._system_metrics) > self._max_metrics_history:
                self._system_metrics.pop(0)
            
            self.logger.debug(f"系統指標收集完成: CPU={cpu_usage}%, 內存={memory.percent}%")
            return metrics
            
        except Exception as e:
            self.logger.error(f"收集系統指標失敗: {e}")
            raise
    
    def collect_application_metrics(self, 
                                  total_requests: int,
                                  active_connections: int,
                                  response_time_avg: float,
                                  error_rate: float,
                                  proxy_count: int,
                                  validation_count: int,
                                  validation_success_rate: float) -> ApplicationMetrics:
        """收集應用程序指標"""
        try:
            metrics = ApplicationMetrics(
                timestamp=datetime.utcnow(),
                total_requests=total_requests,
                active_connections=active_connections,
                response_time_avg=response_time_avg,
                error_rate=error_rate,
                proxy_count=proxy_count,
                validation_count=validation_count,
                validation_success_rate=validation_success_rate
            )
            
            # 更新Prometheus指標
            if self.prometheus_available:
                self.active_connections_gauge.set(active_connections)
                self.error_rate_gauge.set(error_rate)
                self.proxy_count_gauge.labels(status='total').set(proxy_count)
                self.validation_success_rate_gauge.set(validation_success_rate)
            
            # 存儲歷史數據
            self._application_metrics.append(metrics)
            if len(self._application_metrics) > self._max_metrics_history:
                self._application_metrics.pop(0)
            
            self.logger.debug(f"應用程序指標收集完成: 請求數={total_requests}, 連接數={active_connections}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"收集應用程序指標失敗: {e}")
            raise
    
    def record_request(self, method: str, endpoint: str, duration: float, status_code: int):
        """記錄HTTP請求"""
        if self.prometheus_available:
            self.requests_total.labels(method=method, endpoint=endpoint).inc()
            self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_validation(self, success: bool, duration: float):
        """記錄代理驗證"""
        if self.prometheus_available:
            result = "success" if success else "failure"
            self.validation_total.labels(result=result).inc()
            self.validation_duration.observe(duration)
    
    def update_proxy_count(self, active_count: int, inactive_count: int = 0):
        """更新代理數量"""
        if self.prometheus_available:
            self.proxy_count_gauge.labels(status='active').set(active_count)
            self.proxy_count_gauge.labels(status='inactive').set(inactive_count)
    
    def get_metrics_data(self) -> Dict[str, Any]:
        """獲取所有指標數據"""
        try:
            current_system = self.collect_system_metrics()
            
            return {
                "system": {
                    "cpu_usage": current_system.cpu_usage,
                    "memory_usage": current_system.memory_usage,
                    "disk_usage": current_system.disk_usage,
                    "process_count": current_system.process_count,
                    "load_average": current_system.load_average,
                    "network_io": current_system.network_io
                },
                "prometheus_available": self.prometheus_available,
                "metrics_history_size": {
                    "system": len(self._system_metrics),
                    "application": len(self._application_metrics)
                }
            }
        except Exception as e:
            self.logger.error(f"獲取指標數據失敗: {e}")
            return {"error": str(e)}
    
    def get_prometheus_metrics(self) -> Optional[bytes]:
        """獲取Prometheus格式的指標數據"""
        if not self.prometheus_available:
            return None
        
        try:
            return generate_latest()
        except Exception as e:
            self.logger.error(f"生成Prometheus指標失敗: {e}")
            return None
    
    def check_health(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            metrics = self.collect_system_metrics()
            
            # 檢查閾值
            alerts = []
            thresholds = self.config.alert_thresholds
            
            if metrics.cpu_usage > thresholds.get("cpu_usage", 80):
                alerts.append(f"CPU使用率過高: {metrics.cpu_usage}%")
            
            if metrics.memory_usage > thresholds.get("memory_usage", 85):
                alerts.append(f"內存使用率過高: {metrics.memory_usage}%")
            
            if metrics.disk_usage > thresholds.get("disk_usage", 90):
                alerts.append(f"磁盤使用率過高: {metrics.disk_usage}%")
            
            return {
                "status": "healthy" if not alerts else "warning",
                "alerts": alerts,
                "metrics": {
                    "cpu_usage": metrics.cpu_usage,
                    "memory_usage": metrics.memory_usage,
                    "disk_usage": metrics.disk_usage
                }
            }
            
        except Exception as e:
            self.logger.error(f"健康檢查失敗: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "alerts": ["健康檢查失敗"]
            }


# 全局指標收集器實例
_collector: Optional[MetricsCollector] = None


def get_metrics_collector(config: Optional[MonitoringConfig] = None) -> MetricsCollector:
    """獲取指標收集器實例"""
    global _collector
    
    if _collector is None:
        if config is None:
            config = MonitoringConfig.from_env()
        _collector = MetricsCollector(config)
    
    return _collector