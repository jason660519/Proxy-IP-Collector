我現在要做一個 Proxy IP collector的小程式，大致想法如下:

### **代理IP池收集器 (Proxy IP Pool Collector)**

### 1\. 角色與目標 (Role & Goal) 你是一位資深的 Python 後端開發工程師，專精於網路爬蟲和分散式系統。你的任務是設計並實現一個高效、穩定、可擴展的代理IP池收集器 (Proxy IP Pool Collector)。該收集器的核心目標是從多個公開的代理IP網站持續抓取免費代理IP，並進行驗證，將可用的IP存入儲存池中，為上游的爬蟲業務提供匿名的網路請求能力。

2\. 核心功能需求 (Core Functional Requirements)  
請確保程式具備以下功能模組：

* 爬取模組 (Fetchers，每一個網址有一個定製的爬取方法或模組，以利將來方便管理):  
  * 能夠從以下知名的免費代理IP網站抓取IP和端口:  
    

| [https://www.89ip.cn/index\_{1\~100}.html](https://www.89ip.cn/index_99.html) | 每30分鐘收集一次，每一個page約有40個 |
| :---- | :---- |
| [https://www.kuaidaili.com/free/intr/](https://www.kuaidaili.com/free/intr/) | 每2天收集一次 |
| [https://www.kuaidaili.com/free/inha/](https://www.kuaidaili.com/free/inha/) | 每2天收集一次 |
| [https://proxylist.geonode.com/api/proxy-list?limit=500\&page={1\~24}\&sort\_by=lastChecked\&sort\_type=desc](https://proxylist.geonode.com/api/proxy-list?limit=500&page=7&sort_by=lastChecked&sort_type=desc) | 每30分鐘收集一次，有1\~24頁，每一個page 約有100個 |
| [https://proxydb.net/?offset={0\~4600}](https://proxydb.net/?offset=30) | 每48小時收集一次，offset={0\~4600}，每個page約30筆，所以offset後面的數字是30的倍數，從0,30,60,90,120.....4590,4620 |
| [https://www.proxynova.com/proxy-server-list/country-{國家}/](https://www.proxynova.com/proxy-server-list/country-us/) | 每24小時收集一次，一個國家約5\~35個，比如{國家}=us,tw,cn |
| [https://spys.one/en/http-proxy-list/](https://spys.one/en/http-proxy-list/) | 每24小時收集一次，要用playwright點選show 下拉選單，可以選一次顯示500筆。平均一天更新500筆 |
| [https://free-proxy-list.net/](https://free-proxy-list.net/) | 每30分鐘收集一次 |
| [https://free-proxy-list.net/en/socks-proxy.html](https://free-proxy-list.net/en/socks-proxy.html) | 每30分鐘收集一次 |
| [https://free-proxy-list.net/en/](https://free-proxy-list.net/en/) | 每30分鐘收集一次 |
| [https://free-proxy-list.net/en/us-proxy.html](https://free-proxy-list.net/en/us-proxy.html) | 每30分鐘收集一次 |
| [https://free-proxy-list.net/en/uk-proxy.html](https://free-proxy-list.net/en/uk-proxy.html) | 每30分鐘收集一次 |
| [https://free-proxy-list.net/en/ssl-proxy.html](https://free-proxy-list.net/en/ssl-proxy.html) | 每30分鐘收集一次 |
| [https://free-proxy-list.net/en/anonymous-proxy.html](https://free-proxy-list.net/en/anonymous-proxy.html) | 每30分鐘收集一次 |
| [https://free-proxy-list.net/en/google-proxy.html](https://free-proxy-list.net/en/google-proxy.html) | 每30分鐘收集一次 |

    

  * 解析方式應同時支持 HTML 靜態頁面解析和 JSON API 接口解析，並易於擴展新的網站來源。  
  * 需要模擬常見瀏覽器的 User-Agent 並控制請求頻率，避免對目標網站造成壓力。  
* 驗證模組 (Validator):  
  * 對抓取到的代理IP進行有效性驗證。驗證方式為通過該代理IP訪問一個或多個目標測試網站（例如: `http://httpbin.org/ip`, `https://www.baidu.com`），並檢查返回的狀態碼和內容是否包含代理IP本身。  
  * 驗證必須設定連接超時 (Timeout) 時間（例如 10 秒），超時或失敗的IP應被視為無效。  
  * 驗證過程應使用異步併發（如 `aiohttp` \+ `asyncio`）以大幅提高驗證效率。  
* 儲存模組 (Storage):  
  * 將驗證成功的代理IP及其相關信息（協議類型 `http/https`、匿名度、響應速度、來源、最後驗證時間）持久化儲存。  
  * 優先使用 Redis 作為儲存資料庫，因其高性能的數據結構非常適合此場景。使用 `Sorted Set` (有序集合) 來儲存IP，並以最後驗證時間戳或響應速度作為分數 (Score)，方便後續按質量排序和取出。  
* 調度模組 (Scheduler):  
  * 設計一個定時任務調度系統（例如使用 `APScheduler` 庫），例如，定期執行以下任務：  
    1. 定時爬取: 每 30 分鐘運行一次爬取模組。  
    2. 定時驗證: 每 10-15 分鐘對池中的IP進行一次重新驗證，並更新其有效狀態和速度。及時刪除失效的IP。  
    3. 池IP數量維護: 當池中可用IP數量低於某個閾值（如 50 個）時，自動觸發一次完整的爬取-驗證流程。

3\. 非功能與技術要求 (Non-Functional & Technical Requirements)

* 程式語言: Python 3.8+  
* 關鍵技術棧: 建議使用 `aiohttp` 進行異步HTTP請求，`BeautifulSoup4` 或 `Parsel` 進行HTML解析，`redis-py` 操作Redis，`APScheduler` 進行定時任務調度。  
* 代碼質量: 代碼需整潔、模組化、有清晰的註解。遵循 PEP8 規範。關鍵邏輯要有日誌記錄 (`logging` 模組)。  
* 可配置性: 將代理來源網站、測試URL、超時時間、數據庫連接參數等提取為配置文件（如 `config.py` 或 `settings.yaml`），方便後期維護和擴展。  
* 錯誤處理: 具有完善的異常處理機制，單個網站爬取失敗或單個IP驗證失敗不應導致整個程序崩潰。

目前市場上競品:

| [https://brightdata.com/](https://brightdata.com/) |
| :---- |
| [https://iproyal.com/](https://iproyal.com/) |
| [https://netnut.io/](https://netnut.io/) |
| [https://oxylabs.io/](https://oxylabs.io/) |
| [https://proxy-cheap.com/](https://proxy-cheap.com/) |
| [https://proxyempire.io/](https://proxyempire.io/) |
| [https://smartproxy.com/](https://smartproxy.com/) |
| [https://soax.com/](https://soax.com/) |
| [https://thesocialproxy.com/](https://thesocialproxy.com/) |

請根據我以上的大致需求，生成 

1. **本專案的 “Proxy IP Pool Collector\_**PRD.md**  
2. **本專案 “採用的技術棧.md”**  
3. **本專案的 Business\_Model.md**

## 5. 系統架構設計

### 5.1 整體架構概覽

基於新制定的架構規格書，本專案採用分層式微服務架構：

```
┌─────────────────────────────────────────────────────────────┐
│                    前端展示層 (Frontend)                     │
├─────────────────────────────────────────────────────────────┤
│                  API 網關層 (API Gateway)                   │
├─────────────────────────────────────────────────────────────┤
│                   業務邏輯層 (Backend)                      │
│  ┌─────────────┬─────────────┬─────────────┬──────────────┐  │
│  │  代理服務   │  驗證服務   │  統計服務   │  監控服務    │  │
│  └─────────────┴─────────────┴─────────────┴──────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                     ETL 數據處理層                         │
│  ┌─────────────┬─────────────┬─────────────┬──────────────┐  │
│  │  提取模組   │  轉換模組   │  載入模組   │  流程編排    │  │
│  └─────────────┴─────────────┴─────────────┴──────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    數據存儲層 (Storage)                     │
│  ┌─────────────┬─────────────┬─────────────┬──────────────┐  │
│  │   Redis     │ PostgreSQL  │   MongoDB   │   文件系統   │  │
│  └─────────────┴─────────────┴─────────────┴──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 ETL 架構整合

根據《ETL架構規格書.md》，數據處理流程包含：

#### 5.2.1 數據提取層 (Extraction)
- **多源提取架構**：支援 HTML 爬蟲、JSON API、RSS 訂閱
- **提取協調器**：統一管理各數據源提取任務
- **智能調度**：基於網站更新頻率自動調整提取間隔

#### 5.2.2 數據轉換層 (Transformation)
- **清洗驗證**：代理 IP 格式驗證、重複過濾
- **品質評分**：基於響應時間、成功率計算品質分數
- **標準化處理**：統一代理 IP 數據結構

#### 5.2.3 數據載入層 (Loading)
- **多目標策略**：支援 Redis、PostgreSQL、文件匯出
- **批量載入**：優化大量數據寫入性能
- **容錯機制**：失敗重試、錯誤記錄

### 5.3 後端架構設計

根據《後端架構規格書.md》，後端採用微服務架構：

#### 5.3.1 核心服務模組
- **代理服務 (Proxy Service)**：代理 IP 的 CRUD 操作
- **驗證服務 (Validator Service)**：代理 IP 有效性驗證
- **統計服務 (Statistics Service)**：數據統計與報表
- **監控服務 (Monitoring Service)**：系統健康監控

#### 5.3.2 技術選型
- **框架**：FastAPI (異步高性能)
- **數據庫**：PostgreSQL + Redis
- **任務調度**：Celery + Redis
- **API 文檔**：自動生成 OpenAPI 文檔

### 5.4 前端架構設計

根據《前端架構規格書.md》，前端採用現代 React 技術棧：

#### 5.4.1 技術選型
- **框架**：React 18 + TypeScript
- **狀態管理**：Redux Toolkit + RTK Query
- **UI 框架**：Material-UI (MUI)
- **圖表**：Chart.js + react-chartjs-2
- **路由**：React Router v6

#### 5.4.2 核心頁面
- **儀表板**：系統概覽、實時統計
- **代理管理**：代理列表、驗證結果
- **數據分析**：圖表展示、趨勢分析
- **系統監控**：服務狀態、性能指標

## 6. 實施計劃與里程碑

### 6.1 開發階段劃分（整合新架構）

#### 6.1.1 第一階段 - 基礎架構與 ETL（3週）
```
Week 1-3: 核心架構 + ETL 基礎
├── 項目結構設計（整合前後端）
├── ETL 架構搭建
├── 後端微服務架構
├── Redis/PostgreSQL 集成
├── 前端項目初始化
└── Docker 容器化配置
```

#### 6.1.2 第二階段 - 後端核心服務（3週）
```
Week 4-6: 後端功能實現
├── FastAPI 框架搭建
├── 代理服務實現
├── 驗證服務實現
├── 統計服務實現
├── Celery 任務調度
└── API 文檔生成
```

#### 6.1.3 第三階段 - 前端界面開發（3週）
```
Week 7-9: 前端界面實現
├── React 項目架構
├── Redux 狀態管理
├── Material-UI 界面設計
├── 儀表板頁面開發
├── 代理管理頁面
└── 圖表組件開發
```

#### 6.1.4 第四階段 - ETL 流程完善（2週）
```
Week 10-11: ETL 流程優化
├── 爬蟲模組整合
├── 數據清洗優化
├── 品質評分算法
├── 批量載入優化
└── 監控告警集成
```

#### 6.1.5 第五階段 - 前後端整合（2週）
```
Week 12-13: 系統整合測試
├── API 接口對接
├── WebSocket 實時通信
├── 前端後端聯調
├── 性能優化調優
└── 部署腳本準備
```

#### 6.1.6 第六階段 - 測試與部署（2週）
```
Week 14-15: 測試部署完善
├── 單元測試覆蓋
├── 集成測試用例
├── 性能壓力測試
├── 生產環境部署
└── 監控告警配置
```

### 5.2 技術債務管理

#### 5.2.1 代碼質量指標
- **測試覆蓋率**: 目標>80%
- **代碼複雜度**: 圈複雜度<10
- **重複代碼率**: <5%
- **技術債務評級**: A級

#### 5.2.2 重構計劃
```
Phase 1: 架構優化（第8週）
├── 模組依賴梳理
├── 接口抽象完善
├── 錯誤處理統一
└── 配置管理優化

Phase 2: 性能調優（第11週）
├── 異步處理優化
├── 內存使用優化
├── 網絡請求優化
└── 緩存策略改進

Phase 3: 代碼清理（第13週）
├── 死代碼清理
├── 代碼風格統一
├── 註釋文檔完善
└── 依賴版本升級
```

### 5.3 風險緩解策略

#### 5.3.1 技術風險
- **爬蟲被封鎖**: 使用代理池輪換，模擬真人行為
- **目標網站結構變化**: 模組化設計，快速適配新結構
- **性能瓶頸**: 異步處理，連接池優化，分佈式部署
- **數據一致性**: 事務處理，異常恢復，數據校驗

#### 5.3.2 項目管理風險
- **進度延遲**: 迭代開發，關鍵路徑優先，資源調配
- **需求變更**: 靈活架構，配置驅動，模組化設計
- **人員流失**: 代碼文檔，知識沉澱，培訓體系
- **技術選型錯誤**: 技術評估，原型驗證，逐步遷移

### 5.4 質量保證措施

#### 5.4.1 代碼審查流程
```
開發者自測 → 同儕審查 → 自動化測試 → 集成測試 → 發布審批
```

#### 5.4.2 持續集成/持續部署
- **代碼提交觸發**: 自動化測試，靜態分析
- **定時構建**: 每日構建，每週發布
- **環境一致性**: 容器化部署，配置管理
- **回滾機制**: 版本控制，快速回滾，灰度發布

#### 5.4.3 監控與告警
- **系統監控**: CPU、內存、磁盤、網絡
- **應用監控**: 請求量、響應時間、錯誤率
- **業務監控**: 代理收集量、驗證成功率
- **告警機制**: 閾值告警，趨勢告警，異常告警