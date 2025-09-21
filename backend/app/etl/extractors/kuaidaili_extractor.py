"""
kuaidaili.com 爬取器
"""
from typing import List, Dict, Any, Optional
from app.etl.extractors.base import WebScrapingExtractor, ProxyData, ExtractResult
from app.utils.html_parser import ProxyDataExtractor
from app.core.logging import get_logger
import asyncio
import re
from datetime import datetime

logger = get_logger(__name__)


class KuaidailiExtractor(WebScrapingExtractor):
    """kuaidaili.com 網站爬取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化kuaidaili.com爬取器
        
        Args:
            config: 配置字典
        """
        super().__init__("kuaidaili.com", config)
        self.base_url = config.get("base_url", "")
        self.proxy_type = config.get("proxy_type", "intr")  # intr 或 inha
        self.container_selector = config.get("container_selector", "table.table-bordered tbody tr")
        self.ip_selector = config.get("ip_selector", "td[data-title='IP']")
        self.port_selector = config.get("port_selector", "td[data-title='PORT']")
        self.anonymity_selector = config.get("anonymity_selector", "td[data-title='匿名度']")
        self.type_selector = config.get("type_selector", "td[data-title='类型']")
        self.location_selector = config.get("location_selector", "td[data-title='位置']")
        self.response_time_selector = config.get("response_time_selector", "td[data-title='响应速度']")
        
        # 根據代理類型設置URL
        if self.proxy_type == "intr":
            self.base_url = "https://www.kuaidaili.com/free/intr/"
        elif self.proxy_type == "inha":
            self.base_url = "https://www.kuaidaili.com/free/inha/"
        else:
            self.base_url = config.get("base_url", "https://www.kuaidaili.com/free/intr/")
    
    def get_required_config_fields(self) -> List[str]:
        return ["base_url"]
    
    async def extract(self) -> ExtractResult:
        """
        提取代理數據
        
        Returns:
            ExtractResult: 提取結果
        """
        self.logger.info(f"開始從kuaidaili.com提取代理數據，類型: {self.proxy_type}")
        
        start_time = datetime.utcnow()
        
        try:
            # 爬取主頁面
            html_content = await self.fetch_with_retry(self.base_url)
            
            # 解析代理數據
            proxies = self._parse_html(html_content)
            
            # 嘗試爬取分頁（如果存在）
            additional_proxies = await self._extract_pagination()
            proxies.extend(additional_proxies)
            
            # 去重
            unique_proxies = self._deduplicate_proxies(proxies)
            
            result = ExtractResult(
                source=self.name,
                proxies=[proxy.to_dict() for proxy in unique_proxies],
                metadata={
                    "base_url": self.base_url,
                    "proxy_type": self.proxy_type,
                    "total_found": len(proxies),
                    "unique_found": len(unique_proxies),
                    "start_time": start_time,
                    "end_time": datetime.utcnow(),
                    "extraction_method": "html_table_parsing"
                },
                success=True,
                timestamp=start_time,
            )
            
            self.logger.info(f"kuaidaili.com爬取完成，總共找到 {len(proxies)} 個代理，去重後 {len(unique_proxies)} 個")
            return result
            
        except Exception as e:
            self.logger.error(f"kuaidaili.com爬取失敗: {e}")
            return ExtractResult(
                source=self.name,
                proxies=[],
                metadata={"start_time": start_time},
                success=False,
                error_message=str(e),
                timestamp=start_time,
            )
    
    async def _extract_pagination(self) -> List[ProxyData]:
        """提取分頁數據"""
        additional_proxies = []
        
        try:
            # 嘗試爬取前幾頁（通常只有1-2頁有數據）
            for page in range(2, 6):  # 嘗試第2-5頁
                try:
                    page_url = f"{self.base_url}?page={page}"
                    html_content = await self.fetch_with_retry(page_url)
                    
                    page_proxies = self._parse_html(html_content)
                    if page_proxies:
                        additional_proxies.extend(page_proxies)
                        self.logger.info(f"從第{page}頁提取到 {len(page_proxies)} 個代理")
                    else:
                        # 如果沒有數據，停止嘗試後續頁面
                        break
                    
                    # 速率控制
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    self.logger.warning(f"爬取第{page}頁失敗: {e}")
                    break
            
        except Exception as e:
            self.logger.error(f"分頁爬取失敗: {e}")
        
        return additional_proxies
    
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
                    "anonymity": self.anonymity_selector,
                    "type": self.type_selector,
                    "location": self.location_selector,
                    "response_time": self.response_time_selector
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
            self.logger.error(f"解析kuaidaili.com HTML失敗: {e}")
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
            
            # 解析協議類型
            proxy_type = proxy_dict.get("type", "").strip().lower()
            protocol = self._parse_protocol(proxy_type)
            
            # 解析位置信息
            location = proxy_dict.get("location", "").strip()
            country, city = self._parse_location(location)
            
            # 解析匿名度
            anonymity = proxy_dict.get("anonymity", "").strip()
            anonymity_level = self._parse_anonymity(anonymity)
            
            # 解析響應時間
            response_time = proxy_dict.get("response_time", "").strip()
            speed = self._parse_response_time(response_time)
            
            # 創建ProxyData對象
            return ProxyData(
                ip=ip,
                port=port,
                protocol=protocol,
                country=country,
                city=city,
                anonymity_level=anonymity_level,
                speed=speed,
                source=f"kuaidaili.com-{self.proxy_type}"
            )
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"轉換kuaidaili.com代理數據失敗: {e}")
            return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """驗證IP地址格式"""
        try:
            import ipaddress
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _parse_protocol(self, proxy_type: str) -> str:
        """解析協議類型"""
        if not proxy_type:
            return "http"
        
        proxy_type_lower = proxy_type.lower()
        
        if "https" in proxy_type_lower:
            return "https"
        elif "socks4" in proxy_type_lower:
            return "socks4"
        elif "socks5" in proxy_type_lower:
            return "socks5"
        else:
            return "http"  # 默認HTTP
    
    def _parse_location(self, location: str) -> tuple[str, str]:
        """解析位置信息"""
        if not location:
            return "unknown", "unknown"
        
        # kuaidaili.com的位置格式通常是 "國家 城市"
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
    
    def _parse_response_time(self, response_time: str) -> Optional[float]:
        """解析響應時間"""
        if not response_time:
            return None
        
        try:
            # 提取數字部分
            numbers = re.findall(r'\d+\.?\d*', response_time)
            if numbers:
                return float(numbers[0])
        except (ValueError, TypeError):
            pass
        
        return None
    
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
        但kuaidaili.com主要使用HTML，所以返回空列表
        """
        return []


class KuaidailiIntrExtractor(KuaidailiExtractor):
    """kuaidaili.com 國內代理爬取器"""
    
    def __init__(self, config: Dict[str, Any]):
        config["proxy_type"] = "intr"
        super().__init__(config)


class KuaidailiInhaExtractor(KuaidailiExtractor):
    """kuaidaili.com 海外代理爬取器"""
    
    def __init__(self, config: Dict[str, Any]):
        config["proxy_type"] = "inha"
        super().__init__(config)
