"""
速度測試器 - 代理連接速度與性能測試
測試代理的連接速度、響應時間和帶寬性能
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import statistics
import concurrent.futures


class SpeedTester:
    """
    速度測試器
    測試代理的連接速度、響應時間和網絡性能
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化速度測試器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 測試配置
        self.test_urls = self.config.get('test_urls', [
            'https://www.google.com',
            'https://www.baidu.com',
            'https://httpbin.org/delay/1',
            'https://www.cloudflare.com/cdn-cgi/trace'
        ])
        
        self.timeout = self.config.get('timeout', 30)
        self.max_concurrent = self.config.get('max_concurrent', 5)
        self.test_rounds = self.config.get('test_rounds', 3)
        self.download_test_size = self.config.get('download_test_size', 1024 * 1024)  # 1MB
        
        # 性能閾值
        self.response_time_thresholds = {
            'excellent': 1000,   # < 1秒
            'good': 2000,        # < 2秒
            'fair': 5000,        # < 5秒
            'poor': 10000        # < 10秒
        }
        
        self.bandwidth_thresholds = {
            'excellent': 1024 * 1024,     # > 1MB/s
            'good': 512 * 1024,           # > 512KB/s
            'fair': 256 * 1024,           # > 256KB/s
            'poor': 128 * 1024            # > 128KB/s
        }
    
    async def test_speed(self, proxy: Any) -> Dict[str, Any]:
        """
        測試代理速度
        
        Args:
            proxy: 代理對象
            
        Returns:
            Dict: 速度測試結果
        """
        try:
            self.logger.info(f"開始測試代理 {proxy.ip}:{proxy.port} 的速度")
            
            start_time = time.time()
            
            # 1. 連接測試
            connection_test = await self._test_connection(proxy)
            
            # 2. 響應時間測試
            response_time_test = await self._test_response_time(proxy)
            
            # 3. 下載速度測試
            download_speed_test = await self._test_download_speed(proxy)
            
            # 4. 穩定性測試
            stability_test = await self._test_stability(proxy)
            
            # 5. 綜合評分
            overall_score = self._calculate_overall_score(
                connection_test, response_time_test, 
                download_speed_test, stability_test
            )
            
            total_time = time.time() - start_time
            
            result = {
                'success': True,
                'proxy': f"{proxy.ip}:{proxy.port}",
                'total_test_time': round(total_time, 2),
                'connection_test': connection_test,
                'response_time_test': response_time_test,
                'download_speed_test': download_speed_test,
                'stability_test': stability_test,
                'overall_score': overall_score,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(
                f"速度測試完成 - 代理: {proxy.ip}:{proxy.port}, "
                f"總分: {overall_score}/100, 耗時: {total_time:.1f}秒"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"速度測試失敗: {e}")
            return {
                'success': False,
                'error': str(e),
                'proxy': f"{proxy.ip}:{proxy.port}",
                'overall_score': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _test_connection(self, proxy: Any) -> Dict[str, Any]:
        """
        測試代理連接
        
        Args:
            proxy: 代理對象
            
        Returns:
            Dict: 連接測試結果
        """
        try:
            proxy_url = self._build_proxy_url(proxy)
            test_url = 'https://www.google.com'
            
            timeout = aiohttp.ClientTimeout(total=10)
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                start_time = time.time()
                
                async with session.get(
                    test_url,
                    proxy=proxy_url,
                    timeout=5
                ) as response:
                    connect_time = time.time() - start_time
                    
                    success = response.status == 200
                    
                    return {
                        'success': success,
                        'connect_time': round(connect_time * 1000, 2),  # 毫秒
                        'status_code': response.status,
                        'status': 'connected' if success else 'failed'
                    }
            
        except Exception as e:
            self.logger.warning(f"連接測試失敗: {e}")
            return {
                'success': False,
                'connect_time': 0,
                'status_code': 0,
                'status': 'error',
                'error': str(e)
            }
        finally:
            await connector.close()
    
    async def _test_response_time(self, proxy: Any) -> Dict[str, Any]:
        """
        測試代理響應時間
        
        Args:
            proxy: 代理對象
            
        Returns:
            Dict: 響應時間測試結果
        """
        try:
            proxy_url = self._build_proxy_url(proxy)
            response_times = []
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                # 測試多個URL
                for url in self.test_urls:
                    try:
                        start_time = time.time()
                        
                        async with session.get(
                            url,
                            proxy=proxy_url,
                            timeout=15
                        ) as response:
                            response_time = (time.time() - start_time) * 1000  # 毫秒
                            
                            if response.status == 200:
                                response_times.append(response_time)
                            
                    except Exception as e:
                        self.logger.warning(f"響應時間測試失敗 {url}: {e}")
                        continue
            
            if not response_times:
                return {
                    'success': False,
                    'avg_response_time': 0,
                    'min_response_time': 0,
                    'max_response_time': 0,
                    'response_times': [],
                    'grade': 'failed'
                }
            
            # 計算統計數據
            avg_time = statistics.mean(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            # 評級
            grade = self._grade_response_time(avg_time)
            
            return {
                'success': True,
                'avg_response_time': round(avg_time, 2),
                'min_response_time': round(min_time, 2),
                'max_response_time': round(max_time, 2),
                'response_times': [round(rt, 2) for rt in response_times],
                'grade': grade
            }
            
        except Exception as e:
            self.logger.error(f"響應時間測試失敗: {e}")
            return {
                'success': False,
                'avg_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0,
                'response_times': [],
                'grade': 'error',
                'error': str(e)
            }
        finally:
            await connector.close()
    
    async def _test_download_speed(self, proxy: Any) -> Dict[str, Any]:
        """
        測試代理下載速度
        
        Args:
            proxy: 代理對象
            
        Returns:
            Dict: 下載速度測試結果
        """
        try:
            proxy_url = self._build_proxy_url(proxy)
            
            # 使用多個測試文件
            test_files = [
                'https://speed.cloudflare.com/__down?bytes=1048576',  # 1MB
                'https://speed.hetzner.de/1MB.bin',
                'https://httpbin.org/bytes/1048576'
            ]
            
            download_speeds = []
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                # 測試多個文件
                for test_url in test_files:
                    try:
                        start_time = time.time()
                        total_bytes = 0
                        
                        async with session.get(
                            test_url,
                            proxy=proxy_url,
                            timeout=20
                        ) as response:
                            if response.status == 200:
                                # 讀取數據
                                async for chunk in response.content.iter_chunked(8192):
                                    total_bytes += len(chunk)
                                    
                                    # 限制測試大小
                                    if total_bytes >= self.download_test_size:
                                        break
                                
                                download_time = time.time() - start_time
                                
                                if download_time > 0:
                                    speed_bps = total_bytes / download_time
                                    download_speeds.append(speed_bps)
                            
                    except Exception as e:
                        self.logger.warning(f"下載速度測試失敗 {test_url}: {e}")
                        continue
            
            if not download_speeds:
                return {
                    'success': False,
                    'avg_speed_bps': 0,
                    'avg_speed_kbps': 0,
                    'avg_speed_mbps': 0,
                    'download_speeds': [],
                    'grade': 'failed'
                }
            
            # 計算平均速度
            avg_speed_bps = statistics.mean(download_speeds)
            avg_speed_kbps = avg_speed_bps / 1024
            avg_speed_mbps = avg_speed_kbps / 1024
            
            # 評級
            grade = self._grade_bandwidth(avg_speed_bps)
            
            return {
                'success': True,
                'avg_speed_bps': round(avg_speed_bps, 2),
                'avg_speed_kbps': round(avg_speed_kbps, 2),
                'avg_speed_mbps': round(avg_speed_mbps, 2),
                'download_speeds': [round(speed, 2) for speed in download_speeds],
                'grade': grade
            }
            
        except Exception as e:
            self.logger.error(f"下載速度測試失敗: {e}")
            return {
                'success': False,
                'avg_speed_bps': 0,
                'avg_speed_kbps': 0,
                'avg_speed_mbps': 0,
                'download_speeds': [],
                'grade': 'error',
                'error': str(e)
            }
        finally:
            await connector.close()
    
    async def _test_stability(self, proxy: Any) -> Dict[str, Any]:
        """
        測試代理穩定性
        
        Args:
            proxy: 代理對象
            
        Returns:
            Dict: 穩定性測試結果
        """
        try:
            proxy_url = self._build_proxy_url(proxy)
            test_results = []
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                # 進行多輪測試
                for round_num in range(self.test_rounds):
                    round_results = []
                    
                    # 每輪測試多個URL
                    for url in self.test_urls:
                        try:
                            start_time = time.time()
                            
                            async with session.get(
                                url,
                                proxy=proxy_url,
                                timeout=10
                            ) as response:
                                response_time = (time.time() - start_time) * 1000
                                
                                success = response.status == 200
                                round_results.append({
                                    'url': url,
                                    'success': success,
                                    'response_time': response_time,
                                    'status_code': response.status
                                })
                                
                        except Exception as e:
                            round_results.append({
                                'url': url,
                                'success': False,
                                'response_time': 0,
                                'status_code': 0,
                                'error': str(e)
                            })
                    
                    test_results.append(round_results)
                    
                    # 輪次之間等待
                    if round_num < self.test_rounds - 1:
                        await asyncio.sleep(2)
            
            # 分析穩定性
            stability_analysis = self._analyze_stability(test_results)
            
            return {
                'success': True,
                'total_rounds': self.test_rounds,
                'total_tests': len(self.test_urls) * self.test_rounds,
                'success_rate': stability_analysis['success_rate'],
                'avg_response_time_variance': stability_analysis['variance'],
                'stability_grade': stability_analysis['grade'],
                'test_details': test_results
            }
            
        except Exception as e:
            self.logger.error(f"穩定性測試失敗: {e}")
            return {
                'success': False,
                'error': str(e),
                'stability_grade': 'error'
            }
        finally:
            await connector.close()
    
    def _analyze_stability(self, test_results: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        分析穩定性
        
        Args:
            test_results: 測試結果列表
            
        Returns:
            Dict: 穩定性分析
        """
        try:
            all_successes = []
            all_response_times = []
            
            for round_results in test_results:
                for result in round_results:
                    all_successes.append(result.get('success', False))
                    if result.get('success', False):
                        all_response_times.append(result.get('response_time', 0))
            
            if not all_successes:
                return {
                    'success_rate': 0,
                    'variance': 0,
                    'grade': 'failed'
                }
            
            # 計算成功率
            success_rate = sum(all_successes) / len(all_successes)
            
            # 計算響應時間方差
            if len(all_response_times) > 1:
                variance = statistics.variance(all_response_times)
            else:
                variance = 0
            
            # 評級
            if success_rate >= 0.95 and variance < 1000:  # 95%成功率，方差<1000ms
                grade = 'excellent'
            elif success_rate >= 0.9 and variance < 2000:  # 90%成功率，方差<2000ms
                grade = 'good'
            elif success_rate >= 0.8:  # 80%成功率
                grade = 'fair'
            else:
                grade = 'poor'
            
            return {
                'success_rate': round(success_rate, 3),
                'variance': round(variance, 2),
                'grade': grade
            }
            
        except Exception as e:
            self.logger.error(f"穩定性分析失敗: {e}")
            return {
                'success_rate': 0,
                'variance': 0,
                'grade': 'error'
            }
    
    def _grade_response_time(self, avg_time: float) -> str:
        """
        響應時間評級
        
        Args:
            avg_time: 平均響應時間（毫秒）
            
        Returns:
            str: 評級
        """
        if avg_time < self.response_time_thresholds['excellent']:
            return 'excellent'
        elif avg_time < self.response_time_thresholds['good']:
            return 'good'
        elif avg_time < self.response_time_thresholds['fair']:
            return 'fair'
        elif avg_time < self.response_time_thresholds['poor']:
            return 'poor'
        else:
            return 'failed'
    
    def _grade_bandwidth(self, speed_bps: float) -> str:
        """
        帶寬評級
        
        Args:
            speed_bps: 速度（字節/秒）
            
        Returns:
            str: 評級
        """
        if speed_bps > self.bandwidth_thresholds['excellent']:
            return 'excellent'
        elif speed_bps > self.bandwidth_thresholds['good']:
            return 'good'
        elif speed_bps > self.bandwidth_thresholds['fair']:
            return 'fair'
        elif speed_bps > self.bandwidth_thresholds['poor']:
            return 'poor'
        else:
            return 'failed'
    
    def _calculate_overall_score(self, connection_test: Dict[str, Any],
                                response_time_test: Dict[str, Any],
                                download_speed_test: Dict[str, Any],
                                stability_test: Dict[str, Any]) -> float:
        """
        計算綜合評分
        
        Args:
            connection_test: 連接測試結果
            response_time_test: 響應時間測試結果
            download_speed_test: 下載速度測試結果
            stability_test: 穩定性測試結果
            
        Returns:
            float: 綜合評分
        """
        total_score = 0
        
        # 連接測試評分 (25分)
        if connection_test.get('success', False):
            connect_time = connection_test.get('connect_time', 0)
            if connect_time < 1000:  # < 1秒
                total_score += 25
            elif connect_time < 2000:  # < 2秒
                total_score += 20
            elif connect_time < 5000:  # < 5秒
                total_score += 15
            else:
                total_score += 10
        
        # 響應時間評分 (25分)
        if response_time_test.get('success', False):
            response_time = response_time_test.get('avg_response_time', 0)
            if response_time < 1000:  # < 1秒
                total_score += 25
            elif response_time < 2000:  # < 2秒
                total_score += 20
            elif response_time < 5000:  # < 5秒
                total_score += 15
            else:
                total_score += 10
        
        # 下載速度評分 (25分)
        if download_speed_test.get('success', False):
            speed_bps = download_speed_test.get('avg_speed_bps', 0)
            if speed_bps > 1024 * 1024:  # > 1MB/s
                total_score += 25
            elif speed_bps > 512 * 1024:  # > 512KB/s
                total_score += 20
            elif speed_bps > 256 * 1024:  # > 256KB/s
                total_score += 15
            else:
                total_score += 10
        
        # 穩定性評分 (25分)
        if stability_test.get('success', False):
            success_rate = stability_test.get('success_rate', 0)
            if success_rate >= 0.95:  # >= 95%
                total_score += 25
            elif success_rate >= 0.9:  # >= 90%
                total_score += 20
            elif success_rate >= 0.8:  # >= 80%
                total_score += 15
            else:
                total_score += 10
        
        return round(total_score, 1)
    
    def _build_proxy_url(self, proxy: Any) -> str:
        """
        構建代理URL
        
        Args:
            proxy: 代理對象
            
        Returns:
            str: 代理URL
        """
        protocol = getattr(proxy, 'protocol', 'http')
        username = getattr(proxy, 'username', None)
        password = getattr(proxy, 'password', None)
        
        if username and password:
            return f"{protocol}://{username}:{password}@{proxy.ip}:{proxy.port}"
        else:
            return f"{protocol}://{proxy.ip}:{proxy.port}"