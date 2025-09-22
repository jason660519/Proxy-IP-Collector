# 代理收集器配置指南

本指南詳細介紹代理收集器的所有配置選項，幫助您根據實際需求自定義部署。

## 目錄

1. [環境配置](#環境配置)
2. [數據庫配置](#數據庫配置)
3. [監控配置](#監控配置)
4. [代理配置](#代理配置)
5. [安全配置](#安全配置)
6. [性能優化](#性能優化)
7. [故障排除](#故障排除)

## 環境配置

### 基本環境變量

創建 `.env` 文件來配置應用程序：

```bash
# 應用程序配置
APP_NAME=代理收集器
APP_VERSION=1.0.0
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# 服務器配置
HOST=0.0.0.0
PORT=8000
WORKERS=4

# 數據庫配置
DATABASE_TYPE=sqlite  # sqlite 或 postgresql
DATABASE_URL=sqlite:///data/proxy_collector.db
# PostgreSQL配置示例:
# DATABASE_URL=postgresql://user:password@localhost:5432/proxy_collector

# Redis配置
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# 監控配置
ENABLE_MONITORING=true
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=admin123

# 代理配置
PROXY_VALIDATION_TIMEOUT=30
PROXY_CHECK_INTERVAL=300
MAX_CONCURRENT_CHECKS=50
PROXY_TIMEOUT=10
```

### Docker環境變量

在 `docker-compose.yml` 中設置環境變量：

```yaml
environment:
  - APP_ENV=production
  - DATABASE_TYPE=postgresql
  - DATABASE_URL=postgresql://postgres:password@postgres:5432/proxy_collector
  - REDIS_URL=redis://redis:6379/0
  - ENABLE_MONITORING=true
```

## 數據庫配置

### SQLite配置

SQLite適合開發和小型部署：

```python
# backend/app/core/config_manager.py
DATABASE_CONFIG = {
    "type": "sqlite",
    "url": "sqlite:///data/proxy_collector.db",
    "pool_size": 5,
    "max_overflow": 10,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "echo": False  # SQL日誌
}
```

### PostgreSQL配置

PostgreSQL適合生產環境：

```python
# backend/app/core/config_manager.py
DATABASE_CONFIG = {
    "type": "postgresql",
    "url": "postgresql://user:password@localhost:5432/proxy_collector",
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "echo": False,
    "ssl_mode": "require",  # SSL連接
    "connect_args": {
        "connect_timeout": 10,
        "application_name": "proxy-collector"
    }
}
```

### 數據庫連接池優化

```python
# 連接池配置
POOL_CONFIG = {
    "pool_size": 20,          # 基本連接數
    "max_overflow": 30,      # 最大溢出連接數
    "pool_timeout": 30,      # 獲取連接超時時間
    "pool_recycle": 3600,    # 連接回收時間
    "pool_pre_ping": True,   # 連接預檢查
}
```

## 監控配置

### Prometheus配置

編輯 `monitoring/prometheus.yml`：

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'proxy-collector'

scrape_configs:
  - job_name: 'proxy-collector-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
    scrape_timeout: 5s

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 30s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Grafana配置

創建自定義儀表板配置：

```json
{
  "dashboard": {
    "title": "代理收集器監控",
    "refresh": "30s",
    "panels": [
      {
        "title": "代理數量趨勢",
        "type": "graph",
        "targets": [
          {
            "expr": "proxy_count_total",
            "legendFormat": "{{status}}"
          }
        ]
      }
    ]
  }
}
```

### 告警規則配置

編輯 `monitoring/alert_rules.yml`：

```yaml
groups:
  - name: proxy_collector_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: DatabaseConnectionFailed
        expr: health_check_status{component="database"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failed"
          description: "Database health check failed"

      - alert: HighMemoryUsage
        expr: system_memory_usage_percent > 90
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}%"
```

## 代理配置

### 代理驗證配置

```python
# backend/app/core/config_manager.py
PROXY_CONFIG = {
    "validation_timeout": 30,        # 驗證超時時間（秒）
    "check_interval": 300,          # 檢查間隔（秒）
    "max_concurrent_checks": 50,    # 最大並發檢查數
    "proxy_timeout": 10,             # 代理超時時間（秒）
    "retry_attempts": 3,             # 重試次數
    "retry_delay": 5,               # 重試延遲（秒）
    
    # 測試URL配置
    "test_urls": [
        "http://httpbin.org/ip",
        "https://api.ipify.org?format=json",
        "http://icanhazip.com"
    ],
    
    # 地理定位API
    "geo_location_api": "http://ip-api.com/json/{ip}",
    
    # 匿名性檢查
    "anonymity_check": {
        "enabled": True,
        "headers": ["X-Forwarded-For", "X-Real-IP", "Via", "Proxy-Connection"],
        "timeout": 15
    }
}
```

### 代理源配置

```python
# 代理源配置
PROXY_SOURCES = {
    "free_proxy_list": {
        "enabled": True,
        "url": "https://www.freeproxy-list.net/",
        "update_interval": 3600,
        "max_proxies": 1000
    },
    "proxy_daily": {
        "enabled": True,
        "url": "https://www.proxydaily.com/",
        "update_interval": 86400,
        "max_proxies": 500
    },
    "custom_sources": [
        {
            "name": "my_proxy_source",
            "url": "https://example.com/proxies.txt",
            "format": "text",  # text, json, csv
            "enabled": False
        }
    ]
}
```

## 安全配置

### API安全

```python
# JWT配置
JWT_CONFIG = {
    "secret_key": "your-secret-key-here",
    "algorithm": "HS256",
    "access_token_expire_minutes": 30,
    "refresh_token_expire_days": 7,
    "token_url": "/api/v1/auth/token"
}

# API限流
RATE_LIMIT_CONFIG = {
    "default": "100/minute",
    "auth_endpoints": "5/minute",
    "proxy_endpoints": "1000/minute"
}
```

### 代理安全

```python
# 代理安全檢查
PROXY_SECURITY = {
    "blacklist_countries": ["CN", "RU", "KP"],  # 黑名單國家
    "whitelist_countries": [],                  # 白名單國家
    "max_response_time": 30,                    # 最大響應時間
    "min_success_rate": 0.8,                   # 最小成功率
    "blocked_keywords": ["captcha", "blocked", "forbidden"]
}
```

### 網絡安全

```nginx
# nginx/conf.d/security.conf
# 安全標頭
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

# IP白名單
location /admin {
    allow 192.168.1.0/24;
    allow 10.0.0.0/8;
    deny all;
}

# 限流
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req zone=api burst=20 nodelay;
```

## 性能優化

### 數據庫優化

```python
# 數據庫性能優化
DATABASE_OPTIMIZATION = {
    "indexes": [
        "CREATE INDEX idx_proxy_ip ON proxies(ip, port)",
        "CREATE INDEX idx_proxy_status ON proxies(status)",
        "CREATE INDEX idx_proxy_country ON proxies(country)",
        "CREATE INDEX idx_proxy_last_checked ON proxies(last_checked)",
        "CREATE INDEX idx_proxy_response_time ON proxies(response_time)"
    ],
    
    "partitioning": {
        "enabled": True,
        "partition_by": "last_checked",
        "retention_days": 90
    }
}
```

### 緩存配置

```python
# Redis緩存配置
CACHE_CONFIG = {
    "default_ttl": 3600,           # 默認TTL（秒）
    "proxy_stats_ttl": 300,        # 代理統計TTL
    "geo_location_ttl": 86400,     # 地理位置TTL
    "max_memory": "512mb",         # 最大內存
    "eviction_policy": "allkeys-lru"
}
```

### 連接池優化

```python
# 連接池優化
CONNECTION_POOL_CONFIG = {
    "http_pool_size": 100,         # HTTP連接池大小
    "http_pool_maxsize": 200,      # HTTP連接池最大大小
    "http_pool_timeout": 30,       # HTTP連接超時
    "http_pool_retries": 3,        # HTTP重試次數
    
    "proxy_pool_size": 50,         # 代理連接池大小
    "proxy_pool_maxsize": 100,     # 代理連接池最大大小
    "proxy_pool_timeout": 20       # 代理連接超時
}
```

## 故障排除

### 常見問題

#### 1. 數據庫連接問題

```bash
# 檢查數據庫連接
docker-compose exec backend python -c "
from app.core.database_manager import get_database_manager
import asyncio

async def test_connection():
    db = get_database_manager()
    async with db.get_session() as session:
        result = await session.execute('SELECT 1')
        print('Database connection successful')

asyncio.run(test_connection())
"
```

#### 2. Redis連接問題

```bash
# 測試Redis連接
docker-compose exec redis redis-cli ping
```

#### 3. 代理驗證失敗

```bash
# 檢查代理驗證日誌
docker-compose logs backend | grep "proxy_validation"
```

#### 4. 監控系統問題

```bash
# 檢查Prometheus目標
curl http://localhost:9090/api/v1/targets

# 檢查Grafana數據源
curl http://admin:admin@localhost:3000/api/datasources
```

### 日誌配置

```python
# 日誌配置
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
        }
    },
    
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/proxy-collector.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json",
            "level": "DEBUG"
        }
    },
    
    "loggers": {
        "app": {
            "level": "DEBUG",
            "handlers": ["console", "file"]
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console"]
        }
    }
}
```

### 性能監控

```python
# 性能監控配置
PERFORMANCE_MONITORING = {
    "enabled": True,
    "metrics_collection_interval": 60,  # 秒
    "slow_query_threshold": 1.0,         # 秒
    "memory_threshold": 0.9,             # 90%
    "cpu_threshold": 0.8,                # 80%
    
    "alerts": {
        "slow_query": True,
        "high_memory": True,
        "high_cpu": True,
        "database_connection_pool_exhausted": True
    }
}
```

## 配置驗證

使用配置驗證腳本檢查配置：

```bash
# 驗證配置
python scripts/validate-config.py

# 測試數據庫連接
python scripts/test-database.py

# 測試監控系統
python scripts/test-monitoring.py
```

## 最佳實踐

1. **安全配置**
   - 使用強密碼和JWT密鑰
   - 配置防火牆規則
   - 使用HTTPS加密通信
   - 定期更新依賴包

2. **性能優化**
   - 使用連接池
   - 配置適當的緩存
   - 優化數據庫索引
   - 監控系統資源使用

3. **監控和告警**
   - 配置關鍵指標監控
   - 設置合理的告警閾值
   - 定期檢查日誌
   - 建立故障處理流程

4. **備份和恢復**
   - 定期備份數據庫
   - 測試恢復流程
   - 保留多個備份版本
   - 文檔化恢復步驟

如需更多幫助，請參考項目文檔或聯繫技術支持。