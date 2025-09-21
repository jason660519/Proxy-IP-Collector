#!/usr/bin/env python3
"""
端到端測試腳本
測試整個代理IP收集系統的完整功能
"""
import json
import time
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, List, Any

def test_api_endpoints():
    """測試API端點"""
    print("🔍 測試API端點...")
    
    # 假設後端服務運行在8000端口
    base_url = "http://localhost:8000"
    
    endpoints_to_test = [
        ("/", "根端點"),
        ("/health", "健康檢查"),
        ("/api/v1/crawl/sources", "獲取爬取來源"),
        ("/api/v1/proxies/stats", "代理統計"),
    ]
    
    results = []
    
    for endpoint, description in endpoints_to_test:
        url = base_url + endpoint
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                status_code = response.getcode()
                content_length = len(response.read())
                
                result = {
                    "endpoint": endpoint,
                    "description": description,
                    "status_code": status_code,
                    "success": 200 <= status_code < 300,
                    "content_length": content_length,
                    "timestamp": datetime.now().isoformat()
                }
                results.append(result)
                
                if result["success"]:
                    print(f"  ✅ {description} ({endpoint}): {status_code} ({content_length} bytes)")
                else:
                    print(f"  ❌ {description} ({endpoint}): {status_code}")
                    
        except urllib.error.URLError as e:
            result = {
                "endpoint": endpoint,
                "description": description,
                "status_code": None,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
            print(f"  ❌ {description} ({endpoint}): {e}")
        except Exception as e:
            result = {
                "endpoint": endpoint,
                "description": description,
                "status_code": None,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
            print(f"  ❌ {description} ({endpoint}): {e}")
    
    return results

def test_frontend_access():
    """測試前端頁面訪問"""
    print("\n🌐 測試前端頁面訪問...")
    
    frontend_files = [
        ("index.html", "主頁"),
        ("extractors_showcase.html", "爬取器展示頁面"),
    ]
    
    results = []
    
    for filename, description in frontend_files:
        try:
            # 嘗試讀取前端文件
            with open(f"../frontend/{filename}", "r", encoding="utf-8") as f:
                content = f.read()
                
            result = {
                "file": filename,
                "description": description,
                "success": True,
                "content_length": len(content),
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
            print(f"  ✅ {description} ({filename}): {len(content)} bytes")
            
        except FileNotFoundError:
            result = {
                "file": filename,
                "description": description,
                "success": False,
                "error": "文件不存在",
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
            print(f"  ❌ {description} ({filename}): 文件不存在")
        except Exception as e:
            result = {
                "file": filename,
                "description": description,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
            print(f"  ❌ {description} ({filename}): {e}")
    
    return results

def test_configuration_files():
    """測試配置文件"""
    print("\n⚙️ 測試配置文件...")
    
    config_files = [
        ("config/proxy_sources.json", "代理來源配置"),
        ("requirements.txt", "Python依賴"),
    ]
    
    results = []
    
    for filepath, description in config_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                if filepath.endswith(".json"):
                    content = json.load(f)
                    result = {
                        "file": filepath,
                        "description": description,
                        "success": True,
                        "content_type": "JSON",
                        "keys": list(content.keys()) if isinstance(content, dict) else "Not a dict",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    content = f.read()
                    result = {
                        "file": filepath,
                        "description": description,
                        "success": True,
                        "content_length": len(content),
                        "timestamp": datetime.now().isoformat()
                    }
                results.append(result)
                print(f"  ✅ {description} ({filepath}): 有效")
                
        except FileNotFoundError:
            result = {
                "file": filepath,
                "description": description,
                "success": False,
                "error": "文件不存在",
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
            print(f"  ❌ {description} ({filepath}): 文件不存在")
        except json.JSONDecodeError as e:
            result = {
                "file": filepath,
                "description": description,
                "success": False,
                "error": f"JSON格式錯誤: {e}",
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
            print(f"  ❌ {description} ({filepath}): JSON格式錯誤")
        except Exception as e:
            result = {
                "file": filepath,
                "description": description,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
            print(f"  ❌ {description} ({filepath}): {e}")
    
    return results

def test_extractor_modules():
    """測試爬取器模組"""
    print("\n🕷️ 測試爬取器模組...")
    
    extractor_files = [
        ("app/etl/extractors/factory.py", "爬取器工廠"),
        ("app/etl/extractors/base.py", "基礎爬取器"),
        ("app/etl/coordinator.py", "ETL協調器"),
    ]
    
    results = []
    
    for filepath, description in extractor_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                
            # 簡單檢查文件內容
            has_class = "class " in content
            has_import = "import " in content
            has_function = "def " in content
            
            result = {
                "file": filepath,
                "description": description,
                "success": True,
                "content_length": len(content),
                "has_class": has_class,
                "has_import": has_import,
                "has_function": has_function,
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
            print(f"  ✅ {description} ({filepath}): {len(content)} bytes, 類: {has_class}, 函數: {has_function}")
            
        except FileNotFoundError:
            result = {
                "file": filepath,
                "description": description,
                "success": False,
                "error": "文件不存在",
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
            print(f"  ❌ {description} ({filepath}): 文件不存在")
        except Exception as e:
            result = {
                "file": filepath,
                "description": description,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
            print(f"  ❌ {description} ({filepath}): {e}")
    
    return results

def generate_e2e_report(api_results, frontend_results, config_results, extractor_results):
    """生成端到端測試報告"""
    print("\n" + "="*60)
    print("📊 端到端測試報告")
    print("="*60)
    
    # 統計結果
    all_results = api_results + frontend_results + config_results + extractor_results
    successful_tests = sum(1 for r in all_results if r["success"])
    total_tests = len(all_results)
    
    print(f"\n📈 總體測試結果:")
    print(f"總測試數: {total_tests}")
    print(f"成功: {successful_tests} ({successful_tests/total_tests*100:.1f}%)")
    print(f"失敗: {total_tests - successful_tests} ({(total_tests - successful_tests)/total_tests*100:.1f}%)")
    
    # 分類統計
    api_success = sum(1 for r in api_results if r["success"])
    frontend_success = sum(1 for r in frontend_results if r["success"])
    config_success = sum(1 for r in config_results if r["success"])
    extractor_success = sum(1 for r in extractor_results if r["success"])
    
    print(f"\n📊 分類測試結果:")
    print(f"API端點: {api_success}/{len(api_results)} ({api_success/len(api_results)*100:.1f}%)")
    print(f"前端頁面: {frontend_success}/{len(frontend_results)} ({frontend_success/len(frontend_results)*100:.1f}%)")
    print(f"配置文件: {config_success}/{len(config_results)} ({config_success/len(config_results)*100:.1f}%)")
    print(f"爬取器模組: {extractor_success}/{len(extractor_results)} ({extractor_success/len(extractor_results)*100:.1f}%)")
    
    # 詳細失敗信息
    failed_tests = [r for r in all_results if not r["success"]]
    if failed_tests:
        print(f"\n❌ 失敗詳情:")
        for result in failed_tests:
            error = result.get("error", "Unknown error")
            print(f"• {result.get('description', result.get('file', result.get('endpoint', 'Unknown')))}: {error}")
    
    # 系統狀態評估
    print(f"\n🎯 系統狀態評估:")
    
    if successful_tests == total_tests:
        print("✅ 系統狀態: 優秀 - 所有測試通過")
        print("✅ 建議: 系統可以正常運行和部署")
    elif successful_tests / total_tests >= 0.8:
        print("✅ 系統狀態: 良好 - 大部分測試通過")
        print("⚠️ 建議: 修復失敗的測試後可以部署")
    elif successful_tests / total_tests >= 0.6:
        print("⚠️ 系統狀態: 一般 - 部分測試通過")
        print("⚠️ 建議: 需要修復關鍵問題後再部署")
    else:
        print("❌ 系統狀態: 差 - 大部分測試失敗")
        print("❌ 建議: 需要大量修復工作")
    
    # 保存報告
    report_data = {
        "test_timestamp": datetime.now().isoformat(),
        "total_tests": total_tests,
        "successful_tests": successful_tests,
        "failed_tests": total_tests - successful_tests,
        "success_rate": successful_tests/total_tests*100,
        "category_results": {
            "api": {
                "total": len(api_results),
                "successful": api_success,
                "success_rate": api_success/len(api_results)*100 if api_results else 0
            },
            "frontend": {
                "total": len(frontend_results),
                "successful": frontend_success,
                "success_rate": frontend_success/len(frontend_results)*100 if frontend_results else 0
            },
            "config": {
                "total": len(config_results),
                "successful": config_success,
                "success_rate": config_success/len(config_results)*100 if config_results else 0
            },
            "extractors": {
                "total": len(extractor_results),
                "successful": extractor_success,
                "success_rate": extractor_success/len(extractor_results)*100 if extractor_results else 0
            }
        },
        "detailed_results": {
            "api_endpoints": api_results,
            "frontend_pages": frontend_results,
            "configuration_files": config_results,
            "extractor_modules": extractor_results
        }
    }
    
    with open("e2e_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 詳細報告已保存到: e2e_test_report.json")

def main():
    """主函數"""
    print("🚀 開始端到端測試...")
    
    # 測試API端點
    api_results = test_api_endpoints()
    
    # 測試前端頁面
    frontend_results = test_frontend_access()
    
    # 測試配置文件
    config_results = test_configuration_files()
    
    # 測試爬取器模組
    extractor_results = test_extractor_modules()
    
    # 生成報告
    generate_e2e_report(api_results, frontend_results, config_results, extractor_results)
    
    print("\n✅ 端到端測試完成！")

if __name__ == "__main__":
    main()
