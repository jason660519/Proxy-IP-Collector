"""
ProxyScan爬取器
"""
from typing import List, Dict, Any, Optional
from app.etl.extractors.base import WebScrapingExtractor, APIExtractor, ProxyData, ExtractResult
from app.utils.html_parser import ProxyDataExtractor
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProxyScanExtractor(WebScrapingExtractor):
    """ProxyScan網站爬取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化ProxyScan爬取器
        
        Args:
            config: 配置字典
        """
        super().__init__("proxyscan.io", config)
        self.base_url = config.get("base_url", "https://www.proxyscan.io/")
        self.table_selector = config.get("table_selector", "table.table")
        self.country_filter = config.get("country_filter", None)
        self.max_pages = config.get("max_pages", 3)
    
    def get_required_config_fields(self) -> List[str]:
        return ["base_url"]
    
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
            proxies_data = extractor.extract_proxies_from_table(self.table_selector)
            
            # 轉換為ProxyData對象
            proxy_objects = []
            for proxy_data in proxies_data:
                proxy_obj = self._convert_to_proxy_data(proxy_data)
                if proxy_obj:
                    proxy_objects.append(proxy_obj)
            
            logger.info(f"從ProxyScan提取到 {len(proxy_objects)} 個代理")
            return proxy_objects
            
        except Exception as e:
            logger.error(f"解析ProxyScan HTML失敗: {e}")
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
            ip = proxy_dict.get("ip")
            port = proxy_dict.get("port")
            
            if not ip or not port:
                return None
            
            # 解析協議類型
            protocol = self._parse_protocol(proxy_dict.get("protocol", ""))
            
            # 解析匿名級別
            anonymity_level = self._parse_anonymity_level(proxy_dict.get("anonymity", ""))
            
            # 創建ProxyData對象
            return ProxyData(
                ip=ip,
                port=int(port),
                protocol=protocol,
                country=proxy_dict.get("country"),
                city=proxy_dict.get("city"),
                anonymity_level=anonymity_level,
                speed=proxy_dict.get("speed"),
                uptime=proxy_dict.get("uptime"),
                source="proxyscan.io"
            )
            
        except (ValueError, TypeError) as e:
            logger.error(f"轉換代理數據失敗: {e}")
            return None
    
    def _parse_protocol(self, protocol_str: str) -> str:
        """
        解析協議類型
        
        Args:
            protocol_str: 協議字符串
            
        Returns:
            str: 標準化協議類型
        """
        if not protocol_str:
            return "http"
        
        protocol_str = protocol_str.lower()
        
        if "https" in protocol_str or "ssl" in protocol_str:
            return "https"
        elif "socks4" in protocol_str:
            return "socks4"
        elif "socks5" in protocol_str:
            return "socks5"
        else:
            return "http"
    
    def _parse_anonymity_level(self, anonymity_str: str) -> str:
        """
        解析匿名級別
        
        Args:
            anonymity_str: 匿名級別字符串
            
        Returns:
            str: 標準化匿名級別
        """
        if not anonymity_str:
            return "unknown"
        
        anonymity_str = anonymity_str.lower()
        
        if "elite" in anonymity_str or "high" in anonymity_str:
            return "elite"
        elif "anonymous" in anonymity_str:
            return "anonymous"
        elif "transparent" in anonymity_str or "low" in anonymity_str:
            return "transparent"
        else:
            return "unknown"
    
    async def extract(self) -> ExtractResult:
        """
        提取代理數據
        
        Returns:
            ExtractResult: 提取結果
        """
        self.logger.info(f"開始從ProxyScan提取代理數據")
        
        try:
            # 構建URL（支持國家過濾）
            url = self.base_url
            if self.country_filter:
                url += f"?country={self.country_filter}"
            
            # 獲取頁面內容
            html_content = await self.fetch_with_retry(url)
            
            # 解析HTML
            proxies = self._parse_html(html_content)
            
            # 構建結果
            result = ExtractResult(
                source=self.name,
                proxies=[proxy.to_dict() for proxy in proxies],
                metadata={
                    "base_url": self.base_url,
                    "country_filter": self.country_filter,
                    "extraction_method": "html_table_parsing",
                    "total_proxies": len(proxies),
                },
                success=True,
            )
            
            self.logger.info(f"從ProxyScan提取到 {len(proxies)} 個代理")
            return result
            
        except Exception as e:
            self.logger.error(f"ProxyScan提取失敗: {e}")
            return ExtractResult(
                source=self.name,
                proxies=[],
                metadata={
                    "base_url": self.base_url,
                    "country_filter": self.country_filter,
                },
                success=False,
                error_message=str(e),
            )


