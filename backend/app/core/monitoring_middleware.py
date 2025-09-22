"""
監控中間件
集成監控功能到FastAPI應用
"""

import time
import asyncio
from typing import Callable, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .monitoring_config import MonitoringConfig
from .structured_logging import get_logger, log_request, log_error
from .metrics_collector import get_metrics_collector


class MonitoringMiddleware(BaseHTTPMiddleware):
    """監控中間件"""
    
    def __init__(self, app, config: Optional[MonitoringConfig] = None):
        """初始化監控中間件"""
        super().__init__(app)
        self.config = config or MonitoringConfig.from_env()
        self.logger = get_logger("monitoring")
        self.metrics_collector = get_metrics_collector(self.config)
        
        # 應用程序指標
        self._total_requests = 0
        self._active_connections = 0
        self._error_count = 0
        self._request_times = []
        self._max_request_times_history = 1000
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """處理請求"""
        start_time = time.time()
        self._total_requests += 1
        self._active_connections += 1
        
        # 記錄請求開始
        self.logger.info(
            f"請求開始: {request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        try:
            # 調用下一個中間件或路由處理器
            response = await call_next(request)
            
            # 計算請求持續時間
            duration = time.time() - start_time
            status_code = response.status_code
            
            # 記錄請求完成
            self.logger.info(
                f"請求完成: {request.method} {request.url.path} - {status_code}",
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration=duration,
                client_host=request.client.host if request.client else "unknown"
            )
            
            # 更新指標
            self._record_request_metrics(request.method, request.url.path, duration, status_code)
            
            if status_code >= 400:
                self._error_count += 1
            
            return response
            
        except Exception as e:
            # 記錄錯誤
            duration = time.time() - start_time
            self._error_count += 1
            
            self.logger.error(
                f"請求錯誤: {request.method} {request.url.path}",
                method=request.method,
                path=request.url.path,
                duration=duration,
                error=str(e),
                error_type=type(e).__name__,
                client_host=request.client.host if request.client else "unknown"
            )
            
            # 更新錯誤指標
            self._record_request_metrics(request.method, request.url.path, duration, 500)
            
            # 返回錯誤響應
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                    "request_id": getattr(request.state, 'request_id', 'unknown')
                }
            )
            
        finally:
            self._active_connections -= 1
    
    def _record_request_metrics(self, method: str, path: str, duration: float, status_code: int):
        """記錄請求指標"""
        try:
            # 記錄到Prometheus
            self.metrics_collector.record_request(method, path, duration, status_code)
            
            # 存儲請求時間
            self._request_times.append(duration)
            if len(self._request_times) > self._max_request_times_history:
                self._request_times.pop(0)
            
        except Exception as e:
            self.logger.error(f"記錄請求指標失敗: {e}")


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """健康檢查中間件"""
    
    def __init__(self, app, config: Optional[MonitoringConfig] = None):
        """初始化健康檢查中間件"""
        super().__init__(app)
        self.config = config or MonitoringConfig.from_env()
        self.logger = get_logger("health_check")
        self.metrics_collector = get_metrics_collector(self.config)
        
        # 健康檢查狀態
        self._last_health_check = None
        self._health_check_interval = self.config.health_check_interval
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """處理請求"""
        # 健康檢查端點
        if request.url.path == "/health":
            return await self._handle_health_check(request)
        
        # 指標端點
        if request.url.path == "/metrics" and request.method == "GET":
            return await self._handle_metrics(request)
        
        # 其他請求正常處理
        return await call_next(request)
    
    async def _handle_health_check(self, request: Request) -> JSONResponse:
        """處理健康檢查請求"""
        try:
            health_status = self.metrics_collector.check_health()
            
            # 記錄健康檢查
            self.logger.info(
                "健康檢查完成",
                status=health_status["status"],
                alerts_count=len(health_status.get("alerts", [])),
                client_host=request.client.host if request.client else "unknown"
            )
            
            # 根據狀態返回適當的HTTP狀態碼
            status_code = 200
            if health_status["status"] == "unhealthy":
                status_code = 503
            elif health_status["status"] == "warning":
                status_code = 200
            
            return JSONResponse(
                status_code=status_code,
                content=health_status
            )
            
        except Exception as e:
            self.logger.error(f"健康檢查失敗: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": str(e),
                    "alerts": ["健康檢查失敗"]
                }
            )
    
    async def _handle_metrics(self, request: Request) -> Response:
        """處理指標請求"""
        try:
            prometheus_metrics = self.metrics_collector.get_prometheus_metrics()
            
            if prometheus_metrics is None:
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": "Prometheus指標不可用",
                        "message": "prometheus_client未安裝或配置錯誤"
                    }
                )
            
            return Response(
                content=prometheus_metrics,
                media_type=CONTENT_TYPE_LATEST
            )
            
        except Exception as e:
            self.logger.error(f"獲取指標失敗: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "無法獲取指標數據"
                }
            )


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """性能監控中間件"""
    
    def __init__(self, app, config: Optional[MonitoringConfig] = None):
        """初始化性能監控中間件"""
        super().__init__(app)
        self.config = config or MonitoringConfig.from_env()
        self.logger = get_logger("performance")
        self.metrics_collector = get_metrics_collector(self.config)
        
        # 性能閾值
        self.slow_request_threshold = 1.0  # 1秒
        self.very_slow_request_threshold = 5.0  # 5秒
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """處理請求"""
        if not self.config.enable_performance_monitoring:
            return await call_next(request)
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            duration = time.time() - start_time
            
            # 記錄性能指標
            self._record_performance_metrics(request, duration, response)
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            self.logger.error(
                f"請求異常: {request.method} {request.url.path} - {duration:.3f}s",
                method=request.method,
                path=request.url.path,
                duration=duration,
                error=str(e)
            )
            
            raise
    
    def _record_performance_metrics(self, request: Request, duration: float, response: Response):
        """記錄性能指標"""
        try:
            # 慢請求警告
            if duration > self.very_slow_request_threshold:
                self.logger.warning(
                    f"極慢請求: {request.method} {request.url.path} - {duration:.3f}s",
                    method=request.method,
                    path=request.url.path,
                    duration=duration,
                    status_code=response.status_code,
                    threshold=self.very_slow_request_threshold
                )
            elif duration > self.slow_request_threshold:
                self.logger.info(
                    f"慢請求: {request.method} {request.url.path} - {duration:.3f}s",
                    method=request.method,
                    path=request.url.path,
                    duration=duration,
                    status_code=response.status_code,
                    threshold=self.slow_request_threshold
                )
            
            # 記錄性能指標
            from .structured_logging import log_performance_metric
            log_performance_metric(
                "request_duration",
                duration,
                "seconds",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code
            )
            
        except Exception as e:
            self.logger.error(f"記錄性能指標失敗: {e}")


