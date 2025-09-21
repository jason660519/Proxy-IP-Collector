#!/usr/bin/env python3
"""
簡化的代理IP來源測試腳本
"""
import sys
import os
import json
from datetime import datetime

# 添加後端目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """測試導入是否正常"""
    print("🔍 測試模組導入...")
    
    try:
        from app.etl.extractors.factory import ExtractorFactory
        print("✅ ExtractorFactory 導入成功")
        
        factory = ExtractorFactory()
        extractors = factory.get_available_extractors()
        print(f"✅ 可用爬取器: {len(extractors)} 個")
        for name in extractors:
            print(f"   - {name}")
        
        return True
    except Exception as e:
        print(f"❌ 導入失敗: {e}")
        return False

def test_basic_functionality():
    """測試基本功能"""
    print("\n🕷️ 測試基本爬取功能...")
    
    try:
        from app.etl.extractors.factory import ExtractorFactory
        
        factory = ExtractorFactory()
        
        # 測試創建爬取器
        test_extractors = ["free-proxy-list.net", "ssl-proxies"]
        
        for name in test_extractors:
            try:
                if factory.is_extractor_available(name):
                    config = {"base_url": "", "test_mode": True}
                    extractor = factory.create_extractor(name, config)
                    print(f"✅ {name}: 創建成功")
                else:
                    print(f"❌ {name}: 不可用")
            except Exception as e:
                print(f"❌ {name}: 創建失敗 - {e}")
        
        return True
    except Exception as e:
        print(f"❌ 基本功能測試失敗: {e}")
        return False

def test_url_availability():
    """測試URL可用性（使用urllib）"""
    print("\n📡 測試URL可用性...")
    
    import urllib.request
    import urllib.error
    
    test_urls = [
        ("89ip.cn", "https://www.89ip.cn/index_1.html"),
        ("快代理國內", "https://www.kuaidaili.com/free/intr/"),
        ("Free Proxy List", "https://free-proxy-list.net/"),
        ("SSL Proxies", "https://www.sslproxies.org/"),
    ]
    
    results = []
    
    for name, url in test_urls:
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
                    "name": name,
                    "url": url,
                    "status_code": status_code,
                    "success": 200 <= status_code < 300,
                    "content_length": content_length,
                    "timestamp": datetime.now().isoformat()
                }
                results.append(result)
                
                if result["success"]:
                    print(f"✅ {name}: {status_code} ({content_length} bytes)")
                else:
                    print(f"❌ {name}: {status_code}")
                    
        except urllib.error.URLError as e:
            result = {
                "name": name,
                "url": url,
                "status_code": None,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
            print(f"❌ {name}: {e}")
        except Exception as e:
            result = {
                "name": name,
                "url": url,
                "status_code": None,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
            print(f"❌ {name}: {e}")
    
    return results

def generate_report(url_results):
    """生成測試報告"""
    print("\n" + "="*60)
    print("📊 代理IP來源測試報告")
    print("="*60)
    
    successful_urls = sum(1 for r in url_results if r["success"])
    total_urls = len(url_results)
    
    print(f"\n📡 URL可用性測試結果:")
    print(f"成功率: {successful_urls}/{total_urls} ({successful_urls/total_urls*100:.1f}%)")
    
    print(f"\n詳細結果:")
    for result in url_results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['name']:<20} {result.get('status_code', 'N/A'):<8} {result.get('content_length', 'N/A'):<8} bytes")
        if not result["success"]:
            print(f"    錯誤: {result.get('error', 'Unknown error')}")
    
    # 保存報告
    report_data = {
        "test_timestamp": datetime.now().isoformat(),
        "url_results": url_results,
        "summary": {
            "url_success_rate": successful_urls/total_urls*100,
            "total_tested": total_urls,
            "successful": successful_urls
        }
    }
    
    with open("simple_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 詳細報告已保存到: simple_test_report.json")

def main():
    """主函數"""
    print("🚀 開始代理IP來源測試...")
    
    # 測試導入
    if not test_imports():
        print("❌ 導入測試失敗，退出")
        return
    
    # 測試基本功能
    if not test_basic_functionality():
        print("❌ 基本功能測試失敗，退出")
        return
    
    # 測試URL可用性
    url_results = test_url_availability()
    
    # 生成報告
    generate_report(url_results)
    
    print("\n✅ 測試完成！")

if __name__ == "__main__":
    main()
