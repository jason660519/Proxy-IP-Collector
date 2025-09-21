"""
SSL Proxies 爬取器
"""
from typing import List, Dict, Any, Optional
from app.etl.extractors.base import WebScrapingExtractor, ProxyData, ExtractResult
from app.utils.html_parser import ProxyDataExtractor
from app.core.logging import get_logger
import asyncio
import re
from datetime import datetime

logger = get_logger(__name__)


class SSLProxiesExtractor(WebScrapingExtractor):
    """SSL Proxies 網站爬取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化SSL Proxies爬取器
        
        Args:
            config: 配置字典
        """
        super().__init__("ssl-proxies.org", config)
        self.base_url = config.get("base_url", "https://www.sslproxies.org/")
        self.container_selector = config.get("container_selector", "table#proxylisttable tbody tr")
        self.ip_selector = config.get("ip_selector", "td:nth-child(1)")
        self.port_selector = config.get("port_selector", "td:nth-child(2)")
        self.code_selector = config.get("code_selector", "td:nth-child(3)")
        self.country_selector = config.get("country_selector", "td:nth-child(4)")
        self.anonymity_selector = config.get("anonymity_selector", "td:nth-child(5)")
        self.google_selector = config.get("google_selector", "td:nth-child(6)")
        self.https_selector = config.get("https_selector", "td:nth-child(7)")
        self.last_checked_selector = config.get("last_checked_selector", "td:nth-child(8)")
    
    def get_required_config_fields(self) -> List[str]:
        return ["base_url"]
    
    async def extract(self) -> ExtractResult:
        """
        提取代理數據
        
        Returns:
            ExtractResult: 提取結果
        """
        self.logger.info(f"開始從SSL Proxies提取代理數據")
        
        start_time = datetime.utcnow()
        
        try:
            # 爬取主頁面
            html_content = await self.fetch_with_retry(self.base_url)
            
            # 解析代理數據
            proxies = self._parse_html(html_content)
            
            # 去重
            unique_proxies = self._deduplicate_proxies(proxies)
            
            result = ExtractResult(
                source=self.name,
                proxies=[proxy.to_dict() for proxy in unique_proxies],
                metadata={
                    "base_url": self.base_url,
                    "total_found": len(proxies),
                    "unique_found": len(unique_proxies),
                    "start_time": start_time,
                    "end_time": datetime.utcnow(),
                    "extraction_method": "html_table_parsing"
                },
                success=True,
                timestamp=start_time,
            )
            
            self.logger.info(f"SSL Proxies爬取完成，總共找到 {len(proxies)} 個代理，去重後 {len(unique_proxies)} 個")
            return result
            
        except Exception as e:
            self.logger.error(f"SSL Proxies爬取失敗: {e}")
            return ExtractResult(
                source=self.name,
                proxies=[],
                metadata={"start_time": start_time},
                success=False,
                error_message=str(e),
                timestamp=start_time,
            )
    
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
                    "code": self.code_selector,
                    "country": self.country_selector,
                    "anonymity": self.anonymity_selector,
                    "google": self.google_selector,
                    "https": self.https_selector,
                    "last_checked": self.last_checked_selector
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
            self.logger.error(f"解析SSL Proxies HTML失敗: {e}")
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
            
            # 清理IP地址
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
            
            # 解析國家代碼
            country_code = proxy_dict.get("code", "").strip()
            country = proxy_dict.get("country", "").strip()
            
            # 解析匿名度
            anonymity = proxy_dict.get("anonymity", "").strip()
            anonymity_level = self._parse_anonymity(anonymity)
            
            # 解析HTTPS支持
            https_support = proxy_dict.get("https", "").strip().lower()
            protocol = "https" if https_support == "yes" else "http"
            
            # 解析Google支持
            google_support = proxy_dict.get("google", "").strip().lower()
            
            # 創建ProxyData對象
            return ProxyData(
                ip=ip,
                port=port,
                protocol=protocol,
                country=country or country_code,
                anonymity_level=anonymity_level,
                source="ssl-proxies.org",
                metadata={
                    "country_code": country_code,
                    "google_support": google_support == "yes",
                    "https_support": https_support == "yes",
                    "last_checked": proxy_dict.get("last_checked", "").strip()
                }
            )
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"轉換SSL Proxies代理數據失敗: {e}")
            return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """驗證IP地址格式"""
        try:
            import ipaddress
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _parse_anonymity(self, anonymity: str) -> str:
        """解析匿名度"""
        if not anonymity:
            return "unknown"
        
        anonymity_lower = anonymity.lower()
        
        if "elite" in anonymity_lower or "high" in anonymity_lower:
            return "elite"
        elif "anonymous" in anonymity_lower or "medium" in anonymity_lower:
            return "anonymous"
        elif "transparent" in anonymity_lower or "low" in anonymity_lower:
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
        但SSL Proxies主要使用HTML，所以返回空列表
        """
        return []