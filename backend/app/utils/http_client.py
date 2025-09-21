"""
HTTP客戶端工具類
"""
import aiohttp
import asyncio
from typing import Optional, Dict, Any, Union
from urllib.parse import urljoin, urlparse
import random
from app.core.config import settings
from app.core.exceptions import NetworkException, RateLimitException
from app.core.logging import get_logger

logger = get_logger(__name__)


class HTTPClient:
    """異步HTTP客戶端"""
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 1,
        user_agents: Optional[list] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.user_agents = user_agents or [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
        ]
        self.default_headers = headers or {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """異步上下文管理器進入"""
        await self.create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出"""
        await self.close_session()
    
    async def create_session(self):
        """創建HTTP會話"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=settings.MAX_CONCURRENT_REQUESTS,
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True,
            )
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers=self.default_headers,
                trust_env=True,
            )
    
    async def close_session(self):
        """關閉HTTP會話"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    def _get_random_user_agent(self) -> str:
        """獲取隨機User-Agent"""
        return random.choice(self.user_agents)
    
    def _prepare_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """準備請求頭"""
        final_headers = self.default_headers.copy()
        final_headers["User-Agent"] = self._get_random_user_agent()
        
        if headers:
            final_headers.update(headers)
        
        return final_headers
    
    async def _make_request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """帶重試的請求"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if not self._session or self._session.closed:
                    await self.create_session()
                
                response = await self._session.request(method, url, **kwargs)
                
                # 檢查速率限制
                if response.status == 429:
                    retry_after = response.headers.get("Retry-After", self.retry_delay)
                    raise RateLimitException(
                        f"速率限制: {url}",
                        source=urlparse(url).netloc,
                        retry_after=int(retry_after),
                        details={"status_code": 429, "attempt": attempt + 1}
                    )
                
                # 檢查HTTP錯誤
                if response.status >= 400:
                    raise NetworkException(
                        f"HTTP錯誤 {response.status}: {url}",
                        url=url,
                        status_code=response.status,
                        details={"attempt": attempt + 1}
                    )
                
                return response
                
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = NetworkException(
                    f"網絡請求失敗: {str(e)}",
                    url=url,
                    details={"attempt": attempt + 1, "error": str(e)}
                )
                
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                
            except RateLimitException as e:
                last_exception = e
                if attempt < self.max_retries and e.retry_after:
                    await asyncio.sleep(e.retry_after)
                else:
                    break
        
        raise last_exception
    
    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """發送GET請求"""
        request_headers = self._prepare_headers(headers)
        
        response = await self._make_request_with_retry(
            "GET", url, headers=request_headers, params=params, **kwargs
        )
        
        content = await response.text()
        logger.debug(f"GET請求成功: {url}, 狀態碼: {response.status}")
        
        return content
    
    async def post(
        self,
        url: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> str:
        """發送POST請求"""
        request_headers = self._prepare_headers(headers)
        
        response = await self._make_request_with_retry(
            "POST", url, headers=request_headers, data=data, **kwargs
        )
        
        content = await response.text()
        logger.debug(f"POST請求成功: {url}, 狀態碼: {response.status}")
        
        return content
    
    async def get_json(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """發送GET請求並解析JSON響應"""
        content = await self.get(url, headers=headers, params=params, **kwargs)
        
        try:
            import json
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失敗: {url}, 錯誤: {e}")
            raise NetworkException(
                f"無效的JSON響應: {str(e)}",
                url=url,
                details={"content": content[:200]}
            )


class HTTPClientPool:
    """HTTP客戶端連接池"""
    
    def __init__(self, max_clients: int = 10):
        self.max_clients = max_clients
        self._clients: list[HTTPClient] = []
        self._semaphore = asyncio.Semaphore(max_clients)
    
    async def get_client(self) -> HTTPClient:
        """獲取客戶端實例"""
        await self._semaphore.acquire()
        
        if not self._clients:
            client = HTTPClient()
            await client.create_session()
            return client
        
        return self._clients.pop()
    
    async def return_client(self, client: HTTPClient):
        """歸還客戶端實例"""
        self._clients.append(client)
        self._semaphore.release()
    
    async def close_all(self):
        """關閉所有客戶端"""
        for client in self._clients:
            await client.close_session()
        self._clients.clear()