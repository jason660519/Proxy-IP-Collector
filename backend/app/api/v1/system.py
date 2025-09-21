"""
系統管理API端點
提供系統配置和日誌管理功能
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
import os
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger
from app.core.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)

router = APIRouter(prefix="/system", tags=["system"])


class ConfigResponse(BaseModel):
    """配置響應模型"""
    app_name: str
    app_version: str
    debug: bool
    environment: str
    host: str
    port: int
    log_level: str
    log_format: str
    max_concurrent_requests: int
    request_timeout: int
    validator_timeout: int
    validator_concurrent_workers: int
    rate_limit_per_minute: int
    enable_metrics: bool
    cache_ttl: int


class ConfigUpdateRequest(BaseModel):
    """配置更新請求模型"""
    log_level: Optional[str] = None
    debug: Optional[bool] = None
    max_concurrent_requests: Optional[int] = None
    request_timeout: Optional[int] = None
    validator_timeout: Optional[int] = None
    validator_concurrent_workers: Optional[int] = None
    rate_limit_per_minute: Optional[int] = None
    enable_metrics: Optional[bool] = None
    cache_ttl: Optional[int] = None


class LogEntry(BaseModel):
    """日誌條目模型"""
    timestamp: str
    level: str
    message: str
    logger: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class LogsResponse(BaseModel):
    """日誌響應模型"""
    logs: List[LogEntry]
    total: int
    page: int
    page_size: int


@router.get("/config", response_model=ConfigResponse)
async def get_config() -> ConfigResponse:
    """
    獲取系統配置
    
    Returns:
        ConfigResponse: 系統配置信息
    """
    try:
        return ConfigResponse(
            app_name=settings.APP_NAME,
            app_version=settings.APP_VERSION,
            debug=settings.DEBUG,
            environment=settings.ENVIRONMENT,
            host=settings.HOST,
            port=settings.PORT,
            log_level=settings.LOG_LEVEL,
            log_format=settings.LOG_FORMAT,
            max_concurrent_requests=settings.MAX_CONCURRENT_REQUESTS,
            request_timeout=settings.REQUEST_TIMEOUT,
            validator_timeout=settings.VALIDATOR_TIMEOUT,
            validator_concurrent_workers=settings.VALIDATOR_CONCURRENT_WORKERS,
            rate_limit_per_minute=settings.RATE_LIMIT_PER_MINUTE,
            enable_metrics=settings.ENABLE_METRICS,
            cache_ttl=settings.CACHE_TTL,
        )
    except Exception as e:
        logger.error(f"獲取配置失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取配置失敗")


@router.put("/config", response_model=Dict[str, Any])
async def update_config(config_update: ConfigUpdateRequest) -> Dict[str, Any]:
    """
    更新系統配置
    
    Args:
        config_update: 配置更新數據
        
    Returns:
        Dict[str, Any]: 更新結果
    """
    try:
        # 注意：這裡只是示例實現
        # 實際應用中，您可能需要：
        # 1. 驗證管理員權限
        # 2. 將配置保存到數據庫或配置文件
        # 3. 重新加載應用配置
        
        updated_fields = []
        
        # 這裡應該實際更新配置
        # 由於配置是從環境變量和設置文件加載的，
        # 我們需要一種機制來持久化更改
        
        logger.info(f"配置更新請求: {config_update.dict(exclude_unset=True)}")
        
        return {
            "status": "success",
            "message": "配置更新已接收，但實際更新需要重啟應用",
            "updated_fields": updated_fields,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"更新配置失敗: {e}")
        raise HTTPException(status_code=500, detail="更新配置失敗")


@router.get("/logs", response_model=LogsResponse)
async def get_logs(
    page: int = 1,
    page_size: int = 100,
    level: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> LogsResponse:
    """
    獲取系統日誌
    
    Args:
        page: 頁碼
        page_size: 每頁數量
        level: 日誌級別篩選
        start_time: 開始時間
        end_time: 結束時間
        
    Returns:
        LogsResponse: 日誌列表
    """
    try:
        # 這是一個基本的實現
        # 實際應用中，您可能需要：
        # 1. 從數據庫或日誌文件讀取日誌
        # 2. 實現更複雜的篩選和分頁
        
        logs = []
        
        # 檢查日誌文件是否存在
        log_file = Path(settings.LOG_FILE_PATH)
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                # 簡單的日誌解析（假設是JSON格式）
                for line in lines[-page_size:]:  # 只返回最後的日誌
                    line = line.strip()
                    if line:
                        if settings.LOG_FORMAT == "json":
                            # 這裡應該解析JSON格式的日誌
                            # 為簡單起見，我們只是模擬
                            logs.append(LogEntry(
                                timestamp=datetime.now().isoformat(),
                                level="INFO",
                                message=line[:200],  # 限制消息長度
                            ))
                        else:
                            # 文本格式日誌
                            logs.append(LogEntry(
                                timestamp=datetime.now().isoformat(),
                                level="INFO",
                                message=line[:200],
                            ))
                            
            except Exception as e:
                logger.error(f"讀取日誌文件失敗: {e}")
                # 如果讀取文件失敗，返回模擬日誌
                logs = [LogEntry(
                    timestamp=datetime.now().isoformat(),
                    level="ERROR",
                    message=f"無法讀取日誌文件: {str(e)}"
                )]
        else:
            # 如果日誌文件不存在，返回模擬日誌
            logs = [LogEntry(
                timestamp=datetime.now().isoformat(),
                level="INFO",
                message="系統日誌功能已啟用，但尚未生成日誌文件"
            )]
        
        return LogsResponse(
            logs=logs,
            total=len(logs),
            page=page,
            page_size=page_size,
        )
        
    except Exception as e:
        logger.error(f"獲取日誌失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取日誌失敗")


@router.delete("/logs")
async def clear_logs() -> Dict[str, Any]:
    """
    清理日誌
    
    Returns:
        Dict[str, Any]: 清理結果
    """
    try:
        log_file = Path(settings.LOG_FILE_PATH)
        if log_file.exists():
            # 備份當前日誌
            backup_path = log_file.with_suffix(f'.{datetime.now().strftime("%Y%m%d_%H%M%S")}.bak')
            log_file.rename(backup_path)
            
            # 創建新的空日誌文件
            log_file.touch()
            
            logger.info(f"日誌已清理，備份文件: {backup_path}")
            
            return {
                "status": "success",
                "message": "日誌已清理",
                "backup_file": str(backup_path),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "info",
                "message": "日誌文件不存在",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"清理日誌失敗: {e}")
        raise HTTPException(status_code=500, detail="清理日誌失敗")