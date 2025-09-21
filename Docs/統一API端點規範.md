# 統一API端點規範

## 概述

本文檔定義了代理IP池收集器項目的統一API端點規範，旨在解決原有架構中API端點不一致、響應格式不統一的問題，提供標準化的接口設計。

## API設計原則

### 1. RESTful設計
- 使用HTTP動詞表示操作類型
- 使用複數名詞表示資源集合
- 使用嵌套路徑表示資源關係

### 2. 統一響應格式
所有API響應遵循統一的標準格式，包含狀態、消息、數據等關鍵信息。

### 3. 版本控制
API使用URL路徑進行版本控制，當前版本為v1。

## 統一響應格式

### 標準響應結構
```json
{
    "status": "success | error",
    "message": "操作結果描述",
    "data": {},
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0.0",
    "request_id": "uuid",
    "path": "/api/v1/endpoint"
}
```

### 響應字段說明
| 字段名 | 類型 | 說明 |
|--------|------|------|
| status | string | 響應狀態：success/error |
| message | string | 操作結果的詳細描述 |
| data | object | 具體的響應數據 |
| timestamp | string | 響應生成時間 (ISO 8601格式) |
| version | string | API版本號 |
| request_id | string | 請求唯一標識符 |
| path | string | 請求的API端點路徑 |

### 分頁響應格式
```json
{
    "status": "success",
    "message": "數據獲取成功",
    "data": {
        "items": [],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total": 100,
            "pages": 5,
            "has_next": true,
            "has_prev": false
        }
    },
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0.0"
}
```

## HTTP狀態碼規範

### 成功響應
| 狀態碼 | 說明 | 使用場景 |
|--------|------|----------|
| 200 | OK | 請求成功，返回請求的數據 |
| 201 | Created | 資源創建成功 |
| 202 | Accepted | 請求已接受，正在處理中 |
| 204 | No Content | 請求成功，無返回內容 |

### 客戶端錯誤
| 狀態碼 | 說明 | 使用場景 |
|--------|------|----------|
| 400 | Bad Request | 請求參數錯誤 |
| 401 | Unauthorized | 未授權，需要身份驗證 |
| 403 | Forbidden | 無權限訪問該資源 |
| 404 | Not Found | 請求的資源不存在 |
| 409 | Conflict | 資源衝突 |
| 422 | Unprocessable Entity | 請求格式正確，但語義錯誤 |

### 服務器錯誤
| 狀態碼 | 說明 | 使用場景 |
|--------|------|----------|
| 500 | Internal Server Error | 服務器內部錯誤 |
| 502 | Bad Gateway | 網關錯誤 |
| 503 | Service Unavailable | 服務暫時不可用 |
| 504 | Gateway Timeout | 網關超時 |

## API端點列表

### 1. 系統管理端點

#### 健康檢查
```http
GET /health
```
**功能**：系統健康狀態檢查
**響應示例**：
```json
{
    "status": "success",
    "message": "系統運行正常",
    "data": {
        "status": "healthy",
        "checks": {
            "database": {"status": "healthy", "response_time": 15},
            "redis": {"status": "healthy", "response_time": 5},
            "memory": {"status": "healthy", "usage_percent": 45},
            "disk": {"status": "healthy", "usage_percent": 62}
        },
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "1.0.0"
    }
}
```

#### 系統信息
```http
GET /info
```
**功能**：獲取系統詳細信息
**響應示例**：
```json
{
    "status": "success",
    "message": "系統信息獲取成功",
    "data": {
        "app_name": "proxy-collector",
        "version": "1.0.0",
        "environment": "production",
        "start_time": "2024-01-01T00:00:00Z",
        "uptime_seconds": 3600,
        "python_version": "3.9.0",
        "system_info": {
            "platform": "linux",
            "architecture": "x86_64",
            "cpu_count": 4,
            "memory_total": 8192
        }
    }
}
```

### 2. 代理管理端點

#### 獲取代理列表
```http
GET /api/v1/proxies
```
**功能**：獲取代理IP列表
**查詢參數**：
- `page` (integer): 頁碼，默認1
- `per_page` (integer): 每頁數量，默認20
- `country` (string): 國家代碼過濾
- `type` (string): 代理類型 (http, https, socks4, socks5)
- `anonymity` (string): 匿名級別 (transparent, anonymous, elite)
- `is_active` (boolean): 是否只返回活躍代理

**響應示例**：
```json
{
    "status": "success",
    "message": "代理列表獲取成功",
    "data": {
        "items": [
            {
                "id": "proxy_001",
                "ip": "192.168.1.100",
                "port": 8080,
                "type": "http",
                "country": "US",
                "city": "New York",
                "anonymity": "elite",
                "response_time": 1500,
                "success_rate": 0.95,
                "last_checked": "2024-01-01T00:00:00Z",
                "is_active": true
            }
        ],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total": 150,
            "pages": 8,
            "has_next": true,
            "has_prev": false
        }
    }
}
```

