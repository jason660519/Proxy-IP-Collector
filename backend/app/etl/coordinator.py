"""
爬取協調器模組
"""
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from app.etl.extractors.base import BaseExtractor, ExtractResult
from app.etl.extractors.factory import extractor_factory
from app.core.logging import get_logger
from app.core.exceptions import FetcherException
from app.core.database import get_db_session
from app.models.proxy import Proxy, ProxyCrawlLog
from app.schemas.proxy import ProxyCreate
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

logger = get_logger(__name__)


class ExtractionCoordinator:
    """爬取協調器類"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化爬取協調器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.max_concurrent = config.get("max_concurrent", 5)
        self.retry_attempts = config.get("retry_attempts", 3)
        self.retry_delay = config.get("retry_delay", 5)
        self.rate_limit_delay = config.get("rate_limit_delay", 1)
        self.enabled_sources = config.get("enabled_sources", [])
        self.config_file_path = config.get("config_file_path", "backend/config/proxy_sources.json")
        
        # 創建線程池
        self.executor = ThreadPoolExecutor(max_workers=self.max_concurrent)
        
        # 速率限制器
        self.rate_limiters = {}
        
        # 爬取統計
        self.stats = {
            "total_sources": 0,
            "successful_sources": 0,
            "failed_sources": 0,
            "total_proxies": 0,
            "start_time": None,
            "end_time": None,
            "extraction_results": []
        }
    
    async def coordinate_extraction(self, sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        協調多個爬取器的提取任務
        
        Args:
            sources: 要提取的來源列表，如果為None則提取所有啟用的來源
            
        Returns:
            Dict[str, Any]: 提取統計信息
        """
        logger.info("開始協調爬取任務")
        
        # 確定要提取的來源
        if sources is None:
            sources = self.enabled_sources
        
        if not sources:
            logger.warning("沒有啟用的爬取來源")
            return self.stats
        
        # 初始化統計
        self.stats.update({
            "total_sources": len(sources),
            "successful_sources": 0,
            "failed_sources": 0,
            "total_proxies": 0,
            "start_time": datetime.utcnow(),
            "end_time": None,
        })
        
        # 創建爬取器實例
        extractors = []
        for source_name in sources:
            try:
                source_config = self._get_source_config(source_name)
                if source_config and source_config.get("enabled", True):
                    # 添加速率限制配置
                    source_config.update({
                        "rate_limit": source_config.get("rate_limit", 60),
                        "timeout": source_config.get("timeout", 30),
                        "retry_count": source_config.get("retry_count", 3)
                    })
                    
                    extractor = extractor_factory.create_extractor(source_name, source_config)
                    extractors.append(extractor)
                    
                    # 初始化速率限制器
                    self._init_rate_limiter(source_name, source_config.get("rate_limit", 60))
            except Exception as e:
                logger.error(f"創建爬取器失敗: {source_name}, 錯誤: {e}")
                self.stats["failed_sources"] += 1
        
        if not extractors:
            logger.warning("沒有可用的爬取器")
            return self.stats
        
        # 執行並發提取
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def extract_with_semaphore(extractor: BaseExtractor) -> ExtractResult:
            async with semaphore:
                # 應用速率限制
                await self._apply_rate_limit(extractor.name)
                return await self._extract_with_retry(extractor)
        
        # 並發執行所有提取任務
        tasks = [extract_with_semaphore(extractor) for extractor in extractors]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果
        all_proxies = []
        for i, result in enumerate(results):
            extractor_name = extractors[i].name
            
            if isinstance(result, Exception):
                logger.error(f"爬取器 {extractor_name} 失敗: {result}")
                self.stats["failed_sources"] += 1
                # 記錄失敗結果
                self.stats["extraction_results"].append({
                    "source": extractor_name,
                    "success": False,
                    "error": str(result),
                    "proxies_count": 0
                })
                continue
            
            if result.success:
                self.stats["successful_sources"] += 1
                self.stats["total_proxies"] += len(result.proxies)
                all_proxies.extend(result.proxies)
                logger.info(f"爬取器 {extractor_name} 成功，提取 {len(result.proxies)} 個代理")
                
                # 記錄成功結果
                self.stats["extraction_results"].append({
                    "source": extractor_name,
                    "success": True,
                    "proxies_count": len(result.proxies),
                    "metadata": result.metadata
                })
            else:
                self.stats["failed_sources"] += 1
                logger.error(f"爬取器 {extractor_name} 失敗: {result.error_message}")
                
                # 記錄失敗結果
                self.stats["extraction_results"].append({
                    "source": extractor_name,
                    "success": False,
                    "error": result.error_message,
                    "proxies_count": 0
                })
        
        # 保存代理到數據庫
        if all_proxies:
            saved_count = await self._save_proxies_to_database(all_proxies)
            logger.info(f"成功保存 {saved_count} 個代理到數據庫")
        
        # 更新統計
        self.stats["end_time"] = datetime.utcnow()
        
        # 記錄爬取日誌
        await self._log_extraction_results(results)
        
        logger.info(f"爬取任務完成，統計: {self.stats}")
        return self.stats
    
    async def _extract_with_retry(self, extractor: BaseExtractor) -> ExtractResult:
        """
        帶重試的提取
        
        Args:
            extractor: 爬取器實例
            
        Returns:
            ExtractResult: 提取結果
        """
        for attempt in range(self.retry_attempts):
            try:
                # 速率限制延遲
                if attempt > 0:
                    await asyncio.sleep(self.rate_limit_delay * attempt)
                
                result = await extractor.extract()
                
                if result.success:
                    return result
                else:
                    logger.warning(f"爬取器 {extractor.name} 第 {attempt + 1} 次嘗試失敗: {result.error_message}")
                    
            except Exception as e:
                logger.error(f"爬取器 {extractor.name} 第 {attempt + 1} 次嘗試異常: {e}")
                
                if attempt == self.retry_attempts - 1:
                    # 最後一次嘗試也失敗
                    return ExtractResult(
                        source=extractor.name,
                        proxies=[],
                        metadata={"attempts": attempt + 1},
                        success=False,
                        error_message=str(e),
                    )
                
                # 等待重試延遲
                await asyncio.sleep(self.retry_delay)
        
        # 所有重試都失敗
        return ExtractResult(
            source=extractor.name,
            proxies=[],
            metadata={"attempts": self.retry_attempts},
            success=False,
            error_message="所有重試都失敗",
        )
    
    async def _save_proxies_to_database(self, proxies_data: List[Dict[str, Any]]) -> int:
        """
        保存代理到數據庫
        
        Args:
            proxies_data: 代理數據列表
            
        Returns:
            int: 成功保存的數量
        """
        saved_count = 0
        
        try:
            async with get_db_session() as session:
                for proxy_data in proxies_data:
                    try:
                        # 檢查是否已存在
                        existing = await session.execute(
                            select(Proxy).where(
                                Proxy.ip == proxy_data["ip"],
                                Proxy.port == proxy_data["port"]
                            )
                        )
                        existing_proxy = existing.scalar_one_or_none()
                        
                        if existing_proxy:
                            # 更新現有代理
                            for key, value in proxy_data.items():
                                if hasattr(existing_proxy, key) and value is not None:
                                    setattr(existing_proxy, key, value)
                            existing_proxy.updated_at = datetime.utcnow()
                        else:
                            # 創建新代理
                            proxy_create = ProxyCreate(**proxy_data)
                            new_proxy = Proxy(**proxy_create.dict())
                            session.add(new_proxy)
                        
                        saved_count += 1
                        
                    except Exception as e:
                        logger.error(f"保存代理失敗: {proxy_data}, 錯誤: {e}")
                        continue
                
                await session.commit()
                
        except SQLAlchemyError as e:
            logger.error(f"數據庫錯誤: {e}")
        except Exception as e:
            logger.error(f"保存代理到數據庫失敗: {e}")
        
        return saved_count
    
    async def _log_extraction_results(self, results: List[ExtractResult]) -> None:
        """
        記錄爬取結果
        
        Args:
            results: 提取結果列表
        """
        try:
            async with get_db_session() as session:
                for result in results:
                    if isinstance(result, Exception):
                        continue
                    
                    log_entry = ProxyCrawlLog(
                        source=result.source,
                        total_found=len(result.proxies),
                        success=result.success,
                        error_message=result.error_message,
                        metadata=result.metadata,
                    )
                    session.add(log_entry)
                
                await session.commit()
                
        except Exception as e:
            logger.error(f"記錄爬取日誌失敗: {e}")
    
    def _get_source_config(self, source_name: str) -> Optional[Dict[str, Any]]:
        """
        獲取來源配置
        
        Args:
            source_name: 來源名稱
            
        Returns:
            Optional[Dict[str, Any]]: 來源配置
        """
        try:
            # 從配置文件加載
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 查找對應的來源配置
            for source_config in config_data.get("proxy_sources", []):
                if source_config.get("name") == source_name:
                    return source_config
            
            logger.warning(f"未找到來源配置: {source_name}")
            return None
            
        except FileNotFoundError:
            logger.error(f"配置文件不存在: {self.config_file_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式錯誤: {e}")
            return None
        except Exception as e:
            logger.error(f"加載來源配置失敗: {e}")
            return None
    
    def _init_rate_limiter(self, source_name: str, rate_limit: int) -> None:
        """
        初始化速率限制器
        
        Args:
            source_name: 來源名稱
            rate_limit: 每分鐘請求限制
        """
        self.rate_limiters[source_name] = {
            "rate_limit": rate_limit,
            "last_request_time": 0,
            "request_count": 0,
            "window_start": datetime.utcnow()
        }
    
    async def _apply_rate_limit(self, source_name: str) -> None:
        """
        應用速率限制
        
        Args:
            source_name: 來源名稱
        """
        if source_name not in self.rate_limiters:
            return
        
        rate_limiter = self.rate_limiters[source_name]
        now = datetime.utcnow()
        
        # 檢查是否在新窗口
        time_diff = (now - rate_limiter["window_start"]).total_seconds()
        if time_diff >= 60:  # 新的一分鐘窗口
            rate_limiter["request_count"] = 0
            rate_limiter["window_start"] = now
        
        # 檢查是否超過速率限制
        if rate_limiter["request_count"] >= rate_limiter["rate_limit"]:
            # 等待到下一個窗口
            wait_time = 60 - time_diff
            if wait_time > 0:
                logger.info(f"速率限制: {source_name} 等待 {wait_time:.1f} 秒")
                await asyncio.sleep(wait_time)
                rate_limiter["request_count"] = 0
                rate_limiter["window_start"] = datetime.utcnow()
        
        # 增加請求計數
        rate_limiter["request_count"] += 1
        
        # 確保請求間隔
        last_request_time = rate_limiter["last_request_time"]
        if last_request_time > 0:
            time_since_last = (now.timestamp() - last_request_time)
            min_interval = 60 / rate_limiter["rate_limit"]  # 最小間隔
            
            if time_since_last < min_interval:
                sleep_time = min_interval - time_since_last
                await asyncio.sleep(sleep_time)
        
        rate_limiter["last_request_time"] = now.timestamp()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        獲取統計信息
        
        Returns:
            Dict[str, Any]: 統計信息
        """
        return self.stats.copy()
    
    async def cleanup(self) -> None:
        """
        清理資源
        """
        logger.info("清理爬取協調器資源")
        self.executor.shutdown(wait=True)


# 創建全局協調器實例
coordinator = None


def get_coordinator(config: Optional[Dict[str, Any]] = None) -> ExtractionCoordinator:
    """
    獲取爬取協調器實例
    
    Args:
        config: 配置字典
        
    Returns:
        ExtractionCoordinator: 爬取協調器實例
    """
    global coordinator
    
    if coordinator is None:
        if config is None:
            config = {
                "max_concurrent": 5,
                "retry_attempts": 3,
                "retry_delay": 5,
                "rate_limit_delay": 1,
                "enabled_sources": [],
            }
        
        coordinator = ExtractionCoordinator(config)
    
    return coordinator