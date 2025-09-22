#!/usr/bin/env python3
"""
代理收集器部署測試腳本

此腳本用於驗證代理收集器的完整部署，包括：
- 數據庫連接測試
- 健康檢查驗證
- 監控系統測試
- API端點測試
- 代理功能測試
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
import logging

# 添加後端模塊路徑
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.config_manager import get_config
from app.core.database_manager import get_database_manager
from app.core.health_check import get_health_check_manager
from app.core.monitoring import get_metrics_exporter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeploymentTester:
    """部署測試器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """記錄測試結果"""
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        logger.info(f"{status_symbol} {test_name}: {status} {details}")
        
    async def test_database_connection(self) -> bool:
        """測試數據庫連接"""
        try:
            db_manager = get_database_manager()
            
            # 測試數據庫連接
            async with db_manager.get_session() as session:
                result = await session.execute("SELECT 1")
                await result.scalar()
                
            self.log_test("數據庫連接", "PASS", "成功連接到數據庫")
            return True
            
        except Exception as e:
            self.log_test("數據庫連接", "FAIL", f"連接失敗: {str(e)}")
            return False
            
    async def test_health_check(self) -> bool:
        """測試健康檢查"""
        try:
            health_manager = get_health_check_manager()
            
            # 運行健康檢查
            health_status = await health_manager.run_all_checks()
            
            if health_status.overall_status == "healthy":
                self.log_test("健康檢查", "PASS", f"系統健康: {len(health_status.results)}個檢查通過")
                return True
            else:
                self.log_test("健康檢查", "FAIL", f"系統不健康: {health_status.summary}")
                return False
                
        except Exception as e:
            self.log_test("健康檢查", "FAIL", f"健康檢查失敗: {str(e)}")
            return False
            
    async def test_monitoring_system(self) -> bool:
        """測試監控系統"""
        try:
            metrics_exporter = get_metrics_exporter()
            
            # 收集系統指標
            system_metrics = await metrics_exporter.collect_system_metrics()
            
            if system_metrics:
                self.log_test("監控系統", "PASS", f"成功收集{len(system_metrics)}個系統指標")
                return True
            else:
                self.log_test("監控系統", "FAIL", "無法收集系統指標")
                return False
                
        except Exception as e:
            self.log_test("監控系統", "FAIL", f"監控系統測試失敗: {str(e)}")
            return False
            
    async def test_api_endpoints(self) -> bool:
        """測試API端點"""
        endpoints = [
            "/health",
            "/metrics",
            "/api/v1/proxies",
            "/api/v1/stats"
        ]
        
        all_passed = True
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                try:
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        if response.status == 200:
                            self.log_test(f"API端點 {endpoint}", "PASS", f"狀態碼: {response.status}")
                        else:
                            self.log_test(f"API端點 {endpoint}", "FAIL", f"狀態碼: {response.status}")
                            all_passed = False
                            
                except Exception as e:
                    self.log_test(f"API端點 {endpoint}", "FAIL", f"請求失敗: {str(e)}")
                    all_passed = False
                    
        return all_passed
        
    async def test_proxy_functionality(self) -> bool:
        """測試代理功能"""
        try:
            async with aiohttp.ClientSession() as session:
                # 測試獲取代理列表
                async with session.get(f"{self.base_url}/api/v1/proxies") as response:
                    if response.status == 200:
                        data = await response.json()
                        proxy_count = len(data.get("proxies", []))
                        self.log_test("代理功能", "PASS", f"成功獲取{proxy_count}個代理")
                        return True
                    else:
                        self.log_test("代理功能", "FAIL", f"無法獲取代理列表: {response.status}")
                        return False
                        
        except Exception as e:
            self.log_test("代理功能", "FAIL", f"代理功能測試失敗: {str(e)}")
            return False
            
    async def test_prometheus_metrics(self) -> bool:
        """測試Prometheus指標"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/metrics") as response:
                    if response.status == 200:
                        metrics_text = await response.text()
                        
                        # 檢查關鍵指標
                        required_metrics = [
                            "http_requests_total",
                            "system_cpu_usage_percent",
                            "proxy_count_total"
                        ]
                        
                        found_metrics = []
                        for metric in required_metrics:
                            if metric in metrics_text:
                                found_metrics.append(metric)
                                
                        if found_metrics:
                            self.log_test("Prometheus指標", "PASS", f"找到指標: {', '.join(found_metrics)}")
                            return True
                        else:
                            self.log_test("Prometheus指標", "FAIL", "未找到關鍵指標")
                            return False
                    else:
                        self.log_test("Prometheus指標", "FAIL", f"指標端點返回狀態碼: {response.status}")
                        return False
                        
        except Exception as e:
            self.log_test("Prometheus指標", "FAIL", f"Prometheus指標測試失敗: {str(e)}")
            return False
            
    async def run_all_tests(self) -> Dict:
        """運行所有測試"""
        logger.info("開始代理收集器部署測試...")
        
        tests = [
            ("數據庫連接", self.test_database_connection),
            ("健康檢查", self.test_health_check),
            ("監控系統", self.test_monitoring_system),
            ("API端點", self.test_api_endpoints),
            ("代理功能", self.test_proxy_functionality),
            ("Prometheus指標", self.test_prometheus_metrics)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                logger.info(f"正在運行測試: {test_name}")
                result = await test_func()
                results[test_name] = result
                await asyncio.sleep(1)  # 避免過快請求
                
            except Exception as e:
                logger.error(f"測試 {test_name} 發生異常: {str(e)}")
                results[test_name] = False
                
        # 生成測試報告
        self.generate_test_report(results)
        
        return {
            "overall_status": "PASS" if all(results.values()) else "FAIL",
            "test_results": results,
            "detailed_results": self.test_results
        }
        
    def generate_test_report(self, results: Dict):
        """生成測試報告"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r)
        failed_tests = total_tests - passed_tests
        
        logger.info("\n" + "="*50)
        logger.info("代理收集器部署測試報告")
        logger.info("="*50)
        logger.info(f"總測試數: {total_tests}")
        logger.info(f"通過測試: {passed_tests}")
        logger.info(f"失敗測試: {failed_tests}")
        logger.info(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            logger.info("\n失敗的測試:")
            for test_name, passed in results.items():
                if not passed:
                    logger.info(f"  ❌ {test_name}")
                    
        logger.info("\n詳細結果:")
        for result in self.test_results:
            status_symbol = "✅" if result["status"] == "PASS" else "❌"
            logger.info(f"  {status_symbol} {result['test_name']}: {result['status']}")
            if result["details"]:
                logger.info(f"    詳情: {result['details']}")
                
        logger.info("="*50)
        
async def main():
    """主函數"""
    # 從環境變量獲取測試參數
    base_url = os.getenv("TEST_BASE_URL", "http://localhost:8000")
    
    tester = DeploymentTester(base_url)
    
    try:
        # 運行所有測試
        results = await tester.run_all_tests()
        
        # 保存測試結果
        results_file = Path(__file__).parent / "test-results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        logger.info(f"測試結果已保存到: {results_file}")
        
        # 根據測試結果退出
        sys.exit(0 if results["overall_status"] == "PASS" else 1)
        
    except KeyboardInterrupt:
        logger.info("測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())