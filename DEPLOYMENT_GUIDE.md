# 代理收集器部署指南

## 概述

本指南提供了兩種部署方式的詳細說明：
- **SQLite版本**：輕量級部署，適合開發和測試環境
- **PostgreSQL版本**：企業級部署，適合生產環境

## 系統要求

### 硬件要求
- **CPU**: 2核心以上
- **內存**: 4GB以上
- **存儲**: 10GB以上可用空間

### 軟件要求
- **Docker**: 20.10+
- **Docker Compose**: 1.29+
- **操作系統**: Windows 10+, Ubuntu 18.04+, macOS 10.15+

## 快速開始

### 1. 環境準備

```bash
# 克隆項目代碼
git clone <repository-url>
cd My-Proxy-Collector

# 確保Docker和Docker Compose已安裝
docker --version
docker-compose --version
```

### 2. SQLite版本部署（推薦）

#### Linux/macOS
```bash
# 賦予執行權限
chmod +x scripts/deploy-sqlite.sh

# 執行部署
./scripts/deploy-sqlite.sh
```

#### Windows
```cmd
# 執行部署
scripts\deploy-sqlite.bat
```

### 3. PostgreSQL版本部署

#### Linux/macOS
```bash
# 賦予執行權限
chmod +x scripts/deploy.sh

# 執行部署
./scripts/deploy.sh
```

#### Windows
```cmd
# 執行部署
scripts\deploy.bat
```

## 部署配置詳解

### SQLite版本特點
- **優點**：
  - 零配置，開箱即用
  - 資源佔用少
  - 單文件數據庫，易於備份
  - 適合開發和測試

- **缺點**：
  - 不適合高並發場景
  - 缺少高級數據庫功能

### PostgreSQL版本特點
- **優點**：
  - 企業級數據庫功能
  - 支持高並發和大数据量
  - 完整的事務支持
  - 豐富的數據類型和索引

- **缺點**：
  - 需要更多系統資源
  - 配置相對複雜

## 服務架構

### 容器服務
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │    Frontend     │    │     Backend     │
│   (端口 80)     │────│  (React App)    │────│   (FastAPI)     │
│  反向代理+負載均衡 │    │   (端口 3001)    │    │   (端口 8000)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   PostgreSQL    │    │     Redis       │
                       │  (關係型數據庫)  │    │   (緩存+隊列)    │
                       │   (端口 5432)    │    │   (端口 6379)    │
                       └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Prometheus    │    │     Grafana     │
                       │   (指標收集)     │    │   (監控面板)     │
                       │   (端口 9090)    │    │   (端口 3000)    │
                       └─────────────────┘    └─────────────────┘
```

## 訪問地址

部署完成後，可以通過以下地址訪問各個服務：

| 服務 | 地址 | 說明 |
|------|------|------|
| 應用界面 | http://localhost | 主要的Web界面 |
| API文檔 | http://localhost/api/docs | Swagger API文檔 |
| 監控面板 | http://localhost:3000 | Grafana儀表板 |
| Prometheus | http://localhost:9090 | 指標收集系統 |

**默認賬號密碼**：
- Grafana: admin/admin123
- 其他服務：無認證（生產環境需配置）

## 管理命令

### 常用Docker命令
```bash
# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f backend
docker-compose logs -f frontend

# 重啟服務
docker-compose restart backend

# 停止服務
docker-compose down

# 重新構建
docker-compose build --no-cache
```

### 數據管理
```bash
# 備份SQLite數據庫
cp backend/data/proxy_collector.db backup_$(date +%Y%m%d).db

# 備份PostgreSQL數據庫
docker-compose exec postgres pg_dump -U postgres proxy_collector > backup.sql

# 恢復PostgreSQL數據庫
docker-compose exec -T postgres psql -U postgres proxy_collector < backup.sql
```

## 配置自定義

### 環境變量

可以在部署前設置以下環境變量：

```bash
# 版本標籤
export BACKEND_TAG=v1.0.0
export FRONTEND_TAG=v1.0.0

# 數據庫配置（PostgreSQL）
export POSTGRES_DB=mydb
export POSTGRES_USER=myuser
export POSTGRES_PASSWORD=mypassword

# 監控配置
export GRAFANA_ADMIN_PASSWORD=mypassword
```

### 端口映射

如需修改默認端口，編輯對應的docker-compose文件：

```yaml
# 修改端口映射
ports:
  - "8080:8000"  # 後端API
  - "8081:3000"  # Grafana
  - "8082:9090"  # Prometheus
```

## 故障排除

### 常見問題

#### 1. 端口被佔用
```bash
# 檢查端口使用情況
netstat -tulpn | grep :80
netstat -tulpn | grep :8000

# 停止佔用端口的進程
sudo kill -9 <PID>
```

#### 2. 容器啟動失敗
```bash
# 查看詳細日誌
docker-compose logs <service-name>

# 檢查容器狀態
docker ps -a
docker inspect <container-id>
```

#### 3. 數據庫連接失敗
```bash
# 檢查數據庫容器狀態
docker-compose ps postgres

# 測試數據庫連接
docker-compose exec postgres psql -U postgres -d proxy_collector
```

### 性能優化

#### 1. 資源限制
在docker-compose文件中添加資源限制：

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '1.0'
      memory: 1G
```

#### 2. 緩存配置
優化Redis配置以提高性能：

```yaml
command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

## 安全建議

### 生產環境部署

1. **SSL證書配置**
   ```bash
   # 使用Let's Encrypt獲取SSL證書
   certbot --nginx -d yourdomain.com
   ```

2. **防火牆配置**
   ```bash
   # 只開放必要端口
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

3. **密碼安全**
   - 修改所有默認密碼
   - 使用強密碼策略
   - 定期更換密碼

4. **訪問控制**
   - 配置Nginx基本認證
   - 限制管理界面訪問IP
   - 使用VPN訪問管理功能

### 監控和告警

1. **設置告警規則**
   - CPU使用率超過80%
   - 內存使用率超過85%
   - 磁盤空間低於10%
   - 服務不可用

2. **日誌監控**
   ```bash
   # 配置日誌收集
   docker-compose logs -f --tail=100 > app.log
   ```

## 更新和維護

### 版本更新
```bash
# 拉取最新代碼
git pull origin main

# 重新部署（SQLite版本）
./scripts/deploy-sqlite.sh

# 或重新部署（PostgreSQL版本）
./scripts/deploy.sh
```

### 日常維護
1. 定期備份數據
2. 監控系統資源使用
3. 清理日誌文件
4. 更新安全補丁

## 技術支持

如遇到問題，請：
1. 查看服務日誌
2. 檢查系統資源
3. 驗證配置文件
4. 參考故障排除章節

---

**最後更新**：2024年12月
**版本**：v1.0.0