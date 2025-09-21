# 代理 IP 池收集器 (Proxy IP Pool Collector) - 專案PRD

## 版本更新歷程

| 版本 | 更新日期 | 更新內容 | 負責人 |
|------|----------|----------|--------|
| v1.0 | 2024-12-19 | 初始版本建立，基礎架構設計 | AI Assistant |
| v2.0 | 2024-12-21 | 新增差異化ETL處理流程規範，完善8個數據源技術規格 | AI Assistant |
| v2.1 | 2024-12-21 | 新增URL專用爬蟲程式設計原則，實現自動化IP驗證評分機制 | AI Assistant |

## 文件狀態
- **當前版本**: v2.1
- **更新狀態**: 持續更新中
- **最後審核**: 2024-12-21

## 1. 專案概述

### 1.1 專案名稱

代理 IP 池收集器 (Proxy IP Pool Collector)

### 1.2 專案目標

設計並實現一個高效、穩定、可擴展的代理 IP 池收集器，從多個公開的代理 IP 網站持續抓取免費代理 IP，進行驗證後存入儲存池，為上游的爬蟲業務提供匿名的網路請求能力。

### 1.3 目標用戶

- 網路爬蟲開發者
- 數據採集工程師
- 需要匿名網路請求的應用開發者
- 市場研究人員
- SEO 分析師

### 1.4 角色與目標

你是一位資深的 Python 後端開發工程師，專精於網路爬蟲和分散式系統。你的任務是設計並實現一個高效、穩定、可擴展的代理 IP 池收集器。

## 2. 核心功能需求

### 2.1 爬取模組 (Fetchers)

#### 2.1.1 支援的代理 IP 來源網站

由於每個代理IP來源網站具有不同的技術特性，包括更新頻率、頁面結構、數據格式、反爬蟲機制等差異，因此需要為每個來源設計專屬的爬蟲程式和ETL處理流程。

##### 2.1.1.1 來源網站詳細特性分析

**1. 89ip.cn**

- **網站特性**: 國內知名代理IP發布平台，採用傳統HTML表格展示
- **更新頻率**: 30分鐘
- **頁面範圍**: 1-100頁（動態生成，實際頁數可能變化）
- **每頁數量**: 約40個代理IP
- **數據格式**: HTML表格結構，包含IP、端口、匿名度、位置等信息
- **解析方法**: BeautifulSoup4 + CSS選擇器
- **反爬蟲**: 中等，需要合理控制請求頻率
- **ETL處理**: 直接提取表格數據，標準化字段格式，過濾無效IP

**2. 快代理 (kuaidaili.com)**

- **網站特性**: 分為國內代理(intr)和海外代理(inha)兩個子站點
- **更新頻率**: 2天
- **頁面範圍**: 單頁面（動態加載）
- **每頁數量**: 動態變化，通常15-25個
- **數據格式**: HTML + JavaScript渲染的表格
- **解析方法**: 靜態HTML解析為主，部分需要Selenium/Playwright
- **反爬蟲**: 較強，有JavaScript挑戰和頻率限制
- **ETL處理**: 需要等待頁面完全加載，提取動態生成的表格數據

**3. GeoNode API (proxylist.geonode.com)**

- **網站特性**: 提供標準化的JSON API接口
- **更新頻率**: 30分鐘
- **頁面範圍**: 1-24頁（API分頁）
- **每頁數量**: 約100個代理IP
- **數據格式**: 標準JSON格式，包含完整的代理元數據
- **解析方法**: 直接API調用，JSON解析
- **反爬蟲**: 低，但需要API密鑰（部分端點）
- **ETL處理**: 直接解析JSON，數據質量高，需要字段映射

**4. ProxyDB.net**

- **網站特性**: 基於偏移量(offset)的分頁系統
- **更新頻率**: 48小時
- **頁面範圍**: 0-4620 offset（步長30）
- **每頁數量**: 約30個代理IP
- **數據格式**: HTML表格，包含詳細的代理信息
- **解析方法**: BeautifulSoup4解析，需要處理偏移量分頁
- **反爬蟲**: 中等，有IP頻率限制
- **ETL處理**: 循環請求不同offset，提取表格數據，需要去重處理

**5. ProxyNova.com**

- **網站特性**: 按國家分類的多頁面結構
- **更新頻率**: 24小時
- **頁面範圍**: 多個國家頁面（country-all, country-us, country-gb等）
- **每頁數量**: 5-35個（因國家而異）
- **數據格式**: HTML表格 + JavaScript動態加載
- **解析方法**: 需要遍歷多個國家頁面，解析動態表格
- **反爬蟲**: 較強，有地理限制和JavaScript渲染
- **ETL處理**: 需要遍歷所有國家頁面，合併數據，按國家分類存儲

**6. Spys.one**

- **網站特性**: 重度依賴JavaScript渲染，有複雜的反爬蟲機制
- **更新頻率**: 24小時
- **頁面範圍**: 單頁面（大量數據）
- **每頁數量**: 約500個代理IP
- **數據格式**: JavaScript動態生成的表格
- **解析方法**: 必須使用Playwright/Selenium等瀏覽器自動化工具
- **反爬蟲**: 非常強，有JavaScript挑戰、Cookie驗證、行為分析
- **ETL處理**: 需要完整的瀏覽器環境，等待JavaScript執行完成，提取渲染後的數據

**7. Free-Proxy-List.net**

