import asyncio
import aiohttp
import json

async def test_debug_api():
    """測試API端點並顯示詳細錯誤信息"""
    base_url = "http://localhost:8000/api/v1"
    
    endpoints = [
        "/proxies/list",
        "/proxies/stats", 
        "/crawl/history",
        "/system/config"
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            try:
                print(f"\n測試 {endpoint}...")
                async with session.get(f"{base_url}{endpoint}") as response:
                    print(f"狀態碼: {response.status}")
                    
                    if response.status == 500:
                        error_text = await response.text()
                        print(f"錯誤響應: {error_text}")
                        
                        # 嘗試獲取更詳細的錯誤信息
                        try:
                            error_data = json.loads(error_text)
                            print(f"錯誤詳情: {error_data}")
                        except:
                            print(f"原始錯誤: {error_text}")
                    else:
                        data = await response.json()
                        print(f"成功: {len(str(data))} 字符")
                        
            except Exception as e:
                print(f"請求異常: {e}")

if __name__ == "__main__":
    asyncio.run(test_debug_api())