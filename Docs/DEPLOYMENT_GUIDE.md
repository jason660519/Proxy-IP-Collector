# 代理收集器部署指南

本指南詳細介紹如何在不同環境中部署代理收集器系統。

## 目錄

1. [系統要求](#系統要求)
2. [快速開始](#快速開始)
3. [Docker部署](#docker部署)
4. [手動部署](#手動部署)
5. [生產環境部署](#生產環境部署)
6. [高可用部署](#高可用部署)
7. [監控和維護](#監控和維護)
8. [故障排除](#故障排除)

## 系統要求

### 最低要求

- **CPU**: 2核心
- **RAM**: 4GB
- **存儲**: 20GB可用空間
- **操作系統**: Linux/Windows/macOS
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### 推薦配置

- **CPU**: 4核心
- **RAM**: 8GB
- **存儲**: 100GB SSD
- **網絡**: 1Gbps帶寬
- **操作系統**: Ubuntu 20.04+ / CentOS 8+

### 依賴服務

- **數據庫**: PostgreSQL 13+ 或 SQLite 3.35+
- **緩存**: Redis 6.2+
- **監控**: Prometheus 2.30+, Grafana 8.0+
- **反向代理**: Nginx 1.20+

## 快速開始

### 使用Docker Compose（推薦）

1. **克隆項目**
```bash
git clone https://github.com/your-username/proxy-collector.git
cd proxy-collector
```

2. **配置環境**
```bash
# 複製環境配置
cp .env.example .env

# 編輯配置
nano .env
```

3. **啟動服務**
```bash
docker-compose up -d
```

4. **驗證部署**
```bash
# 運行驗證腳本
./scripts/verify-deployment.sh

# 或使用Windows
scripts\verify-deployment.bat
```

### 訪問服務

- **應用程序**: http://localhost:8000
- **監控面板**: http://localhost:3000 (Grafana)
- **指標收集**: http://localhost:9090 (Prometheus)
- **API文檔**: http://localhost:8000/docs

## Docker部署

### 單節點部署

1. **創建Docker網絡**
```bash
docker network create proxy-collector-network
```

2. **部署PostgreSQL**
```bash
docker run -d \
  --name postgres \
  --network proxy-collector-network \
  -e POSTGRES_DB=proxy_collector \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=your-password \
  -v postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:13
```

3. **部署Redis**
```bash
docker run -d \
  --name redis \
  --network proxy-collector-network \
  -v redis_data:/data \
  -p 6379:6379 \
  redis:6.2-alpine
```

4. **部署應用程序**
```bash
docker build -t proxy-collector:latest .

docker run -d \
  --name proxy-collector \
  --network proxy-collector-network \
  -e DATABASE_TYPE=postgresql \
  -e DATABASE_URL=postgresql://postgres:your-password@postgres:5432/proxy_collector \
  -e REDIS_URL=redis://redis:6379/0 \
  -p 8000:8000 \
  proxy-collector:latest
```

### Docker Compose完整配置

創建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  # PostgreSQL數據庫
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: proxy_collector
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres123}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    networks:
      - proxy-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis緩存
  redis:
    image: redis:6.2-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - proxy-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 後端應用
  backend:
    build: .
    environment:
      APP_ENV: production
      DATABASE_TYPE: postgresql
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD:-postgres123}@postgres:5432/proxy_collector
      REDIS_URL: redis://redis:6379/0
      ENABLE_MONITORING: true
      PROMETHEUS_PORT: 9090
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    networks:
      - proxy-network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Prometheus監控
  prometheus:
    image: prom/prometheus:latest
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/alert_rules.yml:/etc/prometheus/alert_rules.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - proxy-network
    depends_on:
      - backend

  # Grafana儀表板
  grafana:
    image: grafana/grafana:latest
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin123}
      GF_USERS_ALLOW_SIGN_UP: false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
    ports:
      - "3000:3000"
    networks:
      - proxy-network
    depends_on:
      - prometheus

  # PostgreSQL導出器
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter
    environment:
      DATA_SOURCE_NAME: postgresql://postgres:${POSTGRES_PASSWORD:-postgres123}@postgres:5432/proxy_collector?sslmode=disable
    ports:
      - "9187:9187"
    networks:
      - proxy-network
    depends_on:
      - postgres

  # Redis導出器
  redis-exporter:
    image: oliver006/redis_exporter:latest
    environment:
      REDIS_ADDR: redis://redis:6379
    ports:
      - "9121:9121"
    networks:
      - proxy-network
    depends_on:
      - redis

networks:
  proxy-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

### 生產環境Docker配置

創建 `docker-compose.prod.yml`：

```yaml
version: '3.8'

services:
  backend:
    environment:
      APP_ENV: production
      DEBUG: false
      LOG_LEVEL: INFO
      WORKERS: 4
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
    networks:
      - proxy-network
```

## 手動部署

### 系統準備

1. **安裝依賴**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.9 python3.9-venv python3.9-dev
sudo apt install postgresql postgresql-contrib
sudo apt install redis-server
sudo apt install nginx

# CentOS/RHEL
sudo yum update
sudo yum install python39 python39-devel
sudo yum install postgresql-server postgresql-contrib
sudo yum install redis
sudo yum install nginx
```

2. **創建用戶**
```bash
sudo useradd -m -s /bin/bash proxy-collector
sudo usermod -aG sudo proxy-collector
```

### Python環境配置

1. **創建虛擬環境**
```bash
sudo -u proxy-collector bash
cd /home/proxy-collector
python3.9 -m venv venv
source venv/bin/activate
```

2. **安裝依賴包**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. **配置應用程序**
```bash
# 複製配置文件
cp config/config.example.py config/config.py

# 編輯配置
nano config/config.py
```

### 數據庫配置

1. **PostgreSQL配置**
```bash
# 創建數據庫和用戶
sudo -u postgres psql
CREATE DATABASE proxy_collector;
CREATE USER proxy_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE proxy_collector TO proxy_user;
\q
```

2. **初始化數據庫**
```bash
# 運行數據庫遷移
python manage.py migrate

# 創建超級用戶
python manage.py createsuperuser
```

### 系統服務配置

1. **創建Systemd服務**

創建 `/etc/systemd/system/proxy-collector.service`：

```ini
[Unit]
Description=Proxy Collector Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=proxy-collector
Group=proxy-collector
WorkingDirectory=/home/proxy-collector/proxy-collector
Environment=PATH=/home/proxy-collector/venv/bin
Environment=APP_ENV=production
ExecStart=/home/proxy-collector/venv/bin/python -m app.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

2. **啟動服務**
```bash
sudo systemctl daemon-reload
sudo systemctl enable proxy-collector
sudo systemctl start proxy-collector
```

### Nginx配置

創建 `/etc/nginx/sites-available/proxy-collector`：

```nginx
upstream proxy_collector {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向HTTP到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL配置
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # 日誌配置
    access_log /var/log/nginx/proxy-collector.access.log;
    error_log /var/log/nginx/proxy-collector.error.log;
    
    # 客戶端配置
    client_max_body_size 10M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    
    # 代理配置
    location / {
        proxy_pass http://proxy_collector;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超時配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 靜態文件
    location /static/ {
        alias /home/proxy-collector/proxy-collector/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # 健康檢查
    location /health {
        proxy_pass http://proxy_collector;
        access_log off;
    }
}
```

啟用配置：
```bash
sudo ln -s /etc/nginx/sites-available/proxy-collector /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 生產環境部署

### 環境準備

1. **系統優化**
```bash
# 系統限制優化
sudo nano /etc/security/limits.conf
# 添加以下內容
proxy-collector soft nofile 65536
proxy-collector hard nofile 65536
proxy-collector soft nproc 32768
proxy-collector hard nproc 32768

# 內核參數優化
sudo nano /etc/sysctl.conf
# 添加以下內容
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
```

2. **防火牆配置**
```bash
# UFW配置（Ubuntu）
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw enable

# FirewallD配置（CentOS）
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

### SSL證書配置

1. **使用Let's Encrypt**
```bash
# 安裝Certbot
sudo apt install certbot python3-certbot-nginx

# 獲取證書
sudo certbot --nginx -d your-domain.com

# 自動續期
sudo crontab -e
# 添加：0 2 * * * certbot renew --quiet
```

2. **手動配置SSL**
```bash
# 創建SSL目錄
sudo mkdir -p /etc/nginx/ssl

# 複製證書文件
sudo cp your-cert.pem /etc/nginx/ssl/cert.pem
sudo cp your-key.pem /etc/nginx/ssl/key.pem

# 設置權限
sudo chmod 600 /etc/nginx/ssl/key.pem
sudo chmod 644 /etc/nginx/ssl/cert.pem
```

### 數據庫優化

1. **PostgreSQL優化**
```bash
# 編輯配置文件
sudo nano /etc/postgresql/13/main/postgresql.conf

# 性能參數
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
max_connections = 200
```

2. **Redis優化**
```bash
# 編輯配置文件
sudo nano /etc/redis/redis.conf

# 內存優化
maxmemory 512mb
maxmemory-policy allkeys-lru

# 持久化優化
save 900 1
save 300 10
save 60 10000
```

## 高可用部署

### 負載均衡配置

創建 `nginx-upstream.conf`：

```nginx
upstream proxy_collector_cluster {
    least_conn;
    server backend1:8000 weight=3 max_fails=3 fail_timeout=30s;
    server backend2:8000 weight=3 max_fails=3 fail_timeout=30s;
    server backend3:8000 weight=2 max_fails=3 fail_timeout=30s backup;
    
    keepalive 32;
    keepalive_requests 100;
    keepalive_timeout 60s;
}
```

### 數據庫主從配置

1. **主數據庫配置**
```bash
# postgresql.conf
wal_level = replica
max_wal_senders = 3
wal_keep_segments = 64
hot_standby = on
```

2. **從數據庫配置**
```bash
# recovery.conf
standby_mode = on
primary_conninfo = 'host=master-ip port=5432 user=replicator'
```

### 故障轉移

使用Patroni實現自動故障轉移：

```yaml
# patroni.yml
scope: postgres
name: postgresql0

restapi:
  listen: 0.0.0.0:8008
  connect_address: 10.0.0.10:8008

etcd:
  hosts: 10.0.0.10:2379,10.0.0.11:2379,10.0.0.12:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
```

## 監控和維護

### 健康檢查

```bash
# 創建健康檢查腳本
#!/bin/bash
# health-check.sh

BACKEND_URL="http://localhost:8000/health"
PROMETHEUS_URL="http://localhost:9090/-/healthy"
GRAFANA_URL="http://localhost:3000/api/health"

check_service() {
    local name=$1
    local url=$2
    
    if curl -f -s "$url" > /dev/null; then
        echo "✓ $name is healthy"
        return 0
    else
        echo "✗ $name is unhealthy"
        return 1
    fi
}

check_service "Backend" "$BACKEND_URL"
check_service "Prometheus" "$PROMETHEUS_URL"
check_service "Grafana" "$GRAFANA_URL"
```

### 自動化維護

```bash
# 創建維護腳本
#!/bin/bash
# maintenance.sh

# 清理舊日誌
find /var/log/proxy-collector -name "*.log" -mtime +30 -delete

# 清理舊代理數據
psql -d proxy_collector -c "DELETE FROM proxies WHERE last_checked < NOW() - INTERVAL '30 days';"

# 更新系統
apt update && apt upgrade -y

# 重啟服務
systemctl restart proxy-collector
```

### 監控告警

配置告警規則：

```yaml
# alertmanager.yml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@your-domain.com'
  smtp_auth_username: 'alerts@your-domain.com'
  smtp_auth_password: 'your-app-password'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  email_configs:
  - to: 'admin@your-domain.com'
    subject: 'Proxy Collector Alert'
    body: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

## 故障排除

### 常見問題

1. **服務無法啟動**
```bash
# 檢查日誌
journalctl -u proxy-collector -f

# 檢查端口占用
netstat -tlnp | grep :8000

# 檢查依賴
python -c "import app; print('Dependencies OK')"
```

2. **數據庫連接失敗**
```bash
# 測試連接
psql -h localhost -U postgres -d proxy_collector -c "SELECT 1;"

# 檢查配置
grep -r "DATABASE_URL" /home/proxy-collector/
```

3. **代理驗證失敗**
```bash
# 檢查網絡連接
curl -I http://httpbin.org/ip

# 檢查代理源
docker-compose logs backend | grep "proxy_validation"
```

4. **性能問題**
```bash
# 監控資源使用
top -p $(pgrep -f proxy-collector)

# 檢查數據庫性能
psql -c "SELECT * FROM pg_stat_activity;"

# 檢查Redis性能
redis-cli info stats
```

### 日誌分析

```bash
# 實時日誌監控
tail -f /var/log/proxy-collector/app.log

# 錯誤日誌分析
grep -i error /var/log/proxy-collector/app.log | tail -20

# 性能日誌分析
grep -i "slow\|timeout" /var/log/proxy-collector/app.log
```

### 性能調優

1. **數據庫優化**
```sql
-- 分析查詢計劃
EXPLAIN ANALYZE SELECT * FROM proxies WHERE status = 'active';

-- 創建索引
CREATE INDEX CONCURRENTLY idx_proxies_status ON proxies(status);
CREATE INDEX CONCURRENTLY idx_proxies_last_checked ON proxies(last_checked);
```

2. **應用程序優化**
```python
# 連接池優化
DATABASE_CONFIG = {
    "pool_size": 50,
    "max_overflow": 100,
    "pool_pre_ping": True,
    "pool_recycle": 3600
}

# 緩存優化
CACHE_CONFIG = {
    "default_ttl": 300,
    "proxy_stats_ttl": 60,
    "max_memory": "1gb"
}
```

## 升級指南

### 滾動升級

1. **Docker滾動升級**
```bash
# 構建新鏡像
docker build -t proxy-collector:v2.0.0 .

# 滾動更新
docker-compose up -d --no-deps --build backend

# 驗證升級
curl -f http://localhost:8000/health
```

2. **手動升級**
```bash
# 備份數據庫
pg_dump proxy_collector > backup-$(date +%Y%m%d).sql

# 更新代碼
git pull origin main

# 更新依賴
pip install -r requirements.txt --upgrade

# 運行遷移
python manage.py migrate

# 重啟服務
sudo systemctl restart proxy-collector
```

### 回滾策略

```bash
# Docker回滾
docker-compose down
docker tag proxy-collector:v1.0.0 proxy-collector:latest
docker-compose up -d

# 數據庫回滾
psql proxy_collector < backup-20231201.sql
```

如需更多幫助，請參考項目文檔或聯繫技術支持。