"""
spys.one 爬取器 (使用 Playwright)
"""
from typing import List, Dict, Any, Optional
from app.etl.extractors.base import BaseExtractor, ProxyData, ExtractResult
from app.core.logging import get_logger
import asyncio
import re
from datetime import datetime

logger = get_logger(__name__)


class SpysExtractor(BaseExtractor):
    """spys.one 網站爬取器 (使用 Playwright 處理 JavaScript)"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化spys.one爬取器
        
        Args:
            config: 配置字典
        """
        super().__init__("spys.one", config)
        self.base_url = config.get("base_url", "http://spys.one/free-proxy-list/")
        self.use_playwright = config.get("use_playwright", True)
        self.wait_for_selector = config.get("wait_for_selector", "table table")
        self.container_selector = config.get("container_selector", "table table tr")
        self.skip_rows = config.get("skip_rows", 2)
        self.ip_selector = config.get("ip_selector", "td:nth-child(1)")
        self.port_selector = config.get("port_selector", "td:nth-child(2)")
        self.anonymity_selector = config.get("anonymity_selector", "td:nth-child(3)")
        self.location_selector = config.get("location_selector", "td:nth-child(5)")
        
        # Playwright相關
        self.playwright = None
        self.browser = None
        self.context = None
    
    def get_required_config_fields(self) -> List[str]:
        return ["base_url"]
    
    async def __aenter__(self):
        """異步上下文管理器進入"""
        if self.use_playwright:
            try:
                from playwright.async_api import async_playwright
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-web-security'
                    ]
                )
                self.context = await self.browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            except ImportError:
                self.logger.error("Playwright未安裝，請運行: pip install playwright")
                raise
            except Exception as e:
                self.logger.error(f"初始化Playwright失敗: {e}")
                raise
        else:
            await super().__aenter__()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出"""
        if self.use_playwright and self.browser:
            try:
                await self.browser.close()
            except Exception as e:
                self.logger.error(f"關閉瀏覽器失敗: {e}")
            
            if self.playwright:
                try:
                    await self.playwright.stop()
                except Exception as e:
                    self.logger.error(f"停止Playwright失敗: {e}")
        else:
            await super().__aexit__(exc_type, exc_val, exc_tb)
    
    async def extract(self) -> ExtractResult:
        """
        提取代理數據
        
        Returns:
            ExtractResult: 提取結果
        """
        self.logger.info(f"開始從spys.one提取代理數據，使用Playwright: {self.use_playwright}")
        
        start_time = datetime.utcnow()
        
        try:
            if self.use_playwright:
                proxies = await self._extract_with_playwright()
            else:
                proxies = await self._extract_with_http()
            
            # 去重
            unique_proxies = self._deduplicate_proxies(proxies)
            
            result = ExtractResult(
                source=self.name,
                proxies=[proxy.to_dict() for proxy in unique_proxies],
                metadata={
                    "base_url": self.base_url,
                    "total_found": len(proxies),
                    "unique_found": len(unique_proxies),
                    "use_playwright": self.use_playwright,
                    "start_time": start_time,
                    "end_time": datetime.utcnow(),
                    "extraction_method": "playwright_js_parsing" if self.use_playwright else "html_parsing"
                },
                success=True,
                timestamp=start_time,
            )
            
            self.logger.info(f"spys.one爬取完成，總共找到 {len(proxies)} 個代理，去重後 {len(unique_proxies)} 個")
            return result
            
        except Exception as e:
            self.logger.error(f"spys.one爬取失敗: {e}")
            return ExtractResult(
                source=self.name,
                proxies=[],
                metadata={"start_time": start_time},
                success=False,
                error_message=str(e),
                timestamp=start_time,
            )
    
    async def _extract_with_playwright(self) -> List[ProxyData]:
        """使用Playwright提取數據"""
        proxies = []
        
        try:
            page = await self.context.new_page()
            
            # 設置超時
            page.set_default_timeout(30000)
            
            # 導航到頁面
            await page.goto(self.base_url, wait_until="networkidle")
            
            # 等待表格加載
            await page.wait_for_selector(self.wait_for_selector, timeout=10000)
            
            # 等待JavaScript執行
            await asyncio.sleep(2)
            
            # 提取表格數據
            table_data = await page.evaluate(self._extract_table_data_script())
            
            # 解析數據
            for row_data in table_data:
                proxy_obj = self._convert_to_proxy_data(row_data)
                if proxy_obj:
                    proxies.append(proxy_obj)
            
            await page.close()
            
        except Exception as e:
            self.logger.error(f"Playwright提取失敗: {e}")
            raise
        
        return proxies
    
    async def _extract_with_http(self) -> List[ProxyData]:
        """使用HTTP提取數據（備用方案）"""
        try:
            html_content = await self.fetch_with_retry(self.base_url)
            return self._parse_html(html_content)
        except Exception as e:
            self.logger.error(f"HTTP提取失敗: {e}")
            return []
    
    def _extract_table_data_script(self) -> str:
        """返回用於提取表格數據的JavaScript代碼"""
        return """
        () => {
            const rows = document.querySelectorAll('table table tr');
            const data = [];
            
            for (let i = 2; i < rows.length; i++) { // 跳過前兩行
                const row = rows[i];
                const cells = row.querySelectorAll('td');
                
                if (cells.length >= 5) {
                    const rowData = {
                        ip: cells[0] ? cells[0].innerText.trim() : '',
                        port: cells[1] ? cells[1].innerText.trim() : '',
                        anonymity: cells[2] ? cells[2].innerText.trim() : '',
                        location: cells[4] ? cells[4].innerText.trim() : ''
                    };
                    
                    if (rowData.ip && rowData.port) {
                        data.push(rowData);
                    }
                }
            }
            
            return data;
        }
        """
    
    def _parse_html(self, html_content: str) -> List[ProxyData]:
        """
        解析HTML內容（備用方案）
        
        Args:
            html_content: HTML內容
            
        Returns:
            List[ProxyData]: 代理數據列表
        """
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, 'html.parser')
            rows = soup.select(self.container_selector)
            
            proxies = []
            for i, row in enumerate(rows):
                if i < self.skip_rows:  # 跳過標題行
                    continue
                
                cells = row.find_all('td')
                if len(cells) >= 5:
                    proxy_data = {
                        'ip': cells[0].get_text().strip() if cells[0] else '',
                        'port': cells[1].get_text().strip() if cells[1] else '',
                        'anonymity': cells[2].get_text().strip() if cells[2] else '',
                        'location': cells[4].get_text().strip() if len(cells) > 4 and cells[4] else ''
                    }
                    
                    proxy_obj = self._convert_to_proxy_data(proxy_data)
                    if proxy_obj:
                        proxies.append(proxy_obj)
            
            return proxies
            
        except Exception as e:
            self.logger.error(f"HTML解析失敗: {e}")
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
            
            # 解析位置信息
            location = proxy_dict.get("location", "").strip()
            country, city = self._parse_location(location)
            
            # 解析匿名度
            anonymity = proxy_dict.get("anonymity", "").strip()
            anonymity_level = self._parse_anonymity(anonymity)
            
            # 創建ProxyData對象
            return ProxyData(
                ip=ip,
                port=port,
                protocol="http",  # spys.one主要提供HTTP代理
                country=country,
                city=city,
                anonymity_level=anonymity_level,
                source="spys.one"
            )
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"轉換spys.one代理數據失敗: {e}")
            return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """驗證IP地址格式"""
        try:
            import ipaddress
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _parse_location(self, location: str) -> tuple[str, str]:
        """解析位置信息"""
        if not location:
            return "unknown", "unknown"
        
        # spys.one的位置格式通常是 "國家 城市"
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
        
        if "elite" in anonymity_lower or "high" in anonymity_lower:
            return "elite"
        elif "anonymous" in anonymity_lower or "medium" in anonymity_lower:
            return "anonymous"
        elif "transparent" in anonymity_lower or "low" in anonymity_lower:
            return "transparent"
        else:
            return "unknown"
    
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
        BaseExtractor要求實現的方法
        但spys.one主要使用HTML/JavaScript，所以返回空列表
        """
        return []
