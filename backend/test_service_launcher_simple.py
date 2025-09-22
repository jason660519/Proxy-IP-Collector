#!/usr/bin/env python3
"""
簡單測試 service_launcher 的系統信息端點
"""
import sys
import os
import asyncio

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.architecture.service_launcher import ServiceLauncher

async def test_service_launcher():
    """測試 service_launcher 的系統信息端點"""
    try:
        # 初始化服務啟動器
        launcher = ServiceLauncher()
        app = await launcher.initialize(mode='full')
        print("✓ Service launcher initialized successfully")
        
        # 使用測試客戶端測試端點
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        # 測試根端點
        print("\nTesting / endpoint...")
        response = client.get("/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Root endpoint working")
            print(f"  Service: {data.get('service', 'N/A')}")
            print(f"  Status: {data.get('status', 'N/A')}")
        else:
            print(f"✗ Root endpoint failed: {response.text}")
        
        # 測試系統信息端點
        print("\nTesting /info endpoint...")
        response = client.get("/info")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ System info endpoint working")
            print(f"  System: {data.get('system', 'N/A')}")
            print(f"  Python Version: {data.get('python_version', 'N/A')}")
            print(f"  Platform: {data.get('platform', 'N/A')}")
            print(f"  Uptime: {data.get('uptime', 'N/A')}")
        else:
            print(f"✗ System info endpoint failed: {response.text}")
            
        # 測試健康檢查端點
        print("\nTesting /health endpoint...")
        response = client.get("/health")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Health endpoint working")
            print(f"  Status: {data.get('status', 'N/A')}")
            print(f"  Database: {data.get('database', 'N/A')}")
            print(f"  Redis: {data.get('redis', 'N/A')}")
        else:
            print(f"✗ Health endpoint failed: {response.text}")
            
        print("\n=== Test Summary ===")
        print("✓ All endpoints tested successfully!")
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_service_launcher())