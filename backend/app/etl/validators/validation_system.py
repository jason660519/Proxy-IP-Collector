"""
代理驗證與評分系統 - 綜合代理評估框架
整合多種驗證器，提供全面的代理質量評估
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import json

from .proxy_validator import ProxyValidator
from .ip_scoring_engine import IPScoringEngine
from .geolocation_validator import GeolocationValidator
from .speed_tester import SpeedTester
from .anonymity_tester import AnonymityTester


@dataclass
class ProxyValidationResult:
    """代理驗證結果數據類"""
    proxy_id: str
    success: bool
    overall_score: float
    validation_time: float
    tests_passed: int
    tests_failed: int
    details: Dict[str, Any]
    timestamp: datetime
    recommendations: List[str]


class ProxyValidationSystem:
    """
    代理驗證與評分系統
    提供全面的代理質量評估和評分功能
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化代理驗證系統
        
        Args:
            config: 系統配置
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化驗證組件
        self.validator = ProxyValidator(self.config.get('validator_config', {}))
        self.scoring_engine = IPScoringEngine(self.config.get('scoring_config', {}))
        self.geo_validator = GeolocationValidator(self.config.get('geolocation_config', {}))
        self.speed_tester = SpeedTester(self.config.get('speed_config', {}))
        self.anonymity_tester = AnonymityTester(self.config.get('anonymity_config', {}))
        
        # 系統配置
        self.validation_timeout = self.config.get('validation_timeout', 60)
        self.max_concurrent_tests = self.config.get('max_concurrent_tests', 10)
        self.enable_comprehensive_testing = self.config.get('enable_comprehensive_testing', True)
        self.min_score_threshold = self.config.get('min_score_threshold', 60)
        
        # 統計數據
        self.stats = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'avg_validation_time': 0.0,
            'avg_score': 0.0,
            'score_distribution': {
                'excellent': 0,  # 90-100
                'good': 0,       # 75-89
                'average': 0,    # 60-74
                'poor': 0,       # 40-59
                'bad': 0         # 0-39
            }
        }
    
    async def validate_proxy(self, proxy: Any, test_level: str = 'comprehensive') -> ProxyValidationResult:
        """
        驗證單個代理
        
        Args:
            proxy: 代理對象
            test_level: 測試等級 (basic, standard, comprehensive)
            
        Returns:
            ProxyValidationResult: 驗證結果
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"開始驗證代理: {proxy.ip}:{proxy.port} (等級: {test_level})")
            
            # 根據測試等級選擇測試項目
            test_config = self._get_test_config(test_level)
            
            # 執行基礎驗證
            basic_validation = await self._perform_basic_validation(proxy)
            
            if not basic_validation['success']:
                return self._create_failed_result(proxy, basic_validation, start_time)
            
            # 執行進階測試
            advanced_tests = await self._perform_advanced_tests(proxy, test_config)
            
            # 計算綜合評分
            overall_score = self._calculate_overall_score(basic_validation, advanced_tests)
            
            # 生成建議
            recommendations = self._generate_recommendations(basic_validation, advanced_tests)
            
            # 創建驗證結果
            result = ProxyValidationResult(
                proxy_id=f"{proxy.ip}:{proxy.port}",
                success=True,
                overall_score=overall_score,
                validation_time=(datetime.now() - start_time).total_seconds(),
                tests_passed=advanced_tests.get('tests_passed', 0),
                tests_failed=advanced_tests.get('tests_failed', 0),
                details={
                    'basic_validation': basic_validation,
                    'advanced_tests': advanced_tests,
                    'proxy_info': {
                        'ip': proxy.ip,
                        'port': proxy.port,
                        'protocol': getattr(proxy, 'protocol', 'http'),
                        'country': getattr(proxy, 'country', 'unknown'),
                        'anonymity': getattr(proxy, 'anonymity', 'unknown')
                    }
                },
                timestamp=datetime.now(),
                recommendations=recommendations
            )
            
            # 更新統計數據
            self._update_stats(result)
            
            self.logger.info(
                f"代理驗證完成 - {proxy.ip}:{proxy.port}, "
                f"總分: {overall_score:.1f}/100, "
                f"耗時: {result.validation_time:.1f}s"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"代理驗證失敗: {e}")
            return ProxyValidationResult(
                proxy_id=f"{proxy.ip}:{proxy.port}",
                success=False,
                overall_score=0,
                validation_time=(datetime.now() - start_time).total_seconds(),
                tests_passed=0,
                tests_failed=1,
                details={'error': str(e)},
                timestamp=datetime.now(),
                recommendations=['驗證過程中發生錯誤，請檢查代理配置']
            )
    
    async def validate_proxies_batch(self, proxies: List[Any], test_level: str = 'standard') -> List[ProxyValidationResult]:
        """
        批量驗證代理
        
        Args:
            proxies: 代理列表
            test_level: 測試等級
            
        Returns:
            List[ProxyValidationResult]: 驗證結果列表
        """
        self.logger.info(f"開始批量驗證 {len(proxies)} 個代理 (等級: {test_level})")
        
        semaphore = asyncio.Semaphore(self.max_concurrent_tests)
        
        async def validate_with_semaphore(proxy):
            async with semaphore:
                return await self.validate_proxy(proxy, test_level)
        
        # 並行執行驗證
        tasks = [validate_with_semaphore(proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"代理 {proxies[i].ip}:{proxies[i].port} 驗證異常: {result}")
                continue
            valid_results.append(result)
        
        self.logger.info(f"批量驗證完成 - 成功: {len(valid_results)}, 失敗: {len(results) - len(valid_results)}")
        
        return valid_results
    
    def _get_test_config(self, test_level: str) -> Dict[str, Any]:
        """
        獲取測試配置
        
        Args:
            test_level: 測試等級
            
        Returns:
            Dict: 測試配置
        """
        test_configs = {
            'basic': {
                'connection_test': True,
                'speed_test': False,
                'geolocation_test': False,
                'anonymity_test': False,
                'scoring_test': True
            },
            'standard': {
                'connection_test': True,
                'speed_test': True,
                'geolocation_test': True,
                'anonymity_test': False,
                'scoring_test': True
            },
            'comprehensive': {
                'connection_test': True,
                'speed_test': True,
                'geolocation_test': True,
                'anonymity_test': True,
                'scoring_test': True
            }
        }
        
        return test_configs.get(test_level, test_configs['comprehensive'])
    
    async def _perform_basic_validation(self, proxy: Any) -> Dict[str, Any]:
        """
        執行基礎驗證
        
        Args:
            proxy: 代理對象
            
        Returns:
            Dict: 基礎驗證結果
        """
        try:
            # 使用現有的代理驗證器進行基礎驗證
            is_valid = await self.validator.validate_proxy(proxy)
            
            return {
                'success': is_valid,
                'connection_test': is_valid,
                'message': '基礎連接測試通過' if is_valid else '基礎連接測試失敗'
            }
            
        except Exception as e:
            self.logger.error(f"基礎驗證失敗: {e}")
            return {
                'success': False,
                'connection_test': False,
                'message': f'基礎驗證失敗: {str(e)}'
            }
    
    async def _perform_advanced_tests(self, proxy: Any, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行進階測試
        
        Args:
            proxy: 代理對象
            test_config: 測試配置
            
        Returns:
            Dict: 進階測試結果
        """
        results = {
            'tests_passed': 0,
            'tests_failed': 0,
            'test_details': {}
        }
        
        try:
            # 速度測試
            if test_config.get('speed_test', False):
                try:
                    speed_result = await self.speed_tester.test_connection(proxy)
                    results['test_details']['speed_test'] = speed_result
                    if speed_result.get('success', False):
                        results['tests_passed'] += 1
                    else:
                        results['tests_failed'] += 1
                except Exception as e:
                    self.logger.warning(f"速度測試失敗: {e}")
                    results['tests_failed'] += 1
            
            # 地理位置測試
            if test_config.get('geolocation_test', False):
                try:
                    geo_result = await self.geo_validator.validate_geolocation(proxy)
                    results['test_details']['geolocation_test'] = geo_result
                    if geo_result.get('is_valid', False):
                        results['tests_passed'] += 1
                    else:
                        results['tests_failed'] += 1
                except Exception as e:
                    self.logger.warning(f"地理位置測試失敗: {e}")
                    results['tests_failed'] += 1
            
            # 匿名性測試
            if test_config.get('anonymity_test', False):
                try:
                    anonymity_result = await self.anonymity_tester.test_anonymity(proxy)
                    results['test_details']['anonymity_test'] = anonymity_result
                    if anonymity_result.get('success', False):
                        results['tests_passed'] += 1
                    else:
                        results['tests_failed'] += 1
                except Exception as e:
                    self.logger.warning(f"匿名性測試失敗: {e}")
                    results['tests_failed'] += 1
            
        except Exception as e:
            self.logger.error(f"進階測試執行失敗: {e}")
        
        return results
    
    def _calculate_overall_score(self, basic_validation: Dict[str, Any], 
                                advanced_tests: Dict[str, Any]) -> float:
        """
        計算綜合評分
        
        Args:
            basic_validation: 基礎驗證結果
            advanced_tests: 進階測試結果
            
        Returns:
            float: 綜合評分
        """
        if not basic_validation.get('success', False):
            return 0.0
        
        # 基礎分數（連接測試）
        base_score = 40.0
        
        # 進階測試分數
        advanced_score = 0.0
        test_details = advanced_tests.get('test_details', {})
        
        # 速度測試評分
        if 'speed_test' in test_details:
            speed_result = test_details['speed_test']
            if speed_result.get('success', False):
                # 根據響應時間評分
                response_time = speed_result.get('response_time', 10000)
                if response_time < 1000:  # < 1秒
                    advanced_score += 20
                elif response_time < 3000:  # < 3秒
                    advanced_score += 15
                elif response_time < 5000:  # < 5秒
                    advanced_score += 10
                else:
                    advanced_score += 5
        
        # 地理位置測試評分
        if 'geolocation_test' in test_details:
            geo_result = test_details['geolocation_test']
            if geo_result.get('is_valid', False):
                advanced_score += 15
        
        # 匿名性測試評分
        if 'anonymity_test' in test_details:
            anonymity_result = test_details['anonymity_test']
            if anonymity_result.get('success', False):
                overall_assessment = anonymity_result.get('overall_assessment', {})
                anonymity_score = overall_assessment.get('score', 0)
                # 將匿名性評分轉換為系統評分
                advanced_score += (anonymity_score * 25) / 100
        
        # 測試完成度獎勵
        total_tests = advanced_tests.get('tests_passed', 0) + advanced_tests.get('tests_failed', 0)
        if total_tests > 0:
            completion_rate = advanced_tests.get('tests_passed', 0) / total_tests
            advanced_score += completion_rate * 10
        
        return min(base_score + advanced_score, 100.0)
    
    def _generate_recommendations(self, basic_validation: Dict[str, Any], 
                                advanced_tests: Dict[str, Any]) -> List[str]:
        """
        生成改進建議
        
        Args:
            basic_validation: 基礎驗證結果
            advanced_tests: 進階測試結果
            
        Returns:
            List: 改進建議列表
        """
        recommendations = []
        
        # 基礎驗證建議
        if not basic_validation.get('success', False):
            recommendations.append("❌ 基礎連接測試失敗，代理可能無法使用")
            return recommendations
        
        # 進階測試建議
        test_details = advanced_tests.get('test_details', {})
        
        # 速度測試建議
        if 'speed_test' in test_details:
            speed_result = test_details['speed_test']
            if speed_result.get('success', False):
                response_time = speed_result.get('response_time', 0)
                if response_time > 5000:  # > 5秒
                    recommendations.append("⚠️ 代理響應時間較慢，可能影響使用體驗")
            else:
                recommendations.append("⚠️ 速度測試失敗，代理性能可能不穩定")
        
        # 地理位置測試建議
        if 'geolocation_test' in test_details:
            geo_result = test_details['geolocation_test']
            if not geo_result.get('is_valid', False):
                recommendations.append("⚠️ 地理位置驗證失敗，代理位置可能不準確")
        
        # 匿名性測試建議
        if 'anonymity_test' in test_details:
            anonymity_result = test_details['anonymity_test']
            if anonymity_result.get('success', False):
                overall_assessment = anonymity_result.get('overall_assessment', {})
                anonymity_level = overall_assessment.get('level', 'unknown')
                anonymity_score = overall_assessment.get('score', 0)
                
                if anonymity_score < 75:
                    recommendations.append(f"⚠️ 匿名性評分較低 ({anonymity_score}/100)，建議更換代理")
                
                if anonymity_level == 'transparent':
                    recommendations.append("⚠️ 檢測到透明代理，真實IP可能會洩露")
                
                # 添加匿名性測試的具體建議
                anonymity_recommendations = overall_assessment.get('recommendations', [])
                recommendations.extend(anonymity_recommendations)
            else:
                recommendations.append("⚠️ 匿名性測試失敗，無法評估代理的隱私保護能力")
        
        # 通用建議
        if not recommendations:
            recommendations.append("✅ 代理各項測試表現良好，可以正常使用")
        
        return recommendations
    
    def _create_failed_result(self, proxy: Any, basic_validation: Dict[str, Any], 
                            start_time: datetime) -> ProxyValidationResult:
        """
        創建失敗的驗證結果
        
        Args:
            proxy: 代理對象
            basic_validation: 基礎驗證結果
            start_time: 開始時間
            
        Returns:
            ProxyValidationResult: 失敗的驗證結果
        """
        return ProxyValidationResult(
            proxy_id=f"{proxy.ip}:{proxy.port}",
            success=False,
            overall_score=0,
            validation_time=(datetime.now() - start_time).total_seconds(),
            tests_passed=0,
            tests_failed=1,
            details={'error': basic_validation.get('message', '基礎驗證失敗')},
            timestamp=datetime.now(),
            recommendations=['基礎連接測試失敗，代理無法使用']
        )
    
    def _update_stats(self, result: ProxyValidationResult):
        """
        更新統計數據
        
        Args:
            result: 驗證結果
        """
        self.stats['total_validations'] += 1
        
        if result.success:
            self.stats['successful_validations'] += 1
        else:
            self.stats['failed_validations'] += 1
        
        # 更新平均驗證時間
        total_time = self.stats['avg_validation_time'] * (self.stats['total_validations'] - 1)
        self.stats['avg_validation_time'] = (total_time + result.validation_time) / self.stats['total_validations']
        
        # 更新平均分數
        total_score = self.stats['avg_score'] * (self.stats['total_validations'] - 1)
        self.stats['avg_score'] = (total_score + result.overall_score) / self.stats['total_validations']
        
        # 更新分數分布
        score = result.overall_score
        if score >= 90:
            self.stats['score_distribution']['excellent'] += 1
        elif score >= 75:
            self.stats['score_distribution']['good'] += 1
        elif score >= 60:
            self.stats['score_distribution']['average'] += 1
        elif score >= 40:
            self.stats['score_distribution']['poor'] += 1
        else:
            self.stats['score_distribution']['bad'] += 1
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        獲取系統統計數據
        
        Returns:
            Dict: 系統統計數據
        """
        return {
            'total_validations': self.stats['total_validations'],
            'successful_validations': self.stats['successful_validations'],
            'failed_validations': self.stats['failed_validations'],
            'success_rate': (
                self.stats['successful_validations'] / self.stats['total_validations'] * 100
                if self.stats['total_validations'] > 0 else 0
            ),
            'avg_validation_time': self.stats['avg_validation_time'],
            'avg_score': self.stats['avg_score'],
            'score_distribution': self.stats['score_distribution']
        }
    
    def reset_stats(self):
        """重置統計數據"""
        self.stats = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'avg_validation_time': 0.0,
            'avg_score': 0.0,
            'score_distribution': {
                'excellent': 0,
                'good': 0,
                'average': 0,
                'poor': 0,
                'bad': 0
            }
        }
        self.logger.info("系統統計數據已重置")


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    # 模擬代理對象
    class MockProxy:
        def __init__(self, ip, port, protocol='http'):
            self.ip = ip
            self.port = port
            self.protocol = protocol
            self.country = 'US'
            self.anonymity = 'elite'
    
    async def test_validation_system():
        # 創建驗證系統
        config = {
            'validation_timeout': 30,
            'max_concurrent_tests': 5,
            'min_score_threshold': 60
        }
        
        validation_system = ProxyValidationSystem(config)
        
        # 測試單個代理
        test_proxy = MockProxy('8.8.8.8', 8080)
        result = await validation_system.validate_proxy(test_proxy, 'comprehensive')
        
        print(f"驗證結果:")
        print(f"  代理: {result.proxy_id}")
        print(f"  成功: {result.success}")
        print(f"  總分: {result.overall_score:.1f}/100")
        print(f"  耗時: {result.validation_time:.1f}s")
        print(f"  建議: {result.recommendations}")
        
        # 顯示系統統計
        stats = validation_system.get_system_stats()
        print(f"\n系統統計:")
        print(f"  總驗證數: {stats['total_validations']}")
        print(f"  成功率: {stats['success_rate']:.1f}%")
        print(f"  平均分數: {stats['avg_score']:.1f}")
    
    # 運行測試
    asyncio.run(test_validation_system())