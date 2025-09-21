"""
ProxyListPlus爬取器
"""
from typing import List, Dict, Any, Optional
from app.etl.extractors.base import WebScrapingExtractor, ProxyData, ExtractResult
from app.utils.html_parser import ProxyDataExtractor
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProxyListPlusExtractor(WebScrapingExtractor):
    """ProxyListPlus網站爬取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化ProxyListPlus爬取器
        
        Args:
            config: 配置字典
        """
        super().__init__("proxy-list.plus", config)
        self.base_url = config.get("base_url", "https://proxy-list.plus/")
        self.table_selector = config.get("table_selector", "table.table")
        self.pagination = config.get("pagination", True)
        self.max_pages = config.get("max_pages", 5)
    
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
            
            logger.info(f"從ProxyListPlus提取到 {len(proxy_objects)} 個代理")
            return proxy_objects
            
        except Exception as e:
            logger.error(f"解析ProxyListPlus HTML失敗: {e}")
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
            
            # 解析速度
            speed = self._parse_speed(proxy_dict.get("speed", ""))
            
            # 創建ProxyData對象
            return ProxyData(
                ip=ip,
                port=int(port),
                protocol=protocol,
                country=proxy_dict.get("country"),
                city=proxy_dict.get("city"),
                anonymity_level=anonymity_level,
                speed=speed,
                reliability=proxy_dict.get("reliity"),
                source="proxy-list.plus"
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
    
    def _parse_speed(self, speed_str: str) -> Optional[float]:
        """
        解析速度
        
        Args:
            speed_str: 速度字符串
            
        Returns:
            Optional[float]: 速度值或None
        """
        if not speed_str:
            return None
        
        try:
            # 移除單位並提取數字
            import re
            match = re.search(r'(\d+(?:\.\d+)?)', speed_str)
            if match:
                speed_value = float(match.group(1))
                
                # 根據單位調整
                if "ms" in speed_str.lower():
                    return speed_value
                elif "s" in speed_str.lower():
                    return speed_value * 1000  # 轉換為毫秒
                else:
                    return speed_value
                    
        except (ValueError, TypeError):
            pass
        
        return None
    
    async def extract_with_pagination(self) -> ExtractResult:
        """
        帶分頁的提取方法
        
        Returns:
            ExtractResult: 提取結果
        """
        self.logger.info(f"開始從ProxyListPlus帶分頁提取代理數據")
        
        all_proxies = []
        total_pages = 0
        
        try:
            # 提取第一頁
            first_page_result = await self.extract()
            
            if first_page_result.success and first_page_result.proxies:
                all_proxies.extend(first_page_result.proxies)
                total_pages = 1
                
                # 如果需要分頁，提取後續頁面
                if self.pagination and self.max_pages > 1:
                    for page_num in range(2, self.max_pages + 1):
                        try:
                            # 構建分頁URL
                            page_url = f"{self.base_url}?page={page_num}"
                            
                            # 獲取頁面內容
                            page_content = await self.fetch_with_retry(page_url)
                            
                            # 解析頁面內容
                            page_proxies = self._parse_html(page_content)
                            
                            if page_proxies:
                                all_proxies.extend([proxy.to_dict() for proxy in page_proxies])
                                total_pages += 1
                                self.logger.info(f"提取第 {page_num} 頁成功，獲得 {len(page_proxies)} 個代理")
                            else:
                                self.logger.info(f"第 {page_num} 頁無數據，停止分頁提取")
                                break
                                
                        except Exception as e:
                            self.logger.error(f"提取第 {page_num} 頁失敗: {e}")
                            continue
            
            # 構建最終結果
            result = ExtractResult(
                source=self.name,
                proxies=all_proxies,
                metadata={
                    "base_url": self.base_url,
                    "total_pages": total_pages,
                    "extraction_method": "html_table_parsing_with_pagination",
                    "pagination_enabled": self.pagination,
                    "max_pages": self.max_pages,
                },
                success=True,
            )
            
            self.logger.info(f"從ProxyListPlus總共提取到 {len(all_proxies)} 個代理，來自 {total_pages} 個頁面")
            return result
            
        except Exception as e:
            self.logger.error(f"ProxyListPlus分頁提取失敗: {e}")
            return ExtractResult(
                source=self.name,
                proxies=all_proxies,
                metadata={
                    "base_url": self.base_url,
                    "total_pages": total_pages,
                    "pagination_enabled": self.pagination,
                },
                success=False,
                error_message=str(e),
            )
    
    async def extract(self) -> ExtractResult:
        """
        提取代理數據
        
        Returns:
            ExtractResult: 提取結果
        """
        self.logger.info(f"開始從ProxyListPlus提取代理數據")
        
        try:
            # 調用父類的extract方法
            result = await super().extract()
            
            # 添加特定於ProxyListPlus的元數據
            result.metadata.update({
                "table_selector": self.table_selector,
                "pagination_enabled": self.pagination,
                "max_pages": self.max_pages,
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"ProxyListPlus提取失敗: {e}")
            return ExtractResult(
                source=self.name,
                proxies=[],
                metadata={
                    "table_selector": self.table_selector,
                    "pagination_enabled": self.pagination,
                },
                success=False,
                error_message=str(e),
            )
    
    def _parse_json(self, json_data: Dict[str, Any]) -> List[ProxyData]:
        """
        解析JSON數據（ProxyListPlus主要使用HTML，此方法備用）
        
        Args:
            json_data: JSON數據
            
        Returns:
            List[ProxyData]: 代理數據列表
        """
        # ProxyListPlus主要使用HTML格式，JSON解析作為備用
        proxies = []
        
        if isinstance(json_data, list):
            for item in json_data:
                if isinstance(item, dict):
                    proxy_obj = self._convert_to_proxy_data(item)
                    if proxy_obj:
                        proxies.append(proxy_obj)
        
        return proxies