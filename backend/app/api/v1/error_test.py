"""
錯誤處理測試端點
用於測試統一的錯誤處理框架
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from pydantic import BaseModel

from ...core.exceptions import (
    ProxyNotFoundException,
    ProxyPoolEmptyException,
    ValidationException,
    RateLimitException,
    ConfigurationException,
    ScrapingTimeoutException,
    NetworkException,
    DatabaseConnectionException,
    DatabaseQueryException,
    ErrorCode
)

router = APIRouter()

class ErrorTestRequest(BaseModel):
    """錯誤測試請求模型"""
    error_type: str
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

@router.get("/error-test/proxy-not-found")
async def test_proxy_not_found(proxy_id: Optional[str] = Query(None, description="代理ID")):
    """測試代理未找到錯誤"""
    raise ProxyNotFoundException(proxy_id=proxy_id)

@router.get("/error-test/proxy-pool-empty")
async def test_proxy_pool_empty():
    """測試代理池為空錯誤"""
    raise ProxyPoolEmptyException()

@router.get("/error-test/validation-error")
async def test_validation_error(
    field: str = Query("test_field", description="字段名"),
    message: str = Query("測試驗證錯誤", description="錯誤消息")
):
    """測試驗證錯誤"""
    raise ValidationException(
        message=f"{field}: {message}",
        proxy="test_proxy",
        details={'field': field, 'value': 'test_value'}
    )

@router.get("/error-test/rate-limit")
async def test_rate_limit(
    source: str = Query("test_source", description="來源"),
    retry_after: Optional[int] = Query(None, description="重試等待時間(秒)")
):
    """測試速率限制錯誤"""
    raise RateLimitException(
        message=f"速率限制超過: {source}",
        source=source,
        retry_after=retry_after
    )

@router.get("/error-test/configuration-error")
async def test_configuration_error(
    config_key: str = Query("test_config", description="配置鍵"),
    message: str = Query("測試配置錯誤", description="錯誤消息")
):
    """測試配置錯誤"""
    raise ConfigurationException(
        message=message,
        config_key=config_key
    )

@router.get("/error-test/scraping-timeout")
async def test_scraping_timeout(
    url: str = Query("https://example.com", description="URL"),
    timeout: int = Query(30, description="超時時間")
):
    """測試爬蟲超時錯誤"""
    raise ScrapingTimeoutException(
        url=url,
        timeout=timeout
    )

@router.get("/error-test/network-error")
async def test_network_error(
    url: str = Query("https://example.com", description="URL"),
    status_code: Optional[int] = Query(None, description="HTTP狀態碼")
):
    """測試網絡錯誤"""
    raise NetworkException(
        message=f"網絡錯誤: {url}",
        url=url,
        status_code=status_code
    )

@router.get("/error-test/database-connection-error")
async def test_database_connection_error(
    connection_string: str = Query("postgresql://user:pass@localhost/db", description="連接字符串")
):
    """測試數據庫連接錯誤"""
    import psycopg2
    original_exception = psycopg2.OperationalError("連接失敗")
    
    raise DatabaseConnectionException(
        connection_string=connection_string,
        original_exception=original_exception
    )

@router.get("/error-test/database-query-error")
async def test_database_query_error(
    query: str = Query("SELECT * FROM proxies", description="SQL查詢")
):
    """測試數據庫查詢錯誤"""
    import sqlite3
    original_exception = sqlite3.OperationalError("表不存在")
    
    raise DatabaseQueryException(
        query=query,
        original_exception=original_exception
    )

@router.get("/error-test/fastapi-http-error")
async def test_fastapi_http_error(
    status_code: int = Query(404, description="HTTP狀態碼"),
    detail: str = Query("測試FastAPI HTTP錯誤", description="錯誤詳情")
):
    """測試 FastAPI HTTPException"""
    raise HTTPException(status_code=status_code, detail=detail)

@router.get("/error-test/python-exception")
async def test_python_exception(
    exception_type: str = Query("ValueError", description="異常類型")
):
    """測試 Python 內置異常"""
    exception_map = {
        "ValueError": ValueError("測試值錯誤"),
        "KeyError": KeyError("測試鍵錯誤"),
        "TypeError": TypeError("測試類型錯誤"),
        "ZeroDivisionError": ZeroDivisionError("測試除零錯誤"),
        "AttributeError": AttributeError("測試屬性錯誤")
    }
    
    if exception_type in exception_map:
        raise exception_map[exception_type]
    else:
        raise ValueError(f"未知的異常類型: {exception_type}")

@router.post("/error-test/custom-error")
async def test_custom_error(request: ErrorTestRequest):
    """測試自定義錯誤"""
    error_map = {
        "proxy_not_found": ProxyNotFoundException,
        "proxy_pool_empty": ProxyPoolEmptyException,
        "validation": lambda msg, details: ValidationException(
            message=msg or "自定義驗證錯誤",
            proxy="custom_proxy",
            details=details
        ),
        "rate_limit": lambda msg, details: RateLimitException(
            message=msg or "自定義速率限制錯誤",
            source="custom_source",
            retry_after=details.get('retry_after') if details else None
        ),
        "configuration": lambda msg, details: ConfigurationException(
            message=msg or "自定義配置錯誤",
            config_key=details.get('config_key') if details else "custom_config"
        )
    }
    
    if request.error_type in error_map:
        error_class = error_map[request.error_type]
        if callable(error_class):
            raise error_class(request.message, request.details)
        else:
            raise error_class(**(request.details or {}))
    else:
        raise ValueError(f"未知的錯誤類型: {request.error_type}")

@router.get("/error-test/success")
async def test_success():
    """測試成功響應（對照組）"""
    return {
        "status": "success",
        "message": "這是一個成功的響應",
        "timestamp": "2024-01-01T00:00:00Z",
        "data": {
            "test": "success",
            "error_handling": "working"
        }
    }