#### 獲取代理詳情
```http
GET /api/v1/proxies/{proxy_id}
```
**功能**：獲取指定代理的詳細信息
**路徑參數**：
- `proxy_id` (string): 代理唯一標識符

**響應示例**：
```json
{
    "status": "success",
    "message": "代理詳情獲取成功",
    "data": {
        "id": "proxy_001",
        "ip": "192.168.1.100",
        "port": 8080,
        "type": "http",
        "country": "US",
        "city": "New York",
        "anonymity": "elite",
        "response_time": 1500,
        "success_rate": 0.95,
        "total_requests": 1000,
        "successful_requests": 950,
        "last_checked": "2024-01-01T00:00:00Z",
        "last_success": "2024-01-01T00:00:00Z",
        "is_active": true,
        "source": "free-proxy-list.net",
        "validation_history": []
    }
}
```

#### 驗證代理
```http
POST /api/v1/proxies/{proxy_id}/validate
```
**功能**：驗證指定代理的可用性
**路徑參數**：
- `proxy_id` (string): 代理唯一標識符

**響應示例**：
```json
{
    "status": "success",
    "message": "代理驗證完成",
    "data": {
        "proxy_id": "proxy_001",
        "is_valid": true,
        "response_time": 1200,
        "test_url": "http://httpbin.org/ip",
        "validation_time": "2024-01-01T00:00:00Z"
    }
}
```

#### 批量驗證代理
```http
POST /api/v1/proxies/validate
```
**功能**：批量驗證多個代理的可用性
**請求體**：
```json
{
    "proxy_ids": ["proxy_001", "proxy_002", "proxy_003"]
}
```

**響應示例**：
```json
{
    "status": "success",
    "message": "批量驗證完成",
    "data": {
        "total": 3,
        "valid": 2,
        "invalid": 1,
        "results": [
            {
                "proxy_id": "proxy_001",
                "is_valid": true,
                "response_time": 1200
            },
            {
                "proxy_id": "proxy_002",
                "is_valid": true,
                "response_time": 1500
            },
            {
                "proxy_id": "proxy_003",
                "is_valid": false,
                "error": "Connection timeout"
            }
        ]
    }
}
```

### 3. 爬蟲管理端點

#### 獲取爬蟲狀態
```http
GET /api/v1/scraping/status
```
**功能**：獲取爬蟲任務的當前狀態
**響應示例**：
```json
{
    "status": "success",
    "message": "爬蟲狀態獲取成功",
    "data": {
        "is_running": true,
        "active_tasks": 3,
        "total_tasks": 10,
        "completed_tasks": 7,
        "failed_tasks": 0,
        "start_time": "2024-01-01T00:00:00Z",
        "uptime_seconds": 1800,
        "sources": [
            {
                "name": "free-proxy-list.net",
                "status": "active",
                "last_scrape": "2024-01-01T00:00:00Z",
                "proxies_found": 50
            },
            {
                "name": "proxy-list.download",
                "status": "active",
                "last_scrape": "2024-01-01T00:00:00Z",
                "proxies_found": 30
            }
        ]
    }
}
```

#### 啟動爬蟲任務
```http
POST /api/v1/scraping/start
```
**功能**：啟動爬蟲任務
**響應示例**：
```json
{
    "status": "success",
    "message": "爬蟲任務已啟動",
    "data": {
        "task_id": "task_001",
        "status": "running",
        "start_time": "2024-01-01T00:00:00Z",
        "sources": ["free-proxy-list.net", "proxy-list.download"]
    }
}
```

#### 停止爬蟲任務
```http
POST /api/v1/scraping/stop
```
**功能**：停止爬蟲任務
**響應示例**：
```json
{
    "status": "success",
    "message": "爬蟲任務已停止",
    "data": {
        "task_id": "task_001",
        "status": "stopped",
        "stop_time": "2024-01-01T00:00:00Z",
        "duration_seconds": 3600,
        "summary": {
            "total_proxies": 150,
            "new_proxies": 25,
            "updated_proxies": 125
        }
    }
}
```

#### 獲取爬蟲統計
```http
GET /api/v1/scraping/stats
```
**功能**：獲取爬蟲統計信息
**查詢參數**：
- `time_range` (string): 時間範圍 (1h, 24h, 7d, 30d)

**響應示例**：
```json
{
    "status": "success",
    "message": "爬蟲統計獲取成功",
    "data": {
        "time_range": "24h",
        "total_proxies_found": 1200,
        "total_scraping_tasks": 48,
        "successful_tasks": 45,
        "failed_tasks": 3,
        "average_proxies_per_task": 25,
        "top_sources": [
            {"name": "free-proxy-list.net", "count": 500},
            {"name": "proxy-list.download", "count": 300}
        ],
        "hourly_stats": [
            {"hour": "00:00", "proxies": 45},
            {"hour": "01:00", "proxies": 38}
        ]
    }
}
```

