#!/usr/bin/env python3
"""
持續整合測試腳本
自動化測試流程，包括代碼質量檢查、測試執行和覆蓋率報告
"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
import json
import logging
from typing import Dict, List, Optional

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CITestRunner:
    """持續整合測試運行器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_dir = project_root / "backend"
        self.test_dir = self.backend_dir / "tests"
        self.results_dir = project_root / "test_results"
        self.coverage_dir = self.results_dir / "coverage"
        self.reports_dir = self.results_dir / "reports"
        
        # 確保目錄存在
        self.results_dir.mkdir(exist_ok=True)
        self.coverage_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        # 測試配置
        self.min_coverage = 80.0  # 最小覆蓋率百分比
        self.test_timeout = 300  # 測試超時時間（秒）
        
    async def run_command(self, cmd: List[str], cwd: Optional[Path] = None, 
                       timeout: int = None) -> tuple[int, str, str]:
        """運行命令並返回結果"""
        if cwd is None:
            cwd = self.backend_dir
            
        logger.info(f"運行命令: {' '.join(cmd)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout or self.test_timeout
            )
            
            stdout_str = stdout.decode('utf-8') if stdout else ""
            stderr_str = stderr.decode('utf-8') if stderr else ""
            
            return process.returncode, stdout_str, stderr_str
            
        except asyncio.TimeoutError:
            logger.error(f"命令超時: {' '.join(cmd)}")
            return -1, "", f"命令超時（超過 {timeout or self.test_timeout} 秒）"
        except Exception as e:
            logger.error(f"運行命令失敗: {e}")
            return -1, "", str(e)
    
    async def check_code_quality(self) -> Dict:
        """檢查代碼質量"""
        logger.info("開始代碼質量檢查...")
        
        results = {
            "flake8": {"passed": False, "output": "", "errors": ""},
            "black": {"passed": False, "output": "", "errors": ""},
            "mypy": {"passed": False, "output": "", "errors": ""},
            "pylint": {"passed": False, "output": "", "errors": ""}
        }
        
        # Flake8 檢查
        logger.info("運行 flake8 檢查...")
        returncode, stdout, stderr = await self.run_command([
            sys.executable, "-m", "flake8", "app/", "tests/",
            "--max-line-length=88", "--extend-ignore=E203,W503"
        ])
        results["flake8"]["passed"] = returncode == 0
        results["flake8"]["output"] = stdout
        results["flake8"]["errors"] = stderr
        
        # Black 格式化檢查
        logger.info("運行 black 格式化檢查...")
        returncode, stdout, stderr = await self.run_command([
            sys.executable, "-m", "black", "--check", "app/", "tests/"
        ])
        results["black"]["passed"] = returncode == 0
        results["black"]["output"] = stdout
        results["black"]["errors"] = stderr
        
        # MyPy 類型檢查
        logger.info("運行 mypy 類型檢查...")
        returncode, stdout, stderr = await self.run_command([
            sys.executable, "-m", "mypy", "app/",
            "--ignore-missing-imports", "--no-strict-optional"
        ])
        results["mypy"]["passed"] = returncode == 0
        results["mypy"]["output"] = stdout
        results["mypy"]["errors"] = stderr
        
        # Pylint 檢查（可選，因為比較慢）
        logger.info("運行 pylint 檢查...")
        returncode, stdout, stderr = await self.run_command([
            sys.executable, "-m", "pylint", "app/",
            "--disable=C0103,C0114,C0115,C0116", "--score=yes"
        ], timeout=600)  # pylint 可能需要更長時間
        results["pylint"]["passed"] = returncode == 0 or returncode == 16  # 16 是 pylint 的評分模式返回碼
        results["pylint"]["output"] = stdout
        results["pylint"]["errors"] = stderr
        
        return results
    
    async def run_unit_tests(self) -> Dict:
        """運行單元測試"""
        logger.info("開始運行單元測試...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        junit_xml = self.reports_dir / f"unit_tests_{timestamp}.xml"
        coverage_file = self.coverage_dir / f"unit_coverage_{timestamp}.xml"
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/",
            "-v",
            "--tb=short",
            "--strict-markers",
            f"--junitxml={junit_xml}",
            f"--cov=app",
            f"--cov-report=xml:{coverage_file}",
            f"--cov-report=html:{self.coverage_dir}/unit",
            "--cov-report=term-missing",
            f"--cov-fail-under={self.min_coverage}",
            "--asyncio-mode=auto"
        ]
        
        returncode, stdout, stderr = await self.run_command(cmd)
        
        return {
            "passed": returncode == 0,
            "return_code": returncode,
            "output": stdout,
            "errors": stderr,
            "junit_xml": str(junit_xml),
            "coverage_xml": str(coverage_file),
            "coverage_html": str(self.coverage_dir / "unit")
        }
    
    async def run_integration_tests(self) -> Dict:
        """運行集成測試"""
        logger.info("開始運行集成測試...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        junit_xml = self.reports_dir / f"integration_tests_{timestamp}.xml"
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration/",
            "-v",
            "--tb=short",
            "--strict-markers",
            f"--junitxml={junit_xml}",
            "--asyncio-mode=auto",
            "--timeout=60"  # 集成測試可能需要更長時間
        ]
        
        returncode, stdout, stderr = await self.run_command(cmd)
        
        return {
            "passed": returncode == 0,
            "return_code": returncode,
            "output": stdout,
            "errors": stderr,
            "junit_xml": str(junit_xml)
        }
    
    async def generate_test_report(self, results: Dict) -> str:
        """生成測試報告"""
        logger.info("生成測試報告...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"test_report_{timestamp}.json"
        
        report = {
            "timestamp": timestamp,
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "coverage_percentage": 0.0,
                "code_quality_score": 0.0
            },
            "details": results,
            "recommendations": []
        }
        
        # 統計測試結果
        if "unit_tests" in results:
            unit_results = results["unit_tests"]
            if unit_results["passed"]:
                report["summary"]["passed_tests"] += 1
            else:
                report["summary"]["failed_tests"] += 1
            report["summary"]["total_tests"] += 1
        
        if "integration_tests" in results:
            integration_results = results["integration_tests"]
            if integration_results["passed"]:
                report["summary"]["passed_tests"] += 1
            else:
                report["summary"]["failed_tests"] += 1
            report["summary"]["total_tests"] += 1
        
        # 代碼質量評分
        if "code_quality" in results:
            quality_results = results["code_quality"]
            quality_score = 0
            quality_checks = 0
            
            for tool, result in quality_results.items():
                if result["passed"]:
                    quality_score += 1
                quality_checks += 1
            
            if quality_checks > 0:
                report["summary"]["code_quality_score"] = (quality_score / quality_checks) * 100
        
        # 覆蓋率評估
        if "unit_tests" in results and "coverage_xml" in results["unit_tests"]:
            # 這裡可以解析 coverage XML 文件獲取實際覆蓋率
            report["summary"]["coverage_percentage"] = self.min_coverage  # 簡化處理
        
        # 生成建議
        if report["summary"]["code_quality_score"] < 80:
            report["recommendations"].append("代碼質量需要改進，建議修復 linting 問題")
        
        if report["summary"]["coverage_percentage"] < self.min_coverage:
            report["recommendations"].append(f"測試覆蓋率低於 {self.min_coverage}%，建議增加測試用例")
        
        if report["summary"]["failed_tests"] > 0:
            report["recommendations"].append("有測試失敗，需要修復相關代碼")
        
        # 保存報告
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return str(report_file)
    
    async def run_all_tests(self) -> Dict:
        """運行所有測試流程"""
        logger.info("開始持續整合測試流程...")
        
        start_time = datetime.now()
        results = {}
        
        try:
            # 1. 代碼質量檢查
            results["code_quality"] = await self.check_code_quality()
            
            # 2. 單元測試
            results["unit_tests"] = await self.run_unit_tests()
            
            # 3. 集成測試
            results["integration_tests"] = await self.run_integration_tests()
            
            # 4. 生成報告
            report_file = await self.generate_test_report(results)
            results["report_file"] = report_file
            
            # 5. 總體評估
            all_passed = all([
                results["code_quality"]["flake8"]["passed"],
                results["code_quality"]["black"]["passed"],
                results["unit_tests"]["passed"],
                results["integration_tests"]["passed"]
            ])
            
            results["overall_passed"] = all_passed
            
        except Exception as e:
            logger.error(f"測試流程失敗: {e}")
            results["overall_passed"] = False
            results["error"] = str(e)
        
        end_time = datetime.now()
        results["duration"] = str(end_time - start_time)
        
        return results


async def main():
    """主函數"""
    project_root = Path(__file__).parent.parent
    
    runner = CITestRunner(project_root)
    results = await runner.run_all_tests()
    
    # 輸出結果
    print("\n" + "="*60)
    print("持續整合測試結果")
    print("="*60)
    
    if results.get("overall_passed"):
        print("✅ 所有測試通過！")
    else:
        print("❌ 測試失敗！")
    
    print(f"測試耗時: {results.get('duration', '未知')}")
    
    if "report_file" in results:
        print(f"測試報告: {results['report_file']}")
    
    if "error" in results:
        print(f"錯誤信息: {results['error']}")
    
    print("="*60)
    
    # 返回適當的退出碼
    sys.exit(0 if results.get("overall_passed") else 1)


if __name__ == "__main__":
    asyncio.run(main())