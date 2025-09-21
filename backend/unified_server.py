#!/usr/bin/env python3
"""
統一服務器啟動腳本
解決多重啟動器問題，提供統一的服務入口點
"""
import sys
import os
from pathlib import Path

# 將後端目錄添加到Python路徑
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

try:
    from app.architecture.unified_server import create_server, create_full_server, create_api_server, create_mock_server
except ImportError as e:
    print(f"導入統一服務器模塊失敗: {e}")
    print("請確保已安裝依賴: pip install -r requirements.txt")
    sys.exit(1)


def print_usage():
    """打印使用說明"""
    print("""
統一服務器啟動器 - 代理IP池收集器

使用方法:
    python unified_server.py [選項]

選項:
    --mode MODE     運行模式: full(默認), api, mock
    --host HOST     主機地址 (默認: 0.0.0.0)
    --port PORT     端口 (默認: 8000)
    --mock          使用模擬數據 (等同於 --mode mock)
    --help          顯示此幫助信息

模式說明:
    full    - 完整模式，包含所有功能（數據庫、API、爬取器）
    api     - 僅API模式，提供API服務但不啟動爬取器
    mock    - 模擬模式，使用模擬數據，無需數據庫

示例:
    # 完整模式啟動
    python unified_server.py
    
    # API模式啟動
    python unified_server.py --mode api
    
    # 模擬模式啟動
    python unified_server.py --mode mock
    
    # 指定主機和端口
    python unified_server.py --host 127.0.0.1 --port 8080
""")


def main():
    """主函數"""
    import argparse
    
    # 創建參數解析器
    parser = argparse.ArgumentParser(
        description="統一服務器啟動器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
模式說明:
    full    - 完整模式，包含所有功能
    api     - 僅API模式，提供API服務
    mock    - 模擬模式，使用模擬數據
        """
    )
    
    # 添加參數
    parser.add_argument(
        "--mode", 
        choices=["full", "api", "mock"], 
        default="full",
        help="運行模式 (默認: full)"
    )
    parser.add_argument(
        "--host", 
        type=str,
        default="0.0.0.0",
        help="主機地址 (默認: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000,
        help="端口 (默認: 8000)"
    )
    parser.add_argument(
        "--mock", 
        action="store_true",
        help="使用模擬數據 (等同於 --mode mock)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="啟用代碼熱重載 (開發模式)"
    )
    
    # 解析參數
    args = parser.parse_args()
    
    # 如果指定了--mock，則覆蓋mode
    if args.mock:
        args.mode = "mock"
    
    # 打印啟動信息
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                代理IP池收集器 - 統一服務器                  ║
╠══════════════════════════════════════════════════════════════╣
║ 運行模式: {args.mode:<12}                                    ║
║ 主機地址: {args.host:<15}                                    ║
║ 端口:     {args.port:<6}                                     ║
║ 熱重載:   {'啟用' if args.reload else '禁用':<12}            ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    try:
        # 根據模式創建服務器
        if args.mode == "full":
            server = create_full_server()
        elif args.mode == "api":
            server = create_api_server()
        else:  # mock
            server = create_mock_server()
        
        # 運行服務器
        server.run(
            host=args.host,
            port=args.port,
            reload=args.reload
        )
        
    except KeyboardInterrupt:
        print("\n服務器被用戶中斷")
        sys.exit(0)
    except Exception as e:
        print(f"\n服務器啟動失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 如果沒有參數，顯示使用說明
    if len(sys.argv) == 1:
        print_usage()
        print("\n正在使用默認配置啟動服務器...\n")
    
    main()