- **網站特性**: 經典的免費代理列表，有多個子頁面
- **更新頻率**: 30分鐘
- **頁面範圍**: 多個子頁面（/proxy-list/, /proxy-list/2/等）
- **每頁數量**: 動態變化，通常50-150個
- **數據格式**: HTML表格，包含基礎代理信息
- **解析方法**: BeautifulSoup4解析，需要遍歷多頁
- **反爬蟲**: 低-中等，主要是頻率限制
- **ETL處理**: 遍歷所有子頁面，提取表格數據，需要數據清洗

##### 2.1.1.2 統一的來源特性對照表

| 網站                | 更新頻率 | 頁面範圍      | 每頁數量 | 數據格式 | 解析方法            | 反爬蟲等級 | 特殊要求       |
| ------------------- | -------- | ------------- | -------- | -------- | ------------------- | ---------- | -------------- |
| 89ip.cn             | 30分鐘   | 1-100頁       | ~40個    | HTML表格 | BeautifulSoup       | 中等       | 分頁處理       |
| kuaidaili-intr      | 2天      | 單頁面        | 15-25個  | HTML+JS  | Selenium/Playwright | 強         | 動態加載等待   |
| kuaidaili-inha      | 2天      | 單頁面        | 15-25個  | HTML+JS  | Selenium/Playwright | 強         | 動態加載等待   |
| geonode-api         | 30分鐘   | 1-24頁        | ~100個   | JSON API | JSON解析            | 低         | API密鑰管理    |
| proxydb.net         | 48小時   | 0-4620 offset | ~30個    | HTML表格 | BeautifulSoup       | 中等       | 偏移量分頁     |
| proxynova.com       | 24小時   | 多國家頁面    | 5-35個   | HTML+JS  | BeautifulSoup+JS    | 強         | 多國家遍歷     |
| spys.one            | 24小時   | 單頁面        | ~500個   | JS渲染   | Playwright必需      | 非常強     | 完整瀏覽器環境 |
| free-proxy-list.net | 30分鐘   | 多子頁面      | 50-150個 | HTML表格 | BeautifulSoup       | 低-中等    | 子頁面遍歷     |

##### 2.1.1.3 專用爬蟲程式設計原則

**1. 模組化設計**
每個代理來源都應該有獨立的爬蟲模組，實現統一的提取器接口：

```python
class BaseProxyExtractor(ABC):
    """代理提取器基類"""
  
    def __init__(self, source_config: Dict[str, Any]):
        self.name = source_config['name']
        self.config = source_config
        self.rate_limiter = RateLimiter(source_config.get('rate_limit', 60))
      
    @abstractmethod
    async def extract_proxies(self) -> List[Dict[str, Any]]:
        """提取代理IP數據"""
        pass
      
    @abstractmethod
    def get_source_info(self) -> Dict[str, Any]:
        """獲取來源信息"""
        pass
```

**2. 差異化處理策略**
根據不同來源的特性，採用相應的技術方案：

- **HTML解析型**: 使用BeautifulSoup4 + CSS選擇器
- **JavaScript渲染型**: 使用Playwright/Selenium
- **JSON API型**: 使用aiohttp + JSON解析
- **分頁處理型**: 實現智能分頁遍歷算法

**3. 反爬蟲應對機制**

- 請求頻率控制（每個來源獨立配置）
- User-Agent輪換
- IP代理池（自我循環使用）
- 請求重試和降級策略
- JavaScript挑戰處理

##### 2.1.1.4 ETL處理流程設計

**提取階段 (Extract)**

1. **前置檢查**: 驗證來源可用性、檢查速率限制
2. **數據獲取**: 根據來源特性選擇合適的爬取策略
3. **原始存儲**: 保存原始HTML/JSON數據用於調試和重處理
4. **錯誤處理**: 記錄爬取失敗原因，觸告警機制

**轉換階段 (Transform)**

1. **格式解析**: 根據數據格式選擇對應的解析器
2. **數據清洗**: 過濾無效IP、標準化端口格式、驗證IP格式
3. **字段映射**: 將不同來源的字段統一映射到標準格式
4. **質量評分**: 基於來源可靠性、數據完整性計算質量分數
5. **去重處理**: 基於IP+端口組合進行全局去重

**加載階段 (Load)**

1. **批量寫入**: 使用批量操作提高數據庫寫入效率
2. **索引更新**: 更新搜索索引和統計信息
3. **版本控制**: 記錄數據版本和處理歷史
4. **成功指標**: 統計成功加載的代理數量和質量指標

**標準化數據結構**

```json
{
  "ip": "192.168.1.1",
  "port": 8080,
  "protocol": "http",
  "anonymity": "high",
  "country": "CN",
  "city": "Beijing",
  "response_time": 1.23,
  "source": "89ip.cn",
  "source_quality": 0.85,
  "last_verified": 1640995200,
  "status": "active",
  "created_at": 1640995200,
  "updated_at": 1640998800
}
```

這種細緻的來源分析和專門的處理流程設計，確保了每個代理IP來源都能被最有效地利用，同時保持整個系統的穩定性和可擴展性。

##### 2.1.1.5 差異化ETL處理流程規範

為了確保不同URL來源的數據能夠被正確處理和存儲，制定以下差異化ETL處理流程規範：

**1. 原始數據(Raw Data)管理規範**

*原始數據保留要求*：

