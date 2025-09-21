"""
FreeProxyList爬取器
"""
from typing import List, Dict, Any, Optional
from app.etl.extractors.base import WebScrapingExtractor, ProxyData, ExtractResult
from app.utils.html_parser import ProxyDataExtractor
from app.core.logging import get_logger

logger = get_logger(__name__)


class FreeProxyListExtractor(WebScrapingExtractor):
    """FreeProxyList網站爬取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化FreeProxyList爬取器
        
        Args:
            config: 配置字典
        """
        super().__init__("free-proxy-list.net", config)
        self.base_url = config.get("base_url", "https://free-proxy-list.net/")
        self.table_selector = config.get("table_selector", "table#proxylisttable")
    
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
            
            logger.info(f"從FreeProxyList提取到 {len(proxy_objects)} 個代理")
            return proxy_objects
            
        except Exception as e:
            logger.error(f"解析FreeProxyList HTML失敗: {e}")
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
            
            # 創建ProxyData對象
            return ProxyData(
                ip=ip,
                port=int(port),
                protocol=proxy_dict.get("protocol", "http"),
                country=proxy_dict.get("country"),
                city=proxy_dict.get("city"),
                anonymity_level=proxy_dict.get("anonymity_level"),
                speed=proxy_dict.get("speed"),
                reliability=proxy_dict.get("reliability"),
                source="free-proxy-list.net"
            )
            
        except (ValueError, TypeError) as e:
            logger.error(f"轉換代理數據失敗: {e}")
            return None
    
    def _parse_json(self, json_data: Dict[str, Any]) -> List[ProxyData]:
        """
        解析JSON數據（FreeProxyList主要使用HTML，此方法備用）
        
        Args:
            json_data: JSON數據
            
        Returns:
            List[ProxyData]: 代理數據列表
        """
        # FreeProxyList主要使用HTML格式，JSON解析作為備用
        proxies = []
        
        if isinstance(json_data, list):
            for item in json_data:
                if isinstance(item, dict):
                    proxy_obj = self._convert_to_proxy_data(item)
                    if proxy_obj:
                        proxies.append(proxy_obj)
        
        return proxies
    
    async def extract(self) -> ExtractResult:
        """
        提取代理數據
        
        Returns:
            ExtractResult: 提取結果
        """
        self.logger.info(f"開始從FreeProxyList提取代理數據")
        
        try:
            # 調用父類的extract方法
            result = await super().extract()
            
            # 添加特定於FreeProxyList的元數據
            result.metadata.update({
                "table_selector": self.table_selector,
                "extraction_method": "html_table_parsing",
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"FreeProxyList提取失敗: {e}")
            return ExtractResult(
                source=self.name,
                proxies=[],
                metadata={"error": str(e)},
                success=False,
                error_message=str(e),
            )


class FreeProxyListAPIExtractor(WebScrapingExtractor):
    """FreeProxyList API爬取器（備用方案）"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化FreeProxyList API爬取器
        
        Args:
            config: 配置字典
        """
        super().__init__("free-proxy-list.net-api", config)
        self.api_url = config.get("api_url", "https://www.proxy-list.download/api/v1/get?type=http")
    
    def get_required_config_fields(self) -> List[str]:
        return ["api_url"]
    
    async def extract(self) -> ExtractResult:
        """
        從API提取代理數據
        
        Returns:
            ExtractResult: 提取結果
        """
        self.logger.info(f"開始從FreeProxyList API提取代理數據")
        
        try:
            # 獲取API數據
            response_data = await self.fetch_with_retry(self.api_url)
            
            # 解析代理數據
            proxies = self._parse_api_response(response_data)
            
            result = ExtractResult(
                source=self.name,
                proxies=[proxy.to_dict() for proxy in proxies],
                metadata={
                    "api_url": self.api_url,
                    "total_found": len(proxies),
                    "extraction_method": "api_json_parsing",
                },
                success=True,
            )
            
            self.logger.info(f"從FreeProxyList API提取到 {len(proxies)} 個代理")
            return result
            
        except Exception as e:
            self.logger.error(f"FreeProxyList API提取失敗: {e}")
            return ExtractResult(
                source=self.name,
                proxies=[],
                metadata={"api_url": self.api_url},
                success=False,
                error_message=str(e),
            )
    
    def _parse_api_response(self, response_text: str) -> List[ProxyData]:
        """
        解析API響應
        
        Args:
            response_text: API響應文本
            
        Returns:
            List[ProxyData]: 代理數據列表
        """
        try:
            import json
            
            # 嘗試解析JSON
            try:
                data = json.loads(response_text)
            except json.JSONDecodeError:
                # 如果不是JSON，嘗試按行解析
                return self._parse_text_format(response_text)
            
            proxies = []
            
            if isinstance(data, list):
                for item in data:
                    proxy_obj = self._convert_api_item_to_proxy(item)
                    if proxy_obj:
                        proxies.append(proxy_obj)
            elif isinstance(data, dict):
                # 處理嵌套結構
                if "data" in data and isinstance(data["data"], list):
                    for item in data["data"]:
                        proxy_obj = self._convert_api_item_to_proxy(item)
                        if proxy_obj:
                            proxies.append(proxy_obj)
            
            return proxies
            
        except Exception as e:
            logger.error(f"解析API響應失敗: {e}")
            return []
    
    def _parse_text_format(self, text: str) -> List[ProxyData]:
        """
        解析文本格式的代理數據
        
        Args:
            text: 文本內容
            
        Returns:
            List[ProxyData]: 代理數據列表
        """
        try:
            proxies = []
            lines = text.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 嘗試不同的分隔符
                parts = line.split(':')
                if len(parts) >= 2:
                    ip = parts[0].strip()
                    port_str = parts[1].strip()
                    
                    # 驗證端口
                    try:
                        port = int(port_str)
                        if 1 <= port <= 65535:
                            proxy_obj = ProxyData(
                                ip=ip,
                                port=port,
                                protocol="http",
                                source="free-proxy-list.net-api"
                            )
                            proxies.append(proxy_obj)
                    except ValueError:
                        continue
            
            return proxies
            
        except Exception as e:
            logger.error(f"解析文本格式失敗: {e}")
            return []
    
    def _convert_api_item_to_proxy(self, item: Dict[str, Any]) -> Optional[ProxyData]:
        """
        將API項目轉換為ProxyData
        
        Args:
            item: API項目數據
            
        Returns:
            Optional[ProxyData]: ProxyData對象或None
        """
        try:
            # 嘗試不同的字段映射
            ip = (item.get("ip") or 
                  item.get("IP") or 
                  item.get("host") or 
                  item.get("proxy_ip"))
            
            port = (item.get("port") or 
                   item.get("PORT") or 
                   item.get("proxy_port"))
            
            if not ip or not port:
                return None
            
            # 獲取其他字段
            protocol = (item.get("protocol") or 
                       item.get("type") or 
                       item.get("proxy_type") or 
                       "http").lower()
            
            country = (item.get("country") or 
                      item.get("country_code") or 
                      item.get("location"))
            
            anonymity_level = (item.get("anonymity") or 
                               item.get("anonymityLevel") or 
                               item.get("anonymity_level"))
            
            speed = item.get("speed") or item.get("response_time")
            if speed:
                try:
                    speed = float(speed)
                except (ValueError, TypeError):
                    speed = None
            
            return ProxyData(
                ip=ip,
                port=int(port),
                protocol=protocol,
                country=country,
                anonymity_level=anonymity_level,
                speed=speed,
                source="free-proxy-list.net-api"
            )
            
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"轉換API項目失敗: {e}")
            return None
    
    def _parse_html(self, html_content: str) -> List[ProxyData]:
        """
        WebScrapingExtractor要求實現的方法
        但此類主要使用API，所以返回空列表
        """
        return []
    
    def _parse_json(self, json_data: Dict[str, Any]) -> List[ProxyData]:
        """
        WebScrapingExtractor要求實現的方法
        """
        return []