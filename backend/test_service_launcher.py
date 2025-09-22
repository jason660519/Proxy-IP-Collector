#!/usr/bin/env python3
"""
測試 service_launcher.py 的腳本
"""

import sys
import os

# 將項目根目錄添加到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.architecture.service_launcher import ServiceLauncher
import asyncio

async def test_service_launcher():
    """測試服務啟動器"""
    launcher = ServiceLauncher()
    
    try:
        # 初始化應用
        app = await launcher.initialize(mode="full")
        
        print("服務啟動器初始化成功")
        print(f"應用實例: {app}")
        
        # 測試啟動服務器
        print("啟動服務器...")
        await launcher.run(host="0.0.0.0", port=8002, mode="full", reload=False)
        
    except Exception as e:
        print(f"錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_service_launcher())