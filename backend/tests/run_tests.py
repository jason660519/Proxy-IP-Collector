"""
測試運行器腳本
統一管理所有測試的執行和報告生成
"""

import pytest
import sys
import os
from pathlib import Path
import json
import time
from datetime import datetime
import subprocess
from typing import Dict, List, Optional


class TestRunner:
    """測試運行器類"""
    
    def __init__(self, project_root: str = None):
        """初始化測試運行器"""
        if project_root is None:
            self.project_root = Path(__file__).parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.test_root = self.project_root / "tests"
        self.reports_dir = self.project_root / "test_reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        # 測試配置
        self.test_configs = {
            "unit": {
                "path": self.test_root / "unit",
                "pattern": "test_*.py",
                "markers": ["unit"],
                "description": "單元測試"
            },
            "integration": {
                "path": self.test_root / "integration",
                "pattern": "test_*.py",
                "markers": ["integration"],
                "description": "集成測試"
            },
            "e2e": {
                "path": self.test_root / "e2e",
                "pattern": "test_*.py",
                "markers": ["e2e"],
                "description": "端到端測試"
            },
            "all": {
                "path": self.test_root,
                "pattern": "test_*.py",
                "markers": [],
                "description": "所有測試"
            }
        }
    
    def generate_report_filename(self, test_type: str) -> str:
        """生成報告文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{test_type}_test_report_{timestamp}"
    
    def run_tests(self, test_type: str = "all", 
                  coverage: bool = True, 
                  verbose: bool = True,
                  parallel: bool = False) -> Dict:
        """運行指定類型的測試"""
        
        if test_type not in self.test_configs:
            raise ValueError(f"不支持的測試類型: {test_type}")
        
        config = self.test_configs[test_type]
        report_name = self.generate_report_filename(test_type)
        
        print(f"\n{'='*60}")
        print(f"開始運行 {config['description']}")
        print(f"測試路徑: {config['path']}")
        print(f"報告名稱: {report_name}")
        print(f"{'='*60}\n")
        
        # 構建pytest命令
        cmd = ["python", "-m", "pytest"]
        
        # 添加測試路徑
        cmd.append(str(config['path']))
        
        # 添加測試模式
        if config['pattern']:
            cmd.extend(["-k", config['pattern']])
        
        # 添加標記
        if config['markers']:
            cmd.extend(["-m", " or ".join(config['markers'])])
        
        # 添加輸出選項
        if verbose:
            cmd.append("-v")
        
        # 添加覆蓋率選項
        if coverage:
            cmd.extend([
                "--cov=app",
                "--cov-report=html",
                "--cov-report=term-missing",
                f"--cov-report=html:{self.reports_dir / f'{report_name}_coverage'}"
            ])
        
        # 添加並行選項
        if parallel:
            cmd.extend(["-n", "auto"])
        
        # 添加報告選項
        cmd.extend([
            f"--html={self.reports_dir / f'{report_name}.html'}",
            "--self-contained-html",
            f"--json-report-file={self.reports_dir / f'{report_name}.json'}"
        ])
        
        # 添加其他選項
        cmd.extend([
            "--tb=short",
            "--strict-markers",
            "--disable-warnings"
        ])
        
        # 記錄開始時間
        start_time = time.time()
        
        try:
            # 執行測試
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            # 記錄結束時間
            end_time = time.time()
            duration = end_time - start_time
            
            # 解析結果
            test_result = self._parse_test_results(result.stdout, result.stderr, result.returncode)
            test_result.update({
                "test_type": test_type,
                "duration": duration,
                "report_name": report_name,
                "command": " ".join(cmd),
                "return_code": result.returncode
            })
            
            # 保存詳細結果
            self._save_test_results(test_result)
            
            # 打印摘要
            self._print_test_summary(test_result)
            
            return test_result
            
        except Exception as e:
            print(f"運行測試時出錯: {e}")
            return {
                "test_type": test_type,
                "duration": time.time() - start_time,
                "error": str(e),
                "success": False
            }
    
    def _parse_test_results(self, stdout: str, stderr: str, returncode: int) -> Dict:
        """解析測試結果"""
        
        # 基本結果
        result = {
            "success": returncode == 0,
            "stdout": stdout,
            "stderr": stderr,
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "failures": []
        }
        
        # 解析測試數量
        lines = stdout.split('\n')
        for line in lines:
            if 'passed' in line and 'failed' in line:
                # 解析類似 "5 passed, 2 failed, 1 skipped"
                parts = line.split(',')
                for part in parts:
                    part = part.strip()
                    if 'passed' in part:
                        result['passed'] = int(part.split()[0])
                    elif 'failed' in part:
                        result['failed'] = int(part.split()[0])
                    elif 'skipped' in part:
                        result['skipped'] = int(part.split()[0])
                result['total_tests'] = result['passed'] + result['failed'] + result['skipped']
            elif 'collected' in line and 'items' in line:
                # 解析類似 "collected 8 items"
                try:
                    result['total_tests'] = int(line.split('collected')[1].split('items')[0].strip())
                except:
                    pass
        
        # 解析失敗詳情
        if result['failed'] > 0:
            failure_lines = []
            in_failure = False
            for line in lines:
                if line.startswith('FAILED'):
                    in_failure = True
                    failure_lines.append(line)
                elif in_failure and line.strip() and not line.startswith(' '):
                    in_failure = False
                elif in_failure:
                    failure_lines.append(line)
            
            result['failures'] = failure_lines
        
        return result
    
    def _save_test_results(self, result: Dict):
        """保存測試結果"""
        
        # 保存JSON格式的詳細結果
        json_file = self.reports_dir / f"{result['report_name']}_detailed.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # 保存簡化結果
        summary = {
            "test_type": result["test_type"],
            "success": result["success"],
            "total_tests": result["total_tests"],
            "passed": result["passed"],
            "failed": result["failed"],
            "skipped": result["skipped"],
            "duration": result["duration"],
            "timestamp": datetime.now().isoformat()
        }
        
        summary_file = self.reports_dir / "test_summary.json"
        
        # 讀取現有的摘要
        if summary_file.exists():
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    existing_summary = json.load(f)
            except:
                existing_summary = []
        else:
            existing_summary = []
        
        # 添加新的結果
        existing_summary.append(summary)
        
        # 只保留最近的50次測試結果
        if len(existing_summary) > 50:
            existing_summary = existing_summary[-50:]
        
        # 保存更新後的摘要
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(existing_summary, f, indent=2, ensure_ascii=False)
    
    def _print_test_summary(self, result: Dict):
        """打印測試摘要"""
        
        print(f"\n{'='*60}")
        print(f"測試完成: {result['test_type']}")
        print(f"總耗時: {result['duration']:.2f}秒")
        print(f"總測試數: {result['total_tests']}")
        print(f"通過: {result['passed']}")
        print(f"失敗: {result['failed']}")
        print(f"跳過: {result['skipped']}")
        
        # 計算通過率（防止除零錯誤）
        pass_rate = (result['passed'] / result['total_tests'] * 100) if result['total_tests'] > 0 else 0.0
        print(f"通過率: {pass_rate:.1f}%")
        
        if result['success']:
            print("✅ 測試通過")
        else:
            print("❌ 測試失敗")
            if result['failures']:
                print("\n失敗詳情:")
                for failure in result['failures'][:5]:  # 只顯示前5個失敗
                    print(f"  {failure}")
        
        print(f"報告文件: {result['report_name']}")
        print(f"{'='*60}\n")
    
    def run_all_tests(self, coverage: bool = True, parallel: bool = False) -> Dict:
        """運行所有類型的測試"""
        
        results = {}
        
        for test_type in ["unit", "integration", "e2e"]:
            print(f"\n{'='*60}")
            print(f"開始運行 {test_type} 測試")
            print(f"{'='*60}\n")
            
            result = self.run_tests(test_type, coverage=coverage, parallel=parallel)
            results[test_type] = result
            
            # 如果某個類型的測試失敗，可以選擇停止
            if not result['success']:
                print(f"⚠️  {test_type} 測試失敗，是否繼續運行其他測試？")
                # 這裡可以添加用戶確認邏輯
        
        # 生成總體報告
        self._generate_overall_report(results)
        
        return results
    
    def _generate_overall_report(self, results: Dict):
        """生成總體測試報告"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        overall_report = {
            "timestamp": timestamp,
            "summary": {
                "total_tests": 0,
                "total_passed": 0,
                "total_failed": 0,
                "total_skipped": 0,
                "total_duration": 0
            },
            "details": results
        }
        
        # 計算總體統計
        for test_type, result in results.items():
            if 'total_tests' in result:
                overall_report["summary"]["total_tests"] += result["total_tests"]
                overall_report["summary"]["total_passed"] += result["passed"]
                overall_report["summary"]["total_failed"] += result["failed"]
                overall_report["summary"]["total_skipped"] += result["skipped"]
                overall_report["summary"]["total_duration"] += result["duration"]
        
        # 保存總體報告
        report_file = self.reports_dir / f"overall_test_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(overall_report, f, indent=2, ensure_ascii=False)
        
        # 打印總體摘要
        print(f"\n{'='*80}")
        print("總體測試報告")
        print(f"{'='*80}")
        print(f"總測試數: {overall_report['summary']['total_tests']}")
        print(f"總通過: {overall_report['summary']['total_passed']}")
        print(f"總失敗: {overall_report['summary']['total_failed']}")
        print(f"總跳過: {overall_report['summary']['total_skipped']}")
        print(f"總耗時: {overall_report['summary']['total_duration']:.2f}秒")
        success_rate = (overall_report['summary']['total_passed'] / overall_report['summary']['total_tests'] * 100) if overall_report['summary']['total_tests'] > 0 else 0.0
        print(f"成功率: {success_rate:.1f}%")
        print(f"報告文件: {report_file}")
        print(f"{'='*80}\n")
    
    def clean_old_reports(self, keep_last: int = 10):
        """清理舊的測試報告"""
        
        # 獲取所有報告文件
        report_files = list(self.reports_dir.glob("*_test_report_*.json"))
        report_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # 刪除舊的報告
        if len(report_files) > keep_last:
            for old_file in report_files[keep_last:]:
                old_file.unlink()
                print(f"刪除舊報告: {old_file}")


