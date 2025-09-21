#!/usr/bin/env python3
"""
整合測試腳本

測試所有驗證組件的整合運行
"""

import asyncio
import logging
from typing import Dict, List, Any
from pathlib import Path
import json
from datetime import datetime

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 導入獨立系統
from standalone_validation_system import StandaloneValidationSystem, ProxyData


class IntegrationTestSuite:
    """整合測試套件"""
    
    def __init__(self):
        """初始化測試套件"""
        self.system = StandaloneValidationSystem()
        self.test_results = []
        self.start_time = None
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """
        運行所有測試
        
        Returns:
            Dict: 測試結果
        """
        self.start_time = datetime.now()
        logger.info("開始整合測試")
        
        tests = [
            self.test_single_proxy_validation,
            self.test_batch_validation,
            self.test_system_performance,
            self.test_error_handling,
            self.test_data_export,
            self.test_component_integration
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test in tests:
            test_name = test.__name__
            logger.info(f"運行測試: {test_name}")
            
            try:
                result = await test()
                results[test_name] = {
                    'success': result['success'],
                    'details': result.get('details', {}),
                    'duration': result.get('duration', 0),
                    'error': result.get('error')
                }
                
                if result['success']:
                    passed += 1
                    logger.info(f"✅ {test_name} 通過")
                else:
                    logger.error(f"❌ {test_name} 失敗: {result.get('error', '未知錯誤')}")
                    
            except Exception as e:
                results[test_name] = {
                    'success': False,
                    'error': str(e),
                    'duration': 0
                }
                logger.error(f"❌ {test_name} 異常: {e}")
        
        # 總體結果
        overall_result = {
            'total_tests': total,
            'passed_tests': passed,
            'failed_tests': total - passed,
            'success_rate': passed / total if total > 0 else 0,
            'total_duration': (datetime.now() - self.start_time).total_seconds(),
            'test_details': results,
            'system_stats': self.system.get_stats()
        }
        
        logger.info(f"整合測試完成: {passed}/{total} 通過")
        return overall_result
    
    async def test_single_proxy_validation(self) -> Dict[str, Any]:
        """測試單個代理驗證"""
        start_time = datetime.now()
        
        try:
            # 創建測試代理
            test_proxy = ProxyData(
                ip="8.8.8.8",
                port=8080,
                protocol="http",
                country="US"
            )
            
            # 執行驗證
            result = await self.system.validate_proxy(test_proxy)
            
            # 驗證結果
            success = (
                result is not None and
                hasattr(result, 'proxy') and
                hasattr(result, 'score') and
                hasattr(result, 'success') and
                result.timestamp is not None
            )
            
            return {
                'success': success,
                'details': {
                    'proxy_score': result.score if result else 0,
                    'proxy_status': result.success if result else False,
                    'validation_time': result.duration if result else 0
                },
                'duration': (datetime.now() - start_time).total_seconds()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': (datetime.now() - start_time).total_seconds()
            }
    
    async def test_batch_validation(self) -> Dict[str, Any]:
        """測試批量驗證"""
        start_time = datetime.now()
        
        try:
            # 創建測試代理列表
            test_proxies = [
                ProxyData(f"8.8.8.{i}", 8080, "http", "US")
                for i in range(1, 6)
            ]
            
            # 執行批量驗證
            results = await self.system.validate_batch(test_proxies, max_concurrent=3)
            
            # 驗證結果
            success = (
                len(results) == len(test_proxies) and
                all(isinstance(r, type(results[0])) for r in results) and
                all(hasattr(r, 'score') for r in results)
            )
            
            # 統計信息
            valid_results = [r for r in results if r.success]
            avg_score = sum(r.score for r in results) / len(results) if results else 0
            
            return {
                'success': success,
                'details': {
                    'total_proxies': len(test_proxies),
                    'processed_proxies': len(results),
                    'valid_proxies': len(valid_results),
                    'average_score': avg_score,
                    'success_rate': len(valid_results) / len(results) if results else 0
                },
                'duration': (datetime.now() - start_time).total_seconds()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': (datetime.now() - start_time).total_seconds()
            }
    
    async def test_system_performance(self) -> Dict[str, Any]:
        """測試系統性能"""
        start_time = datetime.now()
        
        try:
            # 創建多個代理進行壓力測試
            test_proxies = [
                ProxyData(f"192.168.1.{i}", 8080, "http", "US")
                for i in range(1, 11)
            ]
            
            # 記錄開始時的系統狀態
            stats_before = self.system.get_stats()
            
            # 執行批量驗證
            results = await self.system.validate_batch(test_proxies, max_concurrent=5)
            
            # 記錄結束時的系統狀態
            stats_after = self.system.get_stats()
            
            # 計算性能指標
            total_time = (datetime.now() - start_time).total_seconds()
            avg_time_per_proxy = total_time / len(results) if results else 0
            throughput = len(results) / total_time if total_time > 0 else 0
            
            success = (
                len(results) == len(test_proxies) and
                stats_after['total_validations'] > stats_before['total_validations']
            )
            
            return {
                'success': success,
                'details': {
                    'total_time': total_time,
                    'avg_time_per_proxy': avg_time_per_proxy,
                    'throughput_per_second': throughput,
                    'validations_before': stats_before['total_validations'],
                    'validations_after': stats_after['total_validations'],
                    'total_processed': len(results)
                },
                'duration': total_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': (datetime.now() - start_time).total_seconds()
            }
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """測試錯誤處理"""
        start_time = datetime.now()
        
        try:
            # 測試各種錯誤情況
            error_cases = [
                # 無效代理
                ProxyData("", 0, "http"),
                ProxyData("invalid.ip", 99999, "http"),
                ProxyData("256.256.256.256", 8080, "http"),
            ]
            
            results = []
            for proxy in error_cases:
                try:
                    result = await self.system.validate_proxy(proxy)
                    results.append(result)
                except Exception as e:
                    logger.warning(f"預期的錯誤處理: {e}")
                    results.append(None)
            
            # 驗證錯誤處理
            success = (
                len(results) == len(error_cases) and
                all(r is not None for r in results) and
                all(not r.success for r in results if r)
            )
            
            return {
                'success': success,
                'details': {
                    'error_cases_tested': len(error_cases),
                    'results_generated': len(results),
                    'all_handled': all(r is not None for r in results)
                },
                'duration': (datetime.now() - start_time).total_seconds()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': (datetime.now() - start_time).total_seconds()
            }
    
    async def test_data_export(self) -> Dict[str, Any]:
        """測試數據導出"""
        start_time = datetime.now()
        
        try:
            # 創建一些測試結果
            test_proxies = [
                ProxyData("10.0.0.1", 8080, "http", "US"),
                ProxyData("10.0.0.2", 8080, "https", "UK"),
            ]
            
            results = await self.system.validate_batch(test_proxies)
            
            # 導出結果
            export_path = "integration_test_results.json"
            self.system.export_results(results, export_path)
            
            # 驗證導出文件
            file_exists = Path(export_path).exists()
            file_valid = False
            file_size = 0
            
            if file_exists:
                file_size = Path(export_path).stat().st_size
                try:
                    with open(export_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    file_valid = (
                        'results' in data and
                        'system_stats' in data and
                        len(data['results']) == len(results)
                    )
                except Exception:
                    file_valid = False
            
            success = file_exists and file_valid and file_size > 0
            
            return {
                'success': success,
                'details': {
                    'file_exists': file_exists,
                    'file_valid': file_valid,
                    'file_size_bytes': file_size,
                    'export_path': export_path
                },
                'duration': (datetime.now() - start_time).total_seconds()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': (datetime.now() - start_time).total_seconds()
            }
    
    async def test_component_integration(self) -> Dict[str, Any]:
        """測試組件整合"""
        start_time = datetime.now()
        
        try:
            # 驗證所有組件都存在且可用
            components = [
                ('scoring_engine', hasattr(self.system, 'scoring_engine')),
                ('geo_validator', hasattr(self.system, 'geo_validator')),
                ('speed_tester', hasattr(self.system, 'speed_tester')),
                ('anonymity_tester', hasattr(self.system, 'anonymity_tester'))
            ]
            
            # 測試組件功能
            test_proxy = ProxyData("8.8.8.8", 8080, "http", "US")
            
            # 測試各個組件
            component_tests = []
            
            try:
                score_result = await self.system.scoring_engine.calculate_score({})
                component_tests.append(('scoring_engine', True))
            except Exception as e:
                component_tests.append(('scoring_engine', False))
                logger.warning(f"評分引擎測試失敗: {e}")
            
            try:
                geo_result = await self.system.geo_validator.validate_location(test_proxy)
                component_tests.append(('geo_validator', True))
            except Exception as e:
                component_tests.append(('geo_validator', False))
                logger.warning(f"地理位置驗證器測試失敗: {e}")
            
            try:
                speed_result = await self.system.speed_tester.test_speed(test_proxy)
                component_tests.append(('speed_tester', True))
            except Exception as e:
                component_tests.append(('speed_tester', False))
                logger.warning(f"速度測試器測試失敗: {e}")
            
            try:
                anonymity_result = await self.system.anonymity_tester.test_anonymity(test_proxy)
                component_tests.append(('anonymity_tester', True))
            except Exception as e:
                component_tests.append(('anonymity_tester', False))
                logger.warning(f"匿名性測試器測試失敗: {e}")
            
            # 驗證結果
            all_components_exist = all(exists for _, exists in components)
            all_components_work = all(works for _, works in component_tests)
            
            success = all_components_exist and all_components_work
            
            return {
                'success': success,
                'details': {
                    'components_exist': dict(components),
                    'components_work': dict(component_tests),
                    'all_exist': all_components_exist,
                    'all_work': all_components_work
                },
                'duration': (datetime.now() - start_time).total_seconds()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': (datetime.now() - start_time).total_seconds()
            }


async def main():
    """主函數"""
    print("=== 代理驗證系統整合測試 ===")
    
    # 創建測試套件
    test_suite = IntegrationTestSuite()
    
    # 運行所有測試
    print("開始運行整合測試...")
    results = await test_suite.run_all_tests()
    
    # 顯示結果
    print(f"\n=== 測試結果總結 ===")
    print(f"總測試數: {results['total_tests']}")
    print(f"通過數: {results['passed_tests']}")
    print(f"失敗數: {results['failed_tests']}")
    print(f"成功率: {results['success_rate']:.1%}")
    print(f"總耗時: {results['total_duration']:.1f}秒")
    
    # 顯示詳細結果
    print(f"\n=== 詳細測試結果 ===")
    for test_name, test_result in results['test_details'].items():
        status = "✅ 通過" if test_result['success'] else "❌ 失敗"
        print(f"{test_name}: {status}")
        
        if not test_result['success'] and test_result.get('error'):
            print(f"  錯誤: {test_result['error']}")
        
        if 'details' in test_result:
            for key, value in test_result['details'].items():
                print(f"  {key}: {value}")
        
        print()
    
    # 顯示系統統計
    stats = results['system_stats']
    print(f"=== 系統統計 ===")
    print(f"總驗證數: {stats['total_validations']}")
    print(f"成功驗證: {stats['successful_validations']}")
    print(f"失敗驗證: {stats['failed_validations']}")
    print(f"系統成功率: {stats['success_rate']:.1%}")
    print(f"平均評分: {stats['average_score']:.1f}")
    print(f"系統運行時間: {stats['uptime_human']}")
    
    # 導出完整測試報告
    try:
        report_path = "integration_test_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n完整測試報告已導出到: {report_path}")
    except Exception as e:
        print(f"\n測試報告導出失敗: {e}")
    
    return results


if __name__ == "__main__":
    # 運行整合測試
    results = asyncio.run(main())