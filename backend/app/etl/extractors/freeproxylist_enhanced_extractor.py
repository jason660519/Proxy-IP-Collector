"""
free-proxy-list.net 增強版爬取器
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


class FreeProxyListEnhancedExtractor(WebScrapingExtractor):
    """
    free-proxy-list.net 增強版專屬爬蟲程式
    
    功能特點：
    - 智能請求標頭輪換
    - 高級反爬蟲機制處理
    - 自動化IP驗證與評分
    - 智能速率控制
    - 完整的錯誤處理和重試機制
    - 支持多種代理類型和國家篩選
    - 高級HTML解析和數據提取
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化free-proxy-list.net增強版爬蟲
        
        Args:
            config: 配置字典，包含爬蟲參數
        """
        super().__init__("free-proxy-list.net", config)
        
        # 基本配置
        self.base_url = config.get("base_url", "https://free-proxy-list.net/")
        self.country_filter = config.get("country_filter", [])  # 國家篩選
        self.anonymity_filter = config.get("anonymity_filter", [])  # 匿名度篩選
        self.https_filter = config.get("https_filter", None)  # HTTPS篩選
        
        # 反爬蟲配置
        self.enable_anti_bot = config.get("enable_anti_bot", True)
        self.min_delay = config.get("min_delay", 2.0)
        self.max_delay = config.get("max_delay", 5.0)
        self.retry_attempts = config.get("retry_attempts", 3)
        self.enable_session_rotation = config.get("enable_session_rotation", True)
        self.enable_captcha_handling = config.get("enable_captcha_handling", True)
        
        # 驗證配置
        self.enable_validation = config.get("enable_validation", True)
        self.validation_timeout = config.get("validation_timeout", 15)
        self.min_quality_score = config.get("min_quality_score", 0.5)
        
        # 選擇器配置
        self.selectors = {
            "proxy_table": "table#proxylisttable tbody tr",
            "ip": "td:nth-child(1)",
            "port": "td:nth-child(2)",
            "country_code": "td:nth-child(3)",
            "country": "td:nth-child(3)",
            "anonymity": "td:nth-child(5)",
            "google": "td:nth-child(6)",
            "https": "td:nth-child(7)",
            "last_checked": "td:nth-child(8)",
            "pagination": "div.pagination"
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
            "session_rotations": 0,
            "captcha_encounters": 0,
            "errors": [],
            "country_distribution": {},
            "anonymity_distribution": {}
        }
        
        # 會話管理
        self.session_cookies = {}
        self.last_request_time = None
        self.success_rate = 1.0
        self.request_count = 0
        self.success_count = 0
    
    def get_required_config_fields(self) -> List[str]:
        """獲取必需的配置字段"""
        return ["base_url"]
    
    def _build_header_pool(self) -> List[Dict[str, str]]:
        """
        構建請求標頭池，專門針對free-proxy-list.net優化
        
        Returns:
            List[Dict[str, str]]: 請求標頭列表
        """
        headers_pool = []
        
        # 桌面瀏覽器標頭配置
        desktop_configs = [
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept_language": "en-US,en;q=0.9",
                "accept_encoding": "gzip, deflate, br",
                "cache_control": "max-age=0"
            },
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "accept_language": "en-US,en;q=0.5",
                "accept_encoding": "gzip, deflate, br",
                "cache_control": "no-cache"
            },
            {
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "accept_language": "en-US",
                "accept_encoding": "gzip, deflate, br"
            },
            {
                "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "accept_language": "en-US,en;q=0.9",
                "accept_encoding": "gzip, deflate, br"
            }
        ]
        
        for config in desktop_configs:
            headers = {
                "User-Agent": config["user_agent"],
                "Accept": config["accept"],
                "Accept-Language": config["accept_language"],
                "Accept-Encoding": config["accept_encoding"],
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": config.get("cache_control", "max-age=0"),
                "DNT": "1"
            }
            
            headers_pool.append(headers)
        
        # 移動端標頭
        mobile_configs = [
            {
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "accept_language": "en-US"
            },
            {
                "user_agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "accept_language": "en-US,en;q=0.9"
            }
        ]
        
        for config in mobile_configs:
            headers = {
                "User-Agent": config["user_agent"],
                "Accept": config["accept"],
                "Accept-Language": config["accept_language"],
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0"
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
        if random.random() > 0.6:
            headers["X-Forwarded-For"] = self._generate_random_ip()
        
        if random.random() > 0.7:
            headers["X-Real-IP"] = self._generate_random_ip()
        
        if random.random() > 0.5:
            headers["Referer"] = "https://www.google.com/"
        
        # 隨機添加Accept變體
        if random.random() > 0.4:
            accept_variants = [
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
            ]
            headers["Accept"] = random.choice(accept_variants)
        
        return headers
    
    def _generate_random_ip(self) -> str:
        """生成隨機IP地址"""
        return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
    
    def _calculate_delay(self) -> float:
        """
        計算請求延遲時間，根據成功率和請求歷史動態調整
        
        Returns:
            float: 延遲時間（秒）
        """
        if not self.enable_anti_bot:
            return 0.5
        
        # 基礎延遲
        base_delay = random.uniform(self.min_delay, self.max_delay)
        
        # 根據成功率調整
        if self.success_rate < 0.3:
            base_delay *= 3.0  # 成功率很低時大幅增加延遲
        elif self.success_rate < 0.6:
            base_delay *= 2.0  # 成功率較低時適度增加延遲
        elif self.success_rate < 0.8:
            base_delay *= 1.5  # 成功率一般時稍微增加延遲
        
        # 根據上次請求時間調整
        if self.last_request_time:
            time_since_last = (datetime.utcnow() - self.last_request_time).total_seconds()
            if time_since_last < 1.0:
                base_delay += 1.0  # 如果請求太頻繁，增加額外延遲
        
        return base_delay
    
    def _detect_captcha(self, html_content: str) -> bool:
        """
        檢測是否遇到驗證碼
        
        Args:
            html_content: HTML內容
            
        Returns:
            bool: 是否遇到驗證碼
        """
        captcha_indicators = [
            "captcha",
            "recaptcha",
            "verify you are human",
            "prove you are not a robot",
            "security check",
            "cloudflare",
            "ddos protection",
            "rate limit exceeded"
        ]
        
        html_lower = html_content.lower()
        for indicator in captcha_indicators:
            if indicator in html_lower:
                self.stats["captcha_encounters"] += 1
                return True
        
        return False
    
    def _update_success_rate(self, success: bool):
        """更新成功率統計"""
        self.request_count += 1
        if success:
            self.success_count += 1
        
        # 計算成功率（使用滑動窗口，最近10次請求）
        window_size = min(10, self.request_count)
        recent_success_rate = self.success_count / self.request_count if self.request_count > 0 else 1.0
        self.success_rate = recent_success_rate
    
    async def extract(self) -> ExtractResult:
        """
        執行增強版代理數據提取
        
        Returns:
            ExtractResult: 提取結果
        """
        self.logger.info(f"開始執行free-proxy-list.net增強版爬取")
        
        start_time = datetime.utcnow()
        all_proxies = []
        
        try:
            # 主要頁面爬取
            main_page_proxies = await self._crawl_main_page()
            all_proxies.extend(main_page_proxies)
            
            # 如果啟用了分頁爬取，嘗試爬取更多頁面
            if config.get("enable_pagination", True):
                pagination_proxies = await self._crawl_pagination_pages()
                all_proxies.extend(pagination_proxies)
            
            # 數據去重
            unique_proxies = self._deduplicate_proxies(all_proxies)
            
            # 應用篩選條件
            filtered_proxies = self._apply_filters(unique_proxies)
            
            # 自動化驗證與評分
            validated_proxies = []
            if self.enable_validation and filtered_proxies:
                self.logger.info(f"開始驗證 {len(filtered_proxies)} 個代理...")
                validated_proxies = await self._validate_and_score_proxies(filtered_proxies)
                self.stats["proxies_validated"] = len(validated_proxies)
                self.stats["high_quality_proxies"] = len([p for p in validated_proxies if p.quality_score >= self.min_quality_score])
            else:
                validated_proxies = filtered_proxies
            
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
                    "country_distribution": self.stats["country_distribution"],
                    "anonymity_distribution": self.stats["anonymity_distribution"],
                    "validation_enabled": self.enable_validation,
                    "anti_bot_enabled": self.enable_anti_bot,
                    "session_rotation_enabled": self.enable_session_rotation,
                    "extraction_method": "enhanced_html_parsing",
                    "start_time": start_time,
                    "end_time": datetime.utcnow(),
                    "duration_seconds": (datetime.utcnow() - start_time).total_seconds()
                },
                success=True,
                timestamp=start_time,
            )
            
            self.logger.info(
                f"free-proxy-list.net增強版爬取完成: "
                f"爬取頁面 {self.stats['pages_crawled']}, "
                f"找到代理 {self.stats['proxies_found']}, "
                f"驗證通過 {self.stats['proxies_validated']}, "
                f"高質量代理 {self.stats['high_quality_proxies']}, "
                f"會話輪換 {self.stats['session_rotations']}, "
                f"遇到驗證碼 {self.stats['captcha_encounters']}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"free-proxy-list.net增強版爬取失敗: {e}")
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
    
    async def _crawl_main_page(self) -> List[ProxyData]:
        """
        爬取主頁面
        
        Returns:
            List[ProxyData]: 代理數據列表
        """
        self.logger.info("開始爬取主頁面...")
        
        for attempt in range(self.retry_attempts):
            try:
                # 會話輪換
                if self.enable_session_rotation and attempt > 0 and attempt % 2 == 0:
                    self._rotate_session()
                
                # 計算延遲
                delay = self._calculate_delay()
                if attempt > 0:
                    delay *= (attempt + 1)
                
                await asyncio.sleep(delay)
                
                # 獲取隨機請求標頭
                headers = self._get_random_headers()
                
                # 爬取頁面
                self.logger.debug(f"爬取主頁面，嘗試 {attempt + 1}: {self.base_url}")
                
                html_content = await self.fetch_with_retry(self.base_url, headers=headers)
                
                if not html_content:
                    raise Exception("獲取頁面內容為空")
                
                # 檢測驗證碼
                if self._detect_captcha(html_content):
                    self.logger.warning(f"遇到驗證碼，嘗試 {attempt + 1}")
                    if attempt < self.retry_attempts - 1:
                        # 遇到驗證碼時大幅增加延遲
                        await asyncio.sleep(delay * 3)
                        continue
                    else:
                        break
                
                # 解析數據
                proxies = self._parse_html_enhanced(html_content, "main_page")
                
                # 更新統計
                self.stats["pages_crawled"] += 1
                self.stats["proxies_found"] += len(proxies)
                
                self.logger.info(f"主頁面爬取成功，找到 {len(proxies)} 個代理")
                
                return proxies
                
            except Exception as e:
                self.logger.warning(f"主頁面爬取失敗 (嘗試 {attempt + 1}): {e}")
                
                if attempt == self.retry_attempts - 1:
                    self.stats["errors"].append(f"主頁面: {str(e)}")
                    return []
                
                # 指數退避重試
                await asyncio.sleep(2 ** attempt)
        
        return []
    
    async def _crawl_pagination_pages(self) -> List[ProxyData]:
        """
        爬取分頁頁面（如果有）
        
        Returns:
            List[ProxyData]: 代理數據列表
        """
        # free-proxy-list.net 通常只有一個主頁面，但這裡預留接口
        # 可以根據實際情況實現分頁爬取邏輯
        return []
    
    def _rotate_session(self):
        """輪換會話"""
        self.stats["session_rotations"] += 1
        self.logger.debug(f"會話輪換 #{self.stats['session_rotations']}")
        
        # 清除會話Cookie
        self.session_cookies.clear()
        
        # 這裡可以實現更複雜的會話管理邏輯
        # 例如使用不同的IP、用戶代理等
    
    def _parse_html_enhanced(self, html_content: str, page_type: str) -> List[ProxyData]:
        """
        增強版HTML解析
        
        Args:
            html_content: HTML內容
            page_type: 頁面類型
            
        Returns:
            List[ProxyData]: 代理數據列表
        """
        try:
            extractor = ProxyDataExtractor(html_content)
            
            # 從表格中提取數據
            proxies_data = extractor.extract_proxies_from_table(
                self.selectors["proxy_table"],
                {
                    "ip": self.selectors["ip"],
                    "port": self.selectors["port"],
                    "country_code": self.selectors["country_code"],
                    "country": self.selectors["country"],
                    "anonymity": self.selectors["anonymity"],
                    "google": self.selectors["google"],
                    "https": self.selectors["https"],
                    "last_checked": self.selectors["last_checked"]
                }
            )
            
            # 轉換為ProxyData對象
            proxy_objects = []
            for proxy_data in proxies_data:
                proxy_obj = self._convert_to_proxy_data_enhanced(proxy_data, page_type)
                if proxy_obj:
                    proxy_objects.append(proxy_obj)
            
            return proxy_objects
            
        except Exception as e:
            self.logger.error(f"解析 {page_type} HTML失敗: {e}")
            return []
    
    def _convert_to_proxy_data_enhanced(self, proxy_dict: Dict[str, Any], page_type: str) -> Optional[ProxyData]:
        """
        增強版代理數據轉換
        
        Args:
            proxy_dict: 代理字典
            page_type: 頁面類型
            
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
            country_code = proxy_dict.get("country_code", "").strip().upper()
            country = proxy_dict.get("country", "").strip()
            anonymity = self._normalize_anonymity(proxy_dict.get("anonymity", ""))
            google_support = self._parse_google_support(proxy_dict.get("google", ""))
            https_support = self._parse_https_support(proxy_dict.get("https", ""))
            last_checked = proxy_dict.get("last_checked", "")
            
            # 更新統計
            self._update_distribution_stats(country_code, anonymity)
            
            # 創建ProxyData對象
            proxy_data = ProxyData(
                ip=ip,
                port=port,
                protocol="https" if https_support else "http",
                anonymity=anonymity,
                country=country_code,
                city="unknown",  # 可以從國家信息中進一步提取
                source=self.name,
                source_url=self.base_url,
                location=f"{country} ({country_code})" if country else country_code,
                response_speed=None,  # 將在驗證階段設置
                verification_time=self._parse_last_checked(last_checked),
                quality_score=0.0,  # 將在驗證階段設置
                last_verified=None,
                response_time=None,
                metadata={
                    "page_type": page_type,
                    "google_support": google_support,
                    "https_support": https_support,
                    "country_code": country_code,
                    "original_anonymity": proxy_dict.get("anonymity", ""),
                    "original_last_checked": last_checked,
                    "crawl_timestamp": datetime.utcnow().isoformat()
                }
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
        
        if "elite" in anonymity or "high" in anonymity or "高匿" in anonymity:
            return "high"
        elif "anonymous" in anonymity or "匿名" in anonymity:
            return "medium"
        elif "transparent" in anonymity or "透明" in anonymity:
            return "low"
        else:
            return "unknown"
    
    def _parse_google_support(self, google_str: str) -> bool:
        """解析Google支持"""
        return "yes" in google_str.lower() or "true" in google_str.lower()
    
    def _parse_https_support(self, https_str: str) -> bool:
        """解析HTTPS支持"""
        return "yes" in https_str.lower() or "true" in https_str.lower()
    
    def _parse_last_checked(self, last_checked_str: str) -> Optional[datetime]:
        """解析最後檢查時間"""
        if not last_checked_str:
            return None
        
        try:
            # 處理相對時間（如 "1 minute ago"）
            time_str = last_checked_str.strip().lower()
            now = datetime.utcnow()
            
            if "second" in time_str or "秒" in time_str:
                seconds = int(re.sub(r'[^0-9]', '', time_str))
                return now - timedelta(seconds=seconds)
            elif "minute" in time_str or "分鐘" in time_str or "分钟" in time_str:
                minutes = int(re.sub(r'[^0-9]', '', time_str))
                return now - timedelta(minutes=minutes)
            elif "hour" in time_str or "小時" in time_str:
                hours = int(re.sub(r'[^0-9]', '', time_str))
                return now - timedelta(hours=hours)
            elif "day" in time_str or "天" in time_str:
                days = int(re.sub(r'[^0-9]', '', time_str))
                return now - timedelta(days=days)
            else:
                # 嘗試解析絕對時間
                return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                
        except (ValueError, TypeError):
            return None
    
    def _update_distribution_stats(self, country_code: str, anonymity: str):
        """更新分佈統計"""
        # 國家分佈
        if country_code:
            self.stats["country_distribution"][country_code] = self.stats["country_distribution"].get(country_code, 0) + 1
        
        # 匿名度分佈
        if anonymity:
            self.stats["anonymity_distribution"][anonymity] = self.stats["anonymity_distribution"].get(anonymity, 0) + 1
    
    def _apply_filters(self, proxies: List[ProxyData]) -> List[ProxyData]:
        """
        應用篩選條件
        
        Args:
            proxies: 代理列表
            
        Returns:
            List[ProxyData]: 篩選後的代理列表
        """
        filtered_proxies = proxies
        
        # 國家篩選
        if self.country_filter:
            filtered_proxies = [p for p in filtered_proxies if p.country in self.country_filter]
        
        # 匿名度篩選
        if self.anonymity_filter:
            filtered_proxies = [p for p in filtered_proxies if p.anonymity in self.anonymity_filter]
        
        # HTTPS篩選
        if self.https_filter is not None:
            if self.https_filter:
                filtered_proxies = [p for p in filtered_proxies if p.protocol == "https"]
            else:
                filtered_proxies = [p for p in filtered_proxies if p.protocol == "http"]
        
        self.logger.info(f"應用篩選條件後: {len(filtered_proxies)}/{len(proxies)} 個代理")
        
        return filtered_proxies
    
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
        semaphore = asyncio.Semaphore(10)  # 適中的併發數
        
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