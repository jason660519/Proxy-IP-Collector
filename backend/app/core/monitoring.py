"""
監控集成模塊
提供與Prometheus和Grafana的集成，導出應用程序指標
"""

import time
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
import psutil

try:
    import aiohttp.web
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from .health_check import get_health_manager, get_metrics_collector
from .config_manager import get_config
from .database_manager import get_db_manager
import json


logger = logging.getLogger(__name__)


# Prometheus指標定義
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

DATABASE_CONNECTIONS = Gauge(
    'database_connections_total',
    'Total number of database connections',
    ['database_type']
)

SYSTEM_CPU_USAGE = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)

SYSTEM_MEMORY_USAGE = Gauge(
    'system_memory_usage_percent',
    'System memory usage percentage'
)

SYSTEM_DISK_USAGE = Gauge(
    'system_disk_usage_percent',
    'System disk usage percentage'
)

APPLICATION_UPTIME = Gauge(
    'application_uptime_seconds',
    'Application uptime in seconds'
)

ERROR_COUNT = Counter(
    'application_errors_total',
    'Total number of application errors',
    ['error_type']
)

PROXY_COUNT = Gauge(
    'proxy_count_total',
    'Total number of proxies in database',
    ['status', 'protocol']
)

TASK_QUEUE_SIZE = Gauge(
    'task_queue_size',
    'Current task queue size'
)

HEALTH_CHECK_STATUS = Gauge(
    'health_check_status',
    'Health check status (1=healthy, 0=unhealthy)',
    ['component']
)


