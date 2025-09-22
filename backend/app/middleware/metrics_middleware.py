"""
指標收集中間件
用於收集HTTP請求的指標數據
"""

import time
import logging
from typing import Optional, Callable, Awaitable
from functools import wraps

from ..core.monitoring import REQUEST_COUNT, REQUEST_DURATION


logger = logging.getLogger(__name__)


class MetricsMiddleware:
    """指標收集中間件"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化應用程序"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """請求前處理"""
        # 在g對象中存儲請求開始時間
        from flask import g
        g.start_time = time.time()
    
    def after_request(self, response):
        """請求後處理"""
        from flask import g, request
        
        try:
            if hasattr(g, 'start_time'):
                # 計算請求持續時間
                duration = time.time() - g.start_time
                
                # 獲取請求信息
                method = request.method
                endpoint = request.endpoint or 'unknown'
                status_code = response.status_code if response else 500
                
                # 記錄指標
                REQUEST_COUNT.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=str(status_code)
                ).inc()
                
                REQUEST_DURATION.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                
                logger.debug(f"指標記錄完成: {method} {endpoint} {status_code} - {duration:.3f}s")
        
        except Exception as e:
            logger.error(f"記錄指標失敗: {e}")
        
        return response


def track_request_metrics(func: Callable) -> Callable:
    """請求指標追蹤裝飾器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            # 執行函數
            result = await func(*args, **kwargs)
            
            # 計算持續時間
            duration = time.time() - start_time
            
            # 獲取函數名稱作為端點
            endpoint = func.__name__
            
            # 記錄成功指標
            REQUEST_COUNT.labels(
                method="FUNCTION",
                endpoint=endpoint,
                status_code="200"
            ).inc()
            
            REQUEST_DURATION.labels(
                method="FUNCTION",
                endpoint=endpoint
            ).observe(duration)
            
            return result
            
        except Exception as e:
            # 計算持續時間（失敗情況）
            duration = time.time() - start_time
            
            # 獲取函數名稱
            endpoint = func.__name__
            
            # 記錄失敗指標
            REQUEST_COUNT.labels(
                method="FUNCTION",
                endpoint=endpoint,
                status_code="500"
            ).inc()
            
            REQUEST_DURATION.labels(
                method="FUNCTION",
                endpoint=endpoint
            ).observe(duration)
            
            # 重新拋出異常
            raise
    
    return wrapper


def track_async_function_metrics(func_name: str = None):
    """異步函數指標追蹤裝飾器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            function_name = func_name or func.__name__
            
            try:
                # 執行函數
                result = await func(*args, **kwargs)
                
                # 計算持續時間
                duration = time.time() - start_time
                
                # 記錄成功指標
                REQUEST_COUNT.labels(
                    method="ASYNC",
                    endpoint=function_name,
                    status_code="200"
                ).inc()
                
                REQUEST_DURATION.labels(
                    method="ASYNC",
                    endpoint=function_name
                ).observe(duration)
                
                return result
                
            except Exception as e:
                # 計算持續時間（失敗情況）
                duration = time.time() - start_time
                
                # 記錄失敗指標
                REQUEST_COUNT.labels(
                    method="ASYNC",
                    endpoint=function_name,
                    status_code="500"
                ).inc()
                
                REQUEST_DURATION.labels(
                    method="ASYNC",
                    endpoint=function_name
                ).observe(duration)
                
                # 重新拋出異常
                raise
        
        return wrapper
    return decorator


class AsyncMetricsMiddleware:
    """異步指標收集中間件"""
    
    def __init__(self):
        self.is_enabled = True
    
    async def __call__(self, scope, receive, send):
        """中間件調用"""
        if not self.is_enabled:
            return await self.app(scope, receive, send)
        
        start_time = time.time()
        
        # 獲取請求信息
        method = scope.get('method', 'UNKNOWN')
        path = scope.get('path', '/')
        
        try:
            # 創建包裝的send函數來捕獲響應狀態
            status_code = 200
            
            async def wrapped_send(message):
                nonlocal status_code
                if message['type'] == 'http.response.start':
                    status_code = message.get('status', 200)
                await send(message)
            
            # 執行請求
            result = await self.app(scope, receive, wrapped_send)
            
            # 計算持續時間
            duration = time.time() - start_time
            
            # 記錄指標
            REQUEST_COUNT.labels(
                method=method,
                endpoint=path,
                status_code=str(status_code)
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=path
            ).observe(duration)
            
            logger.debug(f"異步指標記錄完成: {method} {path} {status_code} - {duration:.3f}s")
            
            return result
            
        except Exception as e:
            # 計算持續時間（失敗情況）
            duration = time.time() - start_time
            
            # 記錄失敗指標
            REQUEST_COUNT.labels(
                method=method,
                endpoint=path,
                status_code="500"
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=path
            ).observe(duration)
            
            logger.error(f"異步請求處理失敗: {method} {path} - {e}")
            raise


def create_metrics_middleware(app_type: str = "flask"):
    """創建指標中間件"""
    if app_type.lower() == "flask":
        return MetricsMiddleware()
    elif app_type.lower() == "async":
        return AsyncMetricsMiddleware()
    else:
        raise ValueError(f"不支持的應用程序類型: {app_type}")


# 全局中間件實例
_metrics_middleware: Optional[MetricsMiddleware] = None


def get_metrics_middleware() -> MetricsMiddleware:
    """獲取指標中間件實例"""
    global _metrics_middleware
    if _metrics_middleware is None:
        _metrics_middleware = MetricsMiddleware()
    return _metrics_middleware


if __name__ == "__main__":
    # 測試中間件
    import asyncio
    
    async def test_async_decorator():
        """測試異步裝飾器"""
        
        @track_async_function_metrics("test_function")
        async def test_function():
            await asyncio.sleep(0.1)
            return "success"
        
        @track_async_function_metrics("test_error_function")
        async def test_error_function():
            await asyncio.sleep(0.1)
            raise ValueError("測試錯誤")
        
        print("測試正常函數...")
        result = await test_function()
        print(f"結果: {result}")
        
        print("測試錯誤函數...")
        try:
            await test_error_function()
        except ValueError as e:
            print(f"捕獲到預期錯誤: {e}")
    
    print("開始測試指標中間件...")
    asyncio.run(test_async_decorator())
    print("測試完成！")