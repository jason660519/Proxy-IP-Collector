"""
代理驗證器 - 自動化IP驗證與評分
提供完整的代理IP驗證、評分和篩選功能
"""

import asyncio
import aiohttp
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import hashlib

from app.models.proxy import Proxy
from .ip_scoring_engine import IPScoringEngine
from .geolocation_validator import GeolocationValidator
from .speed_tester import SpeedTester
from .anonymity_tester import AnonymityTester


class ProxyValidator:
    """
    代理驗證器
    提供多維度的代理IP驗證和評分功能
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化代理驗證器
        
        Args:
            config: 配置字典，包含驗證參數
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化子模塊
        self.scoring_engine = IPScoringEngine(self.config.get('scoring_config', {}))
        self.geolocation_validator = GeolocationValidator(self.config.get('geolocation_config', {}))
        self.speed_tester = SpeedTester(self.config.get('speed_test_config', {}))
        self.anonymity_tester = AnonymityTester(self.config.get('anonymity_config', {}))
        
        # 驗證配置
        self.timeout = self.config.get('timeout', 30)
        self.max_retries = self.config.get('max_retries', 2)
        self.test_urls = self.config.get('test_urls', [
            'http://httpbin.org/ip',
            'https://api.ipify.org?format=json',
            'http://icanhazip.com'
        ])
        self.concurrent_limit = self.config.get('concurrent_limit', 50)
        
        # 統計數據
        self.stats = {
            'total_validated': 0,
            'validation_success': 0,
            'validation_failed': 0,
            'avg_validation_time': 0.0
        }
        
    async def validate_proxy(self, proxy: Proxy) -> bool:
        """
        驗證單個代理
        
        Args:
            proxy: 代理對象
            
        Returns:
            bool: 驗證是否通過
        """
        try:
            self.logger.info(f"開始驗證代理 {proxy.ip}:{proxy.port}")
            
            # 1. 基礎連接測試
            connection_test = await self._test_connection(proxy)
            if not connection_test['success']:
                self.logger.warning(f"代理 {proxy.ip}:{proxy.port} 連接測試失敗")
                return False
            
            # 2. 匿名性測試
            anonymity_test = await self.anonymity_tester.test_anonymity(proxy)
            
            # 3. 地理位置驗證
            geo_result = await self.geo_validator.validate_location(proxy)
            
            # 4. 速度測試
            speed_result = await self.speed_tester.test_proxy_speed(proxy)
            
            # 5. 綜合評分
            validation_data = {
                'connection': connection_test,
                'anonymity': anonymity_test,
                'geolocation': geo_result,
                'speed': speed_result,
                'response_time': connection_test.get('response_time', 0)
            }
            
            score = await self.scoring_engine.calculate_score(validation_data)
            
            # 更新代理信息
            proxy.score = score
            proxy.last_verified = datetime.now()
            proxy.is_active = score >= self.config.get('min_score', 60)
            proxy.anonymity_level = anonymity_test.get('level', 'unknown')
            proxy.response_time = connection_test.get('response_time', 0)
            
            self.logger.info(
                f"代理 {proxy.ip}:{proxy.port} 驗證完成，"
                f"評分: {score:.1f}, 狀態: {'有效' if proxy.is_active else '無效'}"
            )
            
            return proxy.is_active
            
        except Exception as e:
            self.logger.error(f"代理驗證異常 {proxy.ip}:{proxy.port}: {e}")
            proxy.is_active = False
            proxy.last_verified = datetime.now()
            return False
    
    async def validate_proxies_batch(self, proxies: List[Proxy]) -> List[Proxy]:
        """
        批量驗證代理
        
        Args:
            proxies: 代理列表
            
        Returns:
            List[Proxy]: 驗證通過的代理列表
        """
        self.logger.info(f"開始批量驗證 {len(proxies)} 個代理")
        
        valid_proxies = []
        semaphore = asyncio.Semaphore(self.concurrent_limit)
        
        async def validate_with_semaphore(proxy: Proxy) -> Optional[Proxy]:
            async with semaphore:
                is_valid = await self.validate_proxy(proxy)
                return proxy if is_valid else None
        
        # 創建驗證任務
        tasks = [validate_with_semaphore(proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 收集有效代理
        for result in results:
            if isinstance(result, Proxy) and result.is_active:
                valid_proxies.append(result)
        
        self.logger.info(f"批量驗證完成，有效代理: {len(valid_proxies)}/{len(proxies)}")
        return valid_proxies
    
    async def _test_connection(self, proxy: Proxy) -> Dict[str, Any]:
        """
        測試代理連接
        
        Args:
            proxy: 代理對象
            
        Returns:
            Dict: 測試結果
        """
        start_time = time.time()
        
        # 構建代理URL
        proxy_url = f"{proxy.protocol}://{proxy.ip}:{proxy.port}"
        if proxy.username and proxy.password:
            proxy_url = f"{proxy.protocol}://{proxy.username}:{proxy.password}@{proxy.ip}:{proxy.port}"
        
        connector = aiohttp.TCPConnector(ssl=False, limit=1)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        try:
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                test_url = self.test_urls[0]  # 使用第一個測試URL
                
                async with session.get(
                    test_url,
                    proxy=proxy_url,
                    headers={'User-Agent': 'ProxyValidator/1.0'}
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        content = await response.text()
                        return {
                            'success': True,
                            'response_time': response_time,
                            'status_code': response.status,
                            'content': content[:200]  # 限制內容長度
                        }
                    else:
                        return {
                            'success': False,
                            'response_time': response_time,
                            'status_code': response.status,
                            'error': f'HTTP {response.status}'
                        }
                        
        except asyncio.TimeoutError:
            return {
                'success': False,
                'response_time': self.timeout,
                'error': '連接超時'
            }
        except Exception as e:
            return {
                'success': False,
                'response_time': time.time() - start_time,
                'error': str(e)
            }
        finally:
            await connector.close()
    
    async def _test_anonymity(self, proxy: Proxy) -> Dict[str, Any]:
        """
        測試代理匿名性
        
        Args:
            proxy: 代理對象
            
        Returns:
            Dict: 匿名性測試結果
        """
        try:
            # 獲取真實IP
            real_ip = await self._get_real_ip()
            if not real_ip:
                return {'level': 'unknown', 'details': '無法獲取真實IP'}
            
            # 通過代理獲取IP
            proxy_ip = await self._get_ip_through_proxy(proxy)
            if not proxy_ip:
                return {'level': 'transparent', 'details': '代理無法工作'}
            
            # 分析匿名性等級
            if proxy_ip == real_ip:
                return {
                    'level': 'transparent',
                    'real_ip': real_ip,
                    'proxy_ip': proxy_ip,
                    'details': '透明代理，洩露真實IP'
                }
            else:
                # 檢查是否為高匿名代理
                headers_test = await self._test_headers(proxy)
                if headers_test.get('is_elite'):
                    return {
                        'level': 'elite',
                        'real_ip': real_ip,
                        'proxy_ip': proxy_ip,
                        'details': '高匿名代理，無任何頭部信息洩露'
                    }
                else:
                    return {
                        'level': 'anonymous',
                        'real_ip': real_ip,
                        'proxy_ip': proxy_ip,
                        'details': '匿名代理，可能洩露部分信息'
                    }
                    
        except Exception as e:
            self.logger.error(f"匿名性測試失敗: {e}")
            return {'level': 'unknown', 'details': f'測試失敗: {e}'}
    
    async def _get_real_ip(self) -> Optional[str]:
        """獲取真實IP地址"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.ipify.org?format=json', timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('ip')
        except Exception as e:
            self.logger.warning(f"獲取真實IP失敗: {e}")
        return None
    
    async def _get_ip_through_proxy(self, proxy: Proxy) -> Optional[str]:
        """通過代理獲取IP地址"""
        proxy_url = f"{proxy.protocol}://{proxy.ip}:{proxy.port}"
        if proxy.username and proxy.password:
            proxy_url = f"{proxy.protocol}://{proxy.username}:{proxy.password}@{proxy.ip}:{proxy.port}"
        
        try:
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    'https://api.ipify.org?format=json',
                    proxy=proxy_url
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('ip')
        except Exception as e:
            self.logger.warning(f"通過代理獲取IP失敗: {e}")
        return None
    
    async def _test_headers(self, proxy: Proxy) -> Dict[str, Any]:
        """測試HTTP頭部信息"""
        proxy_url = f"{proxy.protocol}://{proxy.ip}:{proxy.port}"
        if proxy.username and proxy.password:
            proxy_url = f"{proxy.protocol}://{proxy.username}:{proxy.password}@{proxy.ip}:{proxy.port}"
        
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    'http://httpbin.org/headers',
                    proxy=proxy_url
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        headers = data.get('headers', {})
                        
                        # 檢查是否包含代理相關頭部
                        proxy_headers = [
                            'X-Forwarded-For', 'X-Real-IP', 'Via',
                            'X-Proxy-ID', 'X-Forwarded', 'Forwarded'
                        ]
                        
                        detected_headers = [
                            header for header in proxy_headers 
                            if header in headers
                        ]
                        
                        return {
                            'is_elite': len(detected_headers) == 0,
                            'detected_headers': detected_headers,
                            'all_headers': headers
                        }
        except Exception as e:
            self.logger.warning(f"頭部測試失敗: {e}")
        
        return {'is_elite': False, 'detected_headers': [], 'all_headers': {}}