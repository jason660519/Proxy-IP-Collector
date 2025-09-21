"""
89ip.cn 增強版爬取器
包含完整的反爬蟲處理、請求標頭設置、自動化IP驗證與評分機制
"""
import asyncio
import random
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import re
from urllib.parse import urljoin

from app.etl.extractors.base import WebScrapingExtractor, ProxyData, ExtractResult
from app.utils.html_parser import ProxyDataExtractor
from app.core.logging import get_logger
from app.utils.user_agents import get_random_user_agent
from app.utils.proxy_validator import ProxyValidator

logger = get_logger(__name__)


class EightyNineIpEnhancedExtractor(WebScrapingExtractor):
    """
    89ip.cn 增強版專屬爬蟲程式
    
    功能特點：
    - 智能請求標頭輪換
    - 高級反爬蟲機制處理
    - 自動化IP驗證與評分
    - 智能速率控制
    - 完整的錯誤處理和重試機制
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化89ip.cn增強版爬蟲
        
        Args:
            config: 配置字典，包含爬蟲參數
        """
        super().__init__("89ip.cn", config)
        
        # 基本配置
        self.base_url = config.get("base_url", "https://www.89ip.cn/index_{page}.html")
        self.max_pages = config.get("max_pages", 50)
        self.start_page = config.get("start_page", 1)
        
        # 反爬蟲配置
        self.enable_anti_bot = config.get("enable_anti_bot", True)
        self.min_delay = config.get("min_delay", 1.0)
        self.max_delay = config.get("max_delay", 3.0)
        self.retry_attempts = config.get("retry_attempts", 3)
        self.use_proxy_rotation = config.get("use_proxy_rotation", False)
        
        # 驗證配置
        self.enable_validation = config.get("enable_validation", True)
        self.validation_timeout = config.get("validation_timeout", 10)
        self.min_quality_score = config.get("min_quality_score", 0.6)
        
        # 選擇器配置
        self.selectors = {
            "container": "table.layui-table tbody tr",
            "ip": "td:nth-child(1)",
            "port": "td:nth-child(2)",
            "location": "td:nth-child(3)",
            "anonymity": "td:nth-child(4)",
            "type": "td:nth-child(5)",
            "verification_time": "td:nth-child(6)"
        }
        
        # 請求標頭池
        self.header_pool = self._build_header_pool()
        
        # 代理驗證器
        self.validator = ProxyValidator() if self.enable_validation else None
        
        # 統計數據
        self.stats = {
            "pages_crawled": 0,
            "proxies_found": 0,
            "proxies_validated": 0,
            "high_quality_proxies": 0,
            "errors": []
        }
    
    def get_required_config_fields(self) -> List[str]:
        """獲取必需的配置字段"""
        return ["base_url"]
    
    def _build_header_pool(self) -> List[Dict[str, str]]:
        """
        構建請求標頭池，用於輪換避免被檢測
        
        Returns:
            List[Dict[str, str]]: 請求標頭列表
        """
        headers_pool = []
        
        # Chrome 瀏覽器標頭
        chrome_versions = [
            "120.0.0.0", "119.0.0.0", "118.0.0.0", "117.0.0.0", "116.0.0.0"
        ]
        
        for version in chrome_versions:
            headers = {
                "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0",
                "DNT": "1"
            }
            headers_pool.append(headers)
        
        # Firefox 瀏覽器標頭
        firefox_versions = ["120.0", "119.0", "118.0", "117.0", "116.0"]
        
        for version in firefox_versions:
            headers = {
                "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{version}) Gecko/20100101 Firefox/{version}",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "DNT": "1"
            }
            headers_pool.append(headers)
        
        return headers_pool
    
    def _get_random_headers(self) -> Dict[str, str]:
        """
        獲取隨機請求標頭
        
        Returns:
            Dict[str, str]: 隨機請求標頭
        """
        if not self.header_pool:
            return {"User-Agent": get_random_user_agent()}
        
        headers = random.choice(self.header_pool).copy()
        
        # 添加隨機的額外標頭
        if random.random() > 0.5:
            headers["X-Forwarded-For"] = self._generate_random_ip()
        
        if random.random() > 0.7:
            headers["Referer"] = "https://www.google.com/"
        
        return headers
    
    def _generate_random_ip(self) -> str:
        """生成隨機IP地址"""
        return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
    
    def _calculate_delay(self) -> float:
        """
        計算請求延遲時間
        
        Returns:
            float: 延遲時間（秒）
        """
        if not self.enable_anti_bot:
            return 0.1
        
        # 基礎延遲 + 隨機延遲
        base_delay = random.uniform(self.min_delay, self.max_delay)
        
        # 根據請求成功率調整延遲
        if hasattr(self, 'success_rate'):
            if self.success_rate < 0.5:
                base_delay *= 2  # 成功率低時增加延遲
        
        return base_delay
    
    async def extract(self) -> ExtractResult:
        """
        執行增強版代理數據提取
        
        Returns:
            ExtractResult: 提取結果
        """
        self.logger.info(f"開始執行89ip.cn增強版爬取，最大頁面: {self.max_pages}")
        
        start_time = datetime.utcnow()
        all_proxies = []
        
        try:
            # 生成爬取任務
            tasks = []
            semaphore = asyncio.Semaphore(3)  # 限制併發數
            
            for page in range(self.start_page, self.max_pages + 1):
                url = self.base_url.format(page=page)
                task = self._crawl_page_with_enhancements(semaphore, url, page)
                tasks.append(task)
            
            # 分批執行任務，避免一次性請求過多
            batch_size = 5
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        self.logger.error(f"批次爬取失敗: {result}")
                        self.stats["errors"].append(str(result))
                    else:
                        all_proxies.extend(result)
                
                # 批次間延遲
                if i + batch_size < len(tasks):
                    await asyncio.sleep(random.uniform(2, 5))
            
            # 數據去重
            unique_proxies = self._deduplicate_proxies(all_proxies)
            
            # 自動化驗證與評分
            validated_proxies = []
            if self.enable_validation and unique_proxies:
                self.logger.info(f"開始驗證 {len(unique_proxies)} 個代理...")
                validated_proxies = await self._validate_and_score_proxies(unique_proxies)
                self.stats["proxies_validated"] = len(validated_proxies)
                self.stats["high_quality_proxies"] = len([p for p in validated_proxies if p.quality_score >= self.min_quality_score])
            else:
                validated_proxies = unique_proxies
            
            # 構建結果
            result = ExtractResult(
                source=self.name,
                proxies=[proxy.to_dict() for proxy in validated_proxies],
                metadata={
                    "crawl_stats": self.stats,
                    "pages_crawled": self.stats["pages_crawled"],
                    "proxies_found": self.stats["proxies_found"],
                    "proxies_validated": self.stats["proxies_validated"],
                    "high_quality_proxies": self.stats["high_quality_proxies"],
                    "validation_enabled": self.enable_validation,
                    "anti_bot_enabled": self.enable_anti_bot,
                    "extraction_method": "enhanced_html_parsing",
                    "start_time": start_time,
                    "end_time": datetime.utcnow(),
                    "duration_seconds": (datetime.utcnow() - start_time).total_seconds()
                },
                success=True,
                timestamp=start_time,
            )
            
            self.logger.info(
                f"89ip.cn增強版爬取完成: "
                f"爬取頁面 {self.stats['pages_crawled']}, "
                f"找到代理 {self.stats['proxies_found']}, "
                f"驗證通過 {self.stats['proxies_validated']}, "
                f"高質量代理 {self.stats['high_quality_proxies']}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"89ip.cn增強版爬取失敗: {e}")
            return ExtractResult(
                source=self.name,
                proxies=[],
                metadata={
                    "error": str(e),
                    "stats": self.stats,
                    "start_time": start_time,
                    "end_time": datetime.utcnow()
                },
                success=False,
                error_message=str(e),
                timestamp=start_time,
            )
    
    async def _crawl_page_with_enhancements(self, semaphore: asyncio.Semaphore, url: str, page: int) -> List[ProxyData]:
        """
        使用增強功能爬取單個頁面
        
        Args:
            semaphore: 信號量控制
            url: 頁面URL
            page: 頁碼
            
        Returns:
            List[ProxyData]: 代理數據列表
        """
        async with semaphore:
            for attempt in range(self.retry_attempts):
                try:
                    # 計算延遲
                    delay = self._calculate_delay()
                    if attempt > 0:  # 重試時增加延遲
                        delay *= (attempt + 1)
                    
                    await asyncio.sleep(delay)
                    
                    # 獲取隨機請求標頭
                    headers = self._get_random_headers()
                    
                    # 爬取頁面
                    self.logger.debug(f"爬取第 {page} 頁，嘗試 {attempt + 1}: {url}")
                    
                    html_content = await self.fetch_with_retry(url, headers=headers)
                    
                    if not html_content:
                        raise Exception("獲取頁面內容為空")
                    
                    # 解析數據
                    proxies = self._parse_html_enhanced(html_content, page)
                    
                    # 更新統計
                    self.stats["pages_crawled"] += 1
                    self.stats["proxies_found"] += len(proxies)
                    
                    self.logger.debug(f"第 {page} 頁爬取成功，找到 {len(proxies)} 個代理")
                    
                    return proxies
                    
                except Exception as e:
                    self.logger.warning(f"第 {page} 頁爬取失敗 (嘗試 {attempt + 1}): {e}")
                    if attempt == self.retry_attempts - 1:
                        self.stats["errors"].append(f"頁面 {page}: {str(e)}")
                        return []
                    
                    # 指數退避重試
                    await asyncio.sleep(2 ** attempt)
            
            return []
    
    def _parse_html_enhanced(self, html_content: str, page: int) -> List[ProxyData]:
        """
        增強版HTML解析
        
        Args:
            html_content: HTML內容
            page: 頁碼
            
        Returns:
            List[ProxyData]: 代理數據列表
        """
        try:
            extractor = ProxyDataExtractor(html_content)
            
            # 從表格中提取數據
            proxies_data = extractor.extract_proxies_from_table(
                self.selectors["container"],
                {
                    "ip": self.selectors["ip"],
                    "port": self.selectors["port"],
                    "location": self.selectors["location"],
                    "anonymity": self.selectors["anonymity"],
                    "type": self.selectors["type"],
                    "verification_time": self.selectors["verification_time"]
                }
            )
            
            # 轉換為ProxyData對象
            proxy_objects = []
            for proxy_data in proxies_data:
                proxy_obj = self._convert_to_proxy_data_enhanced(proxy_data, page)
                if proxy_obj:
                    proxy_objects.append(proxy_obj)
            
            return proxy_objects
            
        except Exception as e:
            self.logger.error(f"解析第 {page} 頁HTML失敗: {e}")
            return []
    
    def _convert_to_proxy_data_enhanced(self, proxy_dict: Dict[str, Any], page: int) -> Optional[ProxyData]:
        """
        增強版代理數據轉換
        
        Args:
            proxy_dict: 代理字典
            page: 頁碼
            
        Returns:
            Optional[ProxyData]: ProxyData對象或None
        """
        try:
            # 清理和驗證必需字段
            ip = self._clean_ip_address(proxy_dict.get("ip", ""))
            port = self._clean_port_number(proxy_dict.get("port", ""))
            
            if not ip or not port:
                return None
            
            # 驗證IP格式
            if not self._is_valid_ip(ip):
                return None
            
            # 獲取可選字段
            location = proxy_dict.get("location", "").strip()
            anonymity = self._normalize_anonymity(proxy_dict.get("anonymity", ""))
            proxy_type = self._normalize_proxy_type(proxy_dict.get("type", ""))
            verification_time = proxy_dict.get("verification_time", "")
            
            # 創建ProxyData對象
            proxy_data = ProxyData(
                ip=ip,
                port=port,
                protocol=proxy_type,
                anonymity=anonymity,
                country=self._extract_country(location),
                city=self._extract_city(location),
                source=self.name,
                source_url=f"https://www.89ip.cn/index_{page}.html",
                location=location,
                verification_time=self._parse_verification_time(verification_time),
                quality_score=0.0,  # 將在驗證階段設置
                last_verified=None,
                response_time=None
            )
            
            return proxy_data
            
        except Exception as e:
            self.logger.debug(f"轉換代理數據失敗: {e}")
            return None
    
    def _clean_ip_address(self, ip_str: str) -> str:
        """清理IP地址字符串"""
        if not ip_str:
            return ""
        
        # 移除HTML標籤和多餘空格
        ip = re.sub(r'<[^>]+>', '', ip_str).strip()
        
        # 驗證IP格式
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        match = re.search(ip_pattern, ip)
        
        return match.group(0) if match else ""
    
    def _clean_port_number(self, port_str: str) -> Optional[int]:
        """清理端口號字符串"""
        if not port_str:
            return None
        
        try:
            # 移除非數字字符
            port = int(re.sub(r'[^0-9]', '', port_str.strip()))
            
            # 驗證端口範圍
            if 1 <= port <= 65535:
                return port
            
            return None
        except (ValueError, TypeError):
            return None
    
    def _normalize_anonymity(self, anonymity_str: str) -> str:
        """標準化匿名度"""
        anonymity = anonymity_str.strip().lower()
        
        if "高匿" in anonymity or "high" in anonymity:
            return "high"
        elif "匿名" in anonymity or "anonymous" in anonymity:
            return "medium"
        elif "透明" in anonymity or "transparent" in anonymity:
            return "low"
        else:
            return "unknown"
    
    def _normalize_proxy_type(self, type_str: str) -> str:
        """標準化代理類型"""
        proxy_type = type_str.strip().lower()
        
        if "http" in proxy_type:
            return "http"
        elif "https" in proxy_type or "ssl" in proxy_type:
            return "https"
        elif "socks4" in proxy_type:
            return "socks4"
        elif "socks5" in proxy_type:
            return "socks5"
        else:
            return "http"  # 默認值
    
    def _extract_country(self, location: str) -> str:
        """從位置信息中提取國家"""
        if not location:
            return "unknown"
        
        # 簡單的國家識別邏輯
        if "中國" in location or "CN" in location:
            return "CN"
        elif "美國" in location or "US" in location:
            return "US"
        elif "香港" in location or "HK" in location:
            return "HK"
        elif "台灣" in location or "TW" in location:
            return "TW"
        else:
            return "unknown"
    
    def _extract_city(self, location: str) -> str:
        """從位置信息中提取城市"""
        if not location:
            return "unknown"
        
        # 這裡可以添加更複雜的城市識別邏輯
        return location.split()[0] if location else "unknown"
    
    def _parse_verification_time(self, time_str: str) -> Optional[datetime]:
        """解析驗證時間"""
        if not time_str:
            return None
        
        try:
            # 這裡可以根據實際的時間格式進行解析
            # 示例：假設格式為 "2024-12-19 14:30:25"
            return datetime.strptime(time_str.strip(), "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return None
    
    async def _validate_and_score_proxies(self, proxies: List[ProxyData]) -> List[ProxyData]:
        """
        驗證和評分代理
        
        Args:
            proxies: 代理列表
            
        Returns:
            List[ProxyData]: 驗證後的代理列表
        """
        if not self.validator:
            return proxies
        
        validated_proxies = []
        
        # 限制併發驗證數量
        semaphore = asyncio.Semaphore(10)
        
        async def validate_single(proxy: ProxyData) -> Optional[ProxyData]:
            async with semaphore:
                try:
                    # 驗證代理
                    result = await self.validator.validate_proxy(proxy)
                    
                    if result.is_valid:
                        # 更新代理的質量分數
                        proxy.quality_score = result.overall_score
                        proxy.last_verified = datetime.utcnow()
                        proxy.response_time = result.response_time
                        
                        return proxy
                    
                except Exception as e:
                    self.logger.debug(f"代理驗證失敗 {proxy.ip}:{proxy.port}: {e}")
                
                return None
        
        # 執行驗證
        validation_tasks = [validate_single(proxy) for proxy in proxies]
        validation_results = await asyncio.gather(*validation_tasks)
        
        # 收集驗證通過的代理
        validated_proxies = [proxy for proxy in validation_results if proxy is not None]
        
        self.logger.info(f"代理驗證完成: {len(validated_proxies)}/{len(proxies)} 通過驗證")
        
        return validated_proxies
    
    def _deduplicate_proxies(self, proxies: List[ProxyData]) -> List[ProxyData]:
        """代理去重"""
        seen = set()
        unique_proxies = []
        
        for proxy in proxies:
            key = f"{proxy.ip}:{proxy.port}"
            if key not in seen:
                seen.add(key)
                unique_proxies.append(proxy)
        
        return unique_proxies
    
    def _is_valid_ip(self, ip: str) -> bool:
        """驗證IP地址格式"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            
            for part in parts:
                num = int(part)
                if not (0 <= num <= 255):
                    return False
            
            return True
        except (ValueError, AttributeError):
            return False