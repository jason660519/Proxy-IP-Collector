"""
代理API端點
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import select, desc, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database_manager import get_db_session_manager, get_db
from app.core.logging import get_logger
from app.models.proxy import Proxy, ProxySource
from app.schemas.proxy import ProxyResponse, ProxyFilter, ProtocolType, AnonymityLevel

logger = get_logger(__name__)

router = APIRouter(prefix="/proxies", tags=["proxies"])


class ProxyStats(BaseModel):
    """代理統計信息"""
    total_count: int
    active_count: int
    by_protocol: Dict[str, int]
    by_anonymity: Dict[str, int]
    by_country: Dict[str, int]
    last_updated: datetime


class ProxyListResponse(BaseModel):
    """代理列表響應"""
    proxies: List[ProxyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int








@router.get("/list", response_model=ProxyListResponse)
async def get_proxies(
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁數量"),
    protocol: Optional[ProtocolType] = Query(None, description="協議篩選"),
    anonymity_level: Optional[AnonymityLevel] = Query(None, description="匿名度篩選"),
    country: Optional[str] = Query(None, description="國家篩選"),
    is_active: Optional[bool] = Query(None, description="活動狀態篩選"),
    source: Optional[str] = Query(None, description="來源篩選"),
    min_response_time: Optional[float] = Query(None, description="最小響應時間篩選"),
    max_response_time: Optional[float] = Query(None, description="最大響應時間篩選"),
    db: AsyncSession = Depends(get_db),
) -> ProxyListResponse:
    """
    獲取代理列表
    
    Args:
        page: 頁碼
        page_size: 每頁數量
        protocol: 協議篩選
        anonymity_level: 匿名度篩選
        country: 國家篩選
        is_active: 活動狀態篩選
        source: 來源篩選
        min_response_time: 最小響應時間篩選
        max_response_time: 最大響應時間篩選
        db: 數據庫會話
        
    Returns:
        ProxyListResponse: 代理列表響應
    """
    try:
        # 構建查詢
        query = select(Proxy)
        
        # 應用篩選條件
        if protocol:
            query = query.where(Proxy.protocol == protocol)
        
        if anonymity_level:
            query = query.where(Proxy.anonymity == anonymity_level)
        
        if country:
            query = query.where(Proxy.country == country)
        
        if is_active is not None:
            query = query.where(Proxy.is_active == is_active)
        
        if source:
            query = query.where(Proxy.source == source)
        
        if min_response_time is not None:
            query = query.where(Proxy.response_time >= min_response_time)
        
        if max_response_time is not None:
            query = query.where(Proxy.response_time <= max_response_time)
        
        # 統計總數
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 獲取分頁數據
        offset = (page - 1) * page_size
        query = query.order_by(desc(Proxy.last_checked)).offset(offset).limit(page_size)
        
        result = await db.execute(query)
        proxies = result.scalars().all()
        
        # 轉換為響應模型
        proxy_responses = [ProxyResponse.from_orm(proxy) for proxy in proxies]
        
        total_pages = (total + page_size - 1) // page_size
        
        return ProxyListResponse(
            proxies=proxy_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
        
    except Exception as e:
        logger.error(f"獲取代理列表失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取代理列表失敗")


@router.get("/{proxy_id}", response_model=ProxyResponse)
async def get_proxy(
    proxy_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProxyResponse:
    """
    獲取單個代理詳情
    
    Args:
        proxy_id: 代理ID
        db: 數據庫會話
        
    Returns:
        ProxyResponse: 代理詳情
    """
    try:
        result = await db.execute(select(Proxy).where(Proxy.id == proxy_id))
        proxy = result.scalar_one_or_none()
        
        if not proxy:
            raise HTTPException(status_code=404, detail="代理不存在")
        
        return ProxyResponse.from_orm(proxy)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取代理詳情失敗: {proxy_id}, 錯誤: {e}")
        raise HTTPException(status_code=500, detail="獲取代理詳情失敗")


@router.delete("/{proxy_id}")
async def delete_proxy(
    proxy_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    刪除代理
    
    Args:
        proxy_id: 代理ID
        db: 數據庫會話
        
    Returns:
        Dict[str, Any]: 刪除結果
    """
    try:
        result = await db.execute(select(Proxy).where(Proxy.id == proxy_id))
        proxy = result.scalar_one_or_none()
        
        if not proxy:
            raise HTTPException(status_code=404, detail="代理不存在")
        
        await db.delete(proxy)
        await db.commit()
        
        logger.info(f"代理已刪除: {proxy_id}")
        
        return {
            "message": "代理已刪除",
            "proxy_id": proxy_id,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除代理失敗: {proxy_id}, 錯誤: {e}")
        raise HTTPException(status_code=500, detail="刪除代理失敗")


@router.get("/stats", response_model=ProxyStats)
async def get_proxy_stats(db: AsyncSession = Depends(get_db)) -> ProxyStats:
    """
    獲取代理統計信息
    
    Args:
        db: 數據庫會話
        
    Returns:
        ProxyStats: 代理統計信息
    """
    try:
        # 總數量
        total_query = select(func.count()).select_from(Proxy)
        total_result = await db.execute(total_query)
        total_count = total_result.scalar() or 0
        
        # 活動代理數量
        active_query = select(func.count()).select_from(Proxy).where(Proxy.is_active == True)
        active_result = await db.execute(active_query)
        active_count = active_result.scalar() or 0
        
        # 按協議統計
        protocol_stats = {}
        try:
            protocol_query = select(Proxy.protocol, func.count()).group_by(Proxy.protocol)
            protocol_result = await db.execute(protocol_query)
            for protocol, count in protocol_result:
                if protocol and protocol != "None" and str(protocol).strip():
                    protocol_stats[str(protocol).strip()] = int(count or 0)
        except Exception as e:
            logger.warning(f"協議統計查詢失敗: {e}")
            protocol_stats = {}
        
        # 按匿名度統計
        anonymity_stats = {}
        try:
            anonymity_query = select(Proxy.anonymity, func.count()).group_by(Proxy.anonymity)
            anonymity_result = await db.execute(anonymity_query)
            for anonymity, count in anonymity_result:
                if anonymity and anonymity != "None" and str(anonymity).strip():
                    anonymity_stats[str(anonymity).strip()] = int(count or 0)
        except Exception as e:
            logger.warning(f"匿名度統計查詢失敗: {e}")
            anonymity_stats = {}
        
        # 按國家統計
        country_stats = {}
        try:
            country_query = select(Proxy.country, func.count()).group_by(Proxy.country)
            country_result = await db.execute(country_query)
            for country, count in country_result:
                if country and country != "None" and str(country).strip():
                    country_stats[str(country).strip()] = int(count or 0)
        except Exception as e:
            logger.warning(f"國家統計查詢失敗: {e}")
            country_stats = {}
        
        # 最後更新時間
        try:
            last_updated_query = select(func.max(Proxy.updated_at))
            last_updated_result = await db.execute(last_updated_query)
            last_updated = last_updated_result.scalar() or datetime.utcnow()
        except Exception as e:
            logger.warning(f"最後更新時間查詢失敗: {e}")
            last_updated = datetime.utcnow()
        
        # 確保所有字典都有有效值
        protocol_stats = protocol_stats or {}
        anonymity_stats = anonymity_stats or {}
        country_stats = country_stats or {}
        
        logger.info(f"代理統計 - 總數: {total_count}, 活動: {active_count}, 協議: {protocol_stats}, 匿名度: {anonymity_stats}, 國家: {country_stats}")
        
        return ProxyStats(
            total_count=int(total_count),
            active_count=int(active_count),
            by_protocol=protocol_stats,
            by_anonymity=anonymity_stats,
            by_country=country_stats,
            last_updated=last_updated,
        )
        
    except Exception as e:
        logger.error(f"獲取代理統計信息失敗: {e}")
        logger.error(f"錯誤詳情: {str(e)}")
        import traceback
        logger.error(f"堆棧跟蹤: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"獲取代理統計信息失敗: {str(e)}")


@router.post("/{proxy_id}/validate")
async def validate_proxy(
    proxy_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    驗證代理
    
    Args:
        proxy_id: 代理ID
        db: 數據庫會話
        
    Returns:
        Dict[str, Any]: 驗證結果
    """
    try:
        result = await db.execute(select(Proxy).where(Proxy.id == proxy_id))
        proxy = result.scalar_one_or_none()
        
        if not proxy:
            raise HTTPException(status_code=404, detail="代理不存在")
        
        # TODO: 實現代理驗證邏輯
        # 這裡應該調用代理驗證服務
        is_valid = True  # 臨時設置為有效
        
        # 更新代理狀態
        proxy.is_active = is_valid
        proxy.last_checked = datetime.utcnow()
        proxy.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "proxy_id": proxy_id,
            "is_valid": is_valid,
            "message": "代理驗證完成",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"驗證代理失敗: {proxy_id}, 錯誤: {e}")
        raise HTTPException(status_code=500, detail="驗證代理失敗")


@router.get("/random", response_model=ProxyResponse)
async def get_random_proxy(
    protocol: Optional[ProtocolType] = Query(None, description="協議篩選"),
    anonymity_level: Optional[AnonymityLevel] = Query(None, description="匿名度篩選"),
    country: Optional[str] = Query(None, description="國家篩選"),
    db: AsyncSession = Depends(get_db),
) -> ProxyResponse:
    """
    獲取隨機代理
    
    Args:
        protocol: 協議篩選
        anonymity_level: 匿名度篩選
        country: 國家篩選
        db: 數據庫會話
        
    Returns:
        ProxyResponse: 隨機代理
    """
    try:
        query = select(Proxy).where(Proxy.is_active == True)
        
        if protocol:
            query = query.where(Proxy.protocol == protocol)
        
        if anonymity_level:
            query = query.where(Proxy.anonymity == anonymity_level)
        
        if country:
            query = query.where(Proxy.country == country)
        
        # 隨機排序
        query = query.order_by(func.random()).limit(1)
        
        result = await db.execute(query)
        proxy = result.scalar_one_or_none()
        
        if not proxy:
            raise HTTPException(status_code=404, detail="沒有符合條件的代理")
        
        return ProxyResponse.from_orm(proxy)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取隨機代理失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取隨機代理失敗")