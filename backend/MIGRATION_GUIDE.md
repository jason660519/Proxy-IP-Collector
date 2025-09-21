# 架構統一化遷移指南

## 概述

本指南說明如何從原有的分散式服務架構遷移到新的統一服務架構，解決架構層面的問題。

## 遷移背景

### 原有問題
1. **多重啟動器混亂**: `react_server.py`, `simple_server.py`, `main.py` 多個啟動文件
2. **API端點不一致**: 不同服務器返回不同格式的響應
3. **配置管理分散**: 配置分散在多個文件中，缺乏統一管理
4. **健康檢查缺失**: 沒有標準化的健康檢查機制
5. **依賴管理混亂**: 各模塊依賴關係不清晰

### 解決方案
創建了統一的架構模塊 (`app.architecture`)，提供標準化的服務架構實現。

## 新架構組件

### 1. 統一服務器 (`unified_server.py`)
- 提供標準化的FastAPI服務配置
- 支持多種運行模式 (full, api, mock)
- 統一的CORS中間件配置
- 標準化的生命周期管理

### 2. API標準化 (`api_standard.py`)
- 統一的響應格式
- 標準化的狀態碼和錯誤處理
- 健康檢查響應標準化
- API端點定義統一

### 3. 健康檢查 (`health_check.py`)
- 多種健康檢查類型
- 可擴展的檢查框架
- 並行檢查執行
- 詳細的檢查報告

### 4. 配置管理 (`config_manager.py`)
- 統一的配置加載機制
- 多配置源支持 (文件、環境變量、數據庫)
- 配置驗證和類型檢查
- 配置優先級管理

### 5. 服務啟動器 (`service_launcher.py`)
- 統一的服務啟動流程
- 信號處理和優雅關閉
- 依賴初始化和清理
- 多模式支持

## 遷移步驟

### 步驟1: 備份原有文件
```bash
# 備份原有的啟動文件
mv react_server.py react_server.py.backup
mv simple_server.py simple_server.py.backup
mv main.py main.py.backup
```

### 步驟2: 使用新的統一啟動器
```bash
# 使用新的統一啟動器
python launch_unified.py --mode full

# 或者使用不同的模式
python launch_unified.py --mode api
python launch_unified.py --mode mock
```

### 步驟3: 更新配置
新的配置管理器支持多種配置源：

1. **環境變量** (最高優先級)
   ```bash
   export DATABASE_URL="postgresql://user:pass@localhost/db"
   export REDIS_URL="redis://localhost:6379"
   export LOG_LEVEL="INFO"
   ```

2. **配置文件** (config/目錄)
   ```yaml
   # config/local.yaml
   app_name: "proxy-collector"
   debug: false
   host: "0.0.0.0"
   port: 8000
   database_url: "sqlite:///./proxy_collector.db"
   redis_url: "redis://localhost:6379"
   log_level: "INFO"
   ```

### 步驟4: 更新API端點
新的API端點遵循統一標準：

```python
# 統一的響應格式
{
    "status": "success",  # success, error
    "message": "操作成功",
    "data": {  # 具體數據
        # ...
    },
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0.0"
}
```

### 步驟5: 健康檢查
新的健康檢查端點：

```bash
# 健康檢查
curl http://localhost:8000/health

# 系統信息
curl http://localhost:8000/info
```

## 運行模式說明

### Full模式 (完整模式)
- 包含所有功能：API、爬蟲、數據庫、緩存
- 適用於生產環境
- 完整的健康檢查

### API模式
- 只提供API服務
- 不包含爬蟲功能
- 適用於API服務器部署

### Mock模式
- 返回模擬數據
- 用於開發和測試
- 不依賴外部服務

## 配置遷移

### 原有配置遷移
將原有的配置遷移到新的配置系統：

1. **環境變量映射**
   ```bash
   # 原有
   export PROXY_DATABASE_URL="..."
   
   # 新的 (使用標準命名)
   export DATABASE_URL="..."
   ```

2. **配置文件遷移**
   將原有的配置項轉換為新的YAML格式。

### 新的配置優先級
1. 環境變量 (最高優先級)
2. local.yaml (本地配置)
3. {environment}.yaml (環境特定配置)
4. default.yaml (默認配置)

## 依賴更新

### 新的依賴要求
```txt
# requirements.txt 新增
pyyaml>=6.0          # YAML配置支持
psutil>=5.9.0        # 系統資源監控
aioredis>=2.0.0      # Redis異步支持
```

### 安裝命令
```bash
pip install pyyaml psutil aioredis
```

## 測試驗證

### 1. 配置檢查
```bash
python launch_unified.py --check
```

### 2. 健康檢查
```bash
curl http://localhost:8000/health
```

### 3. API測試
```bash
# 測試代理列表
curl http://localhost:8000/api/v1/proxies

# 測試爬蟲狀態
curl http://localhost:8000/api/v1/scraping/status
```

## 回滾方案

如果遇到問題，可以快速回滾：

```bash
# 恢復原有文件
mv react_server.py.backup react_server.py
mv simple_server.py.backup simple_server.py
mv main.py.backup main.py

# 使用原有啟動器
python main.py
```

## 常見問題

### Q1: 配置加載失敗
**解決方案**: 檢查配置文件格式和路徑，使用 `--check` 參數診斷。

### Q2: 端口被佔用
**解決方案**: 使用 `--port` 參數指定其他端口。

### Q3: 依賴缺失
**解決方案**: 運行 `pip install -r requirements.txt` 安裝缺失的依賴。

### Q4: 數據庫連接失敗
**解決方案**: 檢查 `DATABASE_URL` 環境變量或配置文件。

## 性能優化建議

1. **生產環境部署**
   - 使用生產模式 (`ENVIRONMENT=production`)
   - 禁用熱重載
   - 使用進程管理器 (如 systemd)

2. **配置優化**
   - 使用環境變量管理敏感信息
   - 分離不同環境的配置
   - 啟用配置緩存

3. **監控建議**
   - 定期檢查健康狀態
   - 監控關鍵指標
   - 設置告警機制

## 總結

新的統一架構解決了原有的架構問題，提供了：
- ✅ 統一的服務啟動機制
- ✅ 標準化的API響應格式
- ✅ 完善的配置管理系統
- ✅ 全面的健康檢查機制
- ✅ 靈活的運行模式支持

遷移完成後，系統將更加穩定、可維護和可擴展。