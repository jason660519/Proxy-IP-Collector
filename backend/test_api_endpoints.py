"""
簡單的API端點測試
測試後端服務是否正常響應
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime


async def test_api_endpoints():
    """測試API端點"""
    base_url = "http://localhost:8000/api/v1"
    
    print(f"開始測試API端點... {datetime.now()}")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 測試1: 獲取代理列表
            print("\n1. 測試獲取代理列表...")
            async with session.get(f"{base_url}/proxies/list") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✓ 代理列表獲取成功: {len(data.get('proxies', []))} 個代理")
                else:
                    text = await response.text()
                    print(f"   ✗ 代理列表獲取失敗: {response.status} - {text}")
            
            # 測試2: 獲取代理統計
            print("\n2. 測試獲取代理統計...")
            async with session.get(f"{base_url}/proxies/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✓ 代理統計獲取成功: {data.get('total_count', 0)} 總數")
                else:
                    text = await response.text()
                    print(f"   ✗ 代理統計獲取失敗: {response.status} - {text}")
            
            # 測試3: 獲取爬取歷史
            print("\n3. 測試獲取爬取歷史...")
            async with session.get(f"{base_url}/crawl/history") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✓ 爬取歷史獲取成功，找到 {len(data.get('items', []))} 條記錄")
                else:
                    text = await response.text()
                    print(f"   ✗ 爬取歷史獲取失敗: {response.status} - {text}")
            
            # 測試4: 獲取系統配置
            print("\n4. 測試獲取系統配置...")
            async with session.get(f"{base_url}/system/config") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✓ 系統配置獲取成功: {data.get('app_name', 'Unknown')}")
                else:
                    print(f"   ✗ 系統配置獲取失敗: {response.status}")
            
            print("\n✅ API端點測試完成！")
            return True
            
        except aiohttp.ClientConnectorError:
            print("\n❌ 無法連接到後端服務，請確保服務正在運行")
            return False
        except Exception as e:
            print(f"\n❌ 測試過程中出錯: {e}")
            return False


if __name__ == "__main__":
    success = asyncio.run(test_api_endpoints())
    sys.exit(0 if success else 1)