"""
代理IP驗證服務
"""
import asyncio
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
import aiohttp
from aiohttp import ClientTimeout, ClientError
import structlog
from sqlalchemy.orm import Session

from ..models.proxy import Proxy, ProxyCheckResult
from ..schemas.proxy import ProxyValidationRequest, ProtocolType
from ..core.exceptions import ValidationException, NetworkException

logger = structlog.get_logger(__name__)


class ProxyValidator:
    """代理IP驗證器"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.timeout = ClientTimeout(total=30)
        self.test_urls = {
            ProtocolType.HTTP: "http://httpbin.org/ip",
            ProtocolType.HTTPS: "https://httpbin.org/ip",
            ProtocolType.SOCKS4: "http://httpbin.org/ip",
            ProtocolType.SOCKS5: "http://httpbin.org/ip"
        }
        self.default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    async def validate_proxies(
        self, 
        proxies: List[Proxy], 
        max_concurrent: int = 10,
        timeout: int = 10,
        test_urls: Optional[List[str]] = None
    ) -> List[ProxyCheckResult]:
        """
        驗證代理IP列表
        
        Args:
            proxies: 要驗證的代理列表
            max_concurrent: 最大並發數
            timeout: 超時時間(秒)
            test_urls: 自定義測試URL列表
            
        Returns:
            驗證結果列表
        """
        if not proxies:
            return []
        
        logger.info("開始驗證代理", count=len(proxies), max_concurrent=max_concurrent)
        
        # 使用信號量控制並發
        semaphore = asyncio.Semaphore(max_concurrent)
        tasks = []
        
        for proxy in proxies:
            task = self._validate_single_proxy(
                proxy, 
                semaphore, 
                timeout, 
                test_urls
            )
            tasks.append(task)
        
        # 等待所有驗證完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 過濾異常結果
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("代理驗證異常", error=str(result))
            else:
                valid_results.append(result)
        
        # 保存驗證結果到數據庫
        await self._save_check_results(valid_results)
        
        logger.info("代理驗證完成", 
                   total=len(proxies), 
                   successful=len([r for r in valid_results if r.is_successful]))
        
        return valid_results
    
    async def _validate_single_proxy(
        self, 
        proxy: Proxy, 
        semaphore: asyncio.Semaphore,
        timeout: int,
        test_urls: Optional[List[str]] = None
    ) -> ProxyCheckResult:
        """驗證單個代理"""
        async with semaphore:
            start_time = time.time()
            
            try:
                # 構建代理URL
                proxy_url = self._build_proxy_url(proxy)
                
                # 選擇測試URL
                test_url = self._select_test_url(proxy, test_urls)
                
                # 執行HTTP請求測試
                success, response_time, status_code, error_msg, headers = \
                    await self._test_proxy_connection(proxy_url, test_url, timeout)
                
                # 計算響應時間
                total_time = int((time.time() - start_time) * 1000)
                
                # 創建檢查結果
                result = ProxyCheckResult(
                    proxy_id=str(proxy.id),
                    is_successful=success,
                    response_time=response_time or total_time,
                    error_message=error_msg,
                    check_type="http_test",
                    target_url=test_url,
                    headers_sent=self.default_headers,
                    headers_received=headers or {},
                    status_code=status_code,
                    checked_at=datetime.now(timezone.utc)
                )
                
                # 更新代理狀態
                await self._update_proxy_status(proxy, success, response_time)
                
                return result
                
            except Exception as e:
                logger.error("代理驗證異常", proxy_id=str(proxy.id), error=str(e))
                return ProxyCheckResult(
                    proxy_id=str(proxy.id),
                    is_successful=False,
                    error_message=str(e),
                    check_type="http_test",
                    checked_at=datetime.now(timezone.utc)
                )
    
    def _build_proxy_url(self, proxy: Proxy) -> str:
        """構建代理URL"""
        return f"{proxy.protocol}://{proxy.ip}:{proxy.port}"
    
    def _select_test_url(self, proxy: Proxy, custom_urls: Optional[List[str]] = None) -> str:
        """選擇測試URL"""
        if custom_urls:
            return custom_urls[0]
        
        protocol = ProtocolType(proxy.protocol)
        return self.test_urls.get(protocol, self.test_urls[ProtocolType.HTTP])
    
    async def _test_proxy_connection(
        self, 
        proxy_url: str, 
        test_url: str, 
        timeout: int
    ) -> Tuple[bool, Optional[int], Optional[int], Optional[str], Optional[Dict[str, str]]]:
        """
        測試代理連接
        
        Returns:
            (success, response_time, status_code, error_message, headers)
        """
        connector = aiohttp.TCPConnector(limit=1, limit_per_host=1)
        timeout_config = ClientTimeout(total=timeout)
        
        try:
            async with aiohttp.ClientSession(
                connector=connector, 
                timeout=timeout_config,
                headers=self.default_headers
            ) as session:
                
                start_time = time.time()
                
                async with session.get(
                    test_url,
                    proxy=proxy_url,
                    ssl=False
                ) as response:
                    
                    response_time = int((time.time() - start_time) * 1000)
                    
                    # 檢查響應狀態
                    if response.status == 200:
                        # 讀取響應內容驗證
                        content = await response.text()
                        if self._validate_response_content(content):
                            return True, response_time, response.status, None, dict(response.headers)
                        else:
                            return False, response_time, response.status, "Invalid response content", dict(response.headers)
                    else:
                        return False, response_time, response.status, f"HTTP {response.status}", dict(response.headers)
                        
        except asyncio.TimeoutError:
            return False, None, None, "Connection timeout", None
        except ClientError as e:
            return False, None, None, f"Client error: {str(e)}", None
        except Exception as e:
            return False, None, None, f"Unexpected error: {str(e)}", None
        finally:
            await connector.close()
    
    def _validate_response_content(self, content: str) -> bool:
        """驗證響應內容是否有效"""
        try:
            import json
            data = json.loads(content)
            # 檢查是否包含IP信息
            return "origin" in data or "ip" in data
        except:
            return False
    
    async def _update_proxy_status(
        self, 
        proxy: Proxy, 
        success: bool, 
        response_time: Optional[int]
    ):
        """更新代理狀態"""
        try:
            if success:
                proxy.status = "active"
                proxy.last_success = datetime.now(timezone.utc)
                if response_time:
                    proxy.response_time = response_time
            else:
                proxy.status = "inactive"
            
            proxy.last_checked = datetime.now(timezone.utc)
            self.db_session.commit()
            
        except Exception as e:
            logger.error("更新代理狀態失敗", proxy_id=str(proxy.id), error=str(e))
            self.db_session.rollback()
    
    async def _save_check_results(self, results: List[ProxyCheckResult]):
        """保存檢查結果到數據庫"""
        try:
            for result in results:
                self.db_session.add(result)
            self.db_session.commit()
            logger.info("檢查結果已保存", count=len(results))
        except Exception as e:
            logger.error("保存檢查結果失敗", error=str(e))
            self.db_session.rollback()
    
    async def validate_proxy_by_criteria(
        self,
        request: ProxyValidationRequest
    ) -> Dict[str, Any]:
        """
        根據條件驗證代理
        
        Args:
            request: 驗證請求參數
            
        Returns:
            驗證結果統計
        """
        start_time = time.time()
        
        # 查詢要驗證的代理
        query = self.db_session.query(Proxy)
        
        if request.proxy_ids:
            query = query.filter(Proxy.id.in_(request.proxy_ids))
        
        if request.protocols:
            query = query.filter(Proxy.protocol.in_(request.protocols))
        
        if request.countries:
            query = query.filter(Proxy.country.in_(request.countries))
        
        proxies = query.limit(1000).all()  # 限制數量避免過載
        
        if not proxies:
            return {
                "total_tested": 0,
                "successful": 0,
                "failed": 0,
                "results": [],
                "duration": 0,
                "started_at": datetime.now(timezone.utc),
                "completed_at": datetime.now(timezone.utc)
            }
        
        # 執行驗證
        results = await self.validate_proxies(
            proxies,
            max_concurrent=request.max_concurrent,
            timeout=request.timeout,
            test_urls=request.test_urls
        )
        
        # 統計結果
        successful = len([r for r in results if r.is_successful])
        failed = len(results) - successful
        duration = int(time.time() - start_time)
        
        return {
            "total_tested": len(results),
            "successful": successful,
            "failed": failed,
            "results": results,
            "duration": duration,
            "started_at": datetime.fromtimestamp(start_time),
            "completed_at": datetime.now(timezone.utc)
        }
    
    async def get_proxy_stats(self) -> Dict[str, Any]:
        """獲取代理統計信息"""
        try:
            total_proxies = self.db_session.query(Proxy).count()
            active_proxies = self.db_session.query(Proxy).filter(Proxy.status == "active").count()
            inactive_proxies = total_proxies - active_proxies
            
            # 協議統計
            protocol_stats = {}
            for protocol in ProtocolType:
                count = self.db_session.query(Proxy).filter(Proxy.protocol == protocol.value).count()
                if count > 0:
                    protocol_stats[protocol.value] = count
            
            # 國家統計
            country_stats = {}
            countries = self.db_session.query(Proxy.country).filter(Proxy.country.isnot(None)).distinct().all()
            for country, in countries:
                count = self.db_session.query(Proxy).filter(Proxy.country == country).count()
                if count > 0:
                    country_stats[country] = count
            
            # 匿名等級統計
            anonymity_stats = {}
            anonymity_levels = self.db_session.query(Proxy.anonymity).filter(Proxy.anonymity.isnot(None)).distinct().all()
            for anonymity, in anonymity_levels:
                count = self.db_session.query(Proxy).filter(Proxy.anonymity == anonymity).count()
                if count > 0:
                    anonymity_stats[anonymity] = count
            
            # 計算平均值
            avg_response_time = self.db_session.query(Proxy.response_time).filter(Proxy.response_time > 0).first()
            avg_response_time = avg_response_time[0] if avg_response_time else 0
            
            avg_success_rate = self.db_session.query(Proxy.success_rate).filter(Proxy.success_rate > 0).first()
            avg_success_rate = avg_success_rate[0] if avg_success_rate else 0
            
            avg_quality_score = self.db_session.query(Proxy.quality_score).filter(Proxy.quality_score > 0).first()
            avg_quality_score = avg_quality_score[0] if avg_quality_score else 0
            
            return {
                "total_proxies": total_proxies,
                "active_proxies": active_proxies,
                "inactive_proxies": inactive_proxies,
                "protocols": protocol_stats,
                "countries": country_stats,
                "anonymity_levels": anonymity_stats,
                "avg_response_time": avg_response_time,
                "avg_success_rate": avg_success_rate,
                "avg_quality_score": avg_quality_score,
                "last_updated": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error("獲取代理統計失敗", error=str(e))
            raise ValidationException(f"Failed to get proxy stats: {str(e)}")
    
    async def cleanup_old_results(self, days: int = 7):
        """清理舊的檢查結果"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            deleted_count = self.db_session.query(ProxyCheckResult).filter(
                ProxyCheckResult.checked_at < cutoff_date
            ).delete()
            
            self.db_session.commit()
            logger.info("清理舊檢查結果", deleted_count=deleted_count, days=days)
            
        except Exception as e:
            logger.error("清理舊檢查結果失敗", error=str(e))
            self.db_session.rollback()