- 必須完整保留來源網站返回的所有原始欄位和數據結構
- 不得刪除、修改或過濾任何原始數據內容
- 需要額外記錄採集時間戳、來源URL、HTTP狀態碼等元數據

*存儲路徑格式*：

```
C:\proxy_collector\raw_data\${source_name}\${date}\${timestamp}_${sequence}.json
```

- `${source_name}`: 數據源名稱（如：89ip、kuaidaili、geonode）
- `${date}`: 採集日期，格式為YYYYMMDD
- `${timestamp}`: 精確到毫秒的時間戳
- `${sequence}`: 同一數據源在同一天內的序號

*文件格式要求*：

```json
{
  "metadata": {
    "source": "89ip.cn",
    "url": "https://www.89ip.cn/index_1.html",
    "collected_at": "2024-12-19T14:30:25.123Z",
    "http_status": 200,
    "collector_version": "v2.1.0",
    "raw_size_bytes": 15360
  },
  "raw_data": {
    // 原始網站返回的完整數據
    "html_content": "<table>...</table>",
    "headers": {},
    "cookies": {}
  }
}
```

**2. 處理後數據(Clean Data)規範**

*必要欄位要求*：

- 僅保留 `ip_address`和 `port_number`兩個必要欄位
- 所有其他欄位必須移除，確保數據最小化
- 需要添加處理時間戳和數據版本號

*標準化字段命名*：

```json
{
  "ip_address": "192.168.1.1",     // 標準化IP地址欄位名
  "port_number": 8080,             // 標準化端口欄位名
  "processed_at": "2024-12-19T14:31:00.000Z",
  "data_version": "v1.0",
  "source": "89ip.cn"
}
```

*存儲路徑格式*：

```
C:\proxy_collector\clean_data\${source_type}\${timestamp}\clean_data.json
```

- `${source_type}`: 數據源類型（html_table、json_api、js_rendered）
- `${timestamp}`: 處理完成的時間戳

**3. 數據流轉示意圖**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   原始網站數據   │───▶│   原始數據存儲    │───▶│   數據清洗處理    │
│  (HTML/JSON)    │    │  (Raw Storage)  │    │  (Clean Process)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  數據源配置     │    │  錯誤日誌記錄    │    │   清潔數據存儲   │
│ (Source Config)│    │  (Error Log)    │    │ (Clean Storage) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                        ┌─────────────────┐
                        │  API接口提供    │
                        │  (API Service)  │
                        └─────────────────┘
