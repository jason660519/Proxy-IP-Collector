#!/usr/bin/env python
"""
代理爬取器測試腳本
測試各個爬取器的功能是否正常
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 將後端目錄添加到Python路徑
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.etl.extractors.factory import ExtractorFactory

async def test_extractor(extractor_name: str, limit: int = 5):
    """測試單個爬取器"""
    print(f"\n🧪 測試爬取器: {extractor_name}")
    print("-" * 50)
    
    try:
        # 創建爬取器實例
        factory = ExtractorFactory()
        extractor = factory.create_extractor(extractor_name)
        
        if not extractor:
            print(f"❌ 爬取器 {extractor_name} 創建失敗")
            return
        
        print(f"✅ 爬取器創建成功: {type(extractor).__name__}")
        
        # 執行爬取
        start_time = datetime.now()
        proxies = await extractor.extract_proxies(limit=limit)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        print(f"⏱️  爬取耗時: {duration:.2f} 秒")
        print(f"📊 獲取代理數量: {len(proxies)}")
        
        if proxies:
            print(f"🌐 代理樣本:")
            for i, proxy in enumerate(proxies[:3]):
                print(f"   {i+1}. {proxy.ip}:{proxy.port} ({proxy.protocol}, {proxy.country})")
            
            if len(proxies) > 3:
                print(f"   ... 還有 {len(proxies) - 3} 個代理")
        else:
            print("⚠️  未獲取到任何代理")
            
        return len(proxies)
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0

async def test_all_extractors():
    """測試所有爬取器"""
    print("🔍 開始測試所有爬取器...")
    print("=" * 60)
    
    # 獲取所有爬取器
    factory = ExtractorFactory()
    extractors = factory.get_available_extractors()
    
    print(f"📋 找到 {len(extractors)} 個爬取器: {', '.join(extractors)}")
    
    total_proxies = 0
    results = {}
    
    # 測試每個爬取器
    for extractor_name in extractors:
        try:
            count = await test_extractor(extractor_name, limit=10)
            results[extractor_name] = count
            total_proxies += count
        except Exception as e:
            print(f"❌ 爬取器 {extractor_name} 測試異常: {str(e)}")
            results[extractor_name] = 0
    
    # 打印總結報告
    print("\n" + "=" * 60)
    print("📈 測試總結報告")
    print("=" * 60)
    
    for extractor_name, count in results.items():
        status = "✅" if count > 0 else "❌"
        print(f"{status} {extractor_name}: {count} 個代理")
    
    print(f"\n🎯 總計: {total_proxies} 個代理")
    print(f"✨ 成功率: {sum(1 for c in results.values() if c > 0)}/{len(results)} 個爬取器")

async def quick_test():
    """快速測試幾個主要的爬取器"""
    print("⚡ 快速測試模式...")
    
    test_extractors = [
        "free-proxy-list",
        "proxy-scrape-api", 
        "proxy-list-plus"
    ]
    
    total_proxies = 0
    
    for extractor_name in test_extractors:
        try:
            count = await test_extractor(extractor_name, limit=3)
            total_proxies += count
        except Exception as e:
            print(f"❌ 快速測試失敗 {extractor_name}: {str(e)}")
    
    print(f"\n🎯 快速測試完成，總計: {total_proxies} 個代理")

def main():
    """主函數"""
    print("🚀 代理爬取器測試工具")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        # 測試指定的爬取器
        extractor_name = sys.argv[1]
        asyncio.run(test_extractor(extractor_name))
    else:
        # 快速測試
        asyncio.run(quick_test())
        
        # 詢問是否進行完整測試
        print("\n是否要進行完整測試？(y/n): ", end="")
        response = input().strip().lower()
        
        if response == 'y':
            asyncio.run(test_all_extractors())

if __name__ == "__main__":
    main()