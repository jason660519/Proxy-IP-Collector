"""
統一服務架構 - 解決多重啟動器問題
提供單一的、可配置的服務入口點
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# 將後端目錄添加到Python路徑
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.database import init_db as init_database, close_db as close_database
from app.core.logging import setup_logging, get_logger
from app.api import v1_router

# 設置日誌
setup_logging()
logger = get_logger(__name__)


class UnifiedServer:
    """
    統一服務器類
    提供單一的服務入口點，支持多種運行模式
    """
    
    def __init__(self, mode: str = "full", mock_data: bool = False):
        """
        初始化統一服務器
        
        Args:
            mode: 運行模式 ("full":完整模式, "api":僅API模式, "mock":模擬數據模式)
            mock_data: 是否使用模擬數據
        """
        self.mode = mode
        self.mock_data = mock_data
        self.app = None
        logger.info(f"初始化統一服務器 - 模式: {mode}, 模擬數據: {mock_data}")
    
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """
        應用程序生命週期管理
        
        Args:
            app: FastAPI應用程序實例
        """
        logger.info(f"正在啟動應用程序 (模式: {self.mode})...")
        
        try:
            # 根據模式初始化資源
            if self.mode in ["full", "api"]:
                # 初始化數據庫
                await init_database()
                logger.info("數據庫初始化完成")
            
            if self.mode == "full":
                # 初始化其他服務
                await self._init_services()
            
            yield
            
        except Exception as e:
            logger.error(f"應用程序啟動失敗: {e}")
            raise
        
        finally:
            # 清理資源
            logger.info("正在關閉應用程序...")
            if self.mode in ["full", "api"]:
                await close_database()
                logger.info("數據庫連接已關閉")
    
    async def _init_services(self):
        """初始化其他服務"""
        logger.info("初始化其他服務...")
        # 這裡可以添加其他服務的初始化邏輯
        pass
    
    def create_app(self) -> FastAPI:
        """
        創建FastAPI應用程序
        
        Returns:
            FastAPI應用程序實例
        """
        # 創建FastAPI應用程序
        self.app = FastAPI(
            title=settings.APP_NAME,
            version=settings.APP_VERSION,
            description=f"代理IP池收集器後端API (模式: {self.mode})",
            lifespan=self.lifespan,
            docs_url="/docs" if self.mode != "mock" else None,
            redoc_url="/redoc" if self.mode != "mock" else None,
        )
        
        # 配置CORS
        self._setup_cors()
        
        # 設置路由
        self._setup_routes()
        
        # 掛載靜態文件（僅在full模式下）
        if self.mode == "full":
            self._setup_static_files()
        
        logger.info(f"FastAPI應用程序創建完成 (模式: {self.mode})")
        return self.app
    
    def _setup_cors(self):
        """設置CORS中間件"""
        origins = settings.ALLOWED_HOSTS if settings.ALLOWED_HOSTS != ["*"] else [
            "http://localhost:3000",
            "http://localhost:5173", 
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173"
        ]
        
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("CORS中間件配置完成")
    
    def _setup_routes(self):
        """設置路由"""
        # 根端點
        @self.app.get("/")
        async def root():
            """根端點"""
            return {
                "message": "代理IP池收集器API",
                "version": settings.APP_VERSION,
                "status": "運行中",
                "mode": self.mode,
                "mock_data": self.mock_data,
                "timestamp": "2024-01-20T10:30:00Z"  # 實際應該使用當前時間
            }
        
        # 統一的健康檢查端點
        @self.app.get("/health")
        @self.app.get("/api/health")
        @self.app.get("/api/v1/health")
        async def health_check():
            """統一健康檢查端點"""
            health_status = {
                "status": "healthy",
                "message": "服務器運行正常",
                "version": settings.APP_VERSION,
                "mode": self.mode,
                "timestamp": "2024-01-20T10:30:00Z"  # 實際應該使用當前時間
            }
            
            # 根據模式添加額外信息
            if self.mode == "full":
                health_status["services"] = {
                    "database": "connected",
                    "api": "running",
                    "crawler": "active"
                }
            elif self.mode == "api":
                health_status["services"] = {
                    "database": "connected", 
                    "api": "running"
                }
            else:
                health_status["services"] = {
                    "api": "running (mock mode)"
                }
            
            return health_status
        
        # 系統信息端點
        @self.app.get("/info")
        async def system_info():
            """系統信息端點"""
            import platform
            import sys
            from datetime import datetime
            
            return {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "app_version": settings.APP_VERSION,
                "mode": self.mode,
                "system": {
                    "platform": platform.system(),
                    "architecture": platform.architecture(),
                    "processor": platform.processor(),
                    "python_implementation": platform.python_implementation()
                },
                "timestamp": datetime.now().isoformat()
            }
        
        # 根據模式註冊不同的API路由
        if self.mode in ["full", "api"]:
            # 註冊完整API路由 (v1_router已經有/api/v1前綴，不需要再次添加)
            self.app.include_router(v1_router)
            logger.info("完整API路由註冊完成")
        
        if self.mode == "mock":
            # 註冊模擬數據路由
            self._setup_mock_routes()
        
        logger.info(f"路由設置完成 (模式: {self.mode})")
    
    def _setup_mock_routes(self):
        """設置模擬數據路由"""
        from datetime import datetime
        
        @self.app.get("/api/v1/crawl/status")
        async def mock_crawl_status():
            """模擬爬取狀態端點"""
            return {
                "running_tasks": 2,
                "completed_tasks": 15,
                "failed_tasks": 3,
                "total_crawled": 1247,
                "tasks": [
                    {
                        "id": "task-001",
                        "source": "89ip.cn",
                        "status": "completed",
                        "progress": 100,
                        "crawled_count": 45,
                        "started_at": "2024-01-20T10:00:00Z",
                        "completed_at": "2024-01-20T10:05:00Z",
                        "duration": 300,
                        "error_message": None
                    },
                    {
                        "id": "task-002",
                        "source": "kuaidaili.com", 
                        "status": "running",
                        "progress": 60,
                        "crawled_count": 30,
                        "started_at": "2024-01-20T10:10:00Z",
                        "completed_at": None,
                        "duration": None,
                        "error_message": None
                    }
                ]
            }
        
        @self.app.get("/api/v1/proxies/stats")
        async def mock_proxy_stats():
            """模擬代理統計端點"""
            return {
                "total_proxies": 1247,
                "active_proxies": 892,
                "inactive_proxies": 355,
                "protocols": {
                    "http": 800,
                    "https": 300,
                    "socks4": 100,
                    "socks5": 47
                },
                "countries": {
                    "CN": 400,
                    "US": 300,
                    "JP": 200,
                    "HK": 150,
                    "SG": 100,
                    "DE": 97
                },
                "anonymity_levels": {
                    "elite": 500,
                    "anonymous": 600,
                    "transparent": 147
                },
                "avg_response_time": 1.2,
                "avg_success_rate": 0.715,
                "avg_quality_score": 0.8,
                "last_updated": datetime.now().isoformat()
            }
    
    def _setup_static_files(self):
        """設置靜態文件"""
        try:
            # 檢查前端構建目錄
            frontend_build_dir = Path(__file__).resolve().parent.parent.parent.parent / "frontend-react" / "dist"
            
            if frontend_build_dir.exists():
                # 掛載前端構建文件
                self.app.mount("/", StaticFiles(directory=str(frontend_build_dir), html=True), name="frontend")
                logger.info(f"前端靜態文件掛載完成: {frontend_build_dir}")
            else:
                # 創建後備靜態文件目錄
                static_dir = Path("static")
                static_dir.mkdir(exist_ok=True)
                
                # 掛載後備靜態文件
                self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
                logger.warning(f"前端構建目錄不存在，使用後備靜態目錄: {static_dir}")
                
                # 創建簡單的HTML頁面
                self._create_fallback_html()
            
        except Exception as e:
            logger.warning(f"靜態文件設置失敗: {e}")
    
    def _create_fallback_html(self):
        """創建後備HTML頁面"""
        try:
            static_dir = Path("static")
            index_html = static_dir / "index.html"
            
            html_content = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>代理IP池收集器</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 40px; }
        .status { padding: 20px; background: #e8f5e8; border-radius: 4px; margin: 20px 0; }
        .warning { padding: 20px; background: #fff3cd; border-radius: 4px; margin: 20px 0; border-left: 4px solid #ffc107; }
        .api-link { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 10px 5px; }
        .api-link:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🕸️ 代理IP池收集器</h1>
            <p>系統運行正常</p>
        </div>
        
        <div class="status">
            <h3>✅ 後端API服務運行中</h3>
            <p>模式: {mode}</p>
            <p>前端構建文件未找到，請執行以下命令構建前端:</p>
            <code>cd frontend-react && npm run build</code>
        </div>
        
        <div class="warning">
            <h3>⚠️ 開發模式提示</h3>
            <p>如果您正在開發前端，請在前端目錄運行:</p>
            <code>cd frontend-react && npm run dev</code>
            <p>這將在 http://localhost:3000 啟動開發服務器</p>
        </div>
        
        <div style="text-align: center; margin-top: 40px;">
            <h3>API文檔</h3>
            <a href="/docs" class="api-link">📚 Swagger文檔</a>
            <a href="/redoc" class="api-link">📖 ReDoc文檔</a>
            <a href="/health" class="api-link">🏥 健康檢查</a>
        </div>
    </div>
</body>
</html>
            """.format(mode=self.mode)
            
            index_html.write_text(html_content, encoding='utf-8')
            logger.info("後備HTML頁面創建完成")
            
        except Exception as e:
            logger.warning(f"後備HTML頁面創建失敗: {e}")
    
    def run(self, host: str = None, port: int = None, reload: bool = None, **kwargs):
        """
        運行服務器
        
        Args:
            host: 主機地址
            port: 端口
            reload: 是否啟用熱重載
            **kwargs: 其他uvicorn參數
        """
        import uvicorn
        
        # 使用配置或默認值
        host = host or settings.HOST
        port = port or settings.PORT
        
        # 創建應用程序
        app = self.create_app()
        
        logger.info(f"啟動服務器 - {host}:{port} (模式: {self.mode})")
        
        # 設置reload參數 - 優先使用傳入的參數，否則使用settings.DEBUG
        if reload is None:
            reload = settings.DEBUG
        
        # 運行服務器
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            log_level=kwargs.pop("log_level", "info"),
            **kwargs
        )