```

**4. 各處理階段數據樣本示例**

*原始數據樣本*（89ip.cn）：

```json
{
  "metadata": {
    "source": "89ip.cn",
    "url": "https://www.89ip.cn/index_1.html",
    "collected_at": "2024-12-19T14:30:25.123Z"
  },
  "raw_data": {
    "html_content": "<table class=\"layui-table\">...</table>",
    "proxy_count": 40,
    "page_number": 1
  }
}
```

*清潔數據樣本*：

```json
[
  {
    "ip_address": "192.168.1.100",
    "port_number": 8080,
    "processed_at": "2024-12-19T14:31:00.000Z",
    "data_version": "v1.0",
    "source": "89ip.cn"
  },
  {
    "ip_address": "10.0.0.50",
    "port_number": 3128,
    "processed_at": "2024-12-19T14:31:00.000Z",
    "data_version": "v1.0",
    "source": "89ip.cn"
  }
]
```

**5. 前端網頁API接口數據格式**

*代理列表API* - `/api/v1/proxies`：

```json
{
  "status": "success",
  "data": {
    "proxies": [
      {
        "id": "proxy_123456",
        "ip_address": "192.168.1.100",
        "port_number": 8080,
        "protocol": "http",
        "anonymity_level": "high",
        "country": "CN",
        "response_time_ms": 1200,
        "validation_rate": 0.95,
        "last_verified": "2024-12-19T14:25:00Z",
        "source": "89ip.cn",
        "status": "active"
      }
    ],
    "pagination": {
      "total": 1523,
      "page": 1,
      "per_page": 20,
      "total_pages": 77
    },
    "statistics": {
      "total_active": 1523,
      "by_protocol": {
        "http": 892,
        "https": 456,
        "socks4": 125,
        "socks5": 50
      },
      "by_anonymity": {
        "high": 823,
        "medium": 456,
        "low": 244
      }
    }
  },
  "timestamp": "2024-12-19T14:31:30.123Z"
}
```

*數據源狀態API* - `/api/v1/sources/status`：

```json
{
  "status": "success",
  "data": {
    "sources": [
      {
        "name": "89ip.cn",
        "type": "html_table",
        "status": "active",
        "last_fetch": "2024-12-19T14:30:25Z",
        "fetch_count": 40,
        "success_rate": 0.98,
        "average_response_time_ms": 1200
      },
      {
        "name": "geonode-api",
        "type": "json_api",
        "status": "active",
        "last_fetch": "2024-12-19T14:25:10Z",
        "fetch_count": 100,
        "success_rate": 0.95,
        "average_response_time_ms": 800
      }
    ],
    "summary": {
      "total_sources": 8,
      "active_sources": 7,
      "failed_sources": 1,
      "overall_success_rate": 0.96
    }
  }
}
```

**6. 路徑規範總結**

所有路徑必須採用絕對路徑表示法：

- **Windows系統**: `C:\proxy_collector\{data_type}\{source}\{date}\{file}.json`
- **Linux系統**: `/opt/proxy_collector/{data_type}/{source}/{date}/{file}.json`
- **環境變量配置**: 通過 `PROXY_COLLECTOR_DATA_PATH`環境變量統一配置

**7. 質量控制檢查點**

每個ETL流程必須經過以下質量檢查：

1. **原始數據完整性檢查**: 驗證所有必需欄位存在
2. **IP地址格式驗證**: 使用正則表達式驗證IPv4格式
3. **端口範圍檢查**: 確保端口在1-65535有效範圍內
4. **重複數據檢測**: 基於IP+端口組合進行去重
5. **數據一致性驗證**: 清潔數據與原始數據的數量對比

這套差異化ETL處理流程規範確保了不同來源的代理IP數據能夠被標準化處理，同時保持數據的完整性和可追溯性。

#### 2.1.2 爬取模組技術要求

- 支援 HTML 靜態頁面解析和 JSON API 接口解析
- 模擬常見瀏覽器 User-Agent
- 控制請求頻率，避免對目標網站造成壓力
- 模組化設計，每個網站獨立爬取模組
- 支援異步併發爬取

### 2.2 驗證模組 (Validator)

#### 2.2.1 驗證機制

- **測試目標**: http://httpbin.org/ip, https://www.baidu.com
- **驗證標準**: 檢查返回狀態碼和內容是否包含代理 IP
- **超時設定**: 10 秒連接超時
- **併發處理**: 使用 aiohttp + asyncio 異步驗證

#### 2.2.2 驗證結果記錄

- 協議類型 (HTTP/HTTPS/SOCKS)
- 匿名度等級
- 響應速度
- 來源網站
- 最後驗證時間
- 驗證狀態 (有效/無效)

### 2.3 儲存模組 (Storage)

#### 2.3.1 資料庫選擇

- **主要儲存**: Redis
- **資料結構**: Sorted Set (有序集合)
- **排序依據**: 最後驗證時間戳或響應速度

#### 2.3.2 儲存內容

```json
{
  "ip": "192.168.1.1",
  "port": 8080,
  "protocol": "http",
  "anonymity": "high",
  "response_time": 1.23,
  "source": "89ip.cn",
  "last_verified": 1640995200,
  "status": "active"
}
```

### 2.4 調度模組 (Scheduler)

#### 2.4.1 定時任務配置

- **爬取任務**: 每 30 分鐘執行一次
- **驗證任務**: 每 10-15 分鐘重新驗證池中 IP
- **維護任務**: 當可用 IP < 50 個時觸發完整流程

#### 2.4.2 任務優先級

1. 高頻率網站 (30 分鐘)
2. 中頻率網站 (24 小時)
3. 低頻率網站 (48 小時)

## 3. 技術架構

### 3.1 整體架構設計

基於完整的分層架構設計，採用微服務架構模式：

```
┌─────────────────────────────────────────────────────────────────┐
│                    前端展示層 (React + TypeScript)              │
├─────────────────────────────────────────────────────────────────┤
│                  API 網關層 (FastAPI + Swagger)                │
├─────────────────────────────────────────────────────────────────┤
│  代理服務  │  驗證服務  │  統計服務  │  監控服務  │  調度服務    │
├─────────────────────────────────────────────────────────────────┤
│                     ETL 數據處理層                            │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │  提取模組    │  轉換模組    │  載入模組    │  流程編排    │  │
│  │ (Fetchers)   │ (Transform) │  (Load)     │ (Orchestrate)│  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                    數據存儲層 (Storage)                        │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │   Redis      │ PostgreSQL   │   MongoDB    │   文件系統   │  │
│  │ (快取+會話)  │ (關係數據)   │ (文檔數據)   │ (日誌+導出) │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.1.1 技術棧詳細規格

**後端技術棧**
- **框架**: FastAPI v0.104.1 (異步Web框架)
- **語言**: Python 3.11+ (類型提示和異步支持)
- **依賴管理**: UV (現代Python包管理器)
- **虛擬環境**: UV venv (高性能虛擬環境)

**數據存儲**
- **主數據庫**: PostgreSQL 15+ (結構化數據)
- **快取層**: Redis 7+ (高性能緩存)
- **文檔存儲**: MongoDB 6+ (非結構化數據)
- **文件存儲**: 本地文件系統 (原始數據和日誌)

**爬蟲技術**
- **HTTP客戶端**: aiohttp 3.9+ (異步HTTP請求)
- **HTML解析**: BeautifulSoup4 4.12+ (HTML解析)
- **瀏覽器自動化**: Playwright 1.40+ (JavaScript渲染)
- **數據提取**: lxml 4.9+ (高性能XML/HTML解析)

**監控和日誌**
- **日誌框架**: structlog 23.0+ (結構化日誌)
- **監控**: Prometheus + Grafana (指標監控)
- **錯誤追蹤**: Sentry (錯誤監控)

#### 3.1.2 架構核心組件

**1. 統一服務啟動器 (Unified Server)**
```python
class UnifiedServer:
    """統一服務啟動器，管理所有後端服務"""
    
    def __init__(self):
        self.services = {
            'api': FastAPIServer(),      # API服務
            'etl': ETLCoordinator(),     # ETL協調器
            'scheduler': TaskScheduler(), # 任務調度器
            'validator': ProxyValidator() # 代理驗證器
        }
    
    async def start_all(self):
        """啟動所有服務"""
        for service_name, service in self.services.items():
            await service.start()
```

