"""
ProxyDB爬取器
"""
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlencode

from app.etl.extractors.base import BaseExtractor, ExtractResult, ProxyData
from app.core.logging import get_logger
from app.core.exceptions import ParserException

logger = get_logger(__name__)


class ProxyDBExtractor(BaseExtractor):
    """ProxyDB爬取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化ProxyDB爬取器
        
        Args:
            config: 爬取器配置
        """
        super().__init__(config)
        self.base_url = config.get("base_url", "https://proxydb.net/")
        self.timeout = config.get("timeout", 30)
        self.max_pages = config.get("max_pages", 5)
    
    async def extract(self) -> ExtractResult:
        """
        提取代理數據
        
        Returns:
            ExtractResult: 提取結果
        """
        try:
            logger.info(f"開始從ProxyDB提取代理數據")
            
            all_proxies = []
            
            # 提取不同類型的代理
            proxy_types = ["http", "https", "socks4", "socks5"]
            
            for proxy_type in proxy_types:
                proxies = await self._extract_by_type(proxy_type)
                all_proxies.extend(proxies)
                
                # 添加延遲避免請求過快
                if proxies:
                    await asyncio.sleep(1)
            
            logger.info(f"ProxyDB提取完成，獲得 {len(all_proxies)} 個代理")
            
            return ExtractResult(
                success=True,
                proxies=all_proxies,
                error_message=None,
                metadata={
                    "total_found": len(all_proxies),
                    "types_extracted": proxy_types,
                },
            )
            
        except Exception as e:
            logger.error(f"ProxyDB提取失敗: {e}")
            return ExtractResult(
                success=False,
                proxies=[],
                error_message=str(e),
                metadata={},
            )
    
    async def _extract_by_type(self, proxy_type: str) -> List[ProxyData]:
        """
        按類型提取代理
        
        Args:
            proxy_type: 代理類型
            
        Returns:
            List[ProxyData]: 代理數據列表
        """
        try:
            proxies = []
            
            for page in range(1, self.max_pages + 1):
                # 構建URL
                url = self._build_url(proxy_type, page)
                
                # 獲取網頁內容
                html = await self._make_request(url)
                
                if not html:
                    break
                
                # 解析網頁內容
                page_proxies = self._parse_proxy_list(html, proxy_type)
                proxies.extend(page_proxies)
                
                # 檢查是否還有更多頁面
                if not self._has_next_page(html):
                    break
                
                # 添加延遲
                await asyncio.sleep(0.5)
            
            return proxies
            
        except Exception as e:
            logger.error(f"提取 {proxy_type} 類型代理失敗: {e}")
            return []
    
    def _build_url(self, proxy_type: str, page: int = 1) -> str:
        """
        構建URL
        
        Args:
            proxy_type: 代理類型
            page: 頁碼
            
        Returns:
            str: URL
        """
        params = {
            "protocol": proxy_type,
            "page": page,
        }
        
        query_string = urlencode(params)
        return f"{self.base_url}?{query_string}"
    
    def _has_next_page(self, html: str) -> bool:
        """
        檢查是否有下一頁
        
        Args:
            html: HTML內容
            
        Returns:
            bool: 是否有下一頁
        """
        try:
            from app.utils.html_parser import HTMLParser
            
            parser = HTMLParser(html)
            
            # 查找分頁鏈接
            next_links = parser.find_elements("a", text=re.compile(r"next|下一頁|»", re.I))
            return len(next_links) > 0
            
        except Exception:
            return False
    
    def _parse_proxy_list(self, html: str, proxy_type: str) -> List[ProxyData]:
        """
        解析代理列表
        
        Args:
            html: HTML內容
            proxy_type: 代理類型
            
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
                    proxy_data = self._parse_proxy_row(data, proxy_type)
                    if proxy_data:
                        proxies.append(proxy_data)
            
            return proxies
            
        except Exception as e:
            logger.error(f"解析ProxyDB列表失敗: {e}")
            raise ParserException(f"解析代理列表失敗: {e}")
    
    def _parse_proxy_row(self, data: Dict[str, str], proxy_type: str) -> Optional[ProxyData]:
        """
        解析代理行數據
        
        Args:
            data: 行數據
            proxy_type: 代理類型
            
        Returns:
            Optional[ProxyData]: 代理數據
        """
        try:
            # 提取IP地址
            host = None
            for key, value in data.items():
                if "ip" in key.lower() or "host" in key.lower():
                    if self._is_valid_ip(value):
                        host = value
                        break
            
            if not host:
                return None
            
            # 提取端口
            port = None
            for key, value in data.items():
                if "port" in key.lower():
                    if value.isdigit():
                        port = int(value)
                        break
            
            if not port:
                return None
            
            # 提取國家
            country = "unknown"
            for key, value in data.items():
                if "country" in key.lower() or "國家" in key.lower():
                    country = value.lower()
                    break
            
            # 提取匿名性
            anonymity = "unknown"
            for key, value in data.items():
                if "anonymity" in key.lower() or "匿名" in key.lower():
                    anonymity = self._determine_anonymity(value)
                    break
            
            # 提取響應時間
            response_time = 0
            for key, value in data.items():
                if "response" in key.lower() or "響應" in key.lower():
                    try:
                        response_time = float(value.replace("ms", ""))
                        break
                    except ValueError:
                        pass
            
            # 提取其他元數據
            metadata = {
                "proxy_type": proxy_type,
                "source_page": "proxydb",
            }
            
            for key, value in data.items():
                if key not in ["ip", "port", "country", "anonymity", "response"]:
                    metadata[key] = value
            
            return ProxyData(
                host=host,
                port=port,
                protocol=proxy_type,
                country=country,
                anonymity=anonymity,
                response_time=response_time,
                source="proxydb",
                metadata=metadata,
            )
            
        except Exception as e:
            logger.error(f"解析ProxyDB代理行失敗: {e}")
            return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """
        檢查是否為有效IP地址
        
        Args:
            ip: IP地址
            
        Returns:
            bool: 是否有效
        """
        pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        return bool(re.match(pattern, ip))
    
    def _determine_anonymity(self, anonymity_text: str) -> str:
        """
        確定匿名性級別
        
        Args:
            anonymity_text: 匿名性文本
            
        Returns:
            str: 匿名性級別
        """
        text = anonymity_text.lower()
        
        if "elite" in text or "高匿" in text:
            return "elite"
        elif "anonymous" in text or "匿名" in text:
            return "anonymous"
        elif "transparent" in text or "透明" in text:
            return "transparent"
        else:
            return "unknown"


class ProxyDBPremiumExtractor(BaseExtractor):
    """ProxyDB Premium爬取器（模擬高級功能）"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化ProxyDB Premium爬取器
        
        Args:
            config: 爬取器配置
        """
        super().__init__(config)
        self.base_url = config.get("base_url", "https://proxydb.net/premium")
        self.timeout = config.get("timeout", 30)
        self.api_key = config.get("api_key", "")
    
    async def extract(self) -> ExtractResult:
        """
        提取代理數據
        
        Returns:
            ExtractResult: 提取結果
        """
        try:
            logger.info(f"開始從ProxyDB Premium提取代理數據")
            
            if not self.api_key:
                logger.warning("未提供API密鑰，使用普通模式")
                # 使用普通模式
                extractor = ProxyDBExtractor({
                    "base_url": "https://proxydb.net/",
                    "timeout": self.timeout,
                })
                return await extractor.extract()
            
            # 使用高級API
            api_url = f"{self.base_url}?api_key={self.api_key}"
            
            # 獲取數據
            response_text = await self._make_request(api_url)
            
            if not response_text:
                return ExtractResult(
                    success=False,
                    proxies=[],
                    error_message="無法獲取高級數據",
                    metadata={"url": api_url},
                )
            
            # 解析JSON響應
            data = json.loads(response_text)
            proxies = self._parse_premium_response(data)
            
            logger.info(f"ProxyDB Premium提取完成，獲得 {len(proxies)} 個代理")
            
            return ExtractResult(
                success=True,
                proxies=proxies,
                error_message=None,
                metadata={
                    "total_found": len(proxies),
                    "premium_mode": True,
                },
            )
            
        except Exception as e:
            logger.error(f"ProxyDB Premium提取失敗: {e}")
            return ExtractResult(
                success=False,
                proxies=[],
                error_message=str(e),
                metadata={},
            )
    
    def _parse_premium_response(self, data: Dict[str, Any]) -> List[ProxyData]:
        """
        解析高級響應
        
        Args:
            data: 響應數據
            
        Returns:
            List[ProxyData]: 代理數據列表
        """
        try:
            proxies = []
            proxy_list = data.get("proxies", [])
            
            for proxy_info in proxy_list:
                proxy_data = self._parse_premium_proxy(proxy_info)
                if proxy_data:
                    proxies.append(proxy_data)
            
            return proxies
            
        except Exception as e:
            logger.error(f"解析高級響應失敗: {e}")
            return []
    
    def _parse_premium_proxy(self, proxy_info: Dict[str, Any]) -> Optional[ProxyData]:
        """
        解析高級代理信息
        
        Args:
            proxy_info: 代理信息
            
        Returns:
            Optional[ProxyData]: 代理數據
        """
        try:
            # 提取基本信息
            host = proxy_info.get("host")
            port = proxy_info.get("port")
            
            if not host or not port:
                return None
            
            # 提取協議
            protocol = proxy_info.get("protocol", "http")
            
            # 提取地理位置
            country = proxy_info.get("country", "unknown")
            city = proxy_info.get("city", "")
            
            # 提取匿名性
            anonymity = proxy_info.get("anonymity", "unknown")
            
            # 提取性能數據
            response_time = proxy_info.get("response_time", 0)
            reliability = proxy_info.get("reliability", 0)
            
            # 構建元數據
            metadata = {
                "premium": True,
                "city": city,
                "reliability": reliability,
                "last_verified": proxy_info.get("last_verified"),
                "uptime": proxy_info.get("uptime", 0),
            }
            
            return ProxyData(
                host=host,
                port=port,
                protocol=protocol,
                country=country.lower(),
                anonymity=anonymity,
                response_time=response_time,
                reliability=reliability,
                source="proxydb_premium",
                metadata=metadata,
            )
            
        except Exception as e:
            logger.error(f"解析高級代理信息失敗: {e}")
            return None