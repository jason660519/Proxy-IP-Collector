"""
簡化版 FastAPI 服務器 - 用於快速啟動和測試
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import json
import os
from datetime import datetime
from typing import List, Dict, Any

app = FastAPI(title="Proxy Collector API", version="1.0.0")

# 靜態文件配置
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

@app.get("/")
async def root():
    """根路徑 - 重定向到前端頁面"""
    return {"message": "Proxy IP Pool Collector API", "status": "running", "timestamp": datetime.now().isoformat()}

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/v1/extract/extractors")
async def get_available_extractors():
    """獲取可用的爬取器列表"""
    extractors = [
        "89ip.cn",
        "kuaidaili-intr", 
        "kuaidaili-inha",
        "geonode-api-v2",
        "proxydb-net",
        "proxynova-com",
        "spys-one",
        "free-proxy-list.net",
        "ssl-proxies"
    ]
    return {
        "success": True,
        "extractors": extractors,
        "count": len(extractors)
    }

@app.post("/api/v1/extract/{extractor_name}")
async def extract_proxies(extractor_name: str, request: Dict[str, Any] = None):
    """模擬代理提取"""
    # 模擬代理數據
    mock_proxies = [
        {
            "ip": "203.0.113.1",
            "port": 8080,
            "protocol": "http",
            "country": "US",
            "anonymity_level": "elite",
            "speed": 150,
            "source": extractor_name,
            "is_active": True,
            "last_checked": datetime.now().isoformat()
        },
        {
            "ip": "198.51.100.2",
            "port": 3128,
            "protocol": "https",
            "country": "DE",
            "anonymity_level": "anonymous",
            "speed": 200,
            "source": extractor_name,
            "is_active": True,
            "last_checked": datetime.now().isoformat()
        },
        {
            "ip": "192.0.2.3",
            "port": 1080,
            "protocol": "socks5",
            "country": "JP",
            "anonymity_level": "transparent",
            "speed": 300,
            "source": extractor_name,
            "is_active": True,
            "last_checked": datetime.now().isoformat()
        }
    ]
    
    # 根據請求限制返回數量
    limit = request.get("limit", 10) if request else 10
    proxies = mock_proxies[:min(limit, len(mock_proxies))]
    
    return {
        "success": True,
        "extractor": extractor_name,
        "proxies": proxies,
        "count": len(proxies),
        "duration": 1.5,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/extract/all")
async def extract_all_proxies(request: Dict[str, Any] = None):
    """模擬所有爬取器提取代理"""
    extractors = [
        "89ip.cn",
        "kuaidaili-intr", 
        "kuaidaili-inha",
        "geonode-api-v2",
        "proxydb-net",
        "proxynova-com",
        "spys-one",
        "free-proxy-list.net",
        "ssl-proxies"
    ]
    
    all_proxies = []
    results = {}
    
    for extractor_name in extractors:
        # 模擬每個爬取器的結果
        mock_proxies = [
            {
                "ip": f"203.{i}.{j}.100",
                "port": 8080 + j,
                "protocol": ["http", "https", "socks5"][j % 3],
                "country": ["US", "DE", "JP", "CN"][i % 4],
                "anonymity_level": ["elite", "anonymous", "transparent"][j % 3],
                "speed": 100 + (i * j * 10),
                "source": extractor_name,
                "is_active": True,
                "last_checked": datetime.now().isoformat()
            }
            for i in range(1, 4) for j in range(1, 3)
        ]
        
        limit = request.get("limit", 20) if request else 20
        proxies = mock_proxies[:min(limit, len(mock_proxies))]
        
        results[extractor_name] = {
            "success": True,
            "count": len(proxies),
            "proxies": proxies
        }
        all_proxies.extend(proxies)
    
    return {
        "success": True,
        "total_proxies": len(all_proxies),
        "results": results,
        "all_proxies": all_proxies,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/docs")
async def get_docs():
    """API 文檔"""
    return {"message": "FastAPI 自動文檔", "url": "/docs"}

# 前端頁面路由
@app.get("/frontend/extractors_showcase.html", response_class=HTMLResponse)
async def get_showcase_page():
    """返回爬取器展示頁面"""
    try:
        with open("../frontend/extractors_showcase.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>前端頁面未找到</h1><p>請確保 frontend/extractors_showcase.html 文件存在</p>",
            status_code=404
        )

if __name__ == "__main__":
    import uvicorn
    print("🚀 啟動簡化版 Proxy Collector API 服務器...")
    print("📖 API 文檔: http://localhost:8001/docs")
    print("🌐 前端頁面: http://localhost:8001/frontend/extractors_showcase.html")
    uvicorn.run(app, host="0.0.0.0", port=8001)
