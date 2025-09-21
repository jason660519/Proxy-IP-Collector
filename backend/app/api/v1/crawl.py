"""
爬取API端點
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from datetime import datetime

from app.etl.coordinator import get_coordinator, ExtractionCoordinator
from app.etl.extractors.factory import extractor_factory
from app.core.logging import get_logger
from app.core.database import get_db_session
from app.models.proxy import ProxyCrawlLog
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)

router = APIRouter(prefix="/crawl", tags=["crawl"])


class CrawlRequest(BaseModel):
    """爬取請求模型"""
    sources: Optional[List[str]] = None
    max_concurrent: Optional[int] = 5
    retry_attempts: Optional[int] = 3
    rate_limit_delay: Optional[float] = 1.0


class CrawlResponse(BaseModel):
    """爬取響應模型"""
    task_id: str
    status: str
    message: str
    started_at: datetime
    sources: List[str]


class CrawlStatus(BaseModel):
    """爬取狀態模型"""
    task_id: str
    status: str
    progress: Dict[str, Any]
    stats: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime] = None


class CrawlHistory(BaseModel):
    """爬取歷史模型"""
    id: int
    source: str
    total_found: int
    success: bool
    error_message: Optional[str] = None
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None


# 全局任務存儲（實際應用中應該使用Redis等持久化存儲）
active_tasks: Dict[str, Dict[str, Any]] = {}


def generate_task_id() -> str:
    """生成任務ID"""
    import uuid
    return str(uuid.uuid4())


@router.post("/start", response_model=CrawlResponse)
async def start_crawl(
    crawl_request: CrawlRequest,
    background_tasks: BackgroundTasks,
) -> CrawlResponse:
    """
    開始爬取任務
    
    Args:
        crawl_request: 爬取請求參數
        background_tasks: 後台任務
        
    Returns:
        CrawlResponse: 爬取響應
    """
    task_id = generate_task_id()
    started_at = datetime.utcnow()
    
    # 獲取要爬取的來源
    if crawl_request.sources is None:
        sources = extractor_factory.get_available_extractors()
    else:
        sources = crawl_request.sources
        
        # 驗證來源
        invalid_sources = [
            source for source in sources
            if not extractor_factory.is_extractor_available(source)
        ]
        if invalid_sources:
            raise HTTPException(
                status_code=400,
                detail=f"無效的爬取來源: {invalid_sources}"
            )
    
    # 創建任務配置
    config = {
        "max_concurrent": crawl_request.max_concurrent,
        "retry_attempts": crawl_request.retry_attempts,
        "rate_limit_delay": crawl_request.rate_limit_delay,
        "enabled_sources": sources,
    }
    
    # 初始化任務狀態
    active_tasks[task_id] = {
        "status": "running",
        "sources": sources,
        "started_at": started_at,
        "progress": {"current": 0, "total": len(sources)},
        "stats": {},
    }
    
    # 在後台執行爬取任務
    background_tasks.add_task(_execute_crawl_task, task_id, config)
    
    logger.info(f"爬取任務已啟動: {task_id}, 來源: {sources}")
    
    return CrawlResponse(
        task_id=task_id,
        status="running",
        message="爬取任務已啟動",
        started_at=started_at,
        sources=sources,
    )


async def _execute_crawl_task(task_id: str, config: Dict[str, Any]) -> None:
    """
    執行爬取任務
    
    Args:
        task_id: 任務ID
        config: 任務配置
    """
    try:
        # 獲取協調器
        coordinator = get_coordinator(config)
        
        # 執行爬取
        stats = await coordinator.coordinate_extraction()
        
        # 更新任務狀態
        if task_id in active_tasks:
            active_tasks[task_id].update({
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "stats": stats,
            })
        
        logger.info(f"爬取任務完成: {task_id}, 統計: {stats}")
        
    except Exception as e:
        logger.error(f"爬取任務失敗: {task_id}, 錯誤: {e}")
        
        # 更新任務狀態為失敗
        if task_id in active_tasks:
            active_tasks[task_id].update({
                "status": "failed",
                "completed_at": datetime.utcnow(),
                "error": str(e),
            })


@router.get("/status/{task_id}", response_model=CrawlStatus)
async def get_crawl_status(task_id: str) -> CrawlStatus:
    """
    獲取爬取任務狀態
    
    Args:
        task_id: 任務ID
        
    Returns:
        CrawlStatus: 爬取狀態
    """
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="任務不存在")
    
    task_info = active_tasks[task_id]
    
    return CrawlStatus(
        task_id=task_id,
        status=task_info["status"],
        progress=task_info["progress"],
        stats=task_info.get("stats", {}),
        started_at=task_info["started_at"],
        completed_at=task_info.get("completed_at"),
    )


@router.get("/history", response_model=List[CrawlHistory])
async def get_crawl_history(
    limit: int = 100,
    offset: int = 0,
    source: Optional[str] = None,
    success: Optional[bool] = None,
    db: AsyncSession = Depends(get_db_session),
) -> List[CrawlHistory]:
    """
    獲取爬取歷史
    
    Args:
        limit: 返回記錄數限制
        offset: 偏移量
        source: 來源篩選
        success: 成功狀態篩選
        db: 數據庫會話
        
    Returns:
        List[CrawlHistory]: 爬取歷史列表
    """
    try:
        query = select(ProxyCrawlLog).order_by(desc(ProxyCrawlLog.created_at))
        
        if source:
            query = query.where(ProxyCrawlLog.source == source)
        
        if success is not None:
            query = query.where(ProxyCrawlLog.success == success)
        
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return [
            CrawlHistory(
                id=log.id,
                source=log.source,
                total_found=log.total_found,
                success=log.success,
                error_message=log.error_message,
                created_at=log.created_at,
                metadata=log.extra_metadata,
            )
            for log in logs
        ]
        
    except Exception as e:
        logger.error(f"獲取爬取歷史失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取爬取歷史失敗")


@router.get("/sources")
async def get_available_sources() -> Dict[str, Any]:
    """
    獲取可用的爬取來源
    
    Returns:
        Dict[str, Any]: 可用來源信息
    """
    sources = extractor_factory.get_available_extractors()
    
    return {
        "sources": sources,
        "total": len(sources),
    }


@router.post("/sources/{source_name}/test")
async def test_source(source_name: str) -> Dict[str, Any]:
    """
    測試特定爬取來源
    
    Args:
        source_name: 來源名稱
        
    Returns:
        Dict[str, Any]: 測試結果
    """
    if not extractor_factory.is_extractor_available(source_name):
        raise HTTPException(status_code=404, detail="來源不存在")
    
    try:
        # 創建爬取器實例
        config = {"base_url": ""}  # 基本配置
        extractor = extractor_factory.create_extractor(source_name, config)
        
        # 執行測試提取
        result = await extractor.extract()
        
        return {
            "source": source_name,
            "success": result.success,
            "proxies_found": len(result.proxies),
            "error_message": result.error_message,
            "metadata": result.extra_metadata,
        }
        
    except Exception as e:
        logger.error(f"測試來源失敗: {source_name}, 錯誤: {e}")
        return {
            "source": source_name,
            "success": False,
            "proxies_found": 0,
            "error_message": str(e),
            "metadata": {},
        }


@router.delete("/tasks/{task_id}")
async def cancel_crawl_task(task_id: str) -> Dict[str, Any]:
    """
    取消爬取任務
    
    Args:
        task_id: 任務ID
        
    Returns:
        Dict[str, Any]: 取消結果
    """
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="任務不存在")
    
    task_info = active_tasks[task_id]
    
    if task_info["status"] == "completed":
        return {
            "task_id": task_id,
            "status": "completed",
            "message": "任務已完成，無法取消",
        }
    
    # 更新任務狀態為已取消
    task_info["status"] = "cancelled"
    task_info["completed_at"] = datetime.utcnow()
    
    return {
        "task_id": task_id,
        "status": "cancelled",
        "message": "任務已取消",
    }