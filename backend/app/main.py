"""
代理收集器主應用
集成監控系統的FastAPI應用
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.monitoring_config import MonitoringConfig
from .core.monitoring_middleware import setup_monitoring
from .core.error_handler import ErrorHandlerMiddleware
from .core.database_config import DatabaseConfig, DatabaseType
from .core.database_manager import get_db_manager, init_db_manager, close_db_manager
from .api.monitoring_endpoints import router as monitoring_router
from .api.v1 import crawl, proxies, system, tasks


def create_app(config: MonitoringConfig = None, db_config: DatabaseConfig = None) -> FastAPI:
    """創建FastAPI應用實例
    
    Args:
        config: 監控配置，如果為None則使用默認配置
        db_config: 數據庫配置，如果為None則使用默認配置
        
    Returns:
        FastAPI: FastAPI應用實例
    """
    
    # 使用提供的配置或創建默認配置
    if config is None:
        config = MonitoringConfig.from_env()
    
    if db_config is None:
        db_config = DatabaseConfig.from_env()
    
    # 創建FastAPI應用
    app = FastAPI(
        title="Proxy Collector API",
        description="代理收集器系統API",
        version="1.0.0",
        docs_url="/docs" if config.log_level == "DEBUG" else None,
        redoc_url="/redoc" if config.log_level == "DEBUG" else None,
    )
    
    # 存儲配置到應用狀態
    app.state.monitoring_config = config
    app.state.database_config = db_config
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 在生產環境中應該配置具體的域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 添加全局錯誤處理中間件
    app.add_middleware(ErrorHandlerMiddleware)
    
    # 設置監控系統
    setup_monitoring(app, config)
    
    # 註冊路由
    app.include_router(monitoring_router)
    app.include_router(crawl.router, prefix="/api/v1", tags=["crawl"])
    app.include_router(proxies.router, prefix="/api/v1", tags=["proxies"])
    app.include_router(system.router, prefix="/api/v1", tags=["system"])
    app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
    
    # 根路由
    @app.get("/")
    async def root():
        # 獲取數據庫管理器信息
        db_manager = get_db_manager()
        db_stats = db_manager.get_connection_stats() if db_manager else {}  # 同步方法，不需要await
        db_info = await db_manager.get_database_info() if db_manager else {}  # 異步方法，需要await
        
        return {
            "message": "Proxy Collector API",
            "version": "1.0.0",
            "status": "running",
            "database": {
                "type": db_config.database_type.value,
                "initialized": db_manager is not None,
                "stats": db_stats,
                "info": db_info
            },
            "monitoring": {
                "enabled": config.prometheus_enabled,
                "health_check": "/monitoring/health",
                "metrics": "/monitoring/metrics",
                "status": "/monitoring/status"
            }
        }
    
    # 應用事件處理
    @app.on_event("startup")
    async def startup_event():
        from .core.structured_logging import get_logger
        logger = get_logger("app")
        logger.info("代理收集器應用啟動", config=config.log_level)
        
        # 初始化數據庫管理器
        try:
            success = await init_db_manager(db_config)
            if success:
                manager = get_db_manager()
                db_info = await manager.get_database_info()
                logger.info("數據庫初始化成功", database_type=db_config.database_type.value)
                logger.info("數據庫配置信息", db_info=db_info)
            else:
                logger.error("數據庫初始化失敗")
                # 在開發模式下允許應用繼續運行
                if config.log_level != "DEBUG":
                    raise RuntimeError("數據庫初始化失敗，應用無法啟動")
        except Exception as e:
            logger.error(f"數據庫初始化錯誤: {str(e)}")
            if config.log_level != "DEBUG":
                raise
    
    @app.on_event("shutdown")
    async def shutdown_event():
        from .core.structured_logging import get_logger
        logger = get_logger("app")
        logger.info("代理收集器應用關閉")
        
        # 關閉數據庫連接
        try:
            await close_db_manager()
            logger.info("數據庫連接已關閉")
        except Exception as e:
            logger.error(f"關閉數據庫連接時出錯: {str(e)}")
    
    return app


# 創建應用實例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    # 開發環境下運行
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )