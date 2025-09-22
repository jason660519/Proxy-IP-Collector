"""
統一服務啟動器
提供標準化的服務啟動和管理機制
"""
import asyncio
import signal
import sys
import os
from typing import Optional, Dict, Any, Callable
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.logging import get_logger, setup_logging
from app.architecture.config_manager import config_manager, setup_config
from app.architecture.health_check import health_checker
from app.api import v1_router as api_router

logger = get_logger(__name__)


class ServiceLauncher:
    """統一服務啟動器"""
    
    def __init__(self):
        self.app: Optional[FastAPI] = None
        self.config: Optional[Dict[str, Any]] = None
        self.running = False
        self.shutdown_event = asyncio.Event()
        self.start_time: Optional[float] = None
        
        # 設置信號處理
        self._setup_signal_handlers()
        
        logger.info("服務啟動器初始化完成")
    
    def _setup_signal_handlers(self):
        """設置信號處理器"""
        def signal_handler(signum, frame):
            logger.info(f"接收到信號 {signum}，開始關閉服務...")
            self.shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize(self, mode: str = "full") -> FastAPI:
        """
        初始化應用
        
        Args:
            mode: 運行模式 (full, api, mock)
            
        Returns:
            FastAPI應用實例
        """
        logger.info(f"開始初始化應用 - 模式: {mode}")
        
        # 記錄啟動時間
        import time
        self.start_time = time.time()
        
        # 設置配置
        self.config = await setup_config()
        
        # 設置日誌
        setup_logging()  # 使用默認配置
        
        # 創建應用
        self.app = self._create_app(mode)
        
        logger.info("應用初始化完成")
        return self.app
    
    def _create_app(self, mode: str) -> FastAPI:
        """創建FastAPI應用"""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """應用生命週期管理"""
            logger.info("應用啟動中...")
            
            # 啟動時的初始化
            await self._startup()
            
            yield
            
            # 關閉時的清理
            logger.info("應用關閉中...")
            await self._shutdown()
        
        # 創建FastAPI應用
        app = FastAPI(
            title="Proxy Collector API",
            description="統一的代理收集和管理服務",
            version="1.0.0",
            lifespan=lifespan,
            docs_url="/docs" if self.config.get("debug", False) else None,
            redoc_url="/redoc" if self.config.get("debug", False) else None,
            openapi_url="/openapi.json" if self.config.get("debug", False) else None
        )
        
        # 根據模式設置應用
        if mode == "full":
            self._setup_full_mode(app)
        elif mode == "api":
            self._setup_api_mode(app)
        elif mode == "mock":
            self._setup_mock_mode(app)
        else:
            raise ValueError(f"不支持的運行模式: {mode}")
        
        return app
    
    def _setup_full_mode(self, app: FastAPI):
        """設置完整模式"""
        logger.info("設置完整模式")
        
        # 添加標準API路由
        app.include_router(api_router, prefix="/api/v1")
        
        # 添加健康檢查端點
        from app.architecture.health_check import get_health_status
        
        @app.get("/health")
        async def health_check():
            """健康檢查端點"""
            return await get_health_status()
        
        # 添加根端點
        @app.get("/")
        async def root():
            """根端點"""
            return {
                "message": "Proxy Collector API",
                "version": "1.0.0",
                "mode": "full",
                "status": "running",
                "uptime": self.get_uptime()
            }
        
        # 添加系統信息端點
        @app.get("/info")
        async def system_info():
            """系統信息端點"""
            import platform
            # 獲取配置信息（同步函數，無需await）
            config_info = config_manager.get_config_info()
            return {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "app_version": "1.0.0",
                "mode": "full",
                "config_info": config_info
            }
    
    def _setup_api_mode(self, app: FastAPI):
        """設置API模式"""
        logger.info("設置API模式")
        
        # 只添加API路由，不包含爬蟲功能
        app.include_router(api_router, prefix="/api/v1")
        
        @app.get("/")
        async def root():
            """根端點"""
            return {
                "message": "Proxy Collector API (API Mode)",
                "version": "1.0.0",
                "mode": "api",
                "status": "running",
                "uptime": self.get_uptime()
            }
    
    def _setup_mock_mode(self, app: FastAPI):
        """設置模擬模式"""
        logger.info("設置模擬模式")
        
        # 添加模擬數據端點
        @app.get("/")
        async def root():
            """根端點"""
            return {
                "message": "Proxy Collector API (Mock Mode)",
                "version": "1.0.0",
                "mode": "mock",
                "status": "running",
                "uptime": self.get_uptime()
            }
        
        @app.get("/api/v1/proxies")
        async def mock_proxies():
            """模擬代理列表"""
            return {
                "status": "success",
                "data": {
                    "proxies": [
                        {
                            "id": 1,
                            "ip": "192.168.1.100",
                            "port": 8080,
                            "country": "US",
                            "anonymity": "elite",
                            "type": "http",
                            "speed": 100,
                            "status": "active"
                        }
                    ],
                    "total": 1,
                    "page": 1,
                    "page_size": 20
                }
            }
        
        @app.get("/api/v1/scraping/status")
        async def mock_scraping_status():
            """模擬爬蟲狀態"""
            return {
                "status": "success",
                "data": {
                    "is_running": False,
                    "last_run": "2024-01-01T00:00:00Z",
                    "proxies_found": 0,
                    "errors": []
                }
            }
    
    async def _startup(self):
        """應用啟動時的初始化"""
        logger.info("執行應用啟動初始化...")
        
        try:
            # 初始化數據庫連接
            await self._init_database()
            
            # 初始化Redis連接
            await self._init_redis()
            
            # 啟動後台任務
            await self._start_background_tasks()
            
            logger.info("應用啟動初始化完成")
            
        except Exception as e:
            logger.error(f"應用啟動初始化失敗: {e}")
            raise
    
    async def _shutdown(self):
        """應用關閉時的清理"""
        logger.info("執行應用關閉清理...")
        
        try:
            # 停止後台任務
            await self._stop_background_tasks()
            
            # 關閉數據庫連接
            await self._close_database()
            
            # 關閉Redis連接
            await self._close_redis()
            
            logger.info("應用關閉清理完成")
            
        except Exception as e:
            logger.error(f"應用關閉清理失敗: {e}")
    
    async def _init_database(self):
        """初始化數據庫"""
        try:
            from app.core.database import init_db
            await init_db()
            logger.info("數據庫初始化完成")
        except Exception as e:
            logger.warning(f"數據庫初始化跳過: {e}")
    
    async def _init_redis(self):
        """初始化Redis"""
        try:
            import aioredis
            # 這裡可以添加Redis初始化邏輯
            logger.info("Redis初始化完成")
        except ImportError:
            logger.info("Redis庫未安裝，跳過Redis初始化")
        except Exception as e:
            logger.warning(f"Redis初始化跳過: {e}")
    
    async def _start_background_tasks(self):
        """啟動後台任務"""
        # 這裡可以添加後台任務啟動邏輯
        logger.info("後台任務啟動完成")
    
    async def _stop_background_tasks(self):
        """停止後台任務"""
        # 這裡可以添加後台任務停止邏輯
        logger.info("後台任務停止完成")
    
    async def _close_database(self):
        """關閉數據庫連接"""
        try:
            from app.core.database import close_db
            await close_db()
            logger.info("數據庫連接關閉完成")
        except Exception as e:
            logger.warning(f"數據庫連接關閉跳過: {e}")
    
    async def _close_redis(self):
        """關閉Redis連接"""
        # 這裡可以添加Redis連接關閉邏輯
        logger.info("Redis連接關閉完成")
    
    def get_uptime(self) -> float:
        """獲取運行時間"""
        if self.start_time:
            import time
            return time.time() - self.start_time
        return 0.0
    
    async def run(self, host: str = "0.0.0.0", port: int = 8000, 
                  mode: str = "full", reload: bool = False):
        """
        運行服務
        
        Args:
            host: 主機地址
            port: 端口
            mode: 運行模式
            reload: 是否啟用熱重載
        """
        logger.info(f"開始啟動服務 - 主機: {host}, 端口: {port}, 模式: {mode}")
        
        # 初始化應用
        app = await self.initialize(mode)
        
        # 設置運行狀態
        self.running = True
        
        # 配置Uvicorn
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            reload=reload,
            log_level=self.config.get("log_level", "info").lower(),
            access_log=True,
            loop="asyncio"
        )
        
        server = uvicorn.Server(config)
        
        try:
            logger.info("服務啟動完成，開始監聽...")
            
            # 運行服務器
            await server.serve()
            
        except KeyboardInterrupt:
            logger.info("接收到鍵盤中斷信號")
        except Exception as e:
            logger.error(f"服務運行錯誤: {e}")
            raise
        finally:
            self.running = False
            logger.info("服務已停止")
    
    def get_status(self) -> Dict[str, Any]:
        """獲取服務狀態"""
        return {
            "running": self.running,
            "uptime": self.get_uptime(),
            "config_loaded": self.config is not None,
            "app_initialized": self.app is not None
        }


