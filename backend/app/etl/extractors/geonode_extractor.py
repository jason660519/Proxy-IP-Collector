"""
proxylist.geonode.com API爬取器
"""
from typing import List, Dict, Any, Optional
from app.etl.extractors.base import APIExtractor, ProxyData, ExtractResult
from app.core.logging import get_logger
import asyncio
import json
from datetime import datetime

logger = get_logger(__name__)


class GeoNodeAPIExtractor(APIExtractor):
    """proxylist.geonode.com API爬取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化GeoNode API爬取器
        
        Args:
            config: 配置字典
        """
        super().__init__("proxylist.geonode.com", config)
        self.api_endpoint = config.get("api_endpoint", "https://proxylist.geonode.com/api/proxy-list")
        self.page_range = config.get("page_range", [1, 24])
        self.limit_per_page = config.get("limit_per_page", 100)
        self.sort_by = config.get("sort_by", "lastChecked")
        self.sort_type = config.get("sort_type", "desc")
    
    def get_required_config_fields(self) -> List[str]:
        return ["api_endpoint"]
    
    async def extract(self) -> ExtractResult:
        """
        提取代理數據
        
        Returns:
            ExtractResult: 提取結果
        """
        self.logger.info(f"開始從proxylist.geonode.com API提取代理數據，頁面範圍: {self.page_range}")
        
        start_time = datetime.utcnow()
        all_proxies = []
        
        try:
            # 併發爬取多個頁面
            semaphore = asyncio.Semaphore(5)  # 限制併發數
            tasks = []
            
            start_page, end_page = self.page_range
            for page in range(start_page, end_page + 1):
                task = self._extract_page_with_semaphore(semaphore, page)
                tasks.append(task)
            
            # 等待所有任務完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 收集結果
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"頁面爬取失敗: {result}")
                else:
                    all_proxies.extend(result)
            
            # 去重
            unique_proxies = self._deduplicate_proxies(all_proxies)
            
            result = ExtractResult(
                source=self.name,
                proxies=[proxy.to_dict() for proxy in unique_proxies],
                metadata={
                    "api_endpoint": self.api_endpoint,
                    "pages_crawled": end_page - start_page + 1,
                    "total_found": len(all_proxies),
                    "unique_found": len(unique_proxies),
                    "page_range": self.page_range,
                    "start_time": start_time,
                    "end_time": datetime.utcnow(),
                    "extraction_method": "api_json_parsing"
                },
                success=True,
                timestamp=start_time,
            )
            
            self.logger.info(f"GeoNode API爬取完成，總共找到 {len(all_proxies)} 個代理，去重後 {len(unique_proxies)} 個")
            return result
            
        except Exception as e:
            self.logger.error(f"GeoNode API爬取失敗: {e}")
            return ExtractResult(
                source=self.name,
                proxies=[],
                metadata={"start_time": start_time},
                success=False,
                error_message=str(e),
                timestamp=start_time,
            )
    
    async def _extract_page_with_semaphore(self, semaphore: asyncio.Semaphore, page: int) -> List[ProxyData]:
        """使用信號量控制併發的頁面提取"""
        async with semaphore:
            try:
                # 構建API URL
                url = self._build_api_url(page)
                
                # 發送請求
                response_data = await self.fetch_with_retry(url)
                
                # 解析JSON數據
                proxies = self._parse_json_response(response_data)
                
                # 速率控制
                await asyncio.sleep(0.5)
                
                return proxies
                
            except Exception as e:
                self.logger.error(f"爬取第{page}頁失敗: {e}")
                return []
    
    def _build_api_url(self, page: int) -> str:
        """構建API URL"""
        params = {
            "limit": self.limit_per_page,
            "page": page,
            "sort_by": self.sort_by,
            "sort_type": self.sort_type
        }
        
        # 構建查詢字符串
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{self.api_endpoint}?{query_string}"
        
        return url
    
    def _parse_json_response(self, response_text: str) -> List[ProxyData]:
        """
        解析JSON響應
        
        Args:
            response_text: API響應文本
            
        Returns:
            List[ProxyData]: 代理數據列表
        """
        try:
            # 解析JSON
            data = json.loads(response_text)
            
            proxies = []
            
            # GeoNode API返回格式
            if "data" in data and isinstance(data["data"], list):
                for item in data["data"]:
                    proxy_obj = self._convert_to_proxy_data(item)
                    if proxy_obj:
                        proxies.append(proxy_obj)
            elif isinstance(data, list):
                # 直接是數組格式
                for item in data:
                    proxy_obj = self._convert_to_proxy_data(item)
                    if proxy_obj:
                        proxies.append(proxy_obj)
            
            return proxies
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失敗: {e}")
            return []
        except Exception as e:
            self.logger.error(f"解析API響應失敗: {e}")
            return []
    
    def _convert_to_proxy_data(self, item: Dict[str, Any]) -> Optional[ProxyData]:
        """
        將API項目轉換為ProxyData
        
        Args:
            item: API項目數據
            
        Returns:
            Optional[ProxyData]: ProxyData對象或None
        """
        try:
            # 必需字段
            ip = item.get("ip", "").strip()
            port = item.get("port")
            
            if not ip or not port:
                return None
            
            # 驗證IP格式
            if not self._is_valid_ip(ip):
                return None
            
            # 轉換端口
            try:
                port = int(port)
                if not (1 <= port <= 65535):
                    return None
            except (ValueError, TypeError):
                return None
            
            # 獲取其他字段
            protocol = item.get("protocol", "http").lower()
            country = item.get("country", "unknown")
            city = item.get("city", "unknown")
            anonymity = item.get("anonymity", "unknown")
            
            # 解析響應時間
            response_time = item.get("responseTime")
            speed = None
            if response_time:
                try:
                    speed = float(response_time)
                except (ValueError, TypeError):
                    pass
            
            # 解析最後檢查時間
            last_checked = item.get("lastChecked")
            
            # 創建ProxyData對象
            return ProxyData(
                ip=ip,
                port=port,
                protocol=protocol,
                country=country,
                city=city,
                anonymity_level=anonymity,
                speed=speed,
                source="proxylist.geonode.com"
            )
            
        except (ValueError, TypeError, KeyError) as e:
            self.logger.error(f"轉換API項目失敗: {e}")
            return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """驗證IP地址格式"""
        try:
            import ipaddress
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _deduplicate_proxies(self, proxies: List[ProxyData]) -> List[ProxyData]:
        """去重代理數據"""
        seen = set()
        unique_proxies = []
        
        for proxy in proxies:
            key = (proxy.ip, proxy.port)
            if key not in seen:
                seen.add(key)
                unique_proxies.append(proxy)
        
        return unique_proxies
    
    def build_api_url(self) -> str:
        """構建API URL（重寫父類方法）"""
        return self._build_api_url(1)  # 返回第一頁URL作為默認
    
    def _parse_json(self, json_data: Dict[str, Any]) -> List[ProxyData]:
        """
        APIExtractor要求實現的方法
        """
        if isinstance(json_data, dict) and "data" in json_data:
            proxies = []
            for item in json_data["data"]:
                proxy_obj = self._convert_to_proxy_data(item)
                if proxy_obj:
                    proxies.append(proxy_obj)
            return proxies
        return []
