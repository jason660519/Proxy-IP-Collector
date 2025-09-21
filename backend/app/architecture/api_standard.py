"""
API標準化模塊
統一API端點規範，解決端點不一致問題
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class APIStatus(str, Enum):
    """API狀態枚舉"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class HealthStatus(str, Enum):
    """健康狀態枚舉"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


# ===== 統一響應模型 =====

class BaseResponse(BaseModel):
    """基礎響應模型"""
    status: APIStatus = Field(..., description="響應狀態")
    message: str = Field(..., description="響應消息")
    timestamp: str = Field(..., description="時間戳")
    version: str = Field(default="1.0.0", description="API版本")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "操作成功",
                "timestamp": "2024-01-20T10:30:00Z",
                "version": "1.0.0"
            }
        }


class HealthResponse(BaseModel):
    """統一健康檢查響應模型"""
    status: HealthStatus = Field(..., description="健康狀態")
    message: str = Field(..., description="狀態描述")
    timestamp: str = Field(..., description="檢查時間")
    version: str = Field(default="1.0.0", description="API版本")
    mode: str = Field(default="full", description="運行模式")
    services: Optional[Dict[str, Any]] = Field(None, description="服務狀態詳情")
    checks: Optional[List[Dict[str, Any]]] = Field(None, description="詳細檢查項")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "message": "所有服務運行正常",
                "timestamp": "2024-01-20T10:30:00Z",
                "version": "1.0.0",
                "mode": "full",
                "services": {
                    "database": "connected",
                    "api": "running",
                    "crawler": "active"
                },
                "checks": [
                    {
                        "name": "database",
                        "status": "healthy",
                        "response_time": 0.1,
                        "message": "數據庫連接正常"
                    }
                ]
            }
        }


class ProxyStats(BaseModel):
    """代理統計模型"""
    total_proxies: int = Field(..., description="代理總數")
    active_proxies: int = Field(..., description="活躍代理數")
    inactive_proxies: int = Field(..., description="非活躍代理數")
    protocols: Dict[str, int] = Field(..., description="協議分布")
    countries: Dict[str, int] = Field(..., description="國家分布")
    anonymity_levels: Dict[str, int] = Field(..., description="匿名級別分布")
    avg_response_time: float = Field(..., description="平均響應時間(秒)")
    avg_success_rate: float = Field(..., description="平均成功率")
    avg_quality_score: float = Field(..., description="平均質量評分")
    last_updated: str = Field(..., description="最後更新時間")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_proxies": 1247,
                "active_proxies": 892,
                "inactive_proxies": 355,
                "protocols": {
                    "http": 800,
                    "https": 300,
                    "socks4": 100,
                    "socks5": 47
                },
                "countries": {
                    "CN": 400,
                    "US": 300,
                    "JP": 200,
                    "HK": 150,
                    "SG": 100,
                    "DE": 97
                },
                "anonymity_levels": {
                    "elite": 500,
                    "anonymous": 600,
                    "transparent": 147
                },
                "avg_response_time": 1.2,
                "avg_success_rate": 0.715,
                "avg_quality_score": 0.8,
                "last_updated": "2024-01-20T10:30:00Z"
            }
        }


class CrawlTask(BaseModel):
    """爬取任務模型"""
    id: str = Field(..., description="任務ID")
    source: str = Field(..., description="數據源")
    status: str = Field(..., description="任務狀態")
    progress: int = Field(..., description="進度百分比")
    crawled_count: int = Field(..., description="已爬取數量")
    started_at: str = Field(..., description="開始時間")
    completed_at: Optional[str] = Field(None, description="完成時間")
    duration: Optional[int] = Field(None, description="耗時(秒)")
    error_message: Optional[str] = Field(None, description="錯誤信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "task-001",
                "source": "89ip.cn",
                "status": "completed",
                "progress": 100,
                "crawled_count": 45,
                "started_at": "2024-01-20T10:00:00Z",
                "completed_at": "2024-01-20T10:05:00Z",
                "duration": 300,
                "error_message": None
            }
        }


class CrawlStatus(BaseModel):
    """爬取狀態模型"""
    running_tasks: int = Field(..., description="運行中任務數")
    completed_tasks: int = Field(..., description="已完成任務數")
    failed_tasks: int = Field(..., description="失敗任務數")
    total_crawled: int = Field(..., description="總爬取數量")
    tasks: List[CrawlTask] = Field(..., description="任務列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "running_tasks": 2,
                "completed_tasks": 15,
                "failed_tasks": 3,
                "total_crawled": 1247,
                "tasks": [
                    {
                        "id": "task-001",
                        "source": "89ip.cn",
                        "status": "completed",
                        "progress": 100,
                        "crawled_count": 45,
                        "started_at": "2024-01-20T10:00:00Z",
                        "completed_at": "2024-01-20T10:05:00Z",
                        "duration": 300,
                        "error_message": None
                    }
                ]
            }
        }


# ===== API端點標準 =====

class APIEndpoints:
    """統一API端點定義"""
    
    # 健康檢查端點
    HEALTH = "/health"
    HEALTH_ALT = "/api/health"
    HEALTH_V1 = "/api/v1/health"
    
    # 系統信息端點
    ROOT = "/"
    INFO = "/api/v1/info"
    
    # 爬取相關端點
    CRAWL_STATUS = "/api/v1/crawl/status"
    CRAWL_START = "/api/v1/crawl/start"
    CRAWL_STOP = "/api/v1/crawl/stop"
    CRAWL_TASKS = "/api/v1/crawl/tasks"
    CRAWL_TASK_DETAIL = "/api/v1/crawl/tasks/{task_id}"
    
    # 代理相關端點
    PROXY_STATS = "/api/v1/proxies/stats"
    PROXY_LIST = "/api/v1/proxies"
    PROXY_DETAIL = "/api/v1/proxies/{proxy_id}"
    PROXY_TEST = "/api/v1/proxies/{proxy_id}/test"
    
    # 配置相關端點
    CONFIG = "/api/v1/config"
    CONFIG_SOURCES = "/api/v1/config/sources"
    CONFIG_VALIDATOR = "/api/v1/config/validator"


# ===== 統一響應生成器 =====

class ResponseBuilder:
    """統一響應構建器"""
    
    @staticmethod
    def success(data: Any = None, message: str = "操作成功") -> Dict[str, Any]:
        """構建成功響應"""
        response = {
            "status": APIStatus.SUCCESS,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        if data is not None:
            response["data"] = data
        
        return response
    
    @staticmethod
    def error(message: str, code: str = None, details: Any = None) -> Dict[str, Any]:
        """構建錯誤響應"""
        response = {
            "status": APIStatus.ERROR,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        if code:
            response["code"] = code
        
        if details:
            response["details"] = details
        
        return response
    
    @staticmethod
    def warning(message: str, data: Any = None) -> Dict[str, Any]:
        """構建警告響應"""
        response = {
            "status": APIStatus.WARNING,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        if data is not None:
            response["data"] = data
        
        return response
    
    @staticmethod
    def info(message: str, data: Any = None) -> Dict[str, Any]:
        """構建信息響應"""
        response = {
            "status": APIStatus.INFO,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        if data is not None:
            response["data"] = data
        
        return response


# ===== 統一錯誤處理 =====

class APIErrorCodes:
    """統一錯誤代碼"""
    
    # 通用錯誤
    INTERNAL_ERROR = "INTERNAL_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    
    # 業務錯誤
    PROXY_NOT_FOUND = "PROXY_NOT_FOUND"
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    CONFIG_ERROR = "CONFIG_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    CRAWLER_ERROR = "CRAWLER_ERROR"
    
    # 系統錯誤
    DATABASE_ERROR = "DATABASE_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"


def create_error_response(
    message: str, 
    code: str = APIErrorCodes.INTERNAL_ERROR,
    status_code: int = 500,
    details: Any = None
) -> Dict[str, Any]:
    """創建統一錯誤響應"""
    response = ResponseBuilder.error(message, code, details)
    response["status_code"] = status_code
    return response


# ===== 統一健康檢查實現 =====

class HealthChecker:
    """統一健康檢查器"""
    
    def __init__(self):
        self.checks = []
    
    def add_check(self, name: str, check_func, timeout: float = 5.0):
        """添加健康檢查項"""
        self.checks.append({
            "name": name,
            "func": check_func,
            "timeout": timeout
        })
    
    async def check_health(self) -> HealthResponse:
        """執行健康檢查"""
        from datetime import datetime
        
        results = []
        overall_status = HealthStatus.HEALTHY
        
        for check in self.checks:
            try:
                # 執行檢查函數
                result = await check["func"]()
                result["name"] = check["name"]
                results.append(result)
                
                # 更新整體狀態
                if result.get("status") != "healthy":
                    if overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.DEGRADED
                    elif overall_status == HealthStatus.DEGRADED:
                        overall_status = HealthStatus.UNHEALTHY
                        
            except Exception as e:
                # 檢查失敗
                results.append({
                    "name": check["name"],
                    "status": "unhealthy",
                    "message": str(e),
                    "response_time": None
                })
                
                if overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
                elif overall_status == HealthStatus.DEGRADED:
                    overall_status = HealthStatus.UNHEALTHY
        
        # 構建響應
        return HealthResponse(
            status=overall_status,
            message=self._get_health_message(overall_status),
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            mode="full",  # 可以從配置中獲取
            services=self._get_services_status(results),
            checks=results
        )
    
    def _get_health_message(self, status: HealthStatus) -> str:
        """獲取健康狀態描述"""
        messages = {
            HealthStatus.HEALTHY: "所有服務運行正常",
            HealthStatus.DEGRADED: "部分服務異常",
            HealthStatus.UNHEALTHY: "多個服務異常",
            HealthStatus.UNKNOWN: "健康狀態未知"
        }
        return messages.get(status, "未知狀態")
    
    def _get_services_status(self, results: List[Dict]) -> Dict[str, Any]:
        """獲取服務狀態匯總"""
        services = {}
        for result in results:
            name = result["name"]
            status = result.get("status", "unknown")
            services[name] = status
        return services