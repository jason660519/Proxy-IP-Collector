#!/usr/bin/env python3
"""
簡單的API測試腳本
測試代理池管理器的API端點是否正常運作
"""

import asyncio
import httpx
import json
from pathlib import Path
import sys
import os

# 添加後端目錄到Python路徑
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# 設置環境變量以避免直接導入主應用
os.environ['PROXY_COLLECTOR_ENV'] = 'test'

async def test_health_endpoint():
    """測試健康檢查端點"""
    print("🧪 測試健康檢查端點...")
    
    try:
        # 使用同步客戶端測試實際運行的服務
        import requests
        response = requests.get("http://localhost:8000/health", timeout=10)
        print(f"✅ 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 響應數據: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ 請求失敗: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到服務器，請確保應用正在運行 (python -m app.main)")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

async def test_proxy_endpoints():
    """測試代理相關端點"""
    print("\n🧪 測試代理端點...")
    
    import requests
    
    endpoints = [
        "/api/v1/proxies/health",
        "/api/v1/proxies/stats", 
        "/api/v1/proxies/count"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=10)
            print(f"  {endpoint}: 狀態碼 {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"    ✅ 數據: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                print(f"    ⚠️  錯誤: {response.text}")
                
        except Exception as e:
            print(f"  ❌ {endpoint} 失敗: {e}")

async def main():
    """主測試函數"""
    print("🚀 開始API測試...")
    print("=" * 50)
    
    # 測試健康檢查
    health_ok = await test_health_endpoint()
    
    if health_ok:
        # 測試代理端點
        await test_proxy_endpoints()
    else:
        print("❌ 健康檢查失敗，跳過其他測試")
    
    print("\n" + "=" * 50)
    print("✅ API測試完成！")

if __name__ == "__main__":
    asyncio.run(main())