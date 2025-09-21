"""
主應用程序模塊
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.database import init_db as init_database, close_db as close_database
from app.core.logging import setup_logging, get_logger
from app.api import v1_router

# 設置日誌
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用程序生命週期管理
    
    Args:
        app: FastAPI應用程序實例
    """
    # 啟動時
    logger.info("正在啟動應用程序...")
    
    # 初始化數據庫
    await init_database()
    logger.info("數據庫初始化完成")
    
    yield
    
    # 關閉時
    logger.info("正在關閉應用程序...")
    
    # 關閉數據庫連接
    await close_database()
    logger.info("應用程序已關閉")


# 創建FastAPI應用程序
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="代理IP池收集器後端API",
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊API路由
app.include_router(v1_router)

# 創建靜態文件目錄
if not os.path.exists("static"):
    os.makedirs("static")

# 掛載靜態文件
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """根端點"""
    return {
        "message": "代理IP池收集器API",
        "version": settings.VERSION,
        "status": "運行中",
    }


@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",  # 這裡應該返回實際時間
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )