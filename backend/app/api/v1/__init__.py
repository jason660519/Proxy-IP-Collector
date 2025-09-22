"""
API v1 路由初始化
"""
from fastapi import APIRouter

from . import crawl, proxies, system, tasks, error_test
from ..routes import extractors

router = APIRouter(prefix="/api/v1")

# 註冊子路由
router.include_router(crawl.router)
router.include_router(proxies.router)
router.include_router(system.router)
router.include_router(tasks.router)
router.include_router(extractors.router)
router.include_router(error_test.router)

# 導出為v1_router供外部使用
v1_router = router