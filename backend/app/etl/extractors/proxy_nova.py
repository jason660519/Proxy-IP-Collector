"""
ProxyNova代理爬取器
"""
import re
import json
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlencode
from datetime import datetime, timedelta

from app.etl.extractors.base import BaseExtractor, ExtractResult, ProxyData
from app.core.logging import get_logger
from app.core.exceptions import ParserException

logger = get_logger(__name__)


class ProxyNovaExtractor(BaseExtractor):
    """ProxyNova代理爬取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化ProxyNova爬取器
        
        Args:
            config: 爬取器配置
        """
        super().__init__(config)
        self.base_url = config.get("base_url", "https://www.proxynova.com/proxy-server-list")
        self.timeout = config.get("timeout", 30)
        self.max_pages = config.get("max_pages", 5)
    
    async def extract(self) -> ExtractResult:
        """
        提取代理數據
        
        Returns:
            ExtractResult: 提取結果
        """
        try:
            logger.info(f"開始從ProxyNova提取代理數據")
            
            all_proxies = []
            
            # 提取不同國家的代理
            countries = await self._get_available_countries()
            
            if not countries:
                # 如果無法獲取國家列表，使用默認國家
                countries = ["cn", "us", "jp", "de", "gb", "fr", "ca", "au"]
            
            for country in countries[:10]:  # 限制國家數量避免請求過多
                proxies = await self._extract_by_country(country)
                all_proxies.extend(proxies)
                
                # 添加延遲避免請求過快
                if proxies:
                    await asyncio.sleep(1)
            
            logger.info(f"ProxyNova提取完成，獲得 {len(all_proxies)} 個代理")
            
            return ExtractResult(
                success=True,
                proxies=all_proxies,
                error_message=None,
                metadata={
                    "total_found": len(all_proxies),
                    "countries_extracted": len(countries),
                    "countries": countries[:10],
                },
            )
            
        except Exception as e:
            logger.error(f"ProxyNova提取失敗: {e}")
            return ExtractResult(
                success=False,
                proxies=[],
                error_message=str(e),
                metadata={},
            )
    
    async def _get_available_countries(self) -> List[str]:
        """
        獲取可用國家列表
        
        Returns:
            List[str]: 國家代碼列表
        """
        try:
            # 獲取主頁面
            html = await self._make_request(self.base_url)
            
            if not html:
                return []
            
            # 解析國家選項
            countries = self._parse_country_options(html)
            return countries
            
        except Exception as e:
            logger.error(f"獲取國家列表失敗: {e}")
            return []
    
    def _parse_country_options(self, html: str) -> List[str]:
        """
        解析國家選項
        
        Args:
            html: HTML內容
            
        Returns:
            List[str]: 國家代碼列表
        """
        try:
            from app.utils.html_parser import HTMLParser
            
            parser = HTMLParser(html)
            countries = []
            
            # 查找國家選擇器
            country_selects = parser.find_elements("select", attrs={"name": re.compile(r"country", re.I)})
            
            for select in country_selects:
                options = select.find_all("option")
                for option in options:
                    value = option.get("value", "")
                    if value and value != "":
                        countries.append(value.lower())
            
            # 如果沒有找到選擇器，嘗試從鏈接中提取
            if not countries:
                country_links = parser.find_elements("a", href=re.compile(r"/country/"))
                for link in country_links:
                    href = link.get("href", "")
                    match = re.search(r"/country/([a-z]{2})", href)
                    if match:
                        countries.append(match.group(1).lower())
            
            return list(set(countries))  # 去重
            
        except Exception as e:
            logger.error(f"解析國家選項失敗: {e}")
            return []
    
    async def _extract_by_country(self, country: str) -> List[ProxyData]:
        """
        按國家提取代理
        
        Args:
            country: 國家代碼
            
        Returns:
            List[ProxyData]: 代理數據列表
        """
        try:
            proxies = []
            
            for page in range(1, self.max_pages + 1):
                # 構建URL
                url = self._build_country_url(country, page)
                
                # 獲取網頁內容
                html = await self._make_request(url)
                
                if not html:
                    break
                
                # 解析網頁內容
                page_proxies = self._parse_proxy_list(html, country)
                proxies.extend(page_proxies)
                
                # 檢查是否還有更多頁面
                if not self._has_next_page(html):
                    break
                
                # 添加延遲
                await asyncio.sleep(0.5)
            
            return proxies
            
        except Exception as e:
            logger.error(f"提取 {country} 國家代理失敗: {e}")
            return []
    
    def _build_country_url(self, country: str, page: int = 1) -> str:
        """
        構建國家URL
        
        Args:
            country: 國家代碼
            page: 頁碼
            
        Returns:
            str: URL
        """
        params = {
            "country": country,
            "page": page,
        }
        
        query_string = urlencode(params)
        return f"{self.base_url}/country-{country}?{query_string}"
    
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
    
    def _parse_proxy_list(self, html: str, country: str) -> List[ProxyData]:
        """
        解析代理列表
        
        Args:
            html: HTML內容
            country: 國家代碼
            
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
                    proxy_data = self._parse_proxy_row(data, country)
                    if proxy_data:
                        proxies.append(proxy_data)
            
            return proxies
            
        except Exception as e:
            logger.error(f"解析ProxyNova列表失敗: {e}")
            raise ParserException(f"解析代理列表失敗: {e}")
    
    def _parse_proxy_row(self, data: Dict[str, str], country: str) -> Optional[ProxyData]:
        """
        解析代理行數據
        
        Args:
            data: 行數據
            country: 國家代碼
            
        Returns:
            Optional[ProxyData]: 代理數據
        """
        try:
            # 提取IP地址
            host = None
            for key, value in data.items():
                if "ip" in key.lower() or "address" in key.lower():
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
            
            # 提取協議
            protocol = "http"
            for key, value in data.items():
                if "protocol" in key.lower() or "type" in key.lower():
                    if value.lower() in ["http", "https", "socks4", "socks5"]:
                        protocol = value.lower()
                        break
            
            # 提取匿名性
            anonymity = "unknown"
            for key, value in data.items():
                if "anonymity" in key.lower() or "level" in key.lower():
                    anonymity = self._determine_anonymity(value)
                    break
            
            # 提取響應時間
            response_time = 0
            for key, value in data.items():
                if "response" in key.lower() or "speed" in key.lower():
                    try:
                        response_time = float(value.replace("ms", ""))
                        break
                    except ValueError:
                        pass
            
            # 提取最後檢查時間
            last_checked = None
            for key, value in data.items():
                if "last" in key.lower() or "checked" in key.lower():
                    last_checked = self._parse_last_checked(value)
                    break
            
            # 提取其他元數據
            metadata = {
                "country": country,
                "last_checked": last_checked,
                "source_page": "proxynova",
            }
            
            for key, value in data.items():
                if key not in ["ip", "port", "protocol", "anonymity", "response", "last"]:
                    metadata[key] = value
            
            return ProxyData(
                host=host,
                port=port,
                protocol=protocol,
                country=country.lower(),
                anonymity=anonymity,
                response_time=response_time,
                source="proxynova",
                metadata=metadata,
            )
            
        except Exception as e:
            logger.error(f"解析ProxyNova代理行失敗: {e}")
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
    
    def _parse_last_checked(self, time_text: str) -> str:
        """
        解析最後檢查時間
        
        Args:
            time_text: 時間文本
            
        Returns:
            str: ISO格式時間字符串
        """
        try:
            # 處理相對時間格式
            if "ago" in time_text.lower():
                # 提取數字
                match = re.search(r'(\d+)', time_text)
                if match:
                    minutes = int(match.group(1))
                    # 計算時間
                    last_checked = datetime.now() - timedelta(minutes=minutes)
                    return last_checked.isoformat()
            
            # 處理絕對時間格式
            # 這裡可以添加更多時間格式解析
            return None
            
        except Exception:
            return None


class ProxyNovaAPIExtractor(BaseExtractor):
    """ProxyNova API爬取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化ProxyNova API爬取器
        
        Args:
            config: 爬取器配置
        """
        super().__init__(config)
        self.api_url = config.get("api_url", "https://api.proxynova.com/proxy-list")
        self.timeout = config.get("timeout", 30)
        self.limit = config.get("limit", 100)
    
    async def extract(self) -> ExtractResult:
        """
        提取代理數據
        
        Returns:
            ExtractResult: 提取結果
        """
        try:
            logger.info(f"開始從ProxyNova API提取代理數據")
            
            all_proxies = []
            
            # 構建API URL
            api_url = self._build_api_url()
            
            # 發送請求
            response_text = await self._make_request(api_url)
            
            if not response_text:
                return ExtractResult(
                    success=False,
                    proxies=[],
                    error_message="無法獲取API響應",
                    metadata={},
                )
            
            # 解析響應數據
            data = json.loads(response_text)
            proxies = self._parse_api_response(data)
            all_proxies.extend(proxies)
            
            logger.info(f"ProxyNova API提取完成，獲得 {len(all_proxies)} 個代理")
            
            return ExtractResult(
                success=True,
                proxies=all_proxies,
                error_message=None,
                metadata={
                    "total_found": len(all_proxies),
                    "api_mode": True,
                },
            )
            
        except Exception as e:
            logger.error(f"ProxyNova API提取失敗: {e}")
            return ExtractResult(
                success=False,
                proxies=[],
                error_message=str(e),
                metadata={},
            )
    
    def _build_api_url(self) -> str:
        """
        構建API URL
        
        Returns:
            str: API URL
        """
        params = {
            "limit": self.limit,
            "sort_by": "last_checked",
            "sort_type": "desc",
            "anonymity": "elite,anonymous",
        }
        
        query_string = urlencode(params)
        return f"{self.api_url}?{query_string}"
    
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
                proxy_data = self._parse_api_proxy(proxy_info)
                if proxy_data:
                    proxy_data.source = "proxynova_api"
                    proxies.append(proxy_data)
            
            return proxies
            
        except Exception as e:
            logger.error(f"解析ProxyNova API響應失敗: {e}")
            return []
    
    def _parse_api_proxy(self, proxy_info: Dict[str, Any]) -> Optional[ProxyData]:
        """
        解析API代理信息
        
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
            response_time = proxy_info.get("response_time", 0)
            
            # 提取其他元數據
            metadata = {
                "last_checked": proxy_info.get("last_checked"),
                "up_time": proxy_info.get("up_time", 0),
                "ssl": proxy_info.get("ssl", False),
                "google": proxy_info.get("google", False),
                "api_source": "proxynova",
            }
            
            return ProxyData(
                host=ip,
                port=port,
                protocol=protocol,
                country=country.lower(),
                anonymity=anonymity,
                response_time=response_time,
                source="proxynova_api",
                metadata=metadata,
            )
            
        except Exception as e:
            logger.error(f"解析API代理信息失敗: {e}")
            return None
    
    def _determine_anonymity(self, proxy_info: Dict[str, Any]) -> str:
        """
        確定匿名性級別
        
        Args:
            proxy_info: 代理信息
            
        Returns:
            str: 匿名性級別
        """
        anonymity_level = proxy_info.get("anonymity_level", "unknown")
        
        if anonymity_level == "elite":
            return "elite"
        elif anonymity_level == "anonymous":
            return "anonymous"
        elif anonymity_level == "transparent":
            return "transparent"
        else:
            return "unknown"