"""
統一的錯誤處理框架
提供自定義異常類和統一的錯誤響應格式
"""

from typing import Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import traceback
import logging

logger = logging.getLogger(__name__)

class ErrorCode(Enum):
    """錯誤代碼枚舉"""
    # 通用錯誤 (1000-1999)
    INTERNAL_ERROR = 1000
    INVALID_PARAMETER = 1001
    RESOURCE_NOT_FOUND = 1002
    UNAUTHORIZED = 1003
    FORBIDDEN = 1004
    RATE_LIMIT_EXCEEDED = 1005
    SERVICE_UNAVAILABLE = 1006
    
    # 代理相關錯誤 (2000-2999)
    PROXY_NOT_FOUND = 2000
    PROXY_VALIDATION_FAILED = 2001
    PROXY_POOL_EMPTY = 2002
    PROXY_CONNECTION_FAILED = 2003
    INVALID_PROXY_FORMAT = 2004
    PROXY_TIMEOUT = 2005
    
    # 爬蟲相關錯誤 (3000-3999)
    SCRAPING_FAILED = 3000
    SCRAPING_TIMEOUT = 3001
    INVALID_URL = 3002
    CONTENT_EXTRACTION_FAILED = 3003
    RATE_LIMIT_BLOCKED = 3004
    
    # 數據庫相關錯誤 (4000-4999)
    DATABASE_CONNECTION_FAILED = 4000
    DATABASE_QUERY_FAILED = 4001
    DATA_VALIDATION_FAILED = 4002
    DUPLICATE_ENTRY = 4003
    
    # 配置相關錯誤 (5000-5999)
    INVALID_CONFIG = 5000
    CONFIG_NOT_FOUND = 5001
    CONFIG_VALIDATION_FAILED = 5002
    
    # 監控相關錯誤 (6000-6999)
    METRIC_COLLECTION_FAILED = 6000
    HEALTH_CHECK_FAILED = 6001
    ALERT_SENDING_FAILED = 6002

class ProxyCollectorException(Exception):
    """基礎異常類 - 統一的錯誤處理基礎"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[Union[str, ErrorCode]] = None, 
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code.value if isinstance(error_code, ErrorCode) else (error_code or "GENERIC_ERROR")
        self.details = details or {}
        self.status_code = status_code
        self.original_exception = original_exception
        self.timestamp = datetime.now()
        
        # 記錄日誌
        self._log_error()
    
    def _log_error(self):
        """記錄錯誤日誌"""
        error_info = {
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
            'status_code': self.status_code,
            'timestamp': self.timestamp.isoformat()
        }
        
        if self.original_exception:
            error_info['original_error'] = str(self.original_exception)
            error_info['traceback'] = traceback.format_exc()
        
        logger.error(f"應用異常: {error_info}")
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式（用於API響應）"""
        return {
            'error': {
                'code': self.error_code,
                'message': self.message,
                'status_code': self.status_code,
                'details': self.details,
                'timestamp': self.timestamp.isoformat()
            }
        }

class FetcherException(ProxyCollectorException):
    """爬取器異常"""
    
    def __init__(self, message: str, source: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, 
            error_code=error_code or ErrorCode.SCRAPING_FAILED, 
            details=details,
            status_code=500
        )
        self.source = source

class ParserException(ProxyCollectorException):
    """解析器異常"""
    
    def __init__(self, message: str, source: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, 
            error_code=error_code or ErrorCode.CONTENT_EXTRACTION_FAILED, 
            details=details,
            status_code=500
        )
        self.source = source

class ValidationException(ProxyCollectorException):
    """驗證異常"""
    
    def __init__(self, message: str, proxy: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, 
            error_code=error_code or ErrorCode.PROXY_VALIDATION_FAILED, 
            details=details,
            status_code=400
        )
        self.proxy = proxy

class StorageException(ProxyCollectorException):
    """存儲異常"""
    
    def __init__(self, message: str, operation: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, 
            error_code=error_code or ErrorCode.DATABASE_QUERY_FAILED, 
            details=details,
            status_code=500
        )
        self.operation = operation

class RateLimitException(ProxyCollectorException):
    """速率限制異常"""
    
    def __init__(self, message: str, source: str, retry_after: Optional[int] = None, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, 
            error_code=error_code or ErrorCode.RATE_LIMIT_EXCEEDED, 
            details=details,
            status_code=429
        )
        self.source = source
        self.retry_after = retry_after

class NetworkException(ProxyCollectorException):
    """網絡異常"""
    
    def __init__(self, message: str, url: str, status_code: Optional[int] = None, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, 
            error_code=error_code or ErrorCode.NETWORK_ERROR, 
            details=details,
            status_code=status_code or 500
        )
        self.url = url
        self.status_code = status_code

