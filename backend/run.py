#!/usr/bin/env python
"""
代理收集器後端服務啟動腳本
簡化版本，用於快速啟動後端服務
"""

import uvicorn
import os
import sys
from pathlib import Path

# 將後端目錄添加到Python路徑
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def main():
    """啟動後端服務"""
    print("🚀 正在啟動代理收集器後端服務...")
    
    # 配置參數
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("DEBUG", "true").lower() == "true"
    
    print(f"📡 服務將運行在: http://{host}:{port}")
    print(f"📖 API文檔: http://{host}:{port}/docs")
    print(f"🔍 健康檢查: http://{host}:{port}/health")
    
    # 啟動服務
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()