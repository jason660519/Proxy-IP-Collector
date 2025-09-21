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
from urllib.parse import urljoin, urlencode

from app.etl.extractors.base import WebScrapingExtractor, ProxyData, ExtractResult
from app.utils.html_parser import ProxyDataExtractor
from app.core.logging import get_logger
from app.utils.user_agents import get_random_user_agent
from app.utils.proxy_validator import ProxyValidator

logger = get_logger(__name__)


class FreeProxyListNetEnhancedExtractor(WebScrapingExtractor):
    """
    free-proxy-list.net 增強版專屬爬蟲程式
    
    功能特點：
    - 智能請求標頭輪換
    - 高級反爬蟲機制處理
    - 自動化IP驗證與評分
    - 智能速率控制
    - 完整的錯誤處理和重試機制
    - 支持多種代理類型和篩選條件
    - 高級HTML解析和數據提取
    - 支持表格數據提取和API端點
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
        self.api_url = config.get("api_url", "https://free-proxy-list.net/api/v1/get")
        self.https_url = config.get("https_url", "https://free-proxy-list.net/https-proxy-list.html")
        self.socks_url = config.get("socks_url", "https://free-proxy-list.net/socks-proxy-list.html")
        self.max_pages = config.get("max_pages", 3)
        
        # 篩選配置
        self.anonymity_filter = config.get("anonymity_filter", ["elite proxy", "anonymous"])
        self.country_filter = config.get("country_filter", [])  # 空列表表示所有國家
        self.https_only = config.get("https_only", False)
        
        # 反爬蟲配置
        self.enable_anti_bot = config.get("enable_anti_bot", True)
        self.min_delay = config.get("min_delay", 2.0)
        self.max_delay = config.get("max_delay", 5.0)
        self.retry_attempts = config.get("retry_attempts", 3)
        self.enable_session_rotation = config.get("enable_session_rotation", True)
        self.enable_rate_limiting = config.get("enable_rate_limiting", True)
        
        # 驗證配置
        self.enable_validation = config.get("enable_validation", True)
        self.validation_timeout = config.get("validation_timeout", 10)
        self.min_quality_score = config.get("min_quality_score", 0.6)
        
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
            "pagination": "div.pagination",
            "next_page": "a.next",
            "current_page": "span.current",
            "table_headers": "table#proxylisttable thead tr th",
            "proxy_count": "div#proxy-count",
            "update_time": "div#last-update"
        }
        
        # 請求標頭池
        self.header_pool = self._build_header_pool()
        
        # 代理驗證器
        self.validator = ProxyValidator() if self.enable_validation else None
        
        # 統計數據
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "proxies_found": 0,
            "proxies_validated": 0,
            "high_quality_proxies": 0,
            "session_rotations": 0,
            "rate_limit_hits": 0,
            "captcha_encounters": 0,
            "api_requests": 0,
            "web_requests": 0,
            "https_requests": 0,
            "socks_requests": 0,
            "errors": [],
            "anonymity_distribution": {},
            "country_distribution": {},
            "https_distribution": {},
            "google_distribution": {},
            "pages_crawled": 0,
            "average_response_time": 0.0
        }
        
        # 會話管理
        self.session_cookies = {}
        self.last_request_time = None
        self.success_rate = 1.0
        self.request_count = 0
        self.success_count = 0
        self.rate_limit_delay = 0
        self.session_start_time = None
    
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
                "accept_language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
                "accept_encoding": "gzip, deflate, br",
                "cache_control": "max-age=0"
            },
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "accept_language": "en-US,en;q=0.5,zh-CN;q=0.4,zh;q=0.3",
                "accept_encoding": "gzip, deflate, br",
                "cache_control": "no-cache"
            },
            {
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "accept_language": "en-US,en;q=0.9",
                "accept_encoding": "gzip, deflate, br"
            },
            {
                "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
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
                "DNT": "1",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"'
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
            headers["Referer"] = "https://free-proxy-list.net/"
        
        return headers
    
    def _generate_random_ip(self) -> str:
        """生成隨機IP地址"""
        return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
    
    def _calculate_delay(self) -> float:
        """
        計算請求延遲時間，根據成功率和網站特性動態調整
        
        Returns:
            float: 延遲時間（秒）
        """
        if not self.enable_anti_bot:
            return 0.5
        
        # 基礎延遲
        base_delay = random.uniform(self.min_delay, self.max_delay)
        
        # 根據成功率調整
        if self.success_rate < 0.3:
            base_delay *= 2.0
        elif self.success_rate < 0.6:
            base_delay *= 1.5
        elif self.success_rate < 0.8:
            base_delay *= 1.2
        
        # 根據速率限制調整
        if self.rate_limit_delay > 0:
            base_delay += self.rate_limit_delay
            self.rate_limit_delay = max(0, self.rate_limit_delay - 1)
        
        return base_delay
    
    def _detect_anti_bot_measures(self, response_text: str) -> Dict[str, Any]:
        """
        檢測反爬蟲措施
        
        Args:
            response_text: 響應文本
            
        Returns:
            Dict[str, Any]: 檢測結果
        """
        result = {
            "rate_limited": False,
            "captcha_detected": False,
            "blocked": False,
            "cloudflare": False,
            "js_challenge": False,
            "redirect_detected": False
        }
        
        response_lower = response_text.lower()
        
        # 速率限制檢測
        rate_limit_indicators = [
            "rate limit",
            "too many requests",
            "429",
            "quota exceeded",
            "limit exceeded",
            "請求過於頻繁",
            "超過限制",
            "you are being rate limited"
        ]
        
        for indicator in rate_limit_indicators:
            if indicator in response_lower:
                result["rate_limited"] = True
                self.stats["rate_limit_hits"] += 1
                self.rate_limit_delay = 8  # 增加8秒延遲
                break
        
        # 驗證碼檢測
        captcha_indicators = [
            "captcha",
            "recaptcha",
            "hcaptcha",
            "驗證碼",
            "verification code",
            "prove you are human"
        ]
        
        for indicator in captcha_indicators:
            if indicator in response_lower:
                result["captcha_detected"] = True
                self.stats["captcha_encounters"] += 1
                break
        
        # Cloudflare檢測
        if "cloudflare" in response_lower or "cf-ray" in response_lower:
            result["cloudflare"] = True
        
        # JavaScript挑戰檢測
        js_challenge_indicators = [
            "checking your browser",
            "please wait",
            "javascript required",
            "enable javascript",
            "just a moment"
        ]
        
        for indicator in js_challenge_indicators:
            if indicator in response_lower:
                result["js_challenge"] = True
                break
        
        # 重定向檢測
        redirect_indicators = [
            "redirecting",
            "please wait while we redirect",
            "meta http-equiv=\"refresh\"",
            "window.location"
        ]
        
        for indicator in redirect_indicators:
            if indicator in response_lower:
                result["redirect_detected"] = True
                break
        
        # 完全阻塞檢測
        blocked_indicators = [
            "access denied",
            "forbidden",
            "blocked",
            "403",
            "your ip has been blocked",
            "banned"
        ]
        
        for indicator in blocked_indicators:
            if indicator in response_lower:
                result["blocked"] = True
                break
        
        return result
    
    def _update_success_rate(self, success: bool):
        """更新成功率統計"""
        self.request_count += 1
        if success:
            self.success_count += 1
        
        # 計算成功率（使用滑動窗口）
        self.success_rate = self.success_count / self.request_count if self.request_count > 0 else 1.0
    
    async def extract(self) -> ExtractResult:
        """
        執行增強版代理數據提取
        
        Returns:
            ExtractResult: 提取結果
        """
        self.logger.info(f"開始執行free-proxy-list.net增強版爬取，最大頁數: {self.max_pages}")
        
        start_time = datetime.utcnow()
        all_proxies = []
        
        try:
            # 優先嘗試主頁面
            main_proxies = await self._extract_from_main_page()
            if main_proxies:
                all_proxies.extend(main_proxies)
                self.logger.info(f"從主頁面獲取 {len(main_proxies)} 個代理")
            
            # 如果HTTPS代理啟用，嘗試HTTPS頁面
            if self.https_only or len(all_proxies) < 20:
                https_proxies = await self._extract_from_https_page()
                if https_proxies:
                    all_proxies.extend(https_proxies)
                    self.logger.info(f"從HTTPS頁面獲取 {len(https_proxies)} 個代理")
            
            # 嘗試SOCKS代理頁面
            if len(all_proxies) < 30:
                socks_proxies = await self._extract_from_socks_page()
                if socks_proxies:
                    all_proxies.extend(socks_proxies)
                    self.logger.info(f"從SOCKS頁面獲取 {len(socks_proxies)} 個代理")
            
            # 嘗試API端點
            if len(all_proxies) < 40:
                api_proxies = await self._extract_from_api()
                if api_proxies:
                    all_proxies.extend(api_proxies)
                    self.logger.info(f"從API端點獲取 {len(api_proxies)} 個代理")
            
            # 數據去重
            unique_proxies = self._deduplicate_proxies(all_proxies)
            
            # 應用篩選條件
            final_proxies = self._apply_filters(unique_proxies)
            
            # 自動化驗證與評分
            validated_proxies = []
            if self.enable_validation and final_proxies:
                self.logger.info(f"開始驗證 {len(final_proxies)} 個代理...")
                validated_proxies = await self._validate_and_score_proxies(final_proxies)
                self.stats["proxies_validated"] = len(validated_proxies)
                self.stats["high_quality_proxies"] = len([p for p in validated_proxies if p.quality_score >= self.min_quality_score])
            else:
                validated_proxies = final_proxies
            
            # 構建結果
            result = ExtractResult(
                source=self.name,
                proxies=[proxy.to_dict() for proxy in validated_proxies],
                metadata={
                    "crawl_stats": self.stats,
                    "total_requests": self.stats["total_requests"],
                    "successful_requests": self.stats["successful_requests"],
                    "failed_requests": self.stats["failed_requests"],
                    "proxies_found": self.stats["proxies_found"],
                    "proxies_validated": self.stats["proxies_validated"],
                    "high_quality_proxies": self.stats["high_quality_proxies"],
                    "pages_crawled": self.stats["pages_crawled"],
                    "session_rotations": self.stats["session_rotations"],
                    "rate_limit_hits": self.stats["rate_limit_hits"],
                    "captcha_encounters": self.stats["captcha_encounters"],
                    "api_requests": self.stats["api_requests"],
                    "web_requests": self.stats["web_requests"],
                    "https_requests": self.stats["https_requests"],
                    "socks_requests": self.stats["socks_requests"],
                    "anonymity_distribution": self.stats["anonymity_distribution"],
                    "country_distribution": self.stats["country_distribution"],
                    "https_distribution": self.stats["https_distribution"],
                    "google_distribution": self.stats["google_distribution"],
                    "validation_enabled": self.enable_validation,
                    "anti_bot_enabled": self.enable_anti_bot,
                    "session_rotation_enabled": self.enable_session_rotation,
                    "success_rate": self.success_rate,
                    "start_time": start_time,
                    "end_time": datetime.utcnow(),
                    "duration_seconds": (datetime.utcnow() - start_time).total_seconds()
                },
                success=True,
                timestamp=start_time,
            )
            
            self.logger.info(
                f"free-proxy-list.net增強版爬取完成: "
                f"總請求 {self.stats['total_requests']}, "
                f"成功 {self.stats['successful_requests']}, "
                f"失敗 {self.stats['failed_requests']}, "
                f"找到代理 {self.stats['proxies_found']}, "
                f"驗證通過 {self.stats['proxies_validated']}, "
                f"高質量代理 {self.stats['high_quality_proxies']}, "
                f"爬取頁數 {self.stats['pages_crawled']}, "
                f"會話輪換 {self.stats['session_rotations']}, "
                f"速率限制命中 {self.stats['rate_limit_hits']}, "
                f"驗證碼遭遇 {self.stats['captcha_encounters']}, "
                f"API請求 {self.stats['api_requests']}, "
                f"網頁請求 {self.stats['web_requests']}, "
                f"HTTPS請求 {self.stats['https_requests']}, "
                f"SOCKS請求 {self.stats['socks_requests']}"
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
    
    async def _extract_from_main_page(self) -> List[ProxyData]:
        """
        從主頁面提取代理數據
        
        Returns:
            List[ProxyData]: 代理數據列表
        """
        self.logger.info("開始從主頁面提取代理數據...")
        all_proxies = []
        
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
                
                # 爬取主頁面
                self.logger.debug(f"爬取主頁面，嘗試 {attempt + 1}: {self.base_url}")
                
                html_content = await self.fetch_with_retry(self.base_url, headers=headers)
                
                if not html_content:
                    raise Exception("獲取主頁面內容為空")
                
                # 檢測反爬蟲措施
                anti_bot_result = self._detect_anti_bot_measures(html_content)
                
                if anti_bot_result["rate_limited"]:
                    if attempt < self.retry_attempts - 1:
                        await asyncio.sleep(self._calculate_delay() * 2)
                        continue
                    else:
                        return []
                
                if anti_bot_result["captcha_detected"] or anti_bot_result["blocked"]:
                    self.logger.warning(f"檢測到反爬蟲措施: {anti_bot_result}")
                    if attempt < self.retry_attempts - 1:
                        await asyncio.sleep(self._calculate_delay() * 3)
                        continue
                    else:
                        return []
                
                # 解析主頁面數據
                proxies = self._parse_html_enhanced(html_content, "main_page")
                
                # 更新統計
                self.stats["total_requests"] += 1
                self.stats["successful_requests"] += 1
                self.stats["web_requests"] += 1
                self.stats["proxies_found"] += len(proxies)
                self.stats["pages_crawled"] += 1
                
                self._update_success_rate(True)
                
                self.logger.debug(f"主頁面爬取成功，找到 {len(proxies)} 個代理")
                
                return proxies
                
            except Exception as e:
                self.logger.warning(f"主頁面爬取失敗 (嘗試 {attempt + 1}): {e}")
                self.stats["failed_requests"] += 1
                self._update_success_rate(False)
                
                if attempt == self.retry_attempts - 1:
                    self.stats["errors"].append(f"主頁面: {str(e)}")
                    return []
                
                # 指數退避重試
                await asyncio.sleep(2 ** attempt)
        
        return []
    
    async def _extract_from_https_page(self) -> List[ProxyData]:
        """
        從HTTPS代理頁面提取代理數據
        
        Returns:
            List[ProxyData]: 代理數據列表
        """
        self.logger.info("開始從HTTPS代理頁面提取代理數據...")
        
        for attempt in range(self.retry_attempts):
            try:
                # 會話輪換
                if self.enable_session_rotation and attempt > 0:
                    self._rotate_session()
                
                # 計算延遲
                delay = self._calculate_delay()
                if attempt > 0:
                    delay *= (attempt + 1)
                
                await asyncio.sleep(delay)
                
                # 獲取隨機請求標頭
                headers = self._get_random_headers()
                
                # 爬取HTTPS頁面
                self.logger.debug(f"爬取HTTPS頁面，嘗試 {attempt + 1}: {self.https_url}")
                
                html_content = await self.fetch_with_retry(self.https_url, headers=headers)
                
                if not html_content:
                    raise Exception("獲取HTTPS頁面內容為空")
                
                # 檢測反爬蟲措施
                anti_bot_result = self._detect_anti_bot_measures(html_content)
                
                if anti_bot_result["rate_limited"] or anti_bot_result["blocked"]:
                    self.logger.warning(f"HTTPS頁面檢測到限制: {anti_bot_result}")
                    if attempt < self.retry_attempts - 1:
                        await asyncio.sleep(self._calculate_delay() * 2)
                        continue
                    else:
                        return []
                
                # 解析HTTPS頁面數據
                proxies = self._parse_html_enhanced(html_content, "https_page")
                
                # 更新統計
                self.stats["total_requests"] += 1
                self.stats["successful_requests"] += 1
                self.stats["https_requests"] += 1
                self.stats["proxies_found"] += len(proxies)
                self.stats["pages_crawled"] += 1
                
                self._update_success_rate(True)
                
                self.logger.debug(f"HTTPS頁面爬取成功，找到 {len(proxies)} 個代理")
                
                return proxies
                
            except Exception as e:
                self.logger.warning(f"HTTPS頁面爬取失敗 (嘗試 {attempt + 1}): {e}")
                self.stats["failed_requests"] += 1
                self._update_success_rate(False)
                
                if attempt == self.retry_attempts - 1:
                    self.stats["errors"].append(f"HTTPS頁面: {str(e)}")
                    return []
                
                await asyncio.sleep(2 ** attempt)
        
        return []
    
    async def _extract_from_socks_page(self) -> List[ProxyData]:
        """
        從SOCKS代理頁面提取代理數據
        
        Returns:
            List[ProxyData]: 代理數據列表
        """
        self.logger.info("開始從SOCKS代理頁面提取代理數據...")
        
        for attempt in range(self.retry_attempts):
            try:
                # 會話輪換
                if self.enable_session_rotation and attempt > 0:
                    self._rotate_session()
                
                # 計算延遲
                delay = self._calculate_delay()
                if attempt > 0:
                    delay *= (attempt + 1)
                
                await asyncio.sleep(delay)
                
                # 獲取隨機請求標頭
                headers = self._get_random_headers()
                
                # 爬取SOCKS頁面
                self.logger.debug(f"爬取SOCKS頁面，嘗試 {attempt + 1}: {self.socks_url}")
                
                html_content = await self.fetch_with_retry(self.socks_url, headers=headers)
                
                if not html_content:
                    raise Exception("獲取SOCKS頁面內容為空")
                
                # 檢測反爬蟲措施
                anti_bot_result = self._detect_anti_bot_measures(html_content)
                
                if anti_bot_result["rate_limited"] or anti_bot_result["blocked"]:
                    self.logger.warning(f"SOCKS頁面檢測到限制: {anti_bot_result}")
                    if attempt < self.retry_attempts - 1:
                        await asyncio.sleep(self._calculate_delay() * 2)
                        continue
                    else:
                        return []
                
                # 解析SOCKS頁面數據
                proxies = self._parse_html_enhanced(html_content, "socks_page")
                
                # 更新統計
                self.stats["total_requests"] += 1
                self.stats["successful_requests"] += 1
                self.stats["socks_requests"] += 1
                self.stats["proxies_found"] += len(proxies)
                self.stats["pages_crawled"] += 1
                
                self._update_success_rate(True)
                
                self.logger.debug(f"SOCKS頁面爬取成功，找到 {len(proxies)} 個代理")
                
                return proxies
                
            except Exception as e:
                self.logger.warning(f"SOCKS頁面爬取失敗 (嘗試 {attempt + 1}): {e}")
                self.stats["failed_requests"] += 1
                self._update_success_rate(False)
                
                if attempt == self.retry_attempts - 1:
                    self.stats["errors"].append(f"SOCKS頁面: {str(e)}")
                    return []
                
                await asyncio.sleep(2 ** attempt)
        
        return []
    
    async def _extract_from_api(self) -> List[ProxyData]:
        """
        從API端點提取代理數據
        
        Returns:
            List[ProxyData]: 代理數據列表
        """
        self.logger.info("開始從API端點提取代理數據...")
        all_proxies = []
        
        # API端點參數
        api_params = {
            "type": "getproxies",
            "country": "all",
            "anonymity": "all",
            "format": "json"
        }
        
        for attempt in range(self.retry_attempts):
            try:
                # 會話輪換
                if self.enable_session_rotation and attempt > 0:
                    self._rotate_session()
                
                # 計算延遲
                delay = self._calculate_delay()
                if attempt > 0:
                    delay *= (attempt + 1)
                
                await asyncio.sleep(delay)
                
                # 獲取隨機請求標頭
                headers = self._get_random_headers()
                
                # 構建API URL
                params = api_params.copy()
                api_url = f"{self.api_url}?{urlencode(params)}"
                
                self.logger.debug(f"請求API端點，嘗試 {attempt + 1}: {api_url}")
                
                # 發送請求
                response = await self.fetch_with_retry(api_url, headers=headers)
                
                if not response:
                    raise Exception("API請求返回空內容")
                
                # 檢測反爬蟲措施
                anti_bot_result = self._detect_anti_bot_measures(response)
                
                if anti_bot_result["rate_limited"] or anti_bot_result["blocked"]:
                    self.logger.warning(f"API請求檢測到限制: {anti_bot_result}")
                    if attempt < self.retry_attempts - 1:
                        await asyncio.sleep(self._calculate_delay() * 2)
                        continue
                    else:
                        return []
                
                # 解析API響應
                proxies = self._parse_api_response(response)
                
                # 更新統計
                self.stats["total_requests"] += 1
                self.stats["successful_requests"] += 1
                self.stats["api_requests"] += 1
                self.stats["proxies_found"] += len(proxies)
                
                self._update_success_rate(True)
                
                self.logger.debug(f"API端點提取成功，找到 {len(proxies)} 個代理")
                
                return proxies
                
            except Exception as e:
                self.logger.warning(f"API端點提取失敗 (嘗試 {attempt + 1}): {e}")
                self.stats["failed_requests"] += 1
                self._update_success_rate(False)
                
                if attempt == self.retry_attempts - 1:
                    self.stats["errors"].append(f"API端點: {str(e)}")
                    return []
                
                await asyncio.sleep(2 ** attempt)
        
        return []
    
    def _parse_api_response(self, response_text: str) -> List[ProxyData]:
        """
        解析API響應
        
        Args:
            response_text: API響應文本
            
        Returns:
            List[ProxyData]: 代理數據列表
        """
        try:
            # 嘗試解析JSON
            try:
                data = json.loads(response_text)
                if isinstance(data, list):
                    return self._parse_api_json_data(data)
            except json.JSONDecodeError:
                # 如果不是JSON，嘗試解析為文本格式
                return self._parse_api_text_data(response_text)
            
            return []
            
        except Exception as e:
            self.logger.error(f"解析API響應失敗: {e}")
            return []
    
    def _parse_api_json_data(self, data: List[Dict]) -> List[ProxyData]:
        """解析API JSON數據"""
        proxies = []
        
        for item in data:
            try:
                proxy_data = self._extract_proxy_from_api_item(item)
                if proxy_data:
                    proxies.append(proxy_data)
            except Exception as e:
                self.logger.debug(f"解析API項目失敗: {e}")
                continue
        
        return proxies
    
    def _parse_api_text_data(self, response_text: str) -> List[ProxyData]:
        """解析API文本數據"""
        proxies = []
        
        # 按行解析
        lines = response_text.strip().split('\n')
        
        for line in lines:
            try:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 嘗試不同的分隔符
                parts = re.split(r'[\s\t,;|]+', line)
                
                if len(parts) >= 2:
                    ip = parts[0].strip()
                    port = parts[1].strip()
                    
                    # 清理端口
                    port_match = re.search(r'\d+', port)
                    if port_match:
                        port = int(port_match.group())
                    else:
                        continue
                    
                    # 創建代理數據
                    proxy_data = ProxyData(
                        ip=ip,
                        port=port,
                        protocol="http",
                        anonymity="unknown",
                        country="unknown",
                        city="unknown",
                        source=self.name,
                        source_url=self.base_url,
                        location="unknown",
                        response_speed=None,
                        verification_time=datetime.utcnow(),
                        quality_score=0.0,
                        last_verified=None,
                        response_time=None,
                        metadata={
                            "extraction_method": "api_text",
                            "crawl_timestamp": datetime.utcnow().isoformat()
                        }
                    )
                    
                    proxies.append(proxy_data)
                    
            except Exception as e:
                self.logger.debug(f"解析API文本行失敗: {e}")
                continue
        
        return proxies
    
    def _extract_proxy_from_api_item(self, item: Dict) -> Optional[ProxyData]:
        """從API項目提取代理數據"""
        try:
            # 提取基本字段
            ip = item.get("ip", item.get("IP", "")).strip()
            port = item.get("port", item.get("PORT", ""))
            
            if not ip or not port:
                return None
            
            # 清理端口
            if isinstance(port, str):
                port_match = re.search(r'\d+', port)
                port = int(port_match.group()) if port_match else None
            else:
                port = int(port)
            
            if not port:
                return None
            
            # 提取其他字段
            country = item.get("country", item.get("COUNTRY", "")).strip()
            country_code = item.get("country_code", item.get("COUNTRY_CODE", "")).strip()
            anonymity = self._normalize_anonymity_level(item.get("anonymity", item.get("ANONYMITY", "")))
            https = item.get("https", item.get("HTTPS", "")).strip().lower() == "yes"
            google = item.get("google", item.get("GOOGLE", "")).strip().lower() == "yes"
            last_checked = item.get("last_checked", item.get("LAST_CHECKED", ""))
            
            # 確定協議
            protocol = "https" if https else "http"
            
            # 創建代理數據
            proxy_data = ProxyData(
                ip=ip,
                port=port,
                protocol=protocol,
                anonymity=anonymity,
                country=self._extract_country_code(country_code or country),
                city="unknown",
                source=self.name,
                source_url=self.base_url,
                location=country or "unknown",
                response_speed=None,
                verification_time=self._parse_last_checked(last_checked),
                quality_score=0.0,
                last_verified=None,
                response_time=None,
                metadata={
                    "extraction_method": "api_json",
                    "https": https,
                    "google": google,
                    "country_code": country_code,
                    "original_data": item,
                    "crawl_timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return proxy_data
            
        except Exception as e:
            self.logger.debug(f"提取API代理數據失敗: {e}")
            return None
    
    def _parse_html_enhanced(self, html_content: str, page_type: str) -> List[ProxyData]:
        """增強版HTML解析"""
        try:
            extractor = ProxyDataExtractor(html_content)
            
            # 從表格中提取數據
            proxies_data = extractor.extract_proxies_from_table(
                self.selectors["proxy_table"],
                {
                    "ip": self.selectors["ip"],
                    "port": self.selectors["port"],
                    "country": self.selectors["country"],
                    "country_code": self.selectors["country_code"],
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
        """增強版代理數據轉換"""
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
            country = proxy_dict.get("country", "").strip()
            country_code = proxy_dict.get("country_code", "").strip()
            anonymity = self._normalize_anonymity_level(proxy_dict.get("anonymity", ""))
            https = self._normalize_boolean(proxy_dict.get("https", ""))
            google = self._normalize_boolean(proxy_dict.get("google", ""))
            last_checked = proxy_dict.get("last_checked", "")
            
            # 確定協議
            protocol = "https" if https else "http"
            
            # 更新統計
            self._update_distribution_stats(anonymity, country_code or country, https, google)
            
            # 創建ProxyData對象
            proxy_data = ProxyData(
                ip=ip,
                port=port,
                protocol=protocol,
                anonymity=anonymity,
                country=self._extract_country_code(country_code or country),
                city="unknown",
                source=self.name,
                source_url=self.base_url,
                location=country or "unknown",
                response_speed=None,
                verification_time=self._parse_last_checked(last_checked),
                quality_score=0.0,
                last_verified=None,
                response_time=None,
                metadata={
                    "page_type": page_type,
                    "https": https,
                    "google": google,
                    "country_code": country_code,
                    "original_anonymity": proxy_dict.get("anonymity", ""),
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
    
    def _normalize_anonymity_level(self, anonymity_str: str) -> str:
        """標準化匿名度級別"""
        anonymity = anonymity_str.strip().lower()
        
        if "elite proxy" in anonymity or "high" in anonymity or "高匿" in anonymity:
            return "high"
        elif "anonymous" in anonymity or "匿名" in anonymity:
            return "medium"
        elif "transparent" in anonymity or "透明" in anonymity:
            return "low"
        else:
            return "unknown"
    
    def _normalize_boolean(self, value_str: str) -> bool:
        """標準化布爾值"""
        return value_str.strip().lower() in ["yes", "true", "1", "是", "有"]
    
    def _extract_country_code(self, country_str: str) -> str:
        """從國家字符串中提取國家代碼"""
        if not country_str:
            return "unknown"
        
        # 嘗試從括號中提取國家代碼
        code_match = re.search(r'\(([A-Z]{2})\)', country_str)
        if code_match:
            return code_match.group(1)
        
        # 嘗試從字符串開頭提取
        words = country_str.split()
        for word in words:
            if len(word) == 2 and word.isupper():
                return word
        
        return "unknown"
    
    def _parse_last_checked(self, last_checked_str: str) -> Optional[datetime]:
        """解析最後檢查時間"""
        if not last_checked_str:
            return None
        
        try:
            # 處理相對時間
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
                return now  # 默認當前時間
                
        except (ValueError, TypeError):
            return None
    
    def _update_distribution_stats(self, anonymity: str, country: str, https: bool, google: bool):
        """更新分佈統計"""
        # 匿名度分佈
        if anonymity:
            self.stats["anonymity_distribution"][anonymity] = self.stats["anonymity_distribution"].get(anonymity, 0) + 1
        
        # 國家分佈
        if country:
            self.stats["country_distribution"][country] = self.stats["country_distribution"].get(country, 0) + 1
        
        # HTTPS分佈
        https_key = "https" if https else "http"
        self.stats["https_distribution"][https_key] = self.stats["https_distribution"].get(https_key, 0) + 1
        
        # Google分佈
        google_key = "google" if google else "no_google"
        self.stats["google_distribution"][google_key] = self.stats["google_distribution"].get(google_key, 0) + 1
    
    def _apply_filters(self, proxies: List[ProxyData]) -> List[ProxyData]:
        """
        應用篩選條件
        
        Args:
            proxies: 代理列表
            
        Returns:
            List[ProxyData]: 篩選後的代理列表
        """
        filtered_proxies = proxies
        
        # 匿名度篩選
        if self.anonymity_filter:
            filtered_proxies = [p for p in filtered_proxies if p.anonymity in self.anonymity_filter]
        
        # 國家篩選
        if self.country_filter:
            filtered_proxies = [p for p in filtered_proxies if p.country in self.country_filter]
        
        # HTTPS篩選
        if self.https_only:
            filtered_proxies = [p for p in filtered_proxies if p.protocol == "https"]
        
        self.logger.info(f"應用篩選條件後: {len(filtered_proxies)}/{len(proxies)} 個代理")
        
        return filtered_proxies
    
    def _rotate_session(self):
        """輪換會話"""
        self.stats["session_rotations"] += 1
        self.logger.debug(f"會話輪換 #{self.stats['session_rotations']}")
        
        # 清除會話Cookie
        self.session_cookies.clear()
        
        # 重置會話開始時間
        self.session_start_time = datetime.utcnow()
    
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
        semaphore = asyncio.Semaphore(6)  # 適中的併發數
        
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