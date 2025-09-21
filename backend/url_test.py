#!/usr/bin/env python3
"""
URL可用性測試腳本
"""
import urllib.request
import urllib.error
import json
from datetime import datetime

def test_url_availability():
    """測試URL可用性"""
    print("🔍 測試代理IP來源URL可用性...")
    
    test_urls = [
        ("89ip.cn", "https://www.89ip.cn/index_1.html"),
        ("快代理國內", "https://www.kuaidaili.com/free/intr/"),
        ("快代理海外", "https://www.kuaidaili.com/free/inha/"),
        ("GeoNode API", "https://proxylist.geonode.com/api/proxy-list?limit=10"),
        ("ProxyDB.net", "http://proxydb.net/?offset=0"),
        ("ProxyNova.com", "https://www.proxynova.com/proxy-server-list/"),
        ("Spys.one", "http://spys.one/free-proxy-list/"),
        ("Free Proxy List", "https://free-proxy-list.net/"),
        ("SSL Proxies", "https://www.sslproxies.org/"),
    ]
    
    results = []
    
    for name, url in test_urls:
        print(f"  測試 {name}...")
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            )
            
            with urllib.request.urlopen(req, timeout=15) as response:
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
                    print(f"  ✅ {name}: {status_code} ({content_length} bytes)")
                else:
                    print(f"  ❌ {name}: {status_code}")
                    
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
            print(f"  ❌ {name}: {e}")
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
            print(f"  ❌ {name}: {e}")
    
    return results

def generate_report(url_results):
    """生成測試報告"""
    print("\n" + "="*60)
    print("📊 代理IP來源URL可用性測試報告")
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
    
    # 分析結果
    print(f"\n📈 分析結果:")
    working_sources = [r["name"] for r in url_results if r["success"]]
    failed_sources = [r["name"] for r in url_results if not r["success"]]
    
    if working_sources:
        print(f"✅ 可用的來源 ({len(working_sources)} 個):")
        for source in working_sources:
            print(f"   - {source}")
    
    if failed_sources:
        print(f"❌ 不可用的來源 ({len(failed_sources)} 個):")
        for source in failed_sources:
            print(f"   - {source}")
    
    # 保存報告
    report_data = {
        "test_timestamp": datetime.now().isoformat(),
        "url_results": url_results,
        "summary": {
            "url_success_rate": successful_urls/total_urls*100,
            "total_tested": total_urls,
            "successful": successful_urls,
            "working_sources": working_sources,
            "failed_sources": failed_sources
        }
    }
    
    with open("url_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 詳細報告已保存到: url_test_report.json")

def main():
    """主函數"""
    print("🚀 開始代理IP來源URL測試...")
    
    # 測試URL可用性
    url_results = test_url_availability()
    
    # 生成報告
    generate_report(url_results)
    
    print("\n✅ 測試完成！")

if __name__ == "__main__":
    main()
