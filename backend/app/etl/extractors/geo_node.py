"""
GeoNode爬取器
"""
import json
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

from app.etl.extractors.base import BaseExtractor, ExtractResult, ProxyData
from app.core.logging import get_logger
from app.core.exceptions import ParserException

logger = get_logger(__name__)


class GeoNodeAPIExtractor(BaseExtractor):
    """GeoNode API爬取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化GeoNode API爬取器
        
        Args:
            config: 爬取器配置
        """
        super().__init__(config)
        self.base_url = config.get("base_url", "https://proxylist.geonode.com/api/proxy-list")
        self.limit = config.get("limit", 500)
        self.timeout = config.get("timeout", 30)
    
    async def extract(self) -> ExtractResult:
        """
        提取代理數據
        
        Returns:
            ExtractResult: 提取結果
        """
        try:
            logger.info(f"開始從GeoNode API提取代理數據")
            
            all_proxies = []
            page = 1
            has_more = True
            
            while has_more:
                # 構建API URL
                api_url = self._build_api_url(page)
                
                # 發送請求
                response_text = await self._make_request(api_url)
                
                if not response_text:
                    break
                
                # 解析響應數據
                data = json.loads(response_text)
                proxies = self._parse_api_response(data)
                
                all_proxies.extend(proxies)
                
                # 檢查是否還有更多數據
                total = data.get("total", 0)
                current_count = page * self.limit
                has_more = current_count < total and len(proxies) > 0
                
                if has_more:
                    page += 1
                    # 添加延遲避免請求過快
                    await asyncio.sleep(0.5)
            
            logger.info(f"GeoNode API提取完成，獲得 {len(all_proxies)} 個代理")
            
            return ExtractResult(
                success=True,
                proxies=all_proxies,
                error_message=None,
                metadata={
                    "total_found": len(all_proxies),
                    "pages": page,
                },
            )
            
        except Exception as e:
            logger.error(f"GeoNode API提取失敗: {e}")
            return ExtractResult(
                success=False,
                proxies=[],
                error_message=str(e),
                metadata={},
            )
    
    def _build_api_url(self, page: int = 1) -> str:
        """
        構建API URL
        
        Args:
            page: 頁碼
            
        Returns:
            str: API URL
        """
        params = {
            "limit": self.limit,
            "page": page,
            "sort_by": "lastChecked",
            "sort_type": "desc",
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.base_url}?{query_string}"
    
    def _parse_api_response(self, data: Dict[str, Any]) -> List[ProxyData]:
        """
        解析API響應
        
        Args:
            data: API響應數據
            
        Returns:
            List[ProxyData]: 代理數據列表
        """
        try:
            proxies = []
            proxy_list = data.get("data", [])
            
            for proxy_info in proxy_list:
                proxy_data = self._parse_proxy_info(proxy_info)
                if proxy_data:
                    proxies.append(proxy_data)
            
            return proxies
            
        except Exception as e:
            logger.error(f"解析GeoNode API響應失敗: {e}")
            raise ParserException(f"解析API響應失敗: {e}")
    
    def _parse_proxy_info(self, proxy_info: Dict[str, Any]) -> Optional[ProxyData]:
        """
        解析代理信息
        
        Args:
            proxy_info: 代理信息
            
        Returns:
            Optional[ProxyData]: 代理數據
        """
        try:
            # 提取基本信息
            ip = proxy_info.get("ip")
            port = proxy_info.get("port")
            
            if not ip or not port:
                return None
            
            # 提取協議信息
            protocols = proxy_info.get("protocols", [])
            protocol = protocols[0].lower() if protocols else "http"
            
            # 提取國家信息
            country = proxy_info.get("country", "unknown")
            
            # 提取匿名性
            anonymity = self._determine_anonymity(proxy_info)
            
            # 提取響應時間
            response_time = proxy_info.get("responseTime", 0)
            
            # 提取其他元數據
            metadata = {
                "last_checked": proxy_info.get("lastChecked"),
                "up_time": proxy_info.get("upTime", 0),
                "ssl": proxy_info.get("ssl", False),
                "google": proxy_info.get("google", False),
            }
            
            return ProxyData(
                host=ip,
                port=port,
                protocol=protocol,
                country=country.lower(),
                anonymity=anonymity,
                response_time=response_time,
                source="geonode",
                metadata=metadata,
            )
            
        except Exception as e:
            logger.error(f"解析代理信息失敗: {e}")
            return None
    
    def _determine_anonymity(self, proxy_info: Dict[str, Any]) -> str:
        """
        確定匿名性級別
        
        Args:
            proxy_info: 代理信息
            
        Returns:
            str: 匿名性級別
        """
        anonymity_level = proxy_info.get("anonymityLevel", "unknown")
        
        if anonymity_level == "elite":
            return "elite"
        elif anonymity_level == "anonymous":
            return "anonymous"
        elif anonymity_level == "transparent":
            return "transparent"
        else:
            return "unknown"