class ConfigurationException(ProxyCollectorException):
    """配置異常"""
    
    def __init__(self, message: str, config_key: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, 
            error_code=error_code or ErrorCode.INVALID_CONFIG, 
            details=details,
            status_code=400
        )
        self.config_key = config_key

# 具體的代理相關異常
class ProxyNotFoundException(ProxyCollectorException):
    """代理未找到異常"""
    
    def __init__(self, proxy_id: Optional[Union[int, str]] = None, details: Optional[Dict[str, Any]] = None):
        message = f"代理未找到"
        if proxy_id:
            message = f"代理未找到: {proxy_id}"
        
        super().__init__(
            message=message,
            error_code=ErrorCode.PROXY_NOT_FOUND,
            status_code=404,
            details=details or {'proxy_id': proxy_id}
        )

class ProxyPoolEmptyException(ProxyCollectorException):
    """代理池為空異常"""
    
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="代理池為空，沒有可用的代理服務器",
            error_code=ErrorCode.PROXY_POOL_EMPTY,
            status_code=503,
            details=details
        )

# 具體的爬蟲相關異常
class ScrapingTimeoutException(ProxyCollectorException):
    """爬蟲超時異常"""
    
    def __init__(self, url: str, timeout: int, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"爬蟲超時: {url} (超時時間: {timeout}秒)",
            error_code=ErrorCode.SCRAPING_TIMEOUT,
            status_code=408,
            details=details or {'url': url, 'timeout': timeout}
        )

# 具體的數據庫相關異常
class DatabaseConnectionException(ProxyCollectorException):
    """數據庫連接失敗異常"""
    
    def __init__(self, connection_string: str, original_exception: Exception, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"數據庫連接失敗: {connection_string}",
            error_code=ErrorCode.DATABASE_CONNECTION_FAILED,
            status_code=500,
            details=details or {'connection_string': connection_string},
            original_exception=original_exception
        )

class DatabaseQueryException(ProxyCollectorException):
    """數據庫查詢失敗異常"""
    
    def __init__(self, query: str, original_exception: Exception, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"數據庫查詢失敗",
            error_code=ErrorCode.DATABASE_QUERY_FAILED,
            status_code=500,
            details=details or {'query': query[:100] + '...' if len(query) > 100 else query},
            original_exception=original_exception
        )

# 異常映射字典，用於將常見異常轉換為自定義異常
EXCEPTION_MAPPING = {
    'sqlite3.OperationalError': lambda e: DatabaseQueryException(
        query="",
        original_exception=e,
        details={'sqlite_error': str(e)}
    ),
    'sqlite3.IntegrityError': lambda e: ValidationException(
        proxy="",
        message=f"數據完整性錯誤: {str(e)}",
        details={'sqlite_error': str(e)}
    ),
    'ConnectionError': lambda e: NetworkException(
        message=f"網絡連接錯誤: {str(e)}",
        url="unknown",
        details={'connection_error': str(e)}
    ),
    'TimeoutError': lambda e: ScrapingTimeoutException(
        url="unknown",
        timeout=0,
        details={'timeout_error': str(e)}
    ),
    'ValueError': lambda e: ValidationException(
        proxy="",
        message=f"值錯誤: {str(e)}",
        details={'value_error': str(e)}
    ),
    'KeyError': lambda e: ConfigurationException(
        message=f"配置鍵錯誤: {str(e)}",
        config_key=str(e),
        details={'key_error': str(e)}
    )
}

def map_exception(exception: Exception) -> ProxyCollectorException:
    """將常見異常映射為自定義異常"""
    exception_type = f"{exception.__class__.__module__}.{exception.__class__.__name__}"
    
    if exception_type in EXCEPTION_MAPPING:
        return EXCEPTION_MAPPING[exception_type](exception)
    
    # 如果沒有匹配的映射，返回通用異常
    return ProxyCollectorException(
        message=f"未處理的異常: {str(exception)}",
        error_code=ErrorCode.INTERNAL_ERROR,
        status_code=500,
        original_exception=exception
    )

def handle_exception(func):
    """異常處理裝飾器（同步函數）"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ProxyCollectorException:
            # 如果是自定義異常，直接拋出
            raise
        except Exception as e:
            # 如果是其他異常，進行映射
            raise map_exception(e)
    
    return wrapper

async def handle_async_exception(func):
    """異常處理裝飾器（異步函數）"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ProxyCollectorException:
            # 如果是自定義異常，直接拋出
            raise
        except Exception as e:
            # 如果是其他異常，進行映射
            raise map_exception(e)
    
    return wrapper