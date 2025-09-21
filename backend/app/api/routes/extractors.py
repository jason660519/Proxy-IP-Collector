"""
代理爬取器API路由
提供RESTful API接口來管理和執行代理爬取任務
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import logging
from datetime import datetime

from app.etl.extractors.factory import ExtractorFactory

logger = logging.getLogger(__name__)

# API請求模型
class ExtractRequest(BaseModel):
    limit: Optional[int] = 100
    timeout: Optional[int] = 30
    test_mode: Optional[bool] = False
    filters: Optional[Dict[str, Any]] = None

class ValidateRequest(BaseModel):
    ip: str
    port: int
    protocol: Optional[str] = "http"
    timeout: Optional[int] = 10

# 創建路由
router = APIRouter(prefix="/api", tags=["proxy-extractors"])

# 全局爬取器工廠實例
extractor_factory = ExtractorFactory()

@router.get("/extractors")
async def get_available_extractors():
    """獲取所有可用的爬取器列表"""
    try:
        extractors = extractor_factory.get_available_extractors()
        return {
            "success": True,
            "extractors": extractors,
            "count": len(extractors)
        }
    except Exception as e:
        logger.error(f"獲取爬取器列表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取爬取器列表失敗: {str(e)}")

@router.post("/extract/{extractor_name}")
async def extract_proxies(extractor_name: str, request: ExtractRequest, background_tasks: BackgroundTasks):
    """使用指定的爬取器提取代理"""
    try:
        # 創建爬取器實例
        extractor = extractor_factory.create_extractor(extractor_name)
        if not extractor:
            raise HTTPException(status_code=404, detail=f"爬取器 '{extractor_name}' 不存在")
        
        logger.info(f"開始使用 {extractor_name} 爬取代理，限制: {request.limit}")
        
        # 執行爬取任務
        start_time = datetime.now()
        
        if request.test_mode:
            # 測試模式：快速爬取少量數據
            result = await extractor.extract()
            proxies = result.proxies[:min(request.limit, 10)]
        else:
            # 正常模式：完整爬取
            result = await extractor.extract()
            proxies = result.proxies[:request.limit]
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"爬取完成: {extractor_name}, 耗時: {duration:.2f}s, 獲取代理: {len(proxies)}")
        
        return {
            "success": result.success if hasattr(result, 'success') else True,
            "extractor": extractor_name,
            "proxies": proxies,
            "count": len(proxies),
            "duration": duration,
            "timestamp": end_time.isoformat()
        }
        
    except asyncio.TimeoutError:
        logger.error(f"爬取器 {extractor_name} 超時")
        raise HTTPException(status_code=408, detail="爬取任務超時")
    except ValueError as e:
        logger.error(f"爬取器參數錯誤: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"爬取器執行失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"爬取器執行失敗: {str(e)}")

@router.post("/extract-all")
async def extract_all_proxies(request: ExtractRequest):
    """使用所有可用的爬取器提取代理"""
    try:
        all_proxies = []
        results = {}
        
        extractors = extractor_factory.get_available_extractors()
        logger.info(f"開始使用所有爬取器提取代理，共 {len(extractors)} 個爬取器")
        
        # 並行執行所有爬取任務
        tasks = []
        for extractor_name in extractors:
            try:
                extractor = extractor_factory.create_extractor(extractor_name)
                if extractor:
                    task = asyncio.create_task(
                        extractor.extract()
                    )
                    tasks.append((extractor_name, task))
            except Exception as e:
                logger.warning(f"創建爬取器任務失敗 {extractor_name}: {str(e)}")
                continue
        
        # 等待所有任務完成
        for extractor_name, task in tasks:
            try:
                result = await task
                proxies = result.proxies[:max(1, request.limit // len(extractors))]
                results[extractor_name] = {
                    "success": result.success,
                    "count": len(proxies),
                    "proxies": proxies
                }
                all_proxies.extend(proxies)
                logger.info(f"爬取器 {extractor_name} 完成，獲取 {len(proxies)} 個代理")
            except Exception as e:
                logger.error(f"爬取器 {extractor_name} 失敗: {str(e)}")
                results[extractor_name] = {
                    "success": False,
                    "error": str(e),
                    "count": 0,
                    "proxies": []
                }
        
        logger.info(f"所有爬取任務完成，共獲取 {len(all_proxies)} 個代理")
        
        return {
            "success": True,
            "total_proxies": len(all_proxies),
            "results": results,
            "all_proxies": all_proxies,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"批量爬取失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量爬取失敗: {str(e)}")

@router.post("/proxies/validate")
async def validate_proxy(request: ValidateRequest):
    """驗證單個代理的可用性"""
    try:
        # 這裡可以集成代理驗證邏輯
        # 為了演示，返回模擬結果
        is_valid = await simulate_proxy_validation(request.ip, request.port, request.protocol, request.timeout)
        
        return {
            "success": True,
            "ip": request.ip,
            "port": request.port,
            "protocol": request.protocol,
            "is_valid": is_valid,
            "response_time": 150 if is_valid else None,  # 模擬響應時間
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"代理驗證失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"代理驗證失敗: {str(e)}")

@router.get("/proxies")
async def get_proxies(
    source: Optional[str] = None,
    protocol: Optional[str] = None,
    country: Optional[str] = None,
    anonymity_level: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: Optional[int] = 100
):
    """獲取代理列表，支持多種篩選條件"""
    try:
        # 這裡應該從數據庫或緩存中獲取代理數據
        # 為了演示，返回模擬數據
        proxies = await generate_mock_proxies(limit, source, protocol, country, anonymity_level, is_active)
        
        return {
            "success": True,
            "proxies": proxies,
            "count": len(proxies),
            "filters": {
                "source": source,
                "protocol": protocol,
                "country": country,
                "anonymity_level": anonymity_level,
                "is_active": is_active
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"獲取代理列表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取代理列表失敗: {str(e)}")

@router.get("/health")
async def health_check():
    """系統健康檢查"""
    try:
        extractors = extractor_factory.get_available_extractors()
        return {
            "status": "healthy",
            "available_extractors": len(extractors),
            "extractors": extractors,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"健康檢查失敗: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# 輔助函數
async def simulate_proxy_validation(ip: str, port: int, protocol: str, timeout: int) -> bool:
    """模擬代理驗證（實際項目中需要實現真實的驗證邏輯）"""
    # 模擬網絡延遲
    await asyncio.sleep(0.1)
    
    # 簡單的可用性判斷（實際項目中需要真實的連接測試）
    # 假設80%的代理是可用的
    import random
    return random.random() > 0.2

async def generate_mock_proxies(limit: int, source: Optional[str] = None, 
                              protocol: Optional[str] = None, country: Optional[str] = None,
                              anonymity_level: Optional[str] = None, is_active: Optional[bool] = None):
    """生成模擬代理數據（實際項目中應該從數據庫獲取）"""
    import random
    
    protocols = ["http", "https", "socks4", "socks5"]
    countries = ["US", "CN", "JP", "DE", "FR", "GB", "CA", "AU"]
    anonymity_levels = ["elite", "anonymous", "transparent"]
    sources = ["free-proxy-list.net", "proxy-list.plus", "proxy-scrape", "geonode"]
    
    proxies = []
    for i in range(limit):
        # 生成隨機代理數據
        proxy_protocol = protocol or random.choice(protocols)
        proxy_country = country or random.choice(countries)
        proxy_anonymity = anonymity_level or random.choice(anonymity_levels)
        proxy_source = source or random.choice(sources)
        
        proxy = {
            "ip": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "port": random.randint(1000, 65535),
            "protocol": proxy_protocol,
            "country": proxy_country,
            "anonymity_level": proxy_anonymity,
            "speed": random.randint(50, 2000),
            "source": proxy_source,
            "is_active": is_active if is_active is not None else random.choice([True, False]),
            "last_checked": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        proxies.append(proxy)
    
    return proxies