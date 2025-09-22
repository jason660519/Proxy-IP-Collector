"""
統一的錯誤處理中間件
提供全局異常處理和統一的錯誤響應格式
"""

from typing import Any, Dict, Optional, Union
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import traceback
from datetime import datetime

from .exceptions import (
    ProxyCollectorException,
    ErrorCode,
    ProxyNotFoundException,
    ProxyPoolEmptyException,
    ValidationException,
    RateLimitException,
    ConfigurationException,
    DatabaseConnectionException,
    DatabaseQueryException,
    ScrapingTimeoutException,
    NetworkException,
    map_exception
)

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """全局錯誤處理中間件"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """處理所有請求的異常"""
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            return await self.handle_exception(request, exc)
    
    async def handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """統一處理異常"""
        
        # 如果是自定義異常，直接使用
        if isinstance(exc, ProxyCollectorException):
            error_response = exc.to_dict()
            status_code = exc.status_code
            
        # 如果是 FastAPI 的 HTTPException
        elif isinstance(exc, HTTPException):
            error_response = {
                'error': {
                    'code': ErrorCode.INTERNAL_ERROR.value,
                    'message': exc.detail or "內部服務器錯誤",
                    'status_code': exc.status_code,
                    'details': {},
                    'timestamp': datetime.now().isoformat()
                }
            }
            status_code = exc.status_code
            
        # 如果是其他異常，進行映射
        else:
            mapped_exception = map_exception(exc)
            error_response = mapped_exception.to_dict()
            status_code = mapped_exception.status_code
        
        # 記錄錯誤日誌
        self._log_error(request, exc, error_response, status_code)
        
        return JSONResponse(
            status_code=status_code,
            content=error_response
        )
    
    def _log_error(self, request: Request, exc: Exception, error_response: Dict[str, Any], status_code: int):
        """記錄錯誤日誌"""
        error_info = {
            'request_id': id(request),
            'method': request.method,
            'url': str(request.url),
            'client_ip': self._get_client_ip(request),
            'status_code': status_code,
            'error_code': error_response['error']['code'],
            'error_message': error_response['error']['message'],
            'timestamp': error_response['error']['timestamp']
        }
        
        # 添加請求頭信息
        headers = dict(request.headers)
        if 'authorization' in headers:
            headers['authorization'] = '***'  # 隱藏認證信息
        error_info['headers'] = headers
        
        # 添加異常詳情
        if not isinstance(exc, ProxyCollectorException):
            error_info['exception_type'] = f"{exc.__class__.__module__}.{exc.__class__.__name__}"
            error_info['exception_message'] = str(exc)
            error_info['traceback'] = traceback.format_exc()
        
        # 根據錯誤級別記錄日誌
        if status_code >= 500:
            logger.error(f"服務器錯誤: {error_info}")
        elif status_code >= 400:
            logger.warning(f"客戶端錯誤: {error_info}")
        else:
            logger.info(f"應用錯誤: {error_info}")
    
    def _get_client_ip(self, request: Request) -> str:
        """獲取客戶端 IP 地址"""
        # 檢查代理頭部
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 返回直接連接的 IP
        return request.client.host if request.client else "unknown"

class ErrorResponseFormatter:
    """錯誤響應格式化器"""
    
    @staticmethod
    def format_error_response(
        error_code: Union[str, ErrorCode],
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """格式化錯誤響應"""
        
        if isinstance(error_code, ErrorCode):
            error_code = error_code.value
        
        return {
            'error': {
                'code': error_code,
                'message': message,
                'status_code': status_code,
                'details': details or {},
                'timestamp': datetime.now().isoformat(),
                'request_id': request_id
            }
        }
    
    @staticmethod
    def format_validation_error(
        field: str,
        message: str,
        value: Any = None,
        error_type: str = "validation_error"
    ) -> Dict[str, Any]:
        """格式化驗證錯誤"""
        
        details = {
            'field': field,
            'error_type': error_type,
            'value': value
        }
        
        return ErrorResponseFormatter.format_error_response(
            error_code=ErrorCode.INVALID_PARAMETER,
            message=f"參數驗證失敗: {message}",
            status_code=400,
            details=details
        )
    
    @staticmethod
    def format_not_found_error(
        resource_type: str,
        resource_id: Optional[Union[str, int]] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """格式化資源未找到錯誤"""
        
        message = f"{resource_type}未找到"
        if resource_id:
            message = f"{resource_type}未找到: {resource_id}"
        
        return ErrorResponseFormatter.format_error_response(
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            message=message,
            status_code=404,
            details=details or {'resource_type': resource_type, 'resource_id': resource_id}
        )

class ExceptionHandler:
    """異常處理器"""
    
    @staticmethod
    def handle_proxy_not_found(proxy_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """處理代理未找到異常"""
        exception = ProxyNotFoundException(proxy_id)
        return exception.to_dict()
    
    @staticmethod
    def handle_proxy_pool_empty() -> Dict[str, Any]:
        """處理代理池為空異常"""
        exception = ProxyPoolEmptyException()
        return exception.to_dict()
    
    @staticmethod
    def handle_validation_error(field: str, message: str, value: Any = None) -> Dict[str, Any]:
        """處理驗證錯誤"""
        exception = ValidationException(
            message=f"{field}: {message}",
            proxy="",
            details={'field': field, 'value': value}
        )
        return exception.to_dict()
    
    @staticmethod
    def handle_rate_limit(source: str, retry_after: Optional[int] = None) -> Dict[str, Any]:
        """處理速率限制異常"""
        exception = RateLimitException(
            message=f"速率限制超過: {source}",
            source=source,
            retry_after=retry_after
        )
        return exception.to_dict()
    
    @staticmethod
    def handle_configuration_error(config_key: str, message: str) -> Dict[str, Any]:
        """處理配置錯誤"""
        exception = ConfigurationException(
            message=message,
            config_key=config_key
        )
        return exception.to_dict()
    
    @staticmethod
    def handle_database_connection_error(connection_string: str, original_exception: Exception) -> Dict[str, Any]:
        """處理數據庫連接錯誤"""
        exception = DatabaseConnectionException(
            connection_string=connection_string,
            original_exception=original_exception
        )
        return exception.to_dict()
    
    @staticmethod
    def handle_database_query_error(query: str, original_exception: Exception) -> Dict[str, Any]:
        """處理數據庫查詢錯誤"""
        exception = DatabaseQueryException(
            query=query,
            original_exception=original_exception
        )
        return exception.to_dict()
    
    @staticmethod
    def handle_scraping_timeout(url: str, timeout: int) -> Dict[str, Any]:
        """處理爬蟲超時錯誤"""
        exception = ScrapingTimeoutException(
            url=url,
            timeout=timeout
        )
        return exception.to_dict()
    
    @staticmethod
    def handle_network_error(url: str, status_code: Optional[int] = None, message: str = "網絡錯誤") -> Dict[str, Any]:
        """處理網絡錯誤"""
        exception = NetworkException(
            message=message,
            url=url,
            status_code=status_code
        )
        return exception.to_dict()

# 全局異常處理器實例
# 注意：ErrorHandlerMiddleware 需要 app 參數，不能在這裡實例化
# error_handler = ErrorHandlerMiddleware()  # 移除這行
error_formatter = ErrorResponseFormatter()
exception_handler = ExceptionHandler()

# 導出常用的異常處理函數
__all__ = [
    'ErrorHandlerMiddleware',
    'ErrorResponseFormatter', 
    'ExceptionHandler',
    'error_handler',
    'error_formatter',
    'exception_handler'
]