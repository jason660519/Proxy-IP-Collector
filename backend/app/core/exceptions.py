"""
自定義異常類
"""
from typing import Optional, Dict, Any


class ProxyCollectorException(Exception):
    """基礎異常類"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "GENERIC_ERROR"
        self.details = details or {}


class FetcherException(ProxyCollectorException):
    """爬取器異常"""
    
    def __init__(self, message: str, source: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code or "FETCHER_ERROR", details)
        self.source = source


class ParserException(ProxyCollectorException):
    """解析器異常"""
    
    def __init__(self, message: str, source: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code or "PARSER_ERROR", details)
        self.source = source


class ValidationException(ProxyCollectorException):
    """驗證異常"""
    
    def __init__(self, message: str, proxy: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code or "VALIDATION_ERROR", details)
        self.proxy = proxy


class StorageException(ProxyCollectorException):
    """存儲異常"""
    
    def __init__(self, message: str, operation: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code or "STORAGE_ERROR", details)
        self.operation = operation


class RateLimitException(ProxyCollectorException):
    """速率限制異常"""
    
    def __init__(self, message: str, source: str, retry_after: Optional[int] = None, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code or "RATE_LIMIT_ERROR", details)
        self.source = source
        self.retry_after = retry_after


class NetworkException(ProxyCollectorException):
    """網絡異常"""
    
    def __init__(self, message: str, url: str, status_code: Optional[int] = None, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code or "NETWORK_ERROR", details)
        self.url = url
        self.status_code = status_code


class ConfigurationException(ProxyCollectorException):
    """配置異常"""
    
    def __init__(self, message: str, config_key: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code or "CONFIG_ERROR", details)
        self.config_key = config_key