# 全局服務函數
async def validate_proxy_service(
    db_session: Session,
    proxy_id: str,
    test_urls: Optional[List[str]] = None,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    驗證單個代理服務
    
    Args:
        db_session: 數據庫會話
        proxy_id: 代理ID
        test_urls: 測試URL列表
        timeout: 超時時間（秒）
        
    Returns:
        驗證結果
    """
    validator = ProxyValidator(db_session)
    
    # 查詢代理
    proxy = db_session.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not proxy:
        raise ValidationException(f"代理不存在: {proxy_id}")
    
    # 執行驗證
    results = await validator.validate_proxies([proxy], timeout=timeout, test_urls=test_urls)
    
    if not results:
        raise ValidationException("驗證失敗")
    
    result = results[0]
    return {
        "proxy_id": proxy_id,
        "is_successful": result.is_successful,
        "response_time": result.response_time,
        "status_code": result.status_code,
        "error_message": result.error_message,
        "checked_at": result.checked_at
    }


async def validate_proxies_batch_service(
    db_session: Session,
    proxy_ids: List[str],
    max_concurrent: int = 10,
    timeout: int = 10,
    test_urls: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    批量驗證代理服務
    
    Args:
        db_session: 數據庫會話
        proxy_ids: 代理ID列表
        max_concurrent: 最大並發數
        timeout: 超時時間（秒）
        test_urls: 測試URL列表
        
    Returns:
        批量驗證結果
    """
    validator = ProxyValidator(db_session)
    
    # 查詢代理
    proxies = db_session.query(Proxy).filter(Proxy.id.in_(proxy_ids)).all()
    if not proxies:
        raise ValidationException("未找到有效的代理")
    
    # 執行批量驗證
    results = await validator.validate_proxies(
        proxies,
        max_concurrent=max_concurrent,
        timeout=timeout,
        test_urls=test_urls
    )
    
    # 統計結果
    successful = len([r for r in results if r.is_successful])
    failed = len(results) - successful
    
    return {
        "total_tested": len(results),
        "successful": successful,
        "failed": failed,
        "success_rate": successful / len(results) if results else 0,
        "results": [
            {
                "proxy_id": result.proxy_id,
                "is_successful": result.is_successful,
                "response_time": result.response_time,
                "status_code": result.status_code,
                "error_message": result.error_message,
                "checked_at": result.checked_at
            }
            for result in results
        ]
    }