class MetricsExporter:
    """指標導出器"""
    
    def __init__(self):
        self.config = get_config()
        self.health_manager = get_health_manager()
        self.metrics_collector = get_metrics_collector()
        self.start_time = datetime.now()
        self.is_running = False
        self.update_interval = 15  # 秒
        
    async def update_system_metrics(self) -> None:
        """更新系統指標"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            SYSTEM_CPU_USAGE.set(cpu_percent)
            
            # 內存使用率
            memory = psutil.virtual_memory()
            SYSTEM_MEMORY_USAGE.set(memory.percent)
            
            # 磁盤使用率
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            SYSTEM_DISK_USAGE.set(disk_percent)
            
            # 應用程序運行時間
            uptime = (datetime.now() - self.start_time).total_seconds()
            APPLICATION_UPTIME.set(uptime)
            
            logger.debug(f"系統指標更新完成 - CPU: {cpu_percent}%, 內存: {memory.percent}%, 磁盤: {disk_percent:.1f}%")
            
        except Exception as e:
            logger.error(f"更新系統指標失敗: {e}")
    
    async def update_health_metrics(self) -> None:
        """更新健康檢查指標"""
        try:
            # 運行健康檢查
            results = await self.health_manager.run_all_checks()
            
            for component, result in results.items():
                # 將健康狀態轉換為數值
                status_value = 1 if result.status.value == "healthy" else 0
                HEALTH_CHECK_STATUS.labels(component=component).set(status_value)
            
            logger.debug(f"健康檢查指標更新完成 - 檢查了 {len(results)} 個組件")
            
        except Exception as e:
            logger.error(f"更新健康檢查指標失敗: {e}")
    
    async def update_application_metrics(self) -> None:
        """更新應用程序指標"""
        try:
            # 獲取當前應用程序指標
            app_metrics = self.metrics_collector.get_current_metrics()
            
            # 更新活動連接數
            ACTIVE_CONNECTIONS.set(app_metrics.active_connections)
            
            # 更新數據庫連接數
            db_manager = get_db_manager()
            health = await db_manager.health_check()
            
            if health.get("status") == "healthy":
                db_type = health.get("database_type", "unknown")
                connections = health.get("connection_count", 0)
                DATABASE_CONNECTIONS.labels(database_type=db_type).set(connections)
            
            logger.debug(f"應用程序指標更新完成")
            
        except Exception as e:
            logger.error(f"更新應用程序指標失敗: {e}")
    
    async def update_proxy_metrics(self) -> None:
        """更新代理指標"""
        try:
            # 從數據庫獲取代理統計
            db_manager = get_db_manager()
            
            # 獲取不同狀態的代理數量
            status_query = """
            SELECT status, COUNT(*) as count
            FROM proxies
            GROUP BY status
            """
            
            try:
                status_results = await db_manager.fetch_all(status_query)
                
                # 重置所有代理指標
                for status in ['active', 'inactive', 'failed', 'unknown']:
                    for protocol in ['http', 'https', 'socks4', 'socks5', 'all']:
                        PROXY_COUNT.labels(status=status, protocol=protocol).set(0)
                
                # 設置實際值
                for row in status_results:
                    status = row.get('status', 'unknown')
                    count = row.get('count', 0)
                    PROXY_COUNT.labels(status=status, protocol='all').set(count)
                
                logger.debug(f"代理指標更新完成 - 統計了 {len(status_results)} 種狀態")
                
            except Exception as e:
                logger.warning(f"無法從數據庫獲取代理統計: {e}")
                
        except Exception as e:
            logger.error(f"更新代理指標失敗: {e}")
    
    async def start_metrics_collection(self, interval: int = 15) -> None:
        """啟動指標收集"""
        self.is_running = True
        self.update_interval = interval
        
        logger.info(f"啟動指標收集，更新間隔: {interval}秒")
        
        while self.is_running:
            try:
                await asyncio.gather(
                    self.update_system_metrics(),
                    self.update_health_metrics(),
                    self.update_application_metrics(),
                    self.update_proxy_metrics()
                )
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"指標收集循環出錯: {e}")
                await asyncio.sleep(interval)
    
    def stop_metrics_collection(self) -> None:
        """停止指標收集"""
        self.is_running = False
        logger.info("指標收集已停止")
    
    def get_metrics_data(self) -> bytes:
        """獲取Prometheus格式的指標數據"""
        return generate_latest()


class PrometheusExporter:
    """Prometheus指標導出器"""
    
    def __init__(self):
        self.metrics_exporter = MetricsExporter()
        self.is_running = False
        self.server = None
        
    async def handle_metrics_request(self, request):
        """處理指標請求"""
        if not AIOHTTP_AVAILABLE:
            return None
            
        try:
            # 更新指標
            await self.metrics_exporter.update_system_metrics()
            await self.metrics_exporter.update_health_metrics()
            
            # 獲取指標數據
            metrics_data = self.metrics_exporter.get_metrics_data()
            
            return aiohttp.web.Response(
                body=metrics_data,
                content_type=CONTENT_TYPE_LATEST,
                headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
            )
            
        except Exception as e:
            logger.error(f"處理指標請求失敗: {e}")
            return aiohttp.web.Response(
                text=f"Error generating metrics: {str(e)}",
                status=500
            )
    
    async def start_prometheus_server(self, host: str = "0.0.0.0", port: int = 9091) -> None:
        """啟動Prometheus指標服務器"""
        if not AIOHTTP_AVAILABLE:
            logger.warning("aiohttp未安裝，無法啟動Prometheus服務器")
            return
            
        try:
            app = aiohttp.web.Application()
            app.router.add_get('/metrics', self.handle_metrics_request)
            app.router.add_get('/health', self.handle_health_request)
            
            runner = aiohttp.web.AppRunner(app)
            await runner.setup()
            
            site = aiohttp.web.TCPSite(runner, host, port)
            await site.start()
            
            self.server = runner
            self.is_running = True
            
            logger.info(f"Prometheus指標服務器啟動成功 - {host}:{port}")
            
        except Exception as e:
            logger.error(f"啟動Prometheus服務器失敗: {e}")
    
    async def handle_health_request(self, request):
        """處理健康檢查請求"""
        if not AIOHTTP_AVAILABLE:
            return None
            
        try:
            from .health_check import run_health_check
            health_data = await run_health_check()
            
            return aiohttp.web.Response(
                text=json.dumps(health_data, ensure_ascii=False, indent=2),
                content_type="application/json",
                headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
            )
            
        except Exception as e:
            logger.error(f"處理健康檢查請求失敗: {e}")
            return aiohttp.web.Response(
                text=json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False),
                content_type="application/json",
                status=500
            )
    
    def stop_prometheus_server(self) -> None:
        """停止Prometheus服務器"""
        if self.server:
            asyncio.create_task(self.server.cleanup())
            self.is_running = False
            logger.info("Prometheus服務器已停止")


class GrafanaDashboard:
    """Grafana儀表板配置"""
    
    def __init__(self):
        self.config = get_config()
    
    def generate_dashboard_config(self) -> Dict[str, Any]:
        """生成Grafana儀表板配置"""
        dashboard = {
            "dashboard": {
                "id": None,
                "title": "代理收集器監控儀表板",
                "tags": ["proxy-collector", "monitoring"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "系統CPU使用率",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "system_cpu_usage_percent",
                                "legendFormat": "CPU使用率"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {
                                    "mode": "thresholds"
                                },
                                "thresholds": {
                                    "steps": [
                                        {"color": "green", "value": None},
                                        {"color": "yellow", "value": 70},
                                        {"color": "red", "value": 90}
                                    ]
                                },
                                "unit": "percent"
                            }
                        }
                    },
                    {
                        "id": 2,
                        "title": "系統內存使用率",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "system_memory_usage_percent",
                                "legendFormat": "內存使用率"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {
                                    "mode": "thresholds"
                                },
                                "thresholds": {
                                    "steps": [
                                        {"color": "green", "value": None},
                                        {"color": "yellow", "value": 70},
                                        {"color": "red", "value": 90}
                                    ]
                                },
                                "unit": "percent"
                            }
                        }
                    },
                    {
                        "id": 3,
                        "title": "HTTP請求總數",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(http_requests_total[5m])",
                                "legendFormat": "{{method}} {{endpoint}} {{status_code}}"
                            }
                        ]
                    },
                    {
                        "id": 4,
                        "title": "HTTP請求持續時間",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])",
                                "legendFormat": "平均響應時間"
                            }
                        ]
                    },
                    {
                        "id": 5,
                        "title": "代理數量統計",
                        "type": "piechart",
                        "targets": [
                            {
                                "expr": "proxy_count_total",
                                "legendFormat": "{{status}}"
                            }
                        ]
                    },
                    {
                        "id": 6,
                        "title": "健康檢查狀態",
                        "type": "table",
                        "targets": [
                            {
                                "expr": "health_check_status",
                                "legendFormat": "{{component}}"
                            }
                        ]
                    },
                    {
                        "id": 7,
                        "title": "數據庫連接數",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "database_connections_total",
                                "legendFormat": "{{database_type}}"
                            }
                        ]
                    },
                    {
                        "id": 8,
                        "title": "應用程序運行時間",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "application_uptime_seconds",
                                "legendFormat": "運行時間"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "s"
                            }
                        }
                    }
                ],
                "time": {
                    "from": "now-1h",
                    "to": "now"
                },
                "refresh": "30s"
            }
        }
        
        return dashboard
    
    def save_dashboard_config(self, filepath: str) -> None:
        """保存儀表板配置到文件"""
        try:
            import json
            dashboard_config = self.generate_dashboard_config()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(dashboard_config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Grafana儀表板配置已保存到: {filepath}")
            
        except Exception as e:
            logger.error(f"保存Grafana儀表板配置失敗: {e}")


# 全局實例
_metrics_exporter: Optional[MetricsExporter] = None
_prometheus_exporter: Optional[PrometheusExporter] = None
_grafana_dashboard: Optional[GrafanaDashboard] = None


def get_metrics_exporter() -> MetricsExporter:
    """獲取指標導出器"""
    global _metrics_exporter
    if _metrics_exporter is None:
        _metrics_exporter = MetricsExporter()
    return _metrics_exporter


def get_prometheus_exporter() -> PrometheusExporter:
    """獲取Prometheus導出器"""
    global _prometheus_exporter
    if _prometheus_exporter is None:
        _prometheus_exporter = PrometheusExporter()
    return _prometheus_exporter


def get_grafana_dashboard() -> GrafanaDashboard:
    """獲取Grafana儀表板"""
    global _grafana_dashboard
    if _grafana_dashboard is None:
        _grafana_dashboard = GrafanaDashboard()
    return _grafana_dashboard


async def initialize_monitoring() -> None:
    """初始化監控系統"""
    try:
        # 初始化指標導出器
        metrics_exporter = get_metrics_exporter()
        
        # 啟動指標收集
        asyncio.create_task(metrics_exporter.start_metrics_collection())
        
        # 初始化Prometheus導出器
        prometheus_exporter = get_prometheus_exporter()
        
        # 啟動Prometheus服務器
        await prometheus_exporter.start_prometheus_server()
        
        logger.info("監控系統初始化完成")
        
    except Exception as e:
        logger.error(f"監控系統初始化失敗: {e}")
        raise


if __name__ == "__main__":
    # 測試監控系統
    import asyncio
    
    async def test_monitoring():
        print("測試監控系統...")
        
        # 初始化監控
        await initialize_monitoring()
        
        # 測試指標收集
        metrics_exporter = get_metrics_exporter()
        await metrics_exporter.update_system_metrics()
        
        # 測試Grafana儀表板
        grafana = get_grafana_dashboard()
        dashboard_config = grafana.generate_dashboard_config()
        print(f"Grafana儀表板配置生成完成，包含 {len(dashboard_config['dashboard']['panels'])} 個面板")
        
        print("監控系統測試完成！")
        
        # 保持運行一段時間
        await asyncio.sleep(30)
        
        # 停止監控
        metrics_exporter.stop_metrics_collection()
        prometheus_exporter = get_prometheus_exporter()
        prometheus_exporter.stop_prometheus_server()
    
    asyncio.run(test_monitoring())