class ProxyScanAPIExtractor(APIExtractor):
    """ProxyScan API爬取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化ProxyScan API爬取器
        
        Args:
            config: 配置字典，包含API密鑰等
        """
        super().__init__("proxyscan.io-api", config)
        self.api_base_url = config.get("api_base_url", "https://www.proxyscan.io/api/proxy/")
        self.api_key = config.get("api_key", "")
        self.country_filter = config.get("country_filter", None)
        self.protocol_filter = config.get("protocol_filter", None)
        self.limit = config.get("limit", 100)
    
    def get_required_config_fields(self) -> List[str]:
        return ["api_base_url"]
    
    def _build_api_url(self, **params) -> str:
        """
        構建API URL
        
        Args:
            **params: URL參數
            
        Returns:
            str: 完整的API URL
        """
        url = self.api_base_url
        
        # 添加查詢參數
        query_params = {}
        
        if self.country_filter:
            query_params["country"] = self.country_filter
        
        if self.protocol_filter:
            query_params["type"] = self.protocol_filter
        
        if self.limit:
            query_params["limit"] = self.limit
        
        if self.api_key:
            query_params["key"] = self.api_key
        
        # 構建查詢字符串
        if query_params:
            import urllib.parse
            query_string = urllib.parse.urlencode(query_params)
            url += f"?{query_string}"
        
        return url
    
    def _parse_json(self, json_data: Dict[str, Any]) -> List[ProxyData]:
        """
        解析JSON數據
        
        Args:
            json_data: JSON數據
            
        Returns:
            List[ProxyData]: 代理數據列表
        """
        try:
            proxies = []
            
            # 處理不同格式的響應
            if isinstance(json_data, list):
                # 直接代理列表
                for item in json_data:
                    proxy_obj = self._convert_to_proxy_data(item)
                    if proxy_obj:
                        proxies.append(proxy_obj)
            
            elif isinstance(json_data, dict):
                # 包含元數據的響應
                if "data" in json_data and isinstance(json_data["data"], list):
                    for item in json_data["data"]:
                        proxy_obj = self._convert_to_proxy_data(item)
                        if proxy_obj:
                            proxies.append(proxy_obj)
                elif "proxies" in json_data and isinstance(json_data["proxies"], list):
                    for item in json_data["proxies"]:
                        proxy_obj = self._convert_to_proxy_data(item)
                        if proxy_obj:
                            proxies.append(proxy_obj)
            
            logger.info(f"從ProxyScan API提取到 {len(proxies)} 個代理")
            return proxies
            
        except Exception as e:
            logger.error(f"解析ProxyScan API JSON失敗: {e}")
            return []
    
    def _convert_to_proxy_data(self, proxy_dict: Dict[str, Any]) -> Optional[ProxyData]:
        """
        將API響應轉換為ProxyData對象
        
        Args:
            proxy_dict: API響應中的代理數據
            
        Returns:
            Optional[ProxyData]: ProxyData對象或None
        """
        try:
            # 必需字段
            ip = proxy_dict.get("Ip", proxy_dict.get("ip", ""))
            port = proxy_dict.get("Port", proxy_dict.get("port", ""))
            
            if not ip or not port:
                return None
            
            # 解析協議
            protocol = proxy_dict.get("Type", proxy_dict.get("type", "http")).lower()
            
            # 創建ProxyData對象
            return ProxyData(
                ip=ip,
                port=int(port),
                protocol=protocol,
                country=proxy_dict.get("Country", proxy_dict.get("country")),
                city=proxy_dict.get("City", proxy_dict.get("city")),
                anonymity_level=proxy_dict.get("Anonymity", proxy_dict.get("anonymity", "unknown")),
                speed=proxy_dict.get("Speed", proxy_dict.get("speed")),
                uptime=proxy_dict.get("Uptime", proxy_dict.get("uptime")),
                source="proxyscan.io-api"
            )
            
        except (ValueError, TypeError) as e:
            logger.error(f"轉換ProxyScan API數據失敗: {e}")
            return None
    
    async def extract(self) -> ExtractResult:
        """
        從API提取代理數據
        
        Returns:
            ExtractResult: 提取結果
        """
        self.logger.info(f"開始從ProxyScan API提取代理數據")
        
        try:
            # 構建API URL
            api_url = self._build_api_url()
            
            # 調用API
            json_data = await self.fetch_json_with_retry(api_url)
            
            # 解析數據
            proxies = self._parse_json(json_data)
            
            # 構建結果
            result = ExtractResult(
                source=self.name,
                proxies=[proxy.to_dict() for proxy in proxies],
                metadata={
                    "api_url": api_url,
                    "country_filter": self.country_filter,
                    "protocol_filter": self.protocol_filter,
                    "limit": self.limit,
                    "total_proxies": len(proxies),
                },
                success=True,
            )
            
            self.logger.info(f"從ProxyScan API提取到 {len(proxies)} 個代理")
            return result
            
        except Exception as e:
            self.logger.error(f"ProxyScan API提取失敗: {e}")
            return ExtractResult(
                source=self.name,
                proxies=[],
                metadata={
                    "api_base_url": self.api_base_url,
                    "country_filter": self.country_filter,
                    "protocol_filter": self.protocol_filter,
                },
                success=False,
                error_message=str(e),
            )