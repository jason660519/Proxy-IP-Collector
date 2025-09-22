"""
健康檢查和監控集成模塊
提供系統健康狀態檢查、指標收集和監控告警功能
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import psutil
import aiohttp
from collections import defaultdict, deque

from .database_manager import get_db_manager
from .config_manager import get_config


logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """健康狀態枚舉"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """健康檢查結果"""
    component: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    response_time_ms: float


@dataclass
class SystemMetrics:
    """系統指標"""
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io: Dict[str, int]
    process_count: int
    load_average: List[float]
    timestamp: datetime


@dataclass
class ApplicationMetrics:
    """應用程序指標"""
    total_requests: int
    active_connections: int
    error_count: int
    average_response_time: float
    uptime_seconds: int
    database_connections: int
    redis_connections: int
    timestamp: datetime


class HealthCheckManager:
    """健康檢查管理器"""
    
    def __init__(self):
        self.config = get_config()
        self.checks: Dict[str, Callable] = {}
        self.results: Dict[str, HealthCheckResult] = {}
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.last_check_time: Optional[datetime] = None
        self.is_running = False
        self.check_interval = 30  # 秒
        
        # 註冊默認檢查
        self._register_default_checks()
    
    def _register_default_checks(self) -> None:
        """註冊默認的健康檢查"""
        self.register_check("database", self.check_database)
        self.register_check("redis", self.check_redis)
        self.register_check("system", self.check_system_resources)
        self.register_check("disk_space", self.check_disk_space)
        self.register_check("memory_usage", self.check_memory_usage)
        self.register_check("external_services", self.check_external_services)
    
    def register_check(self, name: str, check_function: Callable) -> None:
        """註冊健康檢查函數"""
        self.checks[name] = check_function
        logger.info(f"已註冊健康檢查: {name}")
    
    async def check_database(self) -> HealthCheckResult:
        """檢查數據庫健康狀態"""
        start_time = time.time()
        
        try:
            db_manager = get_db_manager()
            health = await db_manager.health_check()
            
            response_time = (time.time() - start_time) * 1000
            
            if health.get("status") == "healthy":
                status = HealthStatus.HEALTHY
                message = "數據庫連接正常"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"數據庫連接異常: {health.get('message', '未知錯誤')}"
            
            return HealthCheckResult(
                component="database",
                status=status,
                message=message,
                details=health,
                timestamp=datetime.now(),
                response_time_ms=response_time
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="database",
                status=HealthStatus.UNHEALTHY,
                message=f"數據庫檢查失敗: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time_ms=response_time
            )
    
    async def check_redis(self) -> HealthCheckResult:
        """檢查Redis健康狀態"""
        start_time = time.time()
        
        try:
            # 嘗試導入Redis客戶端
            try:
                import redis.asyncio as redis
            except ImportError:
                return HealthCheckResult(
                    component="redis",
                    status=HealthStatus.UNKNOWN,
                    message="Redis依賴未安裝",
                    details={},
                    timestamp=datetime.now(),
                    response_time_ms=0
                )
            
            # 創建Redis客戶端
            redis_client = redis.Redis(
                host=self.config.redis.host,
                port=self.config.redis.port,
                password=self.config.redis.password if hasattr(self.config, 'redis') else None,
                decode_responses=True
            )
            
            # 測試連接
            await redis_client.ping()
            info = await redis_client.info()
            
            response_time = (time.time() - start_time) * 1000
            
            await redis_client.close()
            
            return HealthCheckResult(
                component="redis",
                status=HealthStatus.HEALTHY,
                message="Redis連接正常",
                details={
                    "version": info.get("redis_version"),
                    "connected_clients": info.get("connected_clients"),
                    "used_memory_human": info.get("used_memory_human"),
                    "keyspace_hits": info.get("keyspace_hits"),
                    "keyspace_misses": info.get("keyspace_misses")
                },
                timestamp=datetime.now(),
                response_time_ms=response_time
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis連接失敗: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time_ms=response_time
            )
    
    async def check_system_resources(self) -> HealthCheckResult:
        """檢查系統資源使用情況"""
        start_time = time.time()
        
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 內存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁盤使用率
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # 系統負載
            load_average = list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            response_time = (time.time() - start_time) * 1000
            
            # 判斷狀態
            if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = "系統資源使用率過高"
            elif cpu_percent > 70 or memory_percent > 70 or disk_percent > 70:
                status = HealthStatus.DEGRADED
                message = "系統資源使用率較高"
            else:
                status = HealthStatus.HEALTHY
                message = "系統資源使用正常"
            
            details = {
                "cpu_percent": round(cpu_percent, 2),
                "memory_percent": round(memory_percent, 2),
                "disk_percent": round(disk_percent, 2),
                "load_average": load_average,
                "available_memory_gb": round(memory.available / (1024**3), 2),
                "total_memory_gb": round(memory.total / (1024**3), 2)
            }
            
            return HealthCheckResult(
                component="system",
                status=status,
                message=message,
                details=details,
                timestamp=datetime.now(),
                response_time_ms=response_time
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="system",
                status=HealthStatus.UNKNOWN,
                message=f"系統資源檢查失敗: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time_ms=response_time
            )
    
    async def check_disk_space(self) -> HealthCheckResult:
        """檢查磁盤空間"""
        start_time = time.time()
        
        try:
            disk = psutil.disk_usage('/')
            free_percent = (disk.free / disk.total) * 100
            used_percent = (disk.used / disk.total) * 100
            
            response_time = (time.time() - start_time) * 1000
            
            if free_percent < 10:
                status = HealthStatus.UNHEALTHY
                message = "磁盤空間不足"
            elif free_percent < 20:
                status = HealthStatus.DEGRADED
                message = "磁盤空間較少"
            else:
                status = HealthStatus.HEALTHY
                message = "磁盤空間充足"
            
            details = {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_percent": round(used_percent, 2),
                "free_percent": round(free_percent, 2)
            }
            
            return HealthCheckResult(
                component="disk_space",
                status=status,
                message=message,
                details=details,
                timestamp=datetime.now(),
                response_time_ms=response_time
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="disk_space",
                status=HealthStatus.UNKNOWN,
                message=f"磁盤空間檢查失敗: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time_ms=response_time
            )
    
    async def check_memory_usage(self) -> HealthCheckResult:
        """檢查內存使用情況"""
        start_time = time.time()
        
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            response_time = (time.time() - start_time) * 1000
            
            if memory.percent > 90 or swap.percent > 80:
                status = HealthStatus.UNHEALTHY
                message = "內存使用率過高"
            elif memory.percent > 70 or swap.percent > 50:
                status = HealthStatus.DEGRADED
                message = "內存使用率較高"
            else:
                status = HealthStatus.HEALTHY
                message = "內存使用正常"
            
            details = {
                "memory_percent": round(memory.percent, 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2),
                "swap_percent": round(swap.percent, 2),
                "swap_used_gb": round(swap.used / (1024**3), 2)
            }
            
            return HealthCheckResult(
                component="memory_usage",
                status=status,
                message=message,
                details=details,
                timestamp=datetime.now(),
                response_time_ms=response_time
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="memory_usage",
                status=HealthStatus.UNKNOWN,
                message=f"內存使用檢查失敗: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time_ms=response_time
            )
    
    async def check_external_services(self) -> HealthCheckResult:
        """檢查外部服務"""
        start_time = time.time()
        
        try:
            services = []
            
            # 檢查Prometheus
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                    async with session.get(f"http://{self.config.monitoring.prometheus_host}:9090/-/healthy") as response:
                        prometheus_status = response.status == 200
                        services.append({"name": "prometheus", "status": "healthy" if prometheus_status else "unhealthy"})
            except Exception:
                services.append({"name": "prometheus", "status": "unreachable"})
            
            # 檢查Grafana
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                    async with session.get(f"http://{self.config.monitoring.grafana_host}:3000/api/health") as response:
                        grafana_status = response.status == 200
                        services.append({"name": "grafana", "status": "healthy" if grafana_status else "unhealthy"})
            except Exception:
                services.append({"name": "grafana", "status": "unreachable"})
            
            response_time = (time.time() - start_time) * 1000
            
            # 判斷整體狀態
            unhealthy_services = [s for s in services if s["status"] != "healthy"]
            
            if not services:
                status = HealthStatus.UNKNOWN
                message = "無外部服務配置"
            elif len(unhealthy_services) == len(services):
                status = HealthStatus.UNHEALTHY
                message = "所有外部服務都不可用"
            elif unhealthy_services:
                status = HealthStatus.DEGRADED
                message = f"{len(unhealthy_services)}個外部服務不可用"
            else:
                status = HealthStatus.HEALTHY
                message = "所有外部服務都正常"
            
            return HealthCheckResult(
                component="external_services",
                status=status,
                message=message,
                details={"services": services},
                timestamp=datetime.now(),
                response_time_ms=response_time
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="external_services",
                status=HealthStatus.UNKNOWN,
                message=f"外部服務檢查失敗: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time_ms=response_time
            )
    
    async def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """運行所有註冊的健康檢查"""
        results = {}
        
        # 並行執行所有檢查
        tasks = []
        for name, check_func in self.checks.items():
            task = asyncio.create_task(check_func())
            tasks.append((name, task))
        
        # 等待所有檢查完成
        for name, task in tasks:
            try:
                result = await task
                results[name] = result
                self.results[name] = result
                
                # 記錄歷史數據
                self.metrics_history[name].append(result)
                
            except Exception as e:
                logger.error(f"健康檢查 {name} 失敗: {e}")
                results[name] = HealthCheckResult(
                    component=name,
                    status=HealthStatus.UNKNOWN,
                    message=f"檢查失敗: {str(e)}",
                    details={"error": str(e)},
                    timestamp=datetime.now(),
                    response_time_ms=0
                )
        
        self.last_check_time = datetime.now()
        return results
    
    def get_overall_status(self, results: Dict[str, HealthCheckResult]) -> HealthStatus:
        """獲取整體健康狀態"""
        if not results:
            return HealthStatus.UNKNOWN
        
        statuses = [result.status for result in results.values()]
        
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        elif HealthStatus.UNKNOWN in statuses:
            return HealthStatus.UNKNOWN
        else:
            return HealthStatus.HEALTHY
    
    def get_health_summary(self, results: Dict[str, HealthCheckResult]) -> Dict[str, Any]:
        """獲取健康檢查摘要"""
        overall_status = self.get_overall_status(results)
        
        summary = {
            "status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "summary": {
                "total": len(results),
                "healthy": sum(1 for r in results.values() if r.status == HealthStatus.HEALTHY),
                "unhealthy": sum(1 for r in results.values() if r.status == HealthStatus.UNHEALTHY),
                "degraded": sum(1 for r in results.values() if r.status == HealthStatus.DEGRADED),
                "unknown": sum(1 for r in results.values() if r.status == HealthStatus.UNKNOWN)
            }
        }
        
        for name, result in results.items():
            summary["checks"][name] = {
                "status": result.status.value,
                "message": result.message,
                "response_time_ms": round(result.response_time_ms, 2),
                "details": result.details
            }
        
        return summary
    
    async def start_periodic_checks(self, interval: int = 30) -> None:
        """啟動定期健康檢查"""
        self.check_interval = interval
        self.is_running = True
        
        logger.info(f"啟動定期健康檢查，間隔: {interval}秒")
        
        while self.is_running:
            try:
                results = await self.run_all_checks()
                summary = self.get_health_summary(results)
                
                # 記錄健康狀態
                logger.info(f"健康檢查完成，整體狀態: {summary['status']}")
                
                # 如果配置了告警，發送告警
                if summary["summary"]["unhealthy"] > 0:
                    await self.send_alerts(summary)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"定期健康檢查出錯: {e}")
                await asyncio.sleep(interval)
    
    def stop_periodic_checks(self) -> None:
        """停止定期健康檢查"""
        self.is_running = False
        logger.info("定期健康檢查已停止")
    
    async def send_alerts(self, summary: Dict[str, Any]) -> None:
        """發送告警"""
        try:
            # 這裡可以集成各種告警方式
            # 例如：郵件、短信、Slack、企業微信等
            
            unhealthy_checks = [
                name for name, check in summary["checks"].items()
                if check["status"] == "unhealthy"
            ]
            
            if unhealthy_checks:
                logger.warning(f"系統健康檢查發現異常組件: {', '.join(unhealthy_checks)}")
                
                # 可以在此處添加實際的告警發送邏輯
                # await self.send_email_alert(summary)
                # await self.send_slack_alert(summary)
                
        except Exception as e:
            logger.error(f"發送告警失敗: {e}")


class MetricsCollector:
    """指標收集器"""
    
    def __init__(self):
        self.config = get_config()
        self.metrics: Dict[str, Any] = {}
        self.start_time = datetime.now()
        self.request_count = 0
        self.error_count = 0
        self.response_times = deque(maxlen=1000)
        
    def record_request(self, response_time: float, status_code: int) -> None:
        """記錄請求指標"""
        self.request_count += 1
        self.response_times.append(response_time)
        
        if status_code >= 400:
            self.error_count += 1
    
    def get_current_metrics(self) -> ApplicationMetrics:
        """獲取當前應用程序指標"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        avg_response_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times else 0
        )
        
        return ApplicationMetrics(
            total_requests=self.request_count,
            active_connections=0,  # 可以從連接池獲取
            error_count=self.error_count,
            average_response_time=avg_response_time,
            uptime_seconds=int(uptime),
            database_connections=0,  # 可以從數據庫管理器獲取
            redis_connections=0,  # 可以從Redis客戶端獲取
            timestamp=datetime.now()
        )
    
    def get_system_metrics(self) -> SystemMetrics:
        """獲取系統指標"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 網絡IO
        net_io = psutil.net_io_counters()
        network_io = {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }
        
        # 進程數
        process_count = len(psutil.pids())
        
        # 系統負載
        load_average = list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_usage_percent=(disk.used / disk.total) * 100,
            network_io=network_io,
            process_count=process_count,
            load_average=load_average,
            timestamp=datetime.now()
        )


# 全局實例
_health_manager: Optional[HealthCheckManager] = None
_metrics_collector: Optional[MetricsCollector] = None


def get_health_manager() -> HealthCheckManager:
    """獲取健康檢查管理器"""
    global _health_manager
    if _health_manager is None:
        _health_manager = HealthCheckManager()
    return _health_manager


def get_metrics_collector() -> MetricsCollector:
    """獲取指標收集器"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


async def initialize_health_check() -> HealthCheckManager:
    """初始化健康檢查系統"""
    health_manager = get_health_manager()
    logger.info("健康檢查系統初始化完成")
    return health_manager


async def run_health_check() -> Dict[str, Any]:
    """運行健康檢查"""
    health_manager = get_health_manager()
    results = await health_manager.run_all_checks()
    return health_manager.get_health_summary(results)


if __name__ == "__main__":
    # 測試健康檢查
    import asyncio
    
    async def test_health_check():
        print("測試健康檢查系統...")
        
        # 初始化
        health_manager = await initialize_health_check()
        
        # 運行檢查
        results = await health_manager.run_all_checks()
        summary = health_manager.get_health_summary(results)
        
        print(f"健康檢查摘要: {json.dumps(summary, indent=2, ensure_ascii=False)}")
        
        print("健康檢查測試完成！")
    
    asyncio.run(test_health_check())