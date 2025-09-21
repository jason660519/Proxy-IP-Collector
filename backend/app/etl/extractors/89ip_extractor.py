"""
89ip.cn 爬取器
"""
from typing import List, Dict, Any, Optional
from app.etl.extractors.base import WebScrapingExtractor, ProxyData, ExtractResult
from app.utils.html_parser import ProxyDataExtractor
from app.core.logging import get_logger
import asyncio
import re
from datetime import datetime

logger = get_logger(__name__)


class EightyNineIpExtractor(WebScrapingExtractor):
    """89ip.cn 網站爬取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化89ip.cn爬取器
        
        Args:
            config: 配置字典
        """
        super().__init__("89ip.cn", config)
        self.base_url = config.get("base_url", "https://www.89ip.cn/index_{page}.html")
        self.page_range = config.get("page_range", [1, 100])
        self.container_selector = config.get("container_selector", "table.layui-table tbody tr")
        self.ip_selector = config.get("ip_selector", "td:nth-child(1)")
        self.port_selector = config.get("port_selector", "td:nth-child(2)")
        self.location_selector = config.get("location_selector", "td:nth-child(3)")
        self.anonymity_selector = config.get("anonymity_selector", "td:nth-child(4)")
    
    def get_required_config_fields(self) -> List[str]:
        return ["base_url"]
    
    async def extract(self) -> ExtractResult:
        """
        提取代理數據
        
        Returns:
            ExtractResult: 提取結果
        """
        self.logger.info(f"開始從89ip.cn提取代理數據，頁面範圍: {self.page_range}")
        
        start_time = datetime.utcnow()
        all_proxies = []
        
        try:
            # 生成要爬取的URL列表
            urls = self._generate_urls()
            self.logger.info(f"將爬取 {len(urls)} 個頁面")
            
            # 併發爬取多個頁面
            semaphore = asyncio.Semaphore(5)  # 限制併發數
            tasks = []
            
            for url in urls:
                task = self._extract_page_with_semaphore(semaphore, url)
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
                    "urls_crawled": len(urls),
                    "total_found": len(all_proxies),
                    "unique_found": len(unique_proxies),
                    "page_range": self.page_range,
                    "start_time": start_time,
                    "end_time": datetime.utcnow(),
                    "extraction_method": "html_table_parsing"
                },
                success=True,
                timestamp=start_time,
            )
            
            self.logger.info(f"89ip.cn爬取完成，總共找到 {len(all_proxies)} 個代理，去重後 {len(unique_proxies)} 個")
            return result
            
        except Exception as e:
            self.logger.error(f"89ip.cn爬取失敗: {e}")
            return ExtractResult(
                source=self.name,
                proxies=[],
                metadata={"start_time": start_time},
                success=False,
                error_message=str(e),
                timestamp=start_time,
            )
    
    def _generate_urls(self) -> List[str]:
        """生成要爬取的URL列表"""
        urls = []
        start_page, end_page = self.page_range
        
        for page in range(start_page, end_page + 1):
            url = self.base_url.format(page=page)
            urls.append(url)
        
        return urls
    
    async def _extract_page_with_semaphore(self, semaphore: asyncio.Semaphore, url: str) -> List[ProxyData]:
        """使用信號量控制併發的頁面提取"""
        async with semaphore:
            try:
                # 爬取頁面
                html_content = await self.fetch_with_retry(url)
                
                # 解析代理數據
                proxies = self._parse_html(html_content)
                
                # 速率控制
                await asyncio.sleep(0.5)
                
                return proxies
                
            except Exception as e:
                self.logger.error(f"爬取頁面失敗 {url}: {e}")
                return []
    
    def _parse_html(self, html_content: str) -> List[ProxyData]:
        """
        解析HTML內容提取代理數據
        
        Args:
            html_content: HTML內容
            
        Returns:
            List[ProxyData]: 代理數據列表
        """
        try:
            extractor = ProxyDataExtractor(html_content)
            
            # 從表格中提取數據
            proxies_data = extractor.extract_proxies_from_table(
                self.container_selector,
                {
                    "ip": self.ip_selector,
                    "port": self.port_selector,
                    "location": self.location_selector,
                    "anonymity": self.anonymity_selector
                }
            )
            
            # 轉換為ProxyData對象
            proxy_objects = []
            for proxy_data in proxies_data:
                proxy_obj = self._convert_to_proxy_data(proxy_data)
                if proxy_obj:
                    proxy_objects.append(proxy_obj)
            
            return proxy_objects
            
        except Exception as e:
            self.logger.error(f"解析89ip.cn HTML失敗: {e}")
            return []
    
    def _convert_to_proxy_data(self, proxy_dict: Dict[str, Any]) -> Optional[ProxyData]:
        """
        將字典轉換為ProxyData對象
        
        Args:
            proxy_dict: 代理字典
            
        Returns:
            Optional[ProxyData]: ProxyData對象或None
        """
        try:
            # 必需字段
            ip = proxy_dict.get("ip", "").strip()
            port = proxy_dict.get("port", "").strip()
            
            if not ip or not port:
                return None
            
            # 清理IP地址（移除可能的HTML標籤）
            ip = re.sub(r'<[^>]+>', '', ip).strip()
            
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
            
            # 解析位置信息
            location = proxy_dict.get("location", "").strip()
            country, city = self._parse_location(location)
            
            # 解析匿名度
            anonymity = proxy_dict.get("anonymity", "").strip()
            anonymity_level = self._parse_anonymity(anonymity)
            
            # 創建ProxyData對象
            return ProxyData(
                ip=ip,
                port=port,
                protocol="http",  # 89ip.cn主要提供HTTP代理
                country=country,
                city=city,
                anonymity_level=anonymity_level,
                source="89ip.cn"
            )
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"轉換89ip.cn代理數據失敗: {e}")
            return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """驗證IP地址格式"""
        try:
            import ipaddress
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _parse_location(self, location: str) -> tuple[str, str]:
        """解析位置信息"""
        if not location:
            return "unknown", "unknown"
        
        # 89ip.cn的位置格式通常是 "國家 城市"
        parts = location.strip().split()
        if len(parts) >= 2:
            country = parts[0]
            city = " ".join(parts[1:])
            return country, city
        elif len(parts) == 1:
            return parts[0], "unknown"
        else:
            return "unknown", "unknown"
    
    def _parse_anonymity(self, anonymity: str) -> str:
        """解析匿名度"""
        if not anonymity:
            return "unknown"
        
        anonymity_lower = anonymity.lower()
        
        if "高匿" in anonymity_lower or "elite" in anonymity_lower:
            return "elite"
        elif "匿名" in anonymity_lower or "anonymous" in anonymity_lower:
            return "anonymous"
        elif "透明" in anonymity_lower or "transparent" in anonymity_lower:
            return "transparent"
        else:
            return "unknown"
    
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
    
    def _parse_json(self, json_data: Dict[str, Any]) -> List[ProxyData]:
        """
        WebScrapingExtractor要求實現的方法
        但89ip.cn主要使用HTML，所以返回空列表
        """
        return []
