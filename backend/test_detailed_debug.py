import asyncio
import aiohttp
import traceback

async def test_with_detailed_errors():
    """測試API並顯示詳細錯誤信息"""
    base_url = "http://localhost:8000/api/v1"
    
    # 測試代理列表
    print("測試代理列表端點...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/proxies/list") as response:
                print(f"狀態碼: {response.status}")
                if response.status != 200:
                    error_text = await response.text()
                    print(f"錯誤響應: {error_text}")
                    
                    # 查看服務器日誌
                    print("\n請查看運行 python -m app.main 的終端窗口中的錯誤日誌")
                    print("錯誤應該包含具體的異常信息")
                else:
                    data = await response.json()
                    print(f"成功: {len(data.get('proxies', []))} 個代理")
    except Exception as e:
        print(f"異常: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_with_detailed_errors())