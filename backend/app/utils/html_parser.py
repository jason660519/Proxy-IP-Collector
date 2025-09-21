"""
HTML解析工具類
"""
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re
from app.core.logging import get_logger

logger = get_logger(__name__)


class HTMLParser:
    """HTML解析器"""
    
    def __init__(self, html_content: str):
        """
        初始化HTML解析器
        
        Args:
            html_content: HTML內容
        """
        self.soup = BeautifulSoup(html_content, 'html.parser')
    
    def find_table_data(self, table_selector: str = "table", row_selector: str = "tr", cell_selector: str = "td") -> List[List[str]]:
        """
        從表格中提取數據
        
        Args:
            table_selector: 表格選擇器
            row_selector: 行選擇器
            cell_selector: 單元格選擇器
            
        Returns:
            List[List[str]]: 表格數據
        """
        try:
            table = self.soup.select_one(table_selector)
            if not table:
                logger.warning(f"未找到表格: {table_selector}")
                return []
            
            rows = table.select(row_selector)
            data = []
            
            for row in rows:
                cells = row.select(cell_selector)
                if cells:
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    data.append(row_data)
            
            return data
            
        except Exception as e:
            logger.error(f"解析表格數據失敗: {e}")
            return []
    
    def find_list_data(self, list_selector: str = "ul", item_selector: str = "li") -> List[str]:
        """
        從列表中提取數據
        
        Args:
            list_selector: 列表選擇器
            item_selector: 項目選擇器
            
        Returns:
            List[str]: 列表數據
        """
        try:
            list_element = self.soup.select_one(list_selector)
            if not list_element:
                logger.warning(f"未找到列表: {list_selector}")
                return []
            
            items = list_element.select(item_selector)
            return [item.get_text(strip=True) for item in items]
            
        except Exception as e:
            logger.error(f"解析列表數據失敗: {e}")
            return []
    
    def find_elements_by_selector(self, selector: str) -> List[BeautifulSoup]:
        """
        根據選擇器查找元素
        
        Args:
            selector: CSS選擇器
            
        Returns:
            List[BeautifulSoup]: 元素列表
        """
        try:
            return self.soup.select(selector)
        except Exception as e:
            logger.error(f"查找元素失敗: {selector}, 錯誤: {e}")
            return []
    
    def find_element_by_selector(self, selector: str) -> Optional[BeautifulSoup]:
        """
        根據選擇器查找單個元素
        
        Args:
            selector: CSS選擇器
            
        Returns:
            Optional[BeautifulSoup]: 元素或None
        """
        try:
            return self.soup.select_one(selector)
        except Exception as e:
            logger.error(f"查找元素失敗: {selector}, 錯誤: {e}")
            return None
    
    def extract_text_by_regex(self, pattern: str, flags: int = 0) -> List[str]:
        """
        使用正則表達式提取文本
        
        Args:
            pattern: 正則表達式模式
            flags: 正則表達式標誌
            
        Returns:
            List[str]: 匹配的文本列表
        """
        try:
            text = self.soup.get_text()
            matches = re.findall(pattern, text, flags)
            return matches
        except Exception as e:
            logger.error(f"正則表達式提取失敗: {pattern}, 錯誤: {e}")
            return []
    
    def extract_attributes(self, selector: str, attribute: str) -> List[str]:
        """
        提取元素屬性
        
        Args:
            selector: CSS選擇器
            attribute: 屬性名稱
            
        Returns:
            List[str]: 屬性值列表
        """
        try:
            elements = self.soup.select(selector)
            attributes = []
            
            for element in elements:
                attr_value = element.get(attribute)
                if attr_value:
                    attributes.append(attr_value)
            
            return attributes
            
        except Exception as e:
            logger.error(f"提取屬性失敗: {selector}[{attribute}], 錯誤: {e}")
            return []


