#!/usr/bin/env python3
"""
統一服務啟動腳本
替換原有的分散啟動器，提供標準化的服務啟動方式
"""
import argparse
import sys
import os
from pathlib import Path
from typing import Optional

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.architecture import run_service_sync, config_manager, service_launcher
from app.core.logging import get_logger

logger = get_logger(__name__)


def setup_environment():
    """設置運行環境"""
    # 確保日誌目錄存在
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 確保配置目錄存在
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # 設置環境變量默認值
    os.environ.setdefault("PYTHONPATH", str(project_root))
    os.environ.setdefault("ENVIRONMENT", "development")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="Proxy Collector 統一服務啟動器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
    # 完整模式（默認）
    python launch_unified.py
    
    # API模式
    python launch_unified.py --mode api
    
    # 模擬模式
    python launch_unified.py --mode mock
    
    # 指定端口
    python launch_unified.py --port 8080
    
    # 開發模式（啟用熱重載）
    python launch_unified.py --reload
    
    # 生產環境
    ENVIRONMENT=production python launch_unified.py --mode full
        """
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="服務器主機地址 (默認: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="服務器端口 (默認: 8000)"
    )
    
    parser.add_argument(
        "--mode",
        default="full",
        choices=["full", "api", "mock"],
        help="運行模式: full(完整模式), api(API模式), mock(模擬模式) (默認: full)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="啟用熱重載 (開發模式)"
    )
    
    parser.add_argument(
        "--config-dir",
        type=str,
        help="配置目錄路徑 (默認: config)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="日誌級別 (默認: INFO)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        help="工作進程數 (生產模式使用)"
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="檢查配置和依賴，不啟動服務"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Proxy Collector 統一服務 1.0.0"
    )
    
    args = parser.parse_args()
    
    # 設置運行環境
    setup_environment()
    
    # 設置配置目錄
    if args.config_dir:
        config_manager.config_dir = Path(args.config_dir)
    
    # 設置日誌級別
    if args.log_level:
        os.environ["LOG_LEVEL"] = args.log_level
    
    # 檢查模式
    if args.check:
        logger.info("執行配置和依賴檢查...")
        return check_system()
    
    # 根據環境設置默認參數
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        # 生產環境默認設置
        if not args.reload:
            args.reload = False
        if args.port == 8000:
            args.port = int(os.getenv("PORT", 8000))
    
    # 記錄啟動信息
    logger.info(f"啟動 Proxy Collector 統一服務")
    logger.info(f"環境: {environment}")
    logger.info(f"模式: {args.mode}")
    logger.info(f"主機: {args.host}:{args.port}")
    logger.info(f"熱重載: {'啟用' if args.reload else '禁用'}")
    
    # 檢查端口可用性
    if not check_port_available(args.port):
        logger.error(f"端口 {args.port} 已被佔用")
        return 1
    
    try:
        # 運行服務
        run_service_sync(
            host=args.host,
            port=args.port,
            mode=args.mode,
            reload=args.reload
        )
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("服務被用戶中斷")
        return 0
    except Exception as e:
        logger.error(f"服務啟動失敗: {e}")
        return 1


def check_system():
    """檢查系統配置和依賴"""
    logger.info("開始系統檢查...")
    
    # 檢查Python版本
    import sys
    if sys.version_info < (3, 8):
        logger.error("需要 Python 3.8 或更高版本")
        return 1
    
    logger.info(f"Python 版本: {sys.version}")
    
    # 檢查關鍵依賴
    dependencies = [
        ("fastapi", "FastAPI 框架"),
        ("uvicorn", "ASGI 服務器"),
        ("sqlalchemy", "數據庫ORM"),
        ("pydantic", "數據驗證"),
        ("aiohttp", "異步HTTP客戶端"),
        ("asyncio", "異步編程")
    ]
    
    missing_deps = []
    
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            logger.info(f"✓ {description} 已安裝")
        except ImportError:
            logger.warning(f"✗ {description} 未安裝")
            missing_deps.append(module_name)
    
    # 檢查配置
    try:
        config_info = config_manager.get_config_info()
        logger.info(f"配置目錄: {config_info['config_dir']}")
        logger.info(f"配置源數量: {len(config_info['loaded_sources'])}")
    except Exception as e:
        logger.warning(f"配置檢查失敗: {e}")
    
    # 檢查端口
    if not check_port_available(8000):
        logger.warning("端口 8000 已被佔用")
    else:
        logger.info("端口 8000 可用")
    
    if missing_deps:
        logger.error(f"缺少關鍵依賴: {', '.join(missing_deps)}")
        logger.info("請運行: pip install -r requirements.txt")
        return 1
    
    logger.info("系統檢查完成")
    return 0


def check_port_available(port: int, host: str = "0.0.0.0") -> bool:
    """檢查端口是否可用"""
    import socket
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.close()
        return True
    except OSError:
        return False


if __name__ == "__main__":
    sys.exit(main())