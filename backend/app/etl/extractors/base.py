"""
基礎爬取器抽象類
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import asyncio
from app.core.exceptions import FetcherException, ParserException
from app.core.logging import get_logger
from app.utils.http_client import HTTPClient

logger = get_logger(__name__)


@dataclass
class ExtractResult:
    """提取結果數據類"""
    
    source: str
    proxies: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class ProxyData:
    """代理數據結構"""
    
    ip: str
    port: int
    protocol: str
    country: Optional[str] = None
    city: Optional[str] = None
    anonymity_level: Optional[str] = None
    speed: Optional[float] = None
    reliability: Optional[float] = None
    source: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "ip": self.ip,
            "port": self.port,
            "protocol": self.protocol,
            "country": self.country,
            "city": self.city,
            "anonymity_level": self.anonymity_level,
            "speed": self.speed,
            "reliability": self.reliability,
            "source": self.source,
        }


class BaseExtractor(ABC):
    """基礎提取器抽象類"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        初始化提取器
        
        Args:
            name: 提取器名稱
            config: 配置字典
        """
        self.name = name
        self.config = config
        self.http_client = HTTPClient(
            timeout=config.get("timeout", 30),
            max_retries=config.get("max_retries", 3),
            retry_delay=config.get("retry_delay", 1),
        )
        self.logger = get_logger(f"{__name__}.{self.name}")
    
    async def __aenter__(self):
        """異步上下文管理器進入"""
        await self.http_client.create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出"""
        await self.http_client.close_session()
    
    @abstractmethod
    async def extract(self) -> ExtractResult:
        """
        提取代理數據
        
        Returns:
            ExtractResult: 提取結果
        """
        pass
    
    async def validate_config(self) -> bool:
        """
        驗證配置
        
        Returns:
            bool: 配置是否有效
        """
        required_fields = self.get_required_config_fields()
        for field in required_fields:
            if field not in self.config:
                self.logger.error(f"缺少必需配置字段: {field}")
                return False
        return True
    
    @abstractmethod
    def get_required_config_fields(self) -> List[str]:
        """
        獲取必需的配置字段
        
        Returns:
            List[str]: 必需字段列表
        """
        pass
    
    def parse_proxies(self, raw_data: Union[str, Dict[str, Any]]) -> List[ProxyData]:
        """
        解析代理數據
        
        Args:
            raw_data: 原始數據
            
        Returns:
            List[ProxyData]: 解析後的代理列表
        """
        try:
            if isinstance(raw_data, str):
                return self._parse_html(raw_data)
            elif isinstance(raw_data, dict):
                return self._parse_json(raw_data)
            else:
                raise ParserException(
                    f"不支持的數據類型: {type(raw_data)}",
                    source=self.name,
                    details={"data_type": str(type(raw_data))}
                )
        except Exception as e:
            self.logger.error(f"解析代理數據失敗: {e}")
            raise ParserException(
                f"解析代理數據失敗: {str(e)}",
                source=self.name,
                details={"error": str(e)}
            )
    
    def _parse_html(self, html_content: str) -> List[ProxyData]:
        """
        解析HTML內容
        
        Args:
            html_content: HTML內容
            
        Returns:
            List[ProxyData]: 解析後的代理列表
        """
        raise NotImplementedError("子類必須實現_parse_html方法")
    
    def _parse_json(self, json_data: Dict[str, Any]) -> List[ProxyData]:
        """
        解析JSON數據
        
        Args:
            json_data: JSON數據
            
        Returns:
            List[ProxyData]: 解析後的代理列表
        """
        raise NotImplementedError("子類必須實現_parse_json方法")
    
    def validate_proxy_data(self, proxy_data: ProxyData) -> bool:
        """
        驗證代理數據
        
        Args:
            proxy_data: 代理數據
            
        Returns:
            bool: 數據是否有效
        """
        try:
            # 驗證IP地址
            import ipaddress
            ipaddress.ip_address(proxy_data.ip)
            
            # 驗證端口
            if not (1 <= proxy_data.port <= 65535):
                return False
            
            # 驗證協議
            valid_protocols = ["http", "https", "socks4", "socks5"]
            if proxy_data.protocol not in valid_protocols:
                return False
            
            return True
            
        except ValueError:
            return False
    
    async def fetch_with_retry(self, url: str, **kwargs) -> str:
        """
        帶重試的抓取
        
        Args:
            url: 目標URL
            **kwargs: 其他參數
            
        Returns:
            str: 響應內容
        """
        try:
            return await self.http_client.get(url, **kwargs)
        except Exception as e:
            self.logger.error(f"抓取失敗: {url}, 錯誤: {e}")
            raise FetcherException(
                f"抓取失敗: {str(e)}",
                source=self.name,
                details={"url": url, "error": str(e)}
            )


