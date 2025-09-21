"""
proxynova.com 爬取器
"""
from typing import List, Dict, Any, Optional
from app.etl.extractors.base import WebScrapingExtractor, ProxyData, ExtractResult
from app.utils.html_parser import ProxyDataExtractor
from app.core.logging import get_logger
import asyncio
import re
from datetime import datetime

logger = get_logger(__name__)


class ProxyNovaExtractor(WebScrapingExtractor):
    """proxynova.com 網站爬取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化proxynova.com爬取器
        
        Args:
            config: 配置字典
        """
        super().__init__("proxynova.com", config)
        self.base_url = config.get("base_url", "https://www.proxynova.com/proxy-server-list/")
        self.country_pages = config.get("country_pages", [
            "country-all",
            "country-us",
            "country-gb",
            "country-ca",
            "country-de",
            "country-fr",
            "country-jp",
            "country-cn"
        ])
        self.container_selector = config.get("container_selector", "table#tbl_proxy_list tbody tr")
        self.ip_selector = config.get("ip_selector", "td:nth-child(1)")
        self.port_selector = config.get("port_selector", "td:nth-child(2)")
        self.speed_selector = config.get("speed_selector", "td:nth-child(5)")
        self.anonymity_selector = config.get("anonymity_selector", "td:nth-child(6)")
    
    def get_required_config_fields(self) -> List[str]:
        return ["base_url"]
    
    async def extract(self) -> ExtractResult:
        """
        提取代理數據
        
        Returns:
            ExtractResult: 提取結果
        """
        self.logger.info(f"開始從proxynova.com提取代理數據，國家頁面: {len(self.country_pages)}個")
        
        start_time = datetime.utcnow()
        all_proxies = []
        
        try:
            # 併發爬取多個國家頁面
            semaphore = asyncio.Semaphore(3)  # 限制併發數
            tasks = []
            
            for country_page in self.country_pages:
                task = self._extract_country_page_with_semaphore(semaphore, country_page)
                tasks.append(task)
            
            # 等待所有任務完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 收集結果
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"國家頁面爬取失敗: {result}")
                else:
                    all_proxies.extend(result)
            
            # 去重
            unique_proxies = self._deduplicate_proxies(all_proxies)
            
            result = ExtractResult(
                source=self.name,
                proxies=[proxy.to_dict() for proxy in unique_proxies],
                metadata={
                    "country_pages_crawled": len(self.country_pages),
                    "total_found": len(all_proxies),
                    "unique_found": len(unique_proxies),
                    "countries": self.country_pages,
                    "start_time": start_time,
                    "end_time": datetime.utcnow(),
                    "extraction_method": "html_table_parsing"
                },
                success=True,
                timestamp=start_time,
            )
            
            self.logger.info(f"proxynova.com爬取完成，總共找到 {len(all_proxies)} 個代理，去重後 {len(unique_proxies)} 個")
            return result
            
        except Exception as e:
            self.logger.error(f"proxynova.com爬取失敗: {e}")
            return ExtractResult(
                source=self.name,
                proxies=[],
                metadata={"start_time": start_time},
                success=False,
                error_message=str(e),
                timestamp=start_time,
            )
    
    async def _extract_country_page_with_semaphore(self, semaphore: asyncio.Semaphore, country_page: str) -> List[ProxyData]:
        """使用信號量控制併發的國家頁面提取"""
        async with semaphore:
            try:
                # 構建URL
                if country_page == "country-all":
                    url = self.base_url
                else:
                    url = f"{self.base_url}?{country_page}"
                
                # 爬取頁面
                html_content = await self.fetch_with_retry(url)
                
                # 解析代理數據
                proxies = self._parse_html(html_content, country_page)
                
                # 速率控制
                await asyncio.sleep(1)
                
                return proxies
                
            except Exception as e:
                self.logger.error(f"爬取國家頁面失敗 {country_page}: {e}")
                return []
    
    def _parse_html(self, html_content: str, country_page: str = "") -> List[ProxyData]:
        """
        解析HTML內容提取代理數據
        
        Args:
            html_content: HTML內容
            country_page: 國家頁面標識
            
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
                    "speed": self.speed_selector,
                    "anonymity": self.anonymity_selector
                }
            )
            
            # 轉換為ProxyData對象
            proxy_objects = []
            for proxy_data in proxies_data:
                proxy_obj = self._convert_to_proxy_data(proxy_data, country_page)
                if proxy_obj:
                    proxy_objects.append(proxy_obj)
            
            return proxy_objects
            
        except Exception as e:
            self.logger.error(f"解析proxynova.com HTML失敗: {e}")
            return []
    
    def _convert_to_proxy_data(self, proxy_dict: Dict[str, Any], country_page: str = "") -> Optional[ProxyData]:
        """
        將字典轉換為ProxyData對象
        
        Args:
            proxy_dict: 代理字典
            country_page: 國家頁面標識
            
        Returns:
            Optional[ProxyData]: ProxyData對象或None
        """
        try:
            # 必需字段
            ip = proxy_dict.get("ip", "").strip()
            port = proxy_dict.get("port", "").strip()
            
            if not ip or not port:
                return None
            
            # ProxyNova的IP格式特殊，需要特殊處理
            ip = self._parse_proxynova_ip(ip)
            if not ip:
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
            
            # 解析速度信息
            speed = proxy_dict.get("speed", "").strip()
            speed_value = self._parse_speed(speed)
            
            # 解析匿名度
            anonymity = proxy_dict.get("anonymity", "").strip()
            anonymity_level = self._parse_anonymity(anonymity)
            
            # 從國家頁面推斷國家
            country = self._infer_country_from_page(country_page)
            
            # 創建ProxyData對象
            return ProxyData(
                ip=ip,
                port=port,
                protocol="http",  # ProxyNova主要提供HTTP代理
                country=country,
                anonymity_level=anonymity_level,
                speed=speed_value,
                source="proxynova.com"
            )
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"轉換proxynova.com代理數據失敗: {e}")
            return None
    
    def _parse_proxynova_ip(self, ip_text: str) -> Optional[str]:
        """
        解析ProxyNova的特殊IP格式
        ProxyNova使用JavaScript來隱藏真實IP，格式通常是：
        <script>document.write('192.168.1.1')</script>
        """
        try:
            # 移除HTML標籤
            clean_ip = re.sub(r'<[^>]+>', '', ip_text).strip()
            
            # 查找IP地址模式
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            match = re.search(ip_pattern, clean_ip)
            
            if match:
                return match.group()
            
            return None
            
        except Exception as e:
            self.logger.error(f"解析ProxyNova IP失敗: {e}")
            return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """驗證IP地址格式"""
        try:
            import ipaddress
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _parse_speed(self, speed_text: str) -> Optional[float]:
        """解析速度信息"""
        if not speed_text:
            return None
        
        try:
            # 提取數字部分
            numbers = re.findall(r'\d+\.?\d*', speed_text)
            if numbers:
                return float(numbers[0])
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _parse_anonymity(self, anonymity_text: str) -> str:
        """解析匿名度"""
        if not anonymity_text:
            return "unknown"
        
        anonymity_lower = anonymity_text.lower()
        
        if "elite" in anonymity_lower or "high" in anonymity_lower:
            return "elite"
        elif "anonymous" in anonymity_lower or "medium" in anonymity_lower:
            return "anonymous"
        elif "transparent" in anonymity_lower or "low" in anonymity_lower:
            return "transparent"
        else:
            return "unknown"
    
    def _infer_country_from_page(self, country_page: str) -> str:
        """從國家頁面推斷國家"""
        if not country_page:
            return "unknown"
        
        country_mapping = {
            "country-all": "unknown",
            "country-us": "United States",
            "country-gb": "United Kingdom",
            "country-ca": "Canada",
            "country-de": "Germany",
            "country-fr": "France",
            "country-jp": "Japan",
            "country-cn": "China",
            "country-au": "Australia",
            "country-br": "Brazil",
            "country-in": "India",
            "country-ru": "Russia",
            "country-kr": "South Korea",
            "country-nl": "Netherlands",
            "country-it": "Italy",
            "country-es": "Spain"
        }
        
        return country_mapping.get(country_page, "unknown")
    
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
        但proxynova.com主要使用HTML，所以返回空列表
        """
        return []