### 4. 統計分析端點

#### 代理統計概覽
```http
GET /api/v1/stats/overview
```
**功能**：獲取代理統計概覽
**響應示例**：
```json
{
    "status": "success",
    "message": "統計概覽獲取成功",
    "data": {
        "total_proxies": 1500,
        "active_proxies": 1200,
        "countries": 45,
        "proxy_types": {
            "http": 800,
            "https": 400,
            "socks4": 200,
            "socks5": 100
        },
        "anonymity_levels": {
            "transparent": 300,
            "anonymous": 700,
            "elite": 500
        },
        "average_response_time": 1200,
        "overall_success_rate": 0.85
    }
}
```

#### 代理質量分析
```http
GET /api/v1/stats/quality
```
**功能**：獲取代理質量分析
**查詢參數**：
- `time_range` (string): 時間範圍 (1h, 24h, 7d, 30d)

**響應示例**：
```json
{
    "status": "success",
    "message": "質量分析獲取成功",
    "data": {
        "time_range": "24h",
        "quality_score": 8.5,
        "response_time_stats": {
            "min": 500,
            "max": 5000,
            "average": 1200,
            "median": 1000,
            "p95": 2500
        },
        "success_rate_stats": {
            "min": 0.3,
            "max": 1.0,
            "average": 0.85,
            "median": 0.9
        },
        "quality_distribution": {
            "excellent": 300,
            "good": 600,
            "fair": 400,
            "poor": 200
        }
    }
}
```

## 錯誤響應格式

### 標準錯誤響應
```json
{
    "status": "error",
    "message": "錯誤描述信息",
    "error_code": "ERROR_CODE",
    "details": {
        "field": "具體錯誤詳情"
    },
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0.0",
    "request_id": "uuid",
    "path": "/api/v1/endpoint"
}
```

### 常見錯誤碼
| 錯誤碼 | 說明 | HTTP狀態碼 |
|--------|------|------------|
| INVALID_PARAMETER | 參數無效 | 400 |
| RESOURCE_NOT_FOUND | 資源不存在 | 404 |
| UNAUTHORIZED | 未授權 | 401 |
| FORBIDDEN | 無權限 | 403 |
| RATE_LIMIT_EXCEEDED | 請求頻率超限 | 429 |
| INTERNAL_ERROR | 服務器內部錯誤 | 500 |
| SERVICE_UNAVAILABLE | 服務不可用 | 503 |

## 分頁參數規範

### 請求參數
| 參數名 | 類型 | 說明 | 默認值 |
|--------|------|------|--------|
| page | integer | 頁碼 | 1 |
| per_page | integer | 每頁數量 (最大100) | 20 |
| sort_by | string | 排序字段 | id |
| sort_order | string | 排序順序 (asc/desc) | asc |

### 響應分頁信息
```json
{
    "pagination": {
        "page": 1,
        "per_page": 20,
        "total": 100,
        "pages": 5,
        "has_next": true,
        "has_prev": false,
        "next_page": 2,
        "prev_page": null
    }
}
```

## 速率限制

### 限制規則
- 匿名用戶：每分鐘100次請求
- 認證用戶：每分鐘1000次請求
- 管理員：無限制

### 速率限制響應頭
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## 認證機制

### API Key認證
```http
GET /api/v1/proxies
Authorization: Bearer YOUR_API_KEY
```

### JWT Token認證
```http
GET /api/v1/proxies
Authorization: Bearer YOUR_JWT_TOKEN
```

## 內容協商

### 支持的格式
- `application/json` (默認)
- `application/xml` (可選)

### 請求頭示例
```http
Accept: application/json
Content-Type: application/json
```

## 實施建議

### 1. 逐步遷移
- 先實現核心端點 (/health, /api/v1/proxies)
- 保持向後兼容性
- 提供遷移期

### 2. 文檔自動生成
- 使用OpenAPI/Swagger規範
- 自動生成API文檔
- 提供交互式測試界面

### 3. 版本管理
- 使用URL路徑版本控制
- 支持多版本並行運行
- 提供版本遷移指南

### 4. 監控和日誌
- 記錄所有API請求和響應
- 監控API性能和錯誤率
- 設置告警機制

## 相關文件

- [架構統一化遷移指南](../backend/MIGRATION_GUIDE.md)
- [後端架構規格書](後端架構規格書.md)
- [API標準化實現](../backend/app/architecture/api_standard.py)

## 修訂歷史

| 版本 | 日期 | 修改內容 | 作者 |
|------|------|----------|------|
| 1.0.0 | 2024-01-01 | 初始版本 | 系統架構師 |

---

*本規範基於RESTful設計原則，結合項目實際需求制定，將根據項目發展持續優化更新。*