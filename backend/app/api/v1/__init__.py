"""
API v1 路由初始化
"""
from fastapi import APIRouter

from app.api.v1 import crawl, proxies, system
from app.api.routes import extractors

router = APIRouter(prefix="/api/v1")

# 註冊子路由
router.include_router(crawl.router)
router.include_router(proxies.router)
router.include_router(system.router)
router.include_router(extractors.router)