class APIExtractor(BaseExtractor):
    """API提取器基類"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_endpoint = config.get("api_endpoint", "")
        self.api_key = config.get("api_key", "")
        self.request_params = config.get("request_params", {})
    
    def get_required_config_fields(self) -> List[str]:
        return ["api_endpoint"]
    
    async def extract(self) -> ExtractResult:
        """提取API數據"""
        start_time = datetime.utcnow()
        
        try:
            # 構建請求參數
            params = self.request_params.copy()
            if self.api_key:
                params["api_key"] = self.api_key
            
            # 發送請求
            url = self.build_api_url()
            self.logger.info(f"開始提取API數據: {url}")
            
            response_data = await self.fetch_with_retry(url, params=params)
            
            # 解析數據
            proxies = self.parse_proxies(response_data)
            
            result = ExtractResult(
                source=self.name,
                proxies=[proxy.to_dict() for proxy in proxies],
                metadata={
                    "url": url,
                    "total_found": len(proxies),
                    "start_time": start_time,
                    "end_time": datetime.utcnow(),
                },
                success=True,
                timestamp=start_time,
            )
            
            self.logger.info(f"API提取完成: {self.name}, 找到 {len(proxies)} 個代理")
            return result
            
        except Exception as e:
            self.logger.error(f"API提取失敗: {self.name}, 錯誤: {e}")
            return ExtractResult(
                source=self.name,
                proxies=[],
                metadata={"start_time": start_time},
                success=False,
                error_message=str(e),
                timestamp=start_time,
            )
    
    def build_api_url(self) -> str:
        """構建API URL"""
        return self.api_endpoint


class WebScrapingExtractor(BaseExtractor):
    """網頁爬取提取器基類"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.base_url = config.get("base_url", "")
        self.start_urls = config.get("start_urls", [])
        self.pagination_config = config.get("pagination", {})
    
    def get_required_config_fields(self) -> List[str]:
        return ["base_url"]
    
    async def extract(self) -> ExtractResult:
        """提取網頁數據"""
        start_time = datetime.utcnow()
        all_proxies = []
        
        try:
            urls_to_crawl = self.start_urls or [self.base_url]
            
            for url in urls_to_crawl:
                self.logger.info(f"開始爬取網頁: {url}")
                
                # 爬取頁面
                html_content = await self.fetch_with_retry(url)
                
                # 解析代理數據
                proxies = self.parse_proxies(html_content)
                all_proxies.extend(proxies)
                
                self.logger.info(f"從 {url} 提取到 {len(proxies)} 個代理")
                
                # 速率控制
                await asyncio.sleep(1)
            
            result = ExtractResult(
                source=self.name,
                proxies=[proxy.to_dict() for proxy in all_proxies],
                metadata={
                    "urls_crawled": urls_to_crawl,
                    "total_found": len(all_proxies),
                    "start_time": start_time,
                    "end_time": datetime.utcnow(),
                },
                success=True,
                timestamp=start_time,
            )
            
            self.logger.info(f"網頁爬取完成: {self.name}, 總共找到 {len(all_proxies)} 個代理")
            return result
            
        except Exception as e:
            self.logger.error(f"網頁爬取失敗: {self.name}, 錯誤: {e}")
            return ExtractResult(
                source=self.name,
                proxies=[],
                metadata={"start_time": start_time},
                success=False,
                error_message=str(e),
                timestamp=start_time,
            )