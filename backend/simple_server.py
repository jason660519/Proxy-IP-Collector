"""
簡化的測試服務器
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# 創建FastAPI應用程序
app = FastAPI(
    title="Proxy IP Pool Collector",
    version="1.0.0",
    description="代理IP池收集器後端API",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載前端靜態文件
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

@app.get("/api/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "message": "服務器運行正常",
        "version": "1.0.0"
    }

@app.get("/api/v1/crawl/status")
async def crawl_status():
    """爬取狀態端點"""
    return {
        "running_tasks": 0,
        "completed_tasks": 5,
        "failed_tasks": 1,
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
                "duration": 300
            },
            {
                "id": "task-002", 
                "source": "kuaidaili.com",
                "status": "running",
                "progress": 60,
                "crawled_count": 30,
                "started_at": "2024-01-20T10:10:00Z",
                "completed_at": None,
                "duration": None
            }
        ]
    }

@app.get("/api/v1/proxies/stats")
async def proxy_stats():
    """代理統計端點"""
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
        "last_updated": "2024-01-20T10:30:00Z"
    }

@app.get("/api/v1/proxies")
async def get_proxies():
    """獲取代理列表"""
    return {
        "proxies": [
            {
                "id": "1",
                "ip": "192.168.1.100",
                "port": 8080,
                "protocol": "http",
                "country": "HK",
                "city": "香港",
                "anonymity": "elite",
                "status": "active",
                "response_time": 125,
                "success_rate": 0.95,
                "source": "89ip.cn",
                "quality_score": 0.9,
                "last_checked": "2024-01-20T10:28:00Z",
                "last_success": "2024-01-20T10:28:00Z",
                "created_at": "2024-01-20T09:00:00Z"
            },
            {
                "id": "2",
                "ip": "203.0.113.45",
                "port": 3128,
                "protocol": "http",
                "country": "US",
                "city": "紐約",
                "anonymity": "anonymous",
                "status": "testing",
                "response_time": None,
                "success_rate": 0.0,
                "source": "kuaidaili.com",
                "quality_score": 0.5,
                "last_checked": "2024-01-20T10:29:00Z",
                "last_success": None,
                "created_at": "2024-01-20T09:30:00Z"
            }
        ],
        "total": 1247,
        "page": 1,
        "page_size": 20,
        "total_pages": 63
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "simple_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