class ProxyDataExtractor:
    """代理數據提取器"""
    
    # IP地址正則表達式
    IP_PATTERN = re.compile(
        r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    )
    
    # 端口正則表達式
    PORT_PATTERN = re.compile(r'\b(?:[1-9]\d{0,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])\b')
    
    # 國家代碼正則表達式
    COUNTRY_PATTERN = re.compile(r'\b[A-Z]{2}\b')
    
    # 協議正則表達式
    PROTOCOL_PATTERN = re.compile(r'\b(http|https|socks4|socks5)\b', re.IGNORECASE)
    
    # 匿名級別正則表達式
    ANONYMITY_PATTERN = re.compile(r'\b(transparent|anonymous|elite|high anonymous)\b', re.IGNORECASE)
    
    def __init__(self, html_content: str):
        """
        初始化代理數據提取器
        
        Args:
            html_content: HTML內容
        """
        self.parser = HTMLParser(html_content)
    
    def extract_proxies_from_table(self, table_selector: str = "table") -> List[Dict[str, Any]]:
        """
        從表格中提取代理數據
        
        Args:
            table_selector: 表格選擇器
            
        Returns:
            List[Dict[str, Any]]: 代理數據列表
        """
        try:
            table_data = self.parser.find_table_data(table_selector)
            if not table_data:
                return []
            
            # 假設第一行是標題
            headers = table_data[0] if table_data else []
            proxies = []
            
            for row in table_data[1:]:
                if len(row) >= 2:  # 至少需要IP和端口
                    proxy_data = self._parse_table_row(headers, row)
                    if proxy_data and self._validate_proxy_data(proxy_data):
                        proxies.append(proxy_data)
            
            return proxies
            
        except Exception as e:
            logger.error(f"從表格提取代理數據失敗: {e}")
            return []
    
    def extract_proxies_from_text(self) -> List[Dict[str, Any]]:
        """
        從文本中提取代理數據
        
        Returns:
            List[Dict[str, Any]]: 代理數據列表
        """
        try:
            text = self.parser.soup.get_text()
            
            # 提取IP地址
            ips = self.IP_PATTERN.findall(text)
            
            # 提取端口
            ports = self.PORT_PATTERN.findall(text)
            
            # 提取協議
            protocols = [p.lower() for p in self.PROTOCOL_PATTERN.findall(text)]
            
            # 提取國家
            countries = self.COUNTRY_PATTERN.findall(text)
            
            # 提取匿名級別
            anonymity_levels = [a.lower() for a in self.ANONYMITY_PATTERN.findall(text)]
            
            proxies = []
            
            # 簡單的配對邏輯：假設IP和端口按順序配對
            for i, ip in enumerate(ips):
                if i < len(ports):
                    proxy_data = {
                        "ip": ip,
                        "port": int(ports[i]),
                        "protocol": protocols[i] if i < len(protocols) else "http",
                        "country": countries[i] if i < len(countries) else None,
                        "anonymity_level": anonymity_levels[i] if i < len(anonymity_levels) else None,
                    }
                    
                    if self._validate_proxy_data(proxy_data):
                        proxies.append(proxy_data)
            
            return proxies
            
        except Exception as e:
            logger.error(f"從文本提取代理數據失敗: {e}")
            return []
    
    def extract_proxies_from_list(self, list_selector: str = "ul") -> List[Dict[str, Any]]:
        """
        從列表中提取代理數據
        
        Args:
            list_selector: 列表選擇器
            
        Returns:
            List[Dict[str, Any]]: 代理數據列表
        """
        try:
            list_items = self.parser.find_list_data(list_selector)
            proxies = []
            
            for item in list_items:
                proxy_data = self._parse_list_item(item)
                if proxy_data and self._validate_proxy_data(proxy_data):
                    proxies.append(proxy_data)
            
            return proxies
            
        except Exception as e:
            logger.error(f"從列表提取代理數據失敗: {e}")
            return []
    
    def _parse_table_row(self, headers: List[str], row: List[str]) -> Optional[Dict[str, Any]]:
        """
        解析表格行數據
        
        Args:
            headers: 表頭
            row: 行數據
            
        Returns:
            Optional[Dict[str, Any]]: 代理數據或None
        """
        try:
            proxy_data = {}
            
            # 映射表頭到字段
            header_mapping = {
                'ip': ['ip', '地址', 'address'],
                'port': ['port', '端口', 'port'],
                'protocol': ['protocol', '協議', 'type'],
                'country': ['country', '國家', '地區'],
                'anonymity': ['anonymity', '匿名度', 'anonymous'],
                'speed': ['speed', '速度', '響應時間'],
            }
            
            for i, cell in enumerate(row):
                if i >= len(headers):
                    break
                
                header = headers[i].lower()
                
                # IP地址
                for key, patterns in header_mapping.items():
                    if any(pattern in header for pattern in patterns):
                        if key == 'ip':
                            if self.IP_PATTERN.match(cell):
                                proxy_data['ip'] = cell
                        elif key == 'port':
                            port_match = self.PORT_PATTERN.search(cell)
                            if port_match:
                                proxy_data['port'] = int(port_match.group())
                        elif key == 'protocol':
                            protocol_match = self.PROTOCOL_PATTERN.search(cell.lower())
                            if protocol_match:
                                proxy_data['protocol'] = protocol_match.group().lower()
                        elif key == 'country':
                            proxy_data['country'] = cell
                        elif key == 'anonymity':
                            anonymity_match = self.ANONYMITY_PATTERN.search(cell.lower())
                            if anonymity_match:
                                proxy_data['anonymity_level'] = anonymity_match.group().lower()
                        elif key == 'speed':
                            # 提取數字作為速度
                            speed_match = re.search(r'\d+', cell)
                            if speed_match:
                                proxy_data['speed'] = float(speed_match.group())
            
            # 如果沒有協議，默認為http
            if 'protocol' not in proxy_data:
                proxy_data['protocol'] = 'http'
            
            return proxy_data if 'ip' in proxy_data and 'port' in proxy_data else None
            
        except Exception as e:
            logger.error(f"解析表格行失敗: {e}")
            return None
    
    def _parse_list_item(self, item: str) -> Optional[Dict[str, Any]]:
        """
        解析列表項數據
        
        Args:
            item: 列表項文本
            
        Returns:
            Optional[Dict[str, Any]]: 代理數據或None
        """
        try:
            # 提取IP地址
            ip_match = self.IP_PATTERN.search(item)
            if not ip_match:
                return None
            
            # 提取端口
            port_match = self.PORT_PATTERN.search(item)
            if not port_match:
                return None
            
            proxy_data = {
                'ip': ip_match.group(),
                'port': int(port_match.group()),
                'protocol': 'http',  # 默認值
            }
            
            # 提取其他信息
            protocol_match = self.PROTOCOL_PATTERN.search(item.lower())
            if protocol_match:
                proxy_data['protocol'] = protocol_match.group().lower()
            
            country_match = self.COUNTRY_PATTERN.search(item)
            if country_match:
                proxy_data['country'] = country_match.group()
            
            anonymity_match = self.ANONYMITY_PATTERN.search(item.lower())
            if anonymity_match:
                proxy_data['anonymity_level'] = anonymity_match.group().lower()
            
            return proxy_data
            
        except Exception as e:
            logger.error(f"解析列表項失敗: {e}")
            return None
    
    def _validate_proxy_data(self, proxy_data: Dict[str, Any]) -> bool:
        """
        驗證代理數據
        
        Args:
            proxy_data: 代理數據
            
        Returns:
            bool: 是否有效
        """
        try:
            # 驗證必需字段
            if 'ip' not in proxy_data or 'port' not in proxy_data:
                return False
            
            # 驗證IP地址
            import ipaddress
            ipaddress.ip_address(proxy_data['ip'])
            
            # 驗證端口
            port = proxy_data['port']
            if not isinstance(port, int) or not (1 <= port <= 65535):
                return False
            
            # 驗證協議（如果有）
            if 'protocol' in proxy_data:
                valid_protocols = ['http', 'https', 'socks4', 'socks5']
                if proxy_data['protocol'] not in valid_protocols:
                    return False
            
            return True
            
        except Exception:
            return False