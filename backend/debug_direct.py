#!/usr/bin/env python3
"""
直接調試API端點
"""

import asyncio
import aiohttp
import json

async def test_endpoints():
    """直接測試各個端點"""
    base_url = "http://localhost:8000/api/v1"
    
    async with aiohttp.ClientSession() as session:
        # 測試代理列表
        try:
            print("測試代理列表端點...")
            async with session.get(f"{base_url}/proxies/list") as response:
                print(f"狀態碼: {response.status}")
                text = await response.text()
                print(f"響應: {text}")
        except Exception as e:
            print(f"代理列表錯誤: {e}")
        
        # 測試代理統計
        try:
            print("\n測試代理統計端點...")
            async with session.get(f"{base_url}/proxies/stats") as response:
                print(f"狀態碼: {response.status}")
                text = await response.text()
                print(f"響應: {text}")
        except Exception as e:
            print(f"代理統計錯誤: {e}")
        
        # 測試爬取歷史
        try:
            print("\n測試爬取歷史端點...")
            async with session.get(f"{base_url}/crawl/history") as response:
                print(f"狀態碼: {response.status}")
                text = await response.text()
                print(f"響應: {text}")
        except Exception as e:
            print(f"爬取歷史錯誤: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())