"""
爬取器工廠模組
"""
from typing import Dict, Any, Type, Optional
from app.etl.extractors.base import BaseExtractor
from app.etl.extractors.free_proxy_list import FreeProxyListExtractor, FreeProxyListAPIExtractor
from app.etl.extractors.proxy_list_plus import ProxyListPlusExtractor
from app.etl.extractors.proxy_scrape import ProxyScrapeAPIExtractor, ProxyScrapeWebExtractor
from app.etl.extractors.geo_node import GeoNodeAPIExtractor, GeoNodeWebExtractor
from app.etl.extractors.proxy_db import ProxyDBExtractor, ProxyDBPremiumExtractor
from app.etl.extractors.hma_proxy import HMAExtractor, HMAAPIExtractor
from app.etl.extractors.proxy_nova import ProxyNovaExtractor, ProxyNovaAPIExtractor
from app.etl.extractors.proxy_scan import ProxyScanExtractor, ProxyScanAPIExtractor
from app.etl.extractors.ssl_proxies import SSLProxiesExtractor
try:
    from app.etl.extractors.eighty_nine_ip_extractor import EightyNineIpExtractor
except ImportError:
    EightyNineIpExtractor = None

try:
    from app.etl.extractors.kuaidaili_extractor import KuaidailiIntrExtractor, KuaidailiInhaExtractor
except ImportError:
    KuaidailiIntrExtractor = None
    KuaidailiInhaExtractor = None

try:
    from app.etl.extractors.geonode_extractor import GeoNodeAPIExtractor as GeoNodeAPIExtractorV2
except ImportError:
    GeoNodeAPIExtractorV2 = None

try:
    from app.etl.extractors.proxydb_extractor import ProxyDBExtractor as ProxyDBExtractorV2
except ImportError:
    ProxyDBExtractorV2 = None

try:
    from app.etl.extractors.proxynova_extractor import ProxyNovaExtractor as ProxyNovaExtractorV2
except ImportError:
    ProxyNovaExtractorV2 = None

try:
    from app.etl.extractors.spys_extractor import SpysExtractor
except ImportError:
    SpysExtractor = None
from app.core.logging import get_logger
from app.core.exceptions import FetcherException

logger = get_logger(__name__)


class ExtractorFactory:
    """爬取器工廠類"""
    
    # 註冊的爬取器類
    _extractors: Dict[str, Type[BaseExtractor]] = {}
    
    # 初始化爬取器字典
    @classmethod
    def _init_extractors(cls) -> Dict[str, Type[BaseExtractor]]:
        """初始化爬取器字典"""
        extractors = {
        "free-proxy-list.net": FreeProxyListExtractor,
        "free-proxy-list.net-api": FreeProxyListAPIExtractor,
        "proxy-list.plus": ProxyListPlusExtractor,
        "proxy-scrape-api": ProxyScrapeAPIExtractor,
        "proxy-scrape-web": ProxyScrapeWebExtractor,
        "geonode-api": GeoNodeAPIExtractor,
        "geonode-web": GeoNodeWebExtractor,
        "proxy-db": ProxyDBExtractor,
        "proxy-db-premium": ProxyDBPremiumExtractor,
        "hma-proxy": HMAExtractor,
        "hma-api": HMAAPIExtractor,
        "proxy-nova": ProxyNovaExtractor,
        "proxy-nova-api": ProxyNovaAPIExtractor,
        "proxy-scan": ProxyScanExtractor,
        "proxy-scan-api": ProxyScanAPIExtractor,
        "ssl-proxies": SSLProxiesExtractor,
            # 新增的爬取器（僅在成功導入時添加）
        }
        
        # 添加新的爬取器（如果導入成功）
        if EightyNineIpExtractor:
            extractors["89ip.cn"] = EightyNineIpExtractor
        if KuaidailiIntrExtractor:
            extractors["kuaidaili-intr"] = KuaidailiIntrExtractor
        if KuaidailiInhaExtractor:
            extractors["kuaidaili-inha"] = KuaidailiInhaExtractor
        if GeoNodeAPIExtractorV2:
            extractors["geonode-api-v2"] = GeoNodeAPIExtractorV2
        if ProxyDBExtractorV2:
            extractors["proxydb-net"] = ProxyDBExtractorV2
        if ProxyNovaExtractorV2:
            extractors["proxynova-com"] = ProxyNovaExtractorV2
        if SpysExtractor:
            extractors["spys-one"] = SpysExtractor
        
        return extractors
    
    @classmethod
    def _ensure_initialized(cls) -> None:
        """確保爬取器字典已初始化"""
        if not cls._extractors:
            cls._extractors = cls._init_extractors()
            logger.info(f"初始化爬取器工廠，共 {len(cls._extractors)} 個爬取器")
    
    @classmethod
    def register_extractor(cls, name: str, extractor_class: Type[BaseExtractor]) -> None:
        """
        註冊新的爬取器
        
        Args:
            name: 爬取器名稱
            extractor_class: 爬取器類
        """
        cls._ensure_initialized()
        cls._extractors[name] = extractor_class
        logger.info(f"註冊爬取器: {name}")
    
    @classmethod
    def create_extractor(cls, name: str, config: Dict[str, Any] = None) -> BaseExtractor:
        """
        創建爬取器實例
        
        Args:
            name: 爬取器名稱
            config: 配置字典
            
        Returns:
            BaseExtractor: 爬取器實例
            
        Raises:
            FetcherException: 當爬取器不存在時
        """
        cls._ensure_initialized()
        
        if name not in cls._extractors:
            available_extractors = list(cls._extractors.keys())
            raise FetcherException(
                f"未知的爬取器: {name}. "
                f"可用的爬取器: {available_extractors}"
            )
        
        try:
            extractor_class = cls._extractors[name]
            extractor = extractor_class(config or {})
            logger.info(f"創建爬取器成功: {name}")
            return extractor
            
        except Exception as e:
            logger.error(f"創建爬取器失敗: {name}, 錯誤: {e}")
            raise FetcherException(f"創建爬取器失敗: {name}, 錯誤: {e}")
    
    @classmethod
    def get_available_extractors(cls) -> list[str]:
        """
        獲取所有可用的爬取器名稱
        
        Returns:
            list[str]: 爬取器名稱列表
        """
        cls._ensure_initialized()
        return list(cls._extractors.keys())
    
    @classmethod
    def is_extractor_available(cls, name: str) -> bool:
        """
        檢查爬取器是否可用
        
        Args:
            name: 爬取器名稱
            
        Returns:
            bool: 是否可用
        """
        cls._ensure_initialized()
        return name in cls._extractors


# 創建全局工廠實例
extractor_factory = ExtractorFactory()