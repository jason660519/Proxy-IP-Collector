#!/usr/bin/env python3
"""
代理IP來源可用性測試腳本
"""
import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import sys
import os

# 添加後端目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.etl.extractors.factory import ExtractorFactory
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProxySourceTester:
    """代理來源測試器"""
    
    def __init__(self):
        self.session = None
        self.results = {}
        
    async def __aenter__(self):
        """異步上下文管理器進入"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    async def test_url_availability(self, url: str, name: str) -> Dict[str, Any]:
        """測試URL可用性"""
        try:
            start_time = time.time()
            async with self.session.get(url) as response:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # 轉換為毫秒
                
                return {
                    "name": name,
                    "url": url,
                    "status_code": response.status,
                    "response_time": round(response_time, 2),
                    "success": 200 <= response.status < 300,
                    "content_length": len(await response.text()) if response.status == 200 else 0,
                    "timestamp": datetime.now().isoformat()
                }
        except asyncio.TimeoutError:
            return {
                "name": name,
                "url": url,
                "status_code": None,
                "response_time": None,
                "success": False,
                "error": "請求超時",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "name": name,
                "url": url,
                "status_code": None,
                "response_time": None,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_extractor_functionality(self, extractor_name: str) -> Dict[str, Any]:
        """測試爬取器功能"""
        try:
            factory = ExtractorFactory()
            
            # 檢查爬取器是否可用
            if not factory.is_extractor_available(extractor_name):
                return {
                    "name": extractor_name,
                    "success": False,
                    "error": "爬取器不可用",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 創建爬取器實例
            config = {"base_url": "", "test_mode": True}
            extractor = factory.create_extractor(extractor_name, config)
            
            # 執行測試爬取
            start_time = time.time()
            result = await extractor.extract()
            end_time = time.time()
            
            return {
                "name": extractor_name,
                "success": result.success,
                "proxies_found": len(result.proxies),
                "duration": round((end_time - start_time), 2),
                "error_message": result.error_message if hasattr(result, 'error_message') else None,
                "metadata": result.metadata if hasattr(result, 'metadata') else {},
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "name": extractor_name,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


async def test_proxy_sources():
    """測試所有代理來源"""
    print("🔍 開始測試代理IP來源可用性...")
    
    # 定義要測試的URL
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
    
    # 定義要測試的爬取器
    test_extractors = [
        "89ip.cn",
        "kuaidaili-intr", 
        "kuaidaili-inha",
        "geonode-api-v2",
        "proxydb-net",
        "proxynova-com",
        "spys-one",
        "free-proxy-list.net",
        "ssl-proxies"
    ]
    
    async with ProxySourceTester() as tester:
        print("\n📡 測試URL可用性...")
        url_results = []
        
        # 測試URL可用性
        for name, url in test_urls:
            print(f"  測試 {name}...")
            result = await tester.test_url_availability(url, name)
            url_results.append(result)
            
            if result["success"]:
                print(f"  ✅ {name}: {result['status_code']} ({result['response_time']}ms)")
            else:
                print(f"  ❌ {name}: {result.get('error', 'Unknown error')}")
        
        print("\n🕷️ 測試爬取器功能...")
        extractor_results = []
        
        # 測試爬取器功能
        for extractor_name in test_extractors:
            print(f"  測試 {extractor_name}...")
            result = await tester.test_extractor_functionality(extractor_name)
            extractor_results.append(result)
            
            if result["success"]:
                print(f"  ✅ {extractor_name}: 找到 {result['proxies_found']} 個代理 ({result['duration']}s)")
            else:
                print(f"  ❌ {extractor_name}: {result.get('error', 'Unknown error')}")
        
        # 生成測試報告
        generate_test_report(url_results, extractor_results)


def generate_test_report(url_results: List[Dict], extractor_results: List[Dict]):
    """生成測試報告"""
    print("\n" + "="*60)
    print("📊 代理IP來源測試報告")
    print("="*60)
    
    # URL測試結果
    print("\n📡 URL可用性測試結果:")
    print("-" * 40)
    successful_urls = 0
    for result in url_results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['name']:<20} {result.get('status_code', 'N/A'):<8} {result.get('response_time', 'N/A'):<8}ms")
        if result["success"]:
            successful_urls += 1
    
    print(f"\nURL測試成功率: {successful_urls}/{len(url_results)} ({successful_urls/len(url_results)*100:.1f}%)")
    
    # 爬取器測試結果
    print("\n🕷️ 爬取器功能測試結果:")
    print("-" * 40)
    successful_extractors = 0
    total_proxies = 0
    
    for result in extractor_results:
        status = "✅" if result["success"] else "❌"
        proxies_count = result.get("proxies_found", 0)
        duration = result.get("duration", "N/A")
        print(f"{status} {result['name']:<20} {proxies_count:<8} 個代理 {duration:<8}s")
        if result["success"]:
            successful_extractors += 1
            total_proxies += proxies_count
    
    print(f"\n爬取器測試成功率: {successful_extractors}/{len(extractor_results)} ({successful_extractors/len(extractor_results)*100:.1f}%)")
    print(f"總計找到代理: {total_proxies} 個")
    
    # 詳細錯誤信息
    print("\n❌ 失敗詳情:")
    print("-" * 40)
    
    for result in url_results + extractor_results:
        if not result["success"]:
            error = result.get("error", result.get("error_message", "Unknown error"))
            print(f"• {result['name']}: {error}")
    
    # 保存報告到文件
    report_data = {
        "test_timestamp": datetime.now().isoformat(),
        "url_results": url_results,
        "extractor_results": extractor_results,
        "summary": {
            "url_success_rate": successful_urls/len(url_results)*100,
            "extractor_success_rate": successful_extractors/len(extractor_results)*100,
            "total_proxies_found": total_proxies
        }
    }
    
    with open("proxy_source_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 詳細報告已保存到: proxy_source_test_report.json")


async def main():
    """主函數"""
    try:
        await test_proxy_sources()
    except KeyboardInterrupt:
        print("\n⏹️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n💥 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