# 監控工具函數
async def start_metrics_collection(app):
    """啟動指標收集"""
    config = MonitoringConfig.from_env()
    if not config.enable_performance_monitoring:
        return
    
    logger = get_logger("monitoring")
    metrics_collector = get_metrics_collector(config)
    
    async def collect_metrics():
        """定期收集指標"""
        while True:
            try:
                # 收集系統指標
                metrics_collector.collect_system_metrics()
                
                # 等待下一個收集週期
                await asyncio.sleep(config.performance_metrics_interval)
                
            except Exception as e:
                logger.error(f"指標收集失敗: {e}")
                await asyncio.sleep(60)  # 出錯後等待1分鐘再試
    
    # 啟動後台任務
    asyncio.create_task(collect_metrics())
    logger.info("指標收集任務已啟動")


def setup_monitoring(app, config: Optional[MonitoringConfig] = None):
    """設置監控系統"""
    config = config or MonitoringConfig.from_env()
    
    # 添加中間件
    app.add_middleware(PerformanceMonitoringMiddleware, config=config)
    app.add_middleware(MonitoringMiddleware, config=config)
    app.add_middleware(HealthCheckMiddleware, config=config)
    
    # 設置啟動事件
    @app.on_event("startup")
    async def startup_monitoring():
        await start_metrics_collection(app)
    
    logger = get_logger("monitoring")
    logger.info("監控系統已設置完成")