**2. ETL協調器 (ETL Coordinator)**
```python
class ETLCoordinator:
    """ETL流程協調器，管理所有數據提取器"""
    
    def __init__(self):
        self.extractors = ExtractorFactory.create_all()
        self.transformers = TransformerFactory.create_all()
        self.loaders = LoaderFactory.create_all()
    
    async def run_etl_pipeline(self, source_name: str):
        """運行指定數據源的ETL流程"""
        # Extract階段
        raw_data = await self.extractors[source_name].extract()
        
        # Transform階段
        clean_data = await self.transformers[source_name].transform(raw_data)
        
        # Load階段
        await self.loaders[source_name].load(clean_data)
```

**3. 代理驗證器 (Proxy Validator)**
```python
class ProxyValidator:
    """代理IP驗證器，提供自動化驗證和評分"""
    
    async def validate_proxy(self, proxy: ProxyData) -> ValidationResult:
        """驗證單個代理"""
        # 連接測試
        connectivity_score = await self.test_connectivity(proxy)
        
        # 匿名度測試
        anonymity_score = await self.test_anonymity(proxy)
        
        # 速度測試
        speed_score = await self.test_speed(proxy)
        
        # 綜合評分
        overall_score = self.calculate_overall_score(
            connectivity_score, anonymity_score, speed_score
        )
        
        return ValidationResult(
            proxy=proxy,
            overall_score=overall_score,
            details={
                'connectivity': connectivity_score,
                'anonymity': anonymity_score,
                'speed': speed_score
            }
        )
```

### 3.2 架構分層說明

#### 3.2.1 前端展示層

- **技術棧**: React 18 + TypeScript + Material-UI
- **核心功能**: 儀表板、代理管理、數據可視化、系統監控
- **狀態管理**: Redux Toolkit + RTK Query
- **實時通信**: WebSocket

#### 3.2.2 API 網關層

- **技術棧**: FastAPI + Pydantic + Uvicorn
- **核心功能**: 路由管理、請求驗證、響應格式化、API 文檔
- **認證授權**: JWT + OAuth2
- **文檔生成**: 自動 OpenAPI 文檔

#### 3.2.3 業務邏輯層

- **代理服務**: 代理 IP 的 CRUD 操作、查詢優化
- **驗證服務**: 異步代理驗證、批量處理
- **統計服務**: 數據分析、報表生成、趨勢預測
- **監控服務**: 系統健康檢查、性能監控、告警通知
- **調度服務**: Celery 任務調度、定時任務管理

#### 3.2.4 ETL 數據處理層

**提取層 (Extraction)**:

- **多源提取**: 支援 HTML 爬蟲、JSON API、RSS 訂閱
- **智能調度**: 基於網站更新頻率自動調整提取間隔
- **錯誤處理**: 重試機制、降級策略、熔斷保護

**轉換層 (Transformation)**:

- **數據清洗**: 代理 IP 格式驗證、重複過濾
- **品質評分**: 基於響應時間、成功率計算品質分數
- **標準化處理**: 統一代理 IP 數據結構

**載入層 (Loading)**:

- **多目標策略**: 支援 Redis、PostgreSQL、文件匯出
- **批量載入**: 優化大量數據寫入性能
- **容錯機制**: 失敗重試、錯誤記錄、事務處理

### 3.3 核心模組設計

#### 3.3.1 ETL 提取層 (Extraction Layer)

```python
import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ExtractionResult:
    """提取結果數據結構"""
    source: str
    data: List[Dict[str, Any]]
    timestamp: datetime
    status: str
    error_message: str = None

class BaseExtractor(ABC):
    """提取器基類"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', True)
        self.retry_count = config.get('retry_count', 3)
        self.timeout = config.get('timeout', 30)

    @abstractmethod
    async def extract(self) -> ExtractionResult:
        """執行數據提取"""
        pass

    async def validate_connection(self) -> bool:
        """驗證連接可用性"""
        return True

class ProxyExtractor(BaseExtractor):
    """代理IP提取器"""

    async def extract(self) -> ExtractionResult:
        """提取代理IP數據"""
        try:
            # 根據配置選擇提取策略
            if self.config.get('use_playwright'):
                data = await self._extract_with_playwright()
            else:
                data = await self._extract_with_aiohttp()

            return ExtractionResult(
                source=self.name,
                data=data,
                timestamp=datetime.now(),
                status='success'
            )
        except Exception as e:
            return ExtractionResult(
                source=self.name,
                data=[],
                timestamp=datetime.now(),
                status='failed',
                error_message=str(e)
            )

class ExtractionCoordinator:
    """提取協調器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.extractors: Dict[str, BaseExtractor] = {}
        self.rate_limiter = RateLimiter(config.get('rate_limit', {}))

    def register_extractor(self, extractor: BaseExtractor):
        """註冊提取器"""
        self.extractors[extractor.name] = extractor

    async def extract_all(self) -> List[ExtractionResult]:
        """執行所有提取任務"""
        tasks = []
        for extractor in self.extractors.values():
            if extractor.enabled:
                task = self._extract_with_rate_limit(extractor)
                tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, ExtractionResult)]
```

#### 3.3.2 ETL 轉換層 (Transformation Layer)

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from abc import ABC, abstractmethod

