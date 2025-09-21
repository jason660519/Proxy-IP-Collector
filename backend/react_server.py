"""
為React前端提供API的簡化服務器
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json
import os
from datetime import datetime

# 創建FastAPI應用程序
app = FastAPI(
    title="Proxy IP Pool Collector API",
    version="1.0.0",
    description="代理IP池收集器API服務",
)

# 配置CORS - 允許React前端訪問
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根端點"""
    return {
        "message": "代理IP池收集器API",
        "version": "1.0.0",
        "status": "運行中",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "message": "服務器運行正常",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/crawl/status")
async def crawl_status():
    """爬取狀態端點"""
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
            },
            {
                "id": "task-003",
                "source": "proxydb.net",
                "status": "failed",
                "progress": 25,
                "crawled_count": 10,
                "started_at": "2024-01-20T10:15:00Z",
                "completed_at": "2024-01-20T10:18:00Z",
                "duration": 180,
                "error_message": "Connection timeout"
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
        "last_updated": datetime.now().isoformat()
    }

@app.get("/api/v1/proxies")
async def get_proxies(page: int = 1, page_size: int = 20, status: str = None):
    """獲取代理列表"""
    # 模擬數據
    proxies = [
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
            "created_at": "2024-01-20T09:00:00Z",
            "metadata": {"region": "asia"}
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
            "created_at": "2024-01-20T09:30:00Z",
            "metadata": {"region": "america"}
        },
        {
            "id": "3",
            "ip": "198.51.100.25",
            "port": 8080,
            "protocol": "https",
            "country": "DE",
            "city": "柏林",
            "anonymity": "transparent",
            "status": "inactive",
            "response_time": None,
            "success_rate": 0.0,
            "source": "proxydb.net",
            "quality_score": 0.3,
            "last_checked": "2024-01-20T10:25:00Z",
            "last_success": None,
            "created_at": "2024-01-20T08:00:00Z",
            "metadata": {"region": "europe"}
        }
    ]
    
    # 根據狀態過濾
    if status:
        proxies = [p for p in proxies if p["status"] == status]
    
    # 分頁
    start = (page - 1) * page_size
    end = start + page_size
    paginated_proxies = proxies[start:end]
    
    return {
        "proxies": paginated_proxies,
        "total": len(proxies),
        "page": page,
        "page_size": page_size,
        "total_pages": (len(proxies) + page_size - 1) // page_size
    }

@app.post("/api/v1/crawl/start")
async def start_crawl():
    """開始爬取"""
    return {
        "message": "爬取任務已開始",
        "task_id": f"task-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "status": "started",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/crawl/stop")
async def stop_crawl():
    """停止爬取"""
    return {
        "message": "爬取任務已停止",
        "status": "stopped",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/crawl/pause")
async def pause_crawl():
    """暫停爬取"""
    return {
        "message": "爬取任務已暫停",
        "status": "paused",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/tasks")
async def get_tasks():
    """獲取任務列表"""
    return {
        "tasks": [
            {
                "id": "task-001",
                "type": "crawl",
                "source": "89ip.cn",
                "status": "completed",
                "progress": 100,
                "result": {"crawled_count": 45},
                "error_message": None,
                "started_at": "2024-01-20T10:00:00Z",
                "completed_at": "2024-01-20T10:05:00Z",
                "duration": 300
            },
            {
                "id": "task-002",
                "type": "validation",
                "source": "batch_validation",
                "status": "running",
                "progress": 75,
                "result": {"validated_count": 150},
                "error_message": None,
                "started_at": "2024-01-20T10:10:00Z",
                "completed_at": None,
                "duration": None
            }
        ],
        "total": 2
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 啟動代理IP池收集器API服務器...")
    print("📡 API地址: http://localhost:8000")
    print("🔗 健康檢查: http://localhost:8000/api/health")
    print("📊 代理統計: http://localhost:8000/api/v1/proxies/stats")
    print("🕷️ 爬取狀態: http://localhost:8000/api/v1/crawl/status")
    
    uvicorn.run(
        "react_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