def create_server(mode: str = "full", mock_data: bool = False) -> UnifiedServer:
    """
    工廠函數 - 創建統一服務器實例
    
    Args:
        mode: 運行模式
        mock_data: 是否使用模擬數據
    
    Returns:
        UnifiedServer實例
    """
    return UnifiedServer(mode=mode, mock_data=mock_data)


# 向後兼容的創建函數
def create_full_server() -> UnifiedServer:
    """創建完整服務器"""
    return create_server(mode="full")


def create_api_server() -> UnifiedServer:
    """創建僅API服務器"""
    return create_server(mode="api")


def create_mock_server() -> UnifiedServer:
    """創建模擬服務器"""
    return create_server(mode="mock", mock_data=True)


if __name__ == "__main__":
    import argparse
    
    # 命令行參數解析
    parser = argparse.ArgumentParser(description="統一服務器啟動器")
    parser.add_argument(
        "--mode", 
        choices=["full", "api", "mock"], 
        default="full",
        help="運行模式"
    )
    parser.add_argument(
        "--mock", 
        action="store_true",
        help="使用模擬數據"
    )
    parser.add_argument(
        "--host", 
        default=None,
        help="主機地址"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=None,
        help="端口"
    )
    
    args = parser.parse_args()
    
    # 創建並運行服務器
    server = create_server(mode=args.mode, mock_data=args.mock)
    server.run(host=args.host, port=args.port)