@dataclass
class TransformationResult:
    """轉換結果數據結構"""
    source_data: List[Dict[str, Any]]
    transformed_data: List[Dict[str, Any]]
    quality_score: float
    timestamp: datetime
    status: str
    errors: List[str] = None

class BaseTransformer(ABC):
    """轉換器基類"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', True)
        self.quality_threshold = config.get('quality_threshold', 0.7)

    @abstractmethod
    async def transform(self, data: List[Dict[str, Any]]) -> TransformationResult:
        """執行數據轉換"""
        pass

    def calculate_quality_score(self, data: List[Dict[str, Any]]) -> float:
        """計算數據品質分數"""
        if not data:
            return 0.0

        # 基於數據完整性、格式正確性等指標計算
        valid_items = sum(1 for item in data if self._validate_item(item))
        return valid_items / len(data)

class ProxyTransformer(BaseTransformer):
    """代理IP轉換器"""

    async def transform(self, data: List[Dict[str, Any]]) -> TransformationResult:
        """轉換代理IP數據"""
        try:
            transformed_data = []
            errors = []

            for item in data:
                try:
                    transformed_item = await self._transform_proxy_item(item)
                    transformed_data.append(transformed_item)
                except Exception as e:
                    errors.append(f"轉換錯誤: {str(e)}")

            quality_score = self.calculate_quality_score(transformed_data)

            return TransformationResult(
                source_data=data,
                transformed_data=transformed_data,
                quality_score=quality_score,
                timestamp=datetime.now(),
                status='success' if quality_score >= self.quality_threshold else 'low_quality',
                errors=errors
            )

        except Exception as e:
            return TransformationResult(
                source_data=data,
                transformed_data=[],
                quality_score=0.0,
                timestamp=datetime.now(),
                status='failed',
                errors=[str(e)]
            )
```

#### 3.3.3 ETL 載入層 (Loading Layer)

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod
import asyncio
import json

@dataclass
class LoadResult:
    """載入結果數據結構"""
    target: str
    loaded_count: int
    failed_count: int
    timestamp: datetime
    status: str
    errors: List[str] = None

class BaseLoader(ABC):
    """載入器基類"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', True)
        self.batch_size = config.get('batch_size', 100)

    @abstractmethod
    async def load(self, data: List[Dict[str, Any]]) -> LoadResult:
        """執行數據載入"""
        pass

class RedisLoader(BaseLoader):
    """Redis載入器"""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.redis_client = None
        self.ttl = config.get('ttl', 3600)  # 預設1小時過期

    async def load(self, data: List[Dict[str, Any]]) -> LoadResult:
        """載入數據到Redis"""
        try:
            # 初始化Redis連接
            if not self.redis_client:
                import redis.asyncio as redis
                self.redis_client = redis.Redis(
                    host=self.config.get('host', 'localhost'),
                    port=self.config.get('port', 6379),
                    decode_responses=True
                )

            loaded_count = 0
            errors = []

            # 批量載入
            for i in range(0, len(data), self.batch_size):
                batch = data[i:i + self.batch_size]
                try:
                    # 使用管道優化性能
                    async with self.redis_client.pipeline() as pipe:
                        for item in batch:
                            key = f"proxy:{item['ip']}:{item['port']}"
                            value = json.dumps(item, ensure_ascii=False)
                            pipe.setex(key, self.ttl, value)

                        await pipe.execute()
                        loaded_count += len(batch)

                except Exception as e:
                    errors.append(f"批量載入錯誤: {str(e)}")

            return LoadResult(
                target=self.name,
                loaded_count=loaded_count,
                failed_count=len(data) - loaded_count,
                timestamp=datetime.now(),
                status='success' if not errors else 'partial_success',
                errors=errors
            )

        except Exception as e:
            return LoadResult(
                target=self.name,
                loaded_count=0,
                failed_count=len(data),
                timestamp=datetime.now(),
                status='failed',
                errors=[str(e)]
            )
```

### 3.4 API 設計

基於 RESTful API 設計：

```python
from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime
import uvicorn

from pydantic import BaseModel, Field, validator
from enum import Enum

