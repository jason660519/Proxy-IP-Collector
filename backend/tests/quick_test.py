"""
快速測試腳本
驗證測試體系是否正常運作
"""

import sys
import os
from pathlib import Path
import subprocess
import json


def run_quick_test():
    """運行快速測試以驗證測試體系"""
    
    # 獲取項目根目錄
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    
    print("🧪 開始運行快速測試...")
    print(f"項目根目錄: {project_root}")
    print(f"測試目錄: {tests_dir}")
    
    # 檢查測試目錄結構
    print("\n📁 檢查測試目錄結構:")
    
    required_files = [
        "__init__.py",
        "conftest.py",
        "run_tests.py",
        "pytest.ini"
    ]
    
    for file in required_files:
        file_path = tests_dir / file if file != "pytest.ini" else project_root / file
        if file_path.exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} (缺失)")
    
    # 檢查測試子目錄
    print("\n📂 檢查測試子目錄:")
    for subdir in ["unit", "integration", "e2e", "data"]:
        subdir_path = tests_dir / subdir
        if subdir_path.exists():
            test_files = list(subdir_path.glob("test_*.py"))
            print(f"  ✅ {subdir}/ ({len(test_files)} 個測試文件)")
        else:
            print(f"  ❌ {subdir}/ (缺失)")
    
    # 運行簡單的單元測試
    print("\n🔍 運行單元測試驗證:")
    try:
        # 運行一個簡單的測試
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/test_validators.py::TestIPScoringEngine::test_calculate_score_valid_data",
            "-v"
        ]
        
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("  ✅ 單元測試運行成功")
        else:
            print("  ❌ 單元測試運行失敗")
            print(f"  錯誤: {result.stderr}")
        
        print(f"  輸出: {result.stdout}")
        
    except Exception as e:
        print(f"  ❌ 運行測試時出錯: {e}")
    
    # 檢查依賴
    print("\n📦 檢查測試依賴:")
    required_packages = [
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "pytest-html",
        "pytest-json-report",
        "httpx"
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (未安裝)")
    
    # 運行覆蓋率測試
    print("\n📊 運行覆蓋率測試:")
    try:
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/",
            "--cov=app",
            "--cov-report=term-missing",
            "--tb=short",
            "-q"
        ]
        
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("  ✅ 覆蓋率測試運行成功")
            # 提取覆蓋率信息
            lines = result.stdout.split('\n')
            for line in lines:
                if 'coverage' in line.lower() or '%' in line:
                    print(f"  📈 {line.strip()}")
        else:
            print("  ❌ 覆蓋率測試運行失敗")
            print(f"  錯誤: {result.stderr}")
        
    except Exception as e:
        print(f"  ❌ 運行覆蓋率測試時出錯: {e}")
    
    print("\n🎉 快速測試完成!")
    print("\n下一步建議:")
    print("1. 運行完整測試: python tests/run_tests.py")
    print("2. 運行特定類型測試: python tests/run_tests.py unit")
    print("3. 生成測試報告: python tests/run_tests.py --no-coverage")


if __name__ == "__main__":
    run_quick_test()