def main():
    """主函數"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="代理收集器測試運行器")
    parser.add_argument("test_type", nargs="?", default="all", 
                       choices=["unit", "integration", "e2e", "all"],
                       help="要運行的測試類型")
    parser.add_argument("--no-coverage", action="store_true",
                       help="不生成覆蓋率報告")
    parser.add_argument("--parallel", action="store_true",
                       help="並行運行測試")
    parser.add_argument("--clean", action="store_true",
                       help="清理舊的測試報告")
    parser.add_argument("--keep-last", type=int, default=10,
                       help="保留最近的報告數量")
    
    args = parser.parse_args()
    
    # 創建測試運行器
    runner = TestRunner()
    
    # 清理舊報告
    if args.clean:
        runner.clean_old_reports(keep_last=args.keep_last)
        return
    
    # 運行測試
    coverage = not args.no_coverage
    
    if args.test_type == "all":
        results = runner.run_all_tests(coverage=coverage, parallel=args.parallel)
    else:
        result = runner.run_tests(args.test_type, coverage=coverage, parallel=args.parallel)
        results = {args.test_type: result}
    
    # 檢查測試結果
    failed_tests = sum(1 for r in results.values() if not r.get('success', False))
    
    if failed_tests > 0:
        print(f"\n❌ {failed_tests} 個測試類型失敗")
        sys.exit(1)
    else:
        print(f"\n✅ 所有測試通過")
        sys.exit(0)


if __name__ == "__main__":
    main()