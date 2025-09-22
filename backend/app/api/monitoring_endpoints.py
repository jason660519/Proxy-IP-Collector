"""
監控API端點
提供系統監控和健康檢查的API接口
"""

from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..core.monitoring_config import MonitoringConfig
from ..core.structured_logging import get_logger
from ..core.metrics_collector import get_metrics_collector


# Pydantic模型
class HealthResponse(BaseModel):
    """健康檢查響應模型"""
    status: str
    timestamp: datetime
    uptime: float
    version: str
    environment: str
    checks: Dict[str, Any]


class MetricsResponse(BaseModel):
    """指標響應模型"""
    timestamp: datetime
    system: Dict[str, Any]
    application: Dict[str, Any]
    prometheus_available: bool


class AlertResponse(BaseModel):
    """告警響應模型"""
    alerts: list
    last_check: datetime
    status: str


# 創建路由器
router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# 獲取配置和日誌器
config = MonitoringConfig.from_env()
logger = get_logger("monitoring_api")
metrics_collector = get_metrics_collector(config)

# 應用啟動時間
app_start_time = datetime.utcnow()


@router.get("/health", response_model=HealthResponse, summary="健康檢查")
async def health_check():
    """
    系統健康檢查端點
    
    返回系統的健康狀態和各項檢查結果
    """
    try:
        # 基礎健康檢查
        health_status = metrics_collector.check_health()
        
        # 計算運行時間
        uptime = (datetime.utcnow() - app_start_time).total_seconds()
        
        # 構建響應
        response = HealthResponse(
            status=health_status["status"],
            timestamp=datetime.utcnow(),
            uptime=uptime,
            version="1.0.0",
            environment="production" if config.alerting_enabled else "development",
            checks={
                "system": health_status.get("metrics", {}),
                "alerts": health_status.get("alerts", []),
                "prometheus": {
                    "available": metrics_collector.prometheus_available,
                    "enabled": config.prometheus_enabled
                },
                "monitoring": {
                    "performance_monitoring": config.enable_performance_monitoring,
                    "structured_logging": config.log_format == "json"
                }
            }
        )
        
        logger.info(
            "健康檢查完成",
            status=health_status["status"],
            uptime=uptime,
            alerts_count=len(health_status.get("alerts", []))
        )
        
        return response
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        raise HTTPException(status_code=503, detail=f"健康檢查失敗: {str(e)}")


@router.get("/metrics", response_model=MetricsResponse, summary="獲取系統指標")
async def get_metrics():
    """
    獲取系統和應用程序指標
    
    返回當前的系統性能指標和應用程序統計
    """
    try:
        # 獲取系統指標
        system_metrics = metrics_collector.get_metrics_data()
        
        # 獲取應用程序指標（這裡需要從應用程序狀態獲取）
        application_metrics = {
            "total_requests": getattr(metrics_collector, '_total_requests', 0),
            "active_connections": getattr(metrics_collector, '_active_connections', 0),
            "error_rate": _calculate_error_rate(),
            "proxy_stats": await _get_proxy_statistics(),
            "validation_stats": await _get_validation_statistics()
        }
        
        response = MetricsResponse(
            timestamp=datetime.utcnow(),
            system=system_metrics.get("system", {}),
            application=application_metrics,
            prometheus_available=system_metrics.get("prometheus_available", False)
        )
        
        logger.debug("指標數據獲取完成")
        return response
        
    except Exception as e:
        logger.error(f"獲取指標失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取指標失敗: {str(e)}")


@router.get("/alerts", response_model=AlertResponse, summary="獲取當前告警")
async def get_alerts():
    """
    獲取當前活動的告警
    
    返回系統當前的告警信息和狀態
    """
    try:
        health_status = metrics_collector.check_health()
        
        response = AlertResponse(
            alerts=health_status.get("alerts", []),
            last_check=datetime.utcnow(),
            status=health_status["status"]
        )
        
        logger.info(
            "告警信息獲取完成",
            alerts_count=len(response.alerts),
            status=response.status
        )
        
        return response
        
    except Exception as e:
        logger.error(f"獲取告警失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取告警失敗: {str(e)}")


@router.get("/status", summary="獲取監控系統狀態")
async def get_monitoring_status():
    """
    獲取監控系統的整體狀態
    
    返回監控系統的配置和運行狀態
    """
    try:
        status = {
            "monitoring_enabled": True,
            "prometheus": {
                "enabled": config.prometheus_enabled,
                "available": metrics_collector.prometheus_available,
                "port": config.prometheus_port,
                "metrics_path": config.prometheus_metrics_path
            },
            "logging": {
                "level": config.log_level,
                "format": config.log_format,
                "file_enabled": bool(config.log_file)
            },
            "performance_monitoring": {
                "enabled": config.enable_performance_monitoring,
                "interval": config.performance_metrics_interval
            },
            "health_check": {
                "interval": config.health_check_interval,
                "timeout": config.health_check_timeout
            },
            "alerting": {
                "enabled": config.alerting_enabled,
                "thresholds": config.alert_thresholds
            }
        }
        
        logger.debug("監控系統狀態獲取完成")
        return status
        
    except Exception as e:
        logger.error(f"獲取監控狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取監控狀態失敗: {str(e)}")


# 輔助函數
def _calculate_error_rate() -> float:
    """計算錯誤率"""
    # 這裡需要從應用程序狀態獲取實際的錯誤率
    # 暫時返回模擬數據
    return 0.5


async def _get_proxy_statistics() -> Dict[str, Any]:
    """獲取代理統計信息"""
    # 這裡需要從數據庫或服務獲取實際的代理統計
    # 暫時返回模擬數據
    return {
        "total": 100,
        "active": 75,
        "inactive": 25,
        "by_country": {
            "US": 30,
            "CN": 25,
            "EU": 20,
            "OTHER": 25
        }
    }


async def _get_validation_statistics() -> Dict[str, Any]:
    """獲取驗證統計信息"""
    # 這裡需要從驗證服務獲取實際的驗證統計
    # 暫時返回模擬數據
    return {
        "total_validations": 1000,
        "successful_validations": 850,
        "failed_validations": 150,
        "average_validation_time": 2.5,
        "success_rate": 85.0
    }