# 全局服務啟動器實例
service_launcher = ServiceLauncher()


def create_app(mode: str = "full") -> FastAPI:
    """
    創建應用（供外部使用）
    
    Args:
        mode: 運行模式
        
    Returns:
        FastAPI應用實例
    """
    # 這是一個同步包裝器，用於創建應用
    # 注意：這需要在事件循環中運行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        app = loop.run_until_complete(service_launcher.initialize(mode))
        return app
    finally:
        loop.close()


async def run_service(host: str = "0.0.0.0", port: int = 8000, 
                     mode: str = "full", reload: bool = False):
    """
    運行服務（異步版本）
    
    Args:
        host: 主機地址
        port: 端口
        mode: 運行模式
        reload: 是否啟用熱重載
    """
    await service_launcher.run(host, port, mode, reload)


def run_service_sync(host: str = "0.0.0.0", port: int = 8000, 
                    mode: str = "full", reload: bool = False):
    """
    運行服務（同步版本）
    
    Args:
        host: 主機地址
        port: 端口
        mode: 運行模式
        reload: 是否啟用熱重載
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(run_service(host, port, mode, reload))
    except KeyboardInterrupt:
        logger.info("服務被用戶中斷")
    except Exception as e:
        logger.error(f"服務運行錯誤: {e}")
        sys.exit(1)
    finally:
        loop.close()


if __name__ == "__main__":
    # 命令行運行支持
    import argparse
    
    parser = argparse.ArgumentParser(description="Proxy Collector 服務啟動器")
    parser.add_argument("--host", default="0.0.0.0", help="主機地址")
    parser.add_argument("--port", type=int, default=8000, help="端口")
    parser.add_argument("--mode", default="full", choices=["full", "api", "mock"], help="運行模式")
    parser.add_argument("--reload", action="store_true", help="啟用熱重載")
    parser.add_argument("--config-dir", help="配置目錄路徑")
    
    args = parser.parse_args()
    
    # 設置配置目錄
    if args.config_dir:
        config_manager.config_dir = Path(args.config_dir)
    
    # 運行服務
    run_service_sync(args.host, args.port, args.mode, args.reload)