class GeoNodeWebExtractor(BaseExtractor):
    """GeoNode網頁爬取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化GeoNode網頁爬取器
        
        Args:
            config: 爬取器配置
        """
        super().__init__(config)
        self.base_url = config.get("base_url", "https://proxylist.geonode.com/")
        self.timeout = config.get("timeout", 30)
    
    async def extract(self) -> ExtractResult:
        """
        提取代理數據
        
        Returns:
            ExtractResult: 提取結果
        """
        try:
            logger.info(f"開始從GeoNode網頁提取代理數據")
            
            # 獲取網頁內容
            html = await self._make_request(self.base_url)
            
            if not html:
                return ExtractResult(
                    success=False,
                    proxies=[],
                    error_message="無法獲取網頁內容",
                    metadata={"url": self.base_url},
                )
            
            # 解析網頁內容
            proxies = self._parse_web_page(html)
            
            logger.info(f"GeoNode網頁提取完成，獲得 {len(proxies)} 個代理")
            
            return ExtractResult(
                success=True,
                proxies=proxies,
                error_message=None,
                metadata={
                    "url": self.base_url,
                    "total_found": len(proxies),
                },
            )
            
        except Exception as e:
            logger.error(f"GeoNode網頁提取失敗: {e}")
            return ExtractResult(
                success=False,
                proxies=[],
                error_message=str(e),
                metadata={},
            )
    
    def _parse_web_page(self, html: str) -> List[ProxyData]:
        """
        解析網頁內容
        
        Args:
            html: HTML內容
            
        Returns:
            List[ProxyData]: 代理數據列表
        """
        try:
            from app.utils.html_parser import HTMLParser
            
            parser = HTMLParser(html)
            proxies = []
            
            # 查找代理表格
            tables = parser.extract_tables()
            
            for table in tables:
                # 查找表頭
                headers = []
                header_row = table.find("thead").find("tr") if table.find("thead") else table.find("tr")
                if header_row:
                    headers = [th.get_text(strip=True).lower() for th in header_row.find_all(["th", "td"])]
                
                # 查找數據行
                rows = table.find_all("tr")[1:] if headers else table.find_all("tr")
                
                for row in rows:
                    cells = row.find_all(["td", "th"])
                    if len(cells) < 2:
                        continue
                    
                    # 提取數據
                    data = {}
                    for i, cell in enumerate(cells):
                        if i < len(headers):
                            data[headers[i]] = cell.get_text(strip=True)
                        else:
                            data[f"column_{i}"] = cell.get_text(strip=True)
                    
                    # 解析代理數據
                    proxy_data = self._parse_proxy_row(data)
                    if proxy_data:
                        proxies.append(proxy_data)
            
            return proxies
            
        except Exception as e:
            logger.error(f"解析GeoNode網頁失敗: {e}")
            raise ParserException(f"解析網頁失敗: {e}")
    
    def _parse_proxy_row(self, data: Dict[str, str]) -> Optional[ProxyData]:
        """
        解析代理行數據
        
        Args:
            data: 行數據
            
        Returns:
            Optional[ProxyData]: 代理數據
        """
        try:
            # 查找IP和端口
            host = None
            port = None
            
            for key, value in data.items():
                if "ip" in key.lower() or "host" in key.lower():
                    if self._is_valid_ip(value):
                        host = value
                elif "port" in key.lower():
                    if value.isdigit():
                        port = int(value)
            
            # 如果沒有找到，嘗試從文本中提取
            if not host or not port:
                text = " ".join(data.values())
                ip_port = self._extract_ip_port(text)
                if ip_port:
                    host, port = ip_port
            
            if not host or not port:
                return None
            
            # 提取其他信息
            country = data.get("country", "unknown")
            anonymity = data.get("anonymity", "unknown")
            protocol = data.get("protocol", "http").lower()
            
            return ProxyData(
                host=host,
                port=port,
                protocol=protocol,
                country=country.lower(),
                anonymity=anonymity.lower(),
                source="geonode_web",
                metadata=data,
            )
            
        except Exception as e:
            logger.error(f"解析代理行失敗: {e}")
            return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """
        檢查是否為有效IP地址
        
        Args:
            ip: IP地址
            
        Returns:
            bool: 是否有效
        """
        import re
        pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        return bool(re.match(pattern, ip))
    
    def _extract_ip_port(self, text: str) -> Optional[tuple]:
        """
        從文本中提取IP和端口
        
        Args:
            text: 文本
            
        Returns:
            Optional[tuple]: IP和端口元組
        """
        import re
        pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})'
        match = re.search(pattern, text)
        if match:
            return match.group(1), int(match.group(2))
        return None