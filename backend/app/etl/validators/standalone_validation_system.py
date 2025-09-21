#!/usr/bin/env python3
"""
獨立代理驗證系統

不依賴數據庫模型的完整代理驗證系統實現
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from pathlib import Path

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ProxyData:
    """代理數據類"""
    ip: str
    port: int
    protocol: str = "http"
    country: str = "Unknown"
    username: Optional[str] = None
    password: Optional[str] = None
    score: float = 0.0
    is_active: bool = False
    anonymity_level: str = "unknown"
    response_time: float = 0.0
    last_checked: Optional[datetime] = None
    check_count: int = 0
    success_count: int = 0
    fail_count: int = 0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'ip': self.ip,
            'port': self.port,
            'protocol': self.protocol,
            'country': self.country,
            'username': self.username,
            'password': self.password,
            'score': self.score,
            'is_active': self.is_active,
            'anonymity_level': self.anonymity_level,
            'response_time': self.response_time,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None,
            'check_count': self.check_count,
            'success_count': self.success_count,
            'fail_count': self.fail_count,
            'tags': self.tags,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProxyData':
        """從字典創建"""
        proxy = cls(
            ip=data['ip'],
            port=data['port'],
            protocol=data.get('protocol', 'http'),
            country=data.get('country', 'Unknown'),
            username=data.get('username'),
            password=data.get('password'),
            score=data.get('score', 0.0),
            is_active=data.get('is_active', False),
            anonymity_level=data.get('anonymity_level', 'unknown'),
            response_time=data.get('response_time', 0.0),
            check_count=data.get('check_count', 0),
            success_count=data.get('success_count', 0),
            fail_count=data.get('fail_count', 0),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        )
        
        if data.get('last_checked'):
            proxy.last_checked = datetime.fromisoformat(data['last_checked'])
        
        return proxy


@dataclass
class ValidationResult:
    """驗證結果類"""
    proxy: ProxyData
    success: bool
    score: float
    details: Dict[str, Any]
    timestamp: datetime
    duration: float
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'proxy': self.proxy.to_dict(),
            'success': self.success,
            'score': self.score,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'duration': self.duration,
            'error': self.error
        }


class StandaloneValidationSystem:
    """獨立代理驗證系統"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化驗證系統
        
        Args:
            config: 系統配置
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化各個驗證組件
        self._init_components()
        
        # 統計信息
        self.stats = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'average_score': 0.0,
            'start_time': datetime.now()
        }
    
    def _init_components(self):
        """初始化驗證組件"""
        try:
            # 導入並初始化各個組件
            from ip_scoring_engine import IPScoringEngine
            from geolocation_validator import GeolocationValidator
            from speed_tester import SpeedTester
            from anonymity_tester import AnonymityTester
            
            self.scoring_engine = IPScoringEngine()
            self.geo_validator = GeolocationValidator()
            self.speed_tester = SpeedTester()
            self.anonymity_tester = AnonymityTester()
            
            self.logger.info("所有驗證組件初始化完成")
            
        except ImportError as e:
            self.logger.error(f"導入組件失敗: {e}")
            raise
        except Exception as e:
            self.logger.error(f"初始化組件失敗: {e}")
            raise
    
    async def validate_proxy(self, proxy: Union[ProxyData, Dict[str, Any]]) -> ValidationResult:
        """
        驗證單個代理
        
        Args:
            proxy: 代理數據
            
        Returns:
            ValidationResult: 驗證結果
        """
        start_time = datetime.now()
        
        try:
            # 轉換為ProxyData對象
            if isinstance(proxy, dict):
                proxy_data = ProxyData.from_dict(proxy)
            else:
                proxy_data = proxy
            
            self.logger.info(f"開始驗證代理: {proxy_data.ip}:{proxy_data.port}")
            
            # 執行各項測試
            validation_data = await self._run_validation_tests(proxy_data)
            
            # 計算綜合評分
            final_score = await self.scoring_engine.calculate_score(validation_data)
            
            # 更新代理信息
            proxy_data.score = final_score
            proxy_data.is_active = final_score >= 60
            proxy_data.anonymity_level = validation_data['anonymity'].get('level', 'unknown')
            proxy_data.response_time = validation_data['connection'].get('response_time', 0)
            proxy_data.last_checked = datetime.now()
            proxy_data.check_count += 1
            
            if final_score >= 60:
                proxy_data.success_count += 1
            else:
                proxy_data.fail_count += 1
            
            # 創建驗證結果
            result = ValidationResult(
                proxy=proxy_data,
                success=final_score >= 60,
                score=final_score,
                details=validation_data,
                timestamp=datetime.now(),
                duration=(datetime.now() - start_time).total_seconds()
            )
            
            # 更新統計信息
            self._update_stats(result)
            
            self.logger.info(
                f"代理驗證完成 - {proxy_data.ip}:{proxy_data.port}, "
                f"評分: {final_score:.1f}/100, 狀態: {'有效' if result.success else '無效'}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"代理驗證失敗: {e}")
            
            # 創建失敗結果
            result = ValidationResult(
                proxy=proxy_data if 'proxy_data' in locals() else ProxyData("0.0.0.0", 0),
                success=False,
                score=0.0,
                details={},
                timestamp=datetime.now(),
                duration=(datetime.now() - start_time).total_seconds(),
                error=str(e)
            )
            
            self._update_stats(result)
            return result
    
    async def _run_validation_tests(self, proxy: ProxyData) -> Dict[str, Any]:
        """
        運行驗證測試
        
        Args:
            proxy: 代理數據
            
        Returns:
            Dict: 測試數據
        """
        self.logger.info(f"開始運行驗證測試: {proxy.ip}:{proxy.port}")
        
        # 並行執行測試
        tasks = [
            self._test_connection(proxy),
            self.geo_validator.validate_location(proxy),
            self.speed_tester.test_speed(proxy),
            self.anonymity_tester.test_anonymity(proxy)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果
        connection_result = results[0] if not isinstance(results[0], Exception) else {'success': False, 'error': str(results[0])}
        geo_result = results[1] if not isinstance(results[1], Exception) else {'success': False, 'error': str(results[1])}
        speed_result = results[2] if not isinstance(results[2], Exception) else {'success': False, 'error': str(results[2])}
        anonymity_result = results[3] if not isinstance(results[3], Exception) else {'success': False, 'error': str(results[3])}
        
        validation_data = {
            'connection': connection_result,
            'anonymity': anonymity_result,
            'geolocation': geo_result,
            'speed': speed_result,
            'response_time': connection_result.get('response_time', 0)
        }
        
        self.logger.info(f"驗證測試完成: {proxy.ip}:{proxy.port}")
        return validation_data
    
    async def _test_connection(self, proxy: ProxyData) -> Dict[str, Any]:
        """
        測試代理連接
        
        Args:
            proxy: 代理數據
            
        Returns:
            Dict: 連接測試結果
        """
        try:
            # 簡化的連接測試
            import aiohttp
            import time
            
            proxy_url = f"{proxy.protocol}://{proxy.ip}:{proxy.port}"
            if proxy.username and proxy.password:
                proxy_url = f"{proxy.protocol}://{proxy.username}:{proxy.password}@{proxy.ip}:{proxy.port}"
            
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                start_time = time.time()
                
                try:
                    async with session.get(
                        'https://httpbin.org/delay/1',
                        proxy=proxy_url,
                        timeout=5
                    ) as response:
                        response_time = time.time() - start_time
                        
                        return {
                            'success': response.status == 200,
                            'response_time': response_time,
                            'status_code': response.status,
                            'error': None
                        }
                        
                except Exception as e:
                    return {
                        'success': False,
                        'response_time': time.time() - start_time,
                        'status_code': 0,
                        'error': str(e)
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'response_time': 0,
                'status_code': 0,
                'error': str(e)
            }
    
    async def validate_batch(self, proxies: List[Union[ProxyData, Dict[str, Any]]], 
                             max_concurrent: int = 10) -> List[ValidationResult]:
        """
        批量驗證代理
        
        Args:
            proxies: 代理列表
            max_concurrent: 最大並發數
            
        Returns:
            List[ValidationResult]: 驗證結果列表
        """
        self.logger.info(f"開始批量驗證: {len(proxies)} 個代理")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def validate_with_semaphore(proxy):
            async with semaphore:
                return await self.validate_proxy(proxy)
        
        tasks = [validate_with_semaphore(proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理異常結果
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"代理 {i} 驗證異常: {result}")
                # 創建失敗結果
                proxy_data = proxies[i] if isinstance(proxies[i], ProxyData) else ProxyData("0.0.0.0", 0)
                fail_result = ValidationResult(
                    proxy=proxy_data,
                    success=False,
                    score=0.0,
                    details={},
                    timestamp=datetime.now(),
                    duration=0.0,
                    error=str(result)
                )
                valid_results.append(fail_result)
            else:
                valid_results.append(result)
        
        self.logger.info(f"批量驗證完成: {len(valid_results)} 個結果")
        return valid_results
    
    def _update_stats(self, result: ValidationResult):
        """更新統計信息"""
        self.stats['total_validations'] += 1
        
        if result.success:
            self.stats['successful_validations'] += 1
        else:
            self.stats['failed_validations'] += 1
        
        # 更新平均分數
        total_score = self.stats['average_score'] * (self.stats['total_validations'] - 1) + result.score
        self.stats['average_score'] = total_score / self.stats['total_validations']
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        uptime = datetime.now() - self.stats['start_time']
        
        return {
            'total_validations': self.stats['total_validations'],
            'successful_validations': self.stats['successful_validations'],
            'failed_validations': self.stats['failed_validations'],
            'success_rate': (
                self.stats['successful_validations'] / self.stats['total_validations'] 
                if self.stats['total_validations'] > 0 else 0
            ),
            'average_score': self.stats['average_score'],
            'uptime_seconds': uptime.total_seconds(),
            'uptime_human': str(uptime).split('.')[0]
        }
    
    def export_results(self, results: List[ValidationResult], filepath: str):
        """導出驗證結果"""
        try:
            data = {
                'export_time': datetime.now().isoformat(),
                'total_results': len(results),
                'system_stats': self.get_stats(),
                'results': [result.to_dict() for result in results]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"結果導出完成: {filepath}")
            
        except Exception as e:
            self.logger.error(f"結果導出失敗: {e}")
            raise


async def demo_standalone_system():
    """演示獨立驗證系統"""
    print("=== 獨立代理驗證系統演示 ===")
    
    # 創建系統實例
    system = StandaloneValidationSystem()
    
    # 測試代理數據
    test_proxies = [
        ProxyData("8.8.8.8", 8080, "http", "US"),
        ProxyData("1.1.1.1", 8080, "https", "AU"),
        ProxyData("208.67.222.222", 3128, "http", "CA"),
    ]
    
    print(f"測試代理數量: {len(test_proxies)}")
    
    # 批量驗證
    results = await system.validate_batch(test_proxies, max_concurrent=3)
    
    # 顯示結果
    print("\n=== 驗證結果 ===")
    for i, result in enumerate(results):
        proxy = result.proxy
        status = "✅ 有效" if result.success else "❌ 無效"
        
        print(f"{i+1}. {proxy.ip}:{proxy.port} {status}")
        print(f"   評分: {result.score:.1f}/100")
        print(f"   匿名等級: {proxy.anonymity_level}")
        print(f"   響應時間: {proxy.response_time:.2f}s")
        print(f"   持續時間: {result.duration:.1f}s")
        
        if result.error:
            print(f"   錯誤: {result.error}")
        
        print()
    
    # 顯示統計信息
    stats = system.get_stats()
    print("=== 系統統計 ===")
    print(f"總驗證數: {stats['total_validations']}")
    print(f"成功數: {stats['successful_validations']}")
    print(f"失敗數: {stats['failed_validations']}")
    print(f"成功率: {stats['success_rate']:.1%}")
    print(f"平均評分: {stats['average_score']:.1f}")
    print(f"運行時間: {stats['uptime_human']}")
    
    # 導出結果
    try:
        export_path = "validation_results.json"
        system.export_results(results, export_path)
        print(f"\n結果已導出到: {export_path}")
    except Exception as e:
        print(f"\n導出失敗: {e}")


if __name__ == "__main__":
    # 運行演示
    asyncio.run(demo_standalone_system())