class ProxyProtocol(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"

class AnonymityLevel(str, Enum):
    TRANSPARENT = "transparent"
    ANONYMOUS = "anonymous"
    HIGH_ANONYMOUS = "high_anonymous"

class ProxyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    VALIDATING = "validating"

class ProxyResponse(BaseModel):
    """代理IP響應模型"""
    id: str = Field(..., description="代理ID")
    ip: str = Field(..., description="IP地址")
    port: int = Field(..., ge=1, le=65535, description="端口")
    protocol: ProxyProtocol = Field(..., description="協議類型")
    anonymity: AnonymityLevel = Field(..., description="匿名度等級")
    country: str = Field(..., description="國家代碼")
    response_time: float = Field(..., ge=0, description="響應時間(秒)")
    success_rate: float = Field(..., ge=0, le=1, description="成功率")
    status: ProxyStatus = Field(..., description="代理狀態")
    source: str = Field(..., description="數據來源")
    last_verified: datetime = Field(..., description="最後驗證時間")
    created_at: datetime = Field(..., description="創建時間")

# FastAPI應用實例
app = FastAPI(
    title="Proxy Pool Collector API",
    description="代理IP池收集器API - 基於新架構設計",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

@app.get("/api/v2/proxies", response_model=Dict[str, Any])
async def get_proxies(
    params: ProxyQueryParams = Depends(),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    獲取代理IP列表

    - **protocol**: 協議類型篩選 (http, https, socks4, socks5)
    - **anonymity**: 匿名度篩選 (transparent, anonymous, high_anonymous)
    - **country**: 國家代碼篩選
    - **status**: 代理狀態篩選
    - **min_success_rate**: 最小成功率篩選
    - **limit**: 返回數量限制 (1-1000)
    """
    try:
        # 調用代理服務獲取數據
        return {
            "proxies": [],
            "total": 0,
            "page": params.offset // params.limit + 1,
            "page_size": params.limit,
            "has_next": False
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取代理列表失敗: {str(e)}"
        )
```

## 4. 非功能性需求

### 4.1 性能要求

- **併發處理**: 支援至少 100 個並發驗證請求
- **響應時間**: 單個 IP 驗證時間 < 10 秒
- **吞吐量**: 每小時處理至少 1000 個 IP 驗證
- **可用性**: 系統可用性 > 99%

### 4.2 可靠性要求

- **錯誤處理**: 單個網站爬取失敗不影響整體系統
- **重試機制**: 失敗的請求自動重試 3 次
- **日誌記錄**: 完整的操作日誌和錯誤追蹤
- **數據備份**: 定期備份 Redis 數據

### 4.3 可擴展性要求

- **模組化設計**: 易於添加新的代理來源
- **配置化**: 所有參數可通過配置文件調整
- **水平擴展**: 支援多實例部署

### 4.4 安全性要求

- **請求限制**: 避免對目標網站造成過大壓力
- **數據保護**: 敏感配置信息加密存儲
- **訪問控制**: API 訪問需要認證

## 5. 技術棧選擇

### 5.1 程式語言與版本

- **Python**: 3.8+
- **Node.js**: 18+ (前端開發環境)

### 5.2 後端技術棧

- **Web 框架**: FastAPI (異步高性能)
- **異步 HTTP**: aiohttp
- **HTML 解析**: BeautifulSoup4, Parsel
- **數據庫**: Redis, PostgreSQL
- **任務調度**: APScheduler, Celery
- **數據驗證**: Pydantic
- **API 文檔**: 自動生成 OpenAPI 文檔

### 5.3 前端技術棧

- **框架**: React 18 + TypeScript
- **狀態管理**: Redux Toolkit + RTK Query
- **UI 框架**: Material-UI (MUI)
- **圖表**: Chart.js + react-chartjs-2
- **路由**: React Router v6
- **構建工具**: Vite

### 5.4 數據存儲

- **Redis**: 高速緩存與會話存儲
- **PostgreSQL**: 結構化數據持久化
- **MongoDB**: 日誌與備份存儲

### 5.5 部署與運維

- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **監控**: Prometheus + Grafana
- **日誌**: ELK Stack

## 6. 實施計劃與里程碑

### 6.1 開發階段劃分

#### 第一階段: 基礎架構與 ETL (3 週)

- **Week 1**: ETL 架構實現
  - 提取協調器開發
  - 轉換協調器開發
  - 載入協調器開發
- **Week 2**: 數據存儲層搭建
  - Redis 集群配置
  - PostgreSQL 數據庫設計
  - 數據訪問對象實現
- **Week 3**: ETL 流程整合測試
  - 端到端 ETL 流程測試
  - 性能基準測試
  - 錯誤處理機制驗證

#### 第二階段: 後端核心服務 (2 週)

- **Week 4**: API 網關層實現
  - FastAPI 框架搭建
  - JWT 認證系統
  - API 路由與中間件
- **Week 5**: 業務服務開發
  - 代理服務實現
  - 統計服務實現
  - 服務間通信機制

#### 第三階段: 前端界面開發 (2 週)

- **Week 6**: 前端架構搭建
  - React 項目初始化
  - Material-UI 組件庫整合
  - TypeScript 配置
- **Week 7**: 核心界面實現
  - 代理管理界面
  - 監控面板開發
  - API 客戶端封裝

#### 第四階段: ETL 流程完善 (1 週)

- **Week 8**: 高級功能實現
  - 增量更新機制
  - 並行處理優化
  - 質量監控系統

#### 第五階段: 前後端整合 (1 週)

- **Week 9**: 系統整合
  - API 集成測試
  - 前端後端聯調
  - 端到端功能驗證

#### 第六階段: 測試與部署 (1 週)

- **Week 10**: 測試與優化
  - 單元測試補充
  - 性能測試
  - 生產環境部署

### 6.2 技術債務管理

#### 高優先級技術債務

1. **ETL 錯誤隔離機制**: 確保單個數據源故障不影響整體流程
2. **API 限流保護**: 防止系統過載和惡意攻擊
3. **數據一致性保障**: 跨存儲層的數據同步機制

#### 中優先級技術債務

1. **前端組件庫文檔**: 完整的組件使用文檔
2. **API 版本管理**: 支持 API 向後兼容
3. **配置中心**: 集中化的配置管理

#### 低優先級技術債務

1. **代碼覆蓋率提升**: 從 60%提升至 80%
2. **性能監控優化**: 更細緻的性能指標
3. **自動化部署**: CI/CD 流程完善

### 6.3 風險緩解策略

#### 技術風險

- **ETL 流程複雜性**: 採用管道模式簡化流程，加強單元測試
- **多存儲層一致性**: 實現分佈式事務機制，定期數據校驗
- **前端後端集成**: 提前進行接口對接，使用 Mock 數據獨立開發

#### 進度風險

- **階段性交付**: 每個階段都有可演示的成果
- **關鍵路徑優化**: 識別並優化關鍵開發路徑
- **資源預留**: 為高風險任務預留緩衝時間

### 6.4 質量保證措施

#### 代碼質量

- **靜態代碼分析**: 使用 pylint、eslint 等工具
- **代碼審查流程**: 強制代碼 Review 機制
- **設計模式應用**: 統一的架構模式和編碼規範

#### 測試策略

- **單元測試**: 核心模組 100%覆蓋
- **集成測試**: 關鍵路徑完整測試
- **端到端測試**: 用戶場景模擬測試

#### 性能保障

- **性能基準**: 建立性能測試基準
- **負載測試**: 模擬高併發場景
- **監控告警**: 實時性能監控和告警

## 7. 配置管理

### 7.1 配置文件結構

```yaml
# config.yaml
database:
  redis:
    host: localhost
    port: 6379
    password: ""
    db: 0

scheduler:
  fetch_interval: 1800 # 30分鐘
  validate_interval: 600 # 10分鐘
  min_pool_size: 50

fetchers:
  - name: "89ip"
    url_template: "https://www.89ip.cn/index_{page}.html"
    pages: [1, 100]
    interval: 1800
    type: "html"

  - name: "geonode"
    url_template: "https://proxylist.geonode.com/api/proxy-list?limit=500&page={page}"
    pages: [1, 24]
    interval: 1800
    type: "api"

validator:
  test_urls:
    - "http://httpbin.org/ip"
    - "https://www.baidu.com"
  timeout: 10
  max_concurrent: 100
```

## 8. 監控與日誌

### 8.1 監控指標

- 代理 IP 池大小
- 有效 IP 比例
- 驗證成功率
- 爬取成功率
- 系統資源使用率

### 8.2 日誌級別

- **DEBUG**: 詳細的調試信息
- **INFO**: 一般操作記錄
- **WARNING**: 警告信息
- **ERROR**: 錯誤信息
- **CRITICAL**: 嚴重錯誤

## 9. 部署與運維

### 9.1 系統要求

- Python 3.8+
- Redis 6.0+
- PostgreSQL 13+
- 至少 2GB RAM
- 穩定的網路連接

### 9.2 部署方式

- Docker 容器化部署
- 支援多實例負載均衡
- 自動重啟機制

### 9.3 運維工具

- 健康檢查接口
- 性能監控面板
- 告警通知機制

## 10. 風險評估

### 10.1 技術風險

- 目標網站反爬蟲機制
- 代理 IP 質量不穩定
- 網路連接不穩定

### 10.2 緩解措施

- 實現多種反反爬蟲策略
- 建立 IP 質量評分機制
- 實現斷線重連和重試機制

## 11. 成功指標

### 11.1 技術指標

- 代理 IP 池維持在 1000+個有效 IP
- 驗證成功率 > 80%
- 系統穩定性 > 99%

### 11.2 業務指標

- 支援至少 10 個並發爬蟲任務
- 平均響應時間 < 2 秒
- 用戶滿意度 > 90%

## 12. 市場競爭分析

### 12.1 主要競品

| 公司        | 網站                    | 特色               |
| ----------- | ----------------------- | ------------------ |
| Bright Data | https://brightdata.com/ | 企業級代理服務     |
| IPRoyal     | https://iproyal.com/    | 住宅代理專業       |
| NetNut      | https://netnut.io/      | 數據中心代理       |
| Oxylabs     | https://oxylabs.io/     | 大規模爬蟲解決方案 |
| SmartProxy  | https://smartproxy.com/ | 易用性導向         |
| SOAX        | https://soax.com/       | 地理位置覆蓋       |

### 12.2 競爭優勢

1. **開源免費**: 完全開源，無使用成本
2. **自主可控**: 完全控制代理來源和驗證邏輯
3. **高度可定制**: 模組化設計，易於擴展和修改
4. **學習價值**: 完整的 ETL 流程和微服務架構範例

### 12.3 目標市場定位

- **開發者社區**: 為開發者提供學習和參考
- **中小企業**: 成本敏感的代理需求
- **教育機構**: 網路爬蟲教學和研究
- **個人項目**: 個人開發者和愛好者

## 13. 商業模式

### 13.1 核心價值主張

1. **技術透明**: 完整的開源代碼，技術實現完全透明
2. **成本效益**: 無需付費，僅需服務器資源
3. **教育價值**: 提供完整的代理池實現範例
4. **社區驅動**: 開源社區協作開發和維護

### 13.2 潛在商業化方向

1. **技術諮詢**: 提供代理池技術諮詢服務
2. **定制開發**: 為企業定制代理池解決方案
3. **託管服務**: 提供代理池託管和管理服務
4. **培訓課程**: 網路爬蟲和代理技術培訓

### 13.3 可持續發展策略

1. **社區建設**: 建立活躍的開發者社區
2. **技術創新**: 持續改進和創新技術實現
3. **生態擴展**: 圍繞代理池建立相關工具生態
4. **知識分享**: 通過博客、技術文章分享經驗

---

_本文檔整合了專案規劃中的 PRD 文檔和專案概述文檔，提供了完整的專案實施指南。_
