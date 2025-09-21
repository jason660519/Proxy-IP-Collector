# Proxy IP Pool Collector - 產品需求文檔 (PRD)

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

## 2. 核心功能需求

### 2.1 爬取模組 (Fetchers)

#### 2.1.1 支援的代理 IP 來源網站

| 網站                     | 更新頻率 | 頁面範圍      | 每頁數量 | 備註       |
| ------------------------ | -------- | ------------- | -------- | ---------- |
| 89ip.cn                  | 30 分鐘  | 1-100 頁      | ~40 個   | HTML 解析  |
| kuaidaili.com/free/intr/ | 2 天     | 1 頁          | 動態     | HTML 解析  |
| kuaidaili.com/free/inha/ | 2 天     | 1 頁          | 動態     | HTML 解析  |
| proxylist.geonode.com    | 30 分鐘  | 1-24 頁       | ~100 個  | JSON API   |
| proxydb.net              | 48 小時  | 0-4620 offset | ~30 個   | HTML 解析  |
| proxynova.com            | 24 小時  | 多國家        | 5-35 個  | HTML 解析  |
| spys.one                 | 24 小時  | 1 頁          | ~500 個  | Playwright |
| free-proxy-list.net      | 30 分鐘  | 多個子頁面    | 動態     | HTML 解析  |

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

基於《ETL架構規格書.md》、《後端架構規格書.md》、《前端架構規格書.md》的完整架構設計：

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

### 3.2 架構分層說明

#### 3.2.1 前端展示層
- **技術棧**: React 18 + TypeScript + Material-UI
- **核心功能**: 儀表板、代理管理、數據可視化、系統監控
- **狀態管理**: Redux Toolkit + RTK Query
- **實時通信**: WebSocket

#### 3.2.2 API 網關層
- **技術棧**: FastAPI + Pydantic + Uvicorn
- **核心功能**: 路由管理、請求驗證、響應格式化、API文檔
- **認證授權**: JWT + OAuth2
- **文檔生成**: 自動OpenAPI文檔

#### 3.2.3 業務邏輯層
- **代理服務**: 代理IP的CRUD操作、查詢優化
- **驗證服務**: 異步代理驗證、批量處理
- **統計服務**: 數據分析、報表生成、趨勢預測
- **監控服務**: 系統健康檢查、性能監控、告警通知
- **調度服務**: Celery任務調度、定時任務管理

#### 3.2.4 ETL 數據處理層
根據《ETL架構規格書.md》設計：

**提取層 (Extraction)**:
- **多源提取**: 支援HTML爬蟲、JSON API、RSS訂閱
- **智能調度**: 基於網站更新頻率自動調整提取間隔
- **錯誤處理**: 重試機制、降級策略、熔斷保護

**轉換層 (Transformation)**:
- **數據清洗**: 代理IP格式驗證、重複過濾
- **品質評分**: 基於響應時間、成功率計算品質分數
- **標準化處理**: 統一代理IP數據結構

**載入層 (Loading)**:
- **多目標策略**: 支援Redis、PostgreSQL、文件匯出
- **批量載入**: 優化大量數據寫入性能
- **容錯機制**: 失敗重試、錯誤記錄、事務處理

### 3.3 核心模組設計

基於新架構設計，核心模組已整合到ETL、後端、前端架構中：

#### 3.3.1 ETL提取層 (Extraction Layer)

根據《ETL架構規格書.md》的提取協調器設計：

根據《ETL架構規格書.md》的提取協調器設計：

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
    
    async def _extract_with_aiohttp(self) -> List[Dict[str, Any]]:
        """使用aiohttp提取"""
        # 實現基於aiohttp的提取邏輯
        pass
    
    async def _extract_with_playwright(self) -> List[Dict[str, Any]]:
        """使用Playwright提取"""
        # 實現基於Playwright的提取邏輯
        pass

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
    
    async def _extract_with_rate_limit(self, extractor: BaseExtractor):
        """使用速率限制執行提取"""
        await self.rate_limiter.acquire(extractor.name)
        return await extractor.extract()
```

#### 3.3.2 ETL轉換層 (Transformation Layer)

根據《ETL架構規格書.md》的轉換協調器設計：

根據《ETL架構規格書.md》的轉換協調器設計：

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
    
    def _validate_item(self, item: Dict[str, Any]) -> bool:
        """驗證單個數據項"""
        required_fields = ['ip', 'port', 'type']
        return all(field in item and item[field] for field in required_fields)

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
    
    async def _transform_proxy_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """轉換單個代理IP項"""
        # 標準化代理IP格式
        return {
            'ip': item['ip'].strip(),
            'port': int(item['port']),
            'type': item['type'].lower(),
            'country': item.get('country', 'Unknown'),
            'anonymity': item.get('anonymity', 'unknown'),
            'source': item.get('source', 'unknown'),
            'response_time': float(item.get('response_time', 0)),
            'last_verified': item.get('last_verified', datetime.now().timestamp())
        }

class TransformationCoordinator:
    """轉換協調器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.transformers: Dict[str, BaseTransformer] = {}
        self.quality_threshold = config.get('quality_threshold', 0.7)
    
    def register_transformer(self, transformer: BaseTransformer):
        """註冊轉換器"""
        self.transformers[transformer.name] = transformer
    
    async def transform_all(self, data: List[Dict[str, Any]]) -> List[TransformationResult]:
        """執行所有轉換任務"""
        tasks = []
        for transformer in self.transformers.values():
            if transformer.enabled:
                task = transformer.transform(data)
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, TransformationResult)]
    
    def filter_by_quality(self, results: List[TransformationResult]) -> List[Dict[str, Any]]:
        """根據品質分數過濾數據"""
        filtered_data = []
        for result in results:
            if result.status == 'success' and result.quality_score >= self.quality_threshold:
                filtered_data.extend(result.transformed_data)
        return filtered_data
```
#### 3.3.3 ETL載入層 (Loading Layer)

根據《ETL架構規格書.md》的載入協調器設計：

根據《ETL架構規格書.md》的載入協調器設計：

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
    
    async def validate_connection(self) -> bool:
        """驗證連接可用性"""
        return True

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

class PostgreSQLLoader(BaseLoader):
    """PostgreSQL載入器"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.connection_pool = None
    
    async def load(self, data: List[Dict[str, Any]]) -> LoadResult:
        """載入數據到PostgreSQL"""
        try:
            # 初始化連接池
            if not self.connection_pool:
                import asyncpg
                self.connection_pool = await asyncpg.create_pool(
                    host=self.config.get('host', 'localhost'),
                    port=self.config.get('port', 5432),
                    database=self.config.get('database', 'proxy_pool'),
                    user=self.config.get('user', 'postgres'),
                    password=self.config.get('password', '')
                )
            
            loaded_count = 0
            errors = []
            
            async with self.connection_pool.acquire() as conn:
                # 使用COPY進行高效批量載入
                await self._bulk_insert(conn, data)
                loaded_count = len(data)
            
            return LoadResult(
                target=self.name,
                loaded_count=loaded_count,
                failed_count=len(data) - loaded_count,
                timestamp=datetime.now(),
                status='success'
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
    
    async def _bulk_insert(self, conn, data: List[Dict[str, Any]]):
        """批量插入數據"""
        # 實現PostgreSQL批量插入邏輯
        pass

class LoadCoordinator:
    """載入協調器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.loaders: Dict[str, BaseLoader] = {}
        self.load_strategy = config.get('load_strategy', 'all')  # all, primary, fallback
    
    def register_loader(self, loader: BaseLoader):
        """註冊載入器"""
        self.loaders[loader.name] = loader
    
    async def load_all(self, data: List[Dict[str, Any]]) -> List[LoadResult]:
        """執行所有載入任務"""
        tasks = []
        
        if self.load_strategy == 'all':
            # 所有載入器都執行
            for loader in self.loaders.values():
                if loader.enabled:
                    task = loader.load(data)
                    tasks.append(task)
        
        elif self.load_strategy == 'primary':
            # 只執行主要載入器
            primary_loader = self.loaders.get(self.config.get('primary_loader'))
            if primary_loader and primary_loader.enabled:
                tasks.append(primary_loader.load(data))
        
        elif self.load_strategy == 'fallback':
            # 失敗時回退到其他載入器
            primary_loader = self.loaders.get(self.config.get('primary_loader'))
            if primary_loader and primary_loader.enabled:
                result = await primary_loader.load(data)
                if result.status == 'failed':
                    # 主要載入器失敗，嘗試備用載入器
                    for loader in self.loaders.values():
                        if loader.enabled and loader.name != primary_loader.name:
                            tasks.append(loader.load(data))
                            break
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, LoadResult)]
    
    def get_load_summary(self, results: List[LoadResult]) -> Dict[str, Any]:
        """生成載入摘要"""
        total_loaded = sum(r.loaded_count for r in results)
        total_failed = sum(r.failed_count for r in results)
        
        return {
            'total_loaded': total_loaded,
            'total_failed': total_failed,
            'success_rate': total_loaded / (total_loaded + total_failed) if (total_loaded + total_failed) > 0 else 0,
            'targets': [r.target for r in results],
            'timestamp': datetime.now().isoformat()
        }
```

## 3.4 API 設計

根據《後端架構規格書.md》的API設計，重新設計RESTful API：

### 3.4.1 API 架構設計

```python
from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime
import uvicorn

# 根據後端架構規格書的Pydantic模型設計
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
    
    class Config:
        schema_extra = {
            "example": {
                "id": "proxy_123",
                "ip": "1.2.3.4",
                "port": 8080,
                "protocol": "http",
                "anonymity": "high_anonymous",
                "country": "US",
                "response_time": 1.5,
                "success_rate": 0.85,
                "status": "active",
                "source": "freeproxy-list",
                "last_verified": "2024-01-15T10:30:00Z",
                "created_at": "2024-01-15T08:00:00Z"
            }
        }

class ProxyQueryParams(BaseModel):
    """代理查詢參數"""
    protocol: Optional[ProxyProtocol] = Field(None, description="協議類型篩選")
    anonymity: Optional[AnonymityLevel] = Field(None, description="匿名度篩選")
    country: Optional[str] = Field(None, description="國家代碼篩選")
    status: Optional[ProxyStatus] = Field(None, description="狀態篩選")
    min_success_rate: float = Field(0.5, ge=0, le=1, description="最小成功率")
    max_response_time: Optional[float] = Field(None, ge=0, description="最大響應時間")
    limit: int = Field(100, ge=1, le=1000, description="返回數量限制")
    offset: int = Field(0, ge=0, description="分頁偏移")

class ProxyStats(BaseModel):
    """代理統計模型"""
    total_count: int = Field(..., description="總代理數")
    active_count: int = Field(..., description="活躍代理數")
    valid_count: int = Field(..., description="有效代理數")
    avg_response_time: float = Field(..., description="平均響應時間")
    avg_success_rate: float = Field(..., description="平均成功率")
    protocol_distribution: Dict[str, int] = Field(..., description="協議分布")
    country_distribution: Dict[str, int] = Field(..., description="國家分布")
    anonymity_distribution: Dict[str, int] = Field(..., description="匿名度分布")

# FastAPI應用實例
app = FastAPI(
    title="Proxy Pool Collector API",
    description="代理IP池收集器API - 基於新架構設計",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境需要配置具體域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全認證
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """獲取當前用戶 - 根據後端架構的JWT認證"""
    # 實現JWT token驗證邏輯
    pass

# API路由實現
@app.get("/api/v2/proxies", response_model=Dict[str, Any])
async def get_proxies(
    params: ProxyQueryParams = Depends(),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    獲取代理IP列表 - 根據後端架構的代理服務設計
    
    - **protocol**: 協議類型篩選 (http, https, socks4, socks5)
    - **anonymity**: 匿名度篩選 (transparent, anonymous, high_anonymous)
    - **country**: 國家代碼篩選
    - **status**: 代理狀態篩選
    - **min_success_rate**: 最小成功率篩選
    - **limit**: 返回數量限制 (1-1000)
    """
    try:
        # 調用代理服務獲取數據
        # proxy_service = ProxyService()
        # proxies = await proxy_service.get_proxies(params)
        
        # 模擬返回數據
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

@app.get("/api/v2/proxies/stats", response_model=ProxyStats)
async def get_proxy_stats(
    current_user: dict = Depends(get_current_user)
) -> ProxyStats:
    """獲取代理池統計信息"""
    try:
        # 調用統計服務
        # stats_service = StatsService()
        # return await stats_service.get_proxy_stats()
        
        # 模擬返回數據
        return ProxyStats(
            total_count=0,
            active_count=0,
            valid_count=0,
            avg_response_time=0.0,
            avg_success_rate=0.0,
            protocol_distribution={},
            country_distribution={},
            anonymity_distribution={}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取統計信息失敗: {str(e)}"
        )

@app.post("/api/v2/proxies/validate")
async def validate_proxies(
    proxy_ids: List[str] = Field(..., description="要驗證的代理ID列表"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """批量驗證代理"""
    try:
        # 調用驗證服務
        # validation_service = ValidationService()
        # results = await validation_service.validate_proxies(proxy_ids)
        
        return {
            "message": "驗證任務已提交",
            "task_id": "task_123",
            "proxy_count": len(proxy_ids)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"驗證代理失敗: {str(e)}"
        )

@app.get("/api/v2/proxies/{proxy_id}", response_model=ProxyResponse)
async def get_proxy(
    proxy_id: str = Field(..., description="代理ID"),
    current_user: dict = Depends(get_current_user)
) -> ProxyResponse:
    """獲取指定代理詳情"""
    try:
        # 調用代理服務
        # proxy_service = ProxyService()
        # proxy = await proxy_service.get_proxy_by_id(proxy_id)
        
        # if not proxy:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="代理不存在"
        #     )
        
        # return proxy
        
        # 模擬返回數據
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="代理不存在"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取代理詳情失敗: {str(e)}"
        )

@app.delete("/api/v2/proxies/{proxy_id}")
async def delete_proxy(
    proxy_id: str = Field(..., description="代理ID"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """刪除指定代理"""
    try:
        # 調用代理服務
        # proxy_service = ProxyService()
        # success = await proxy_service.delete_proxy(proxy_id)
        
        # if not success:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="代理不存在"
        #     )
        
        return {
            "message": "代理刪除成功",
            "proxy_id": proxy_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除代理失敗: {str(e)}"
        )

# ETL流程API
@app.post("/api/v2/etl/extract")
async def trigger_extraction(
    sources: List[str] = Field(..., description="提取源列表"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """觸發ETL提取流程"""
    return {
        "message": "提取任務已提交",
        "task_id": "etl_extract_123",
        "sources": sources
    }

@app.post("/api/v2/etl/transform")
async def trigger_transformation(
    task_id: str = Field(..., description="提取任務ID"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """觸發ETL轉換流程"""
    return {
        "message": "轉換任務已提交",
        "task_id": "etl_transform_123",
        "extract_task_id": task_id
    }

@app.post("/api/v2/etl/load")
async def trigger_loading(
    task_id: str = Field(..., description="轉換任務ID"),
    targets: List[str] = Field(..., description="載入目標列表"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """觸發ETL載入流程"""
    return {
        "message": "載入任務已提交",
        "task_id": "etl_load_123",
        "transform_task_id": task_id,
        "targets": targets
    }

# 系統監控API
@app.get("/api/v2/system/health")
async def health_check() -> Dict[str, Any]:
    """系統健康檢查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "services": {
            "api": "healthy",
            "database": "healthy",
            "redis": "healthy",
            "etl": "healthy"
        }
    }

@app.get("/api/v2/system/metrics")
async def get_metrics(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """獲取系統指標"""
    return {
        "proxies": {
            "total": 0,
            "active": 0,
            "valid": 0,
            "by_protocol": {},
            "by_country": {},
            "by_anonymity": {}
        },
        "etl": {
            "extracted_today": 0,
            "validated_today": 0,
            "loaded_today": 0,
            "failed_tasks": 0
        },
        "system": {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "uptime": 0
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
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

## 5. 系統架構設計

根據《ETL架構規格書.md》、《後端架構規格書.md》、《前端架構規格書.md》的整合設計，本專案採用分層架構設計：

### 5.1 整體架構概覽

```
┌─────────────────────────────────────────────────────────────┐
│                    前端展示層 (Frontend)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Vue 3     │  │  Dashboard  │  │  Monitoring │         │
│  │  Composition│  │  Component  │  │  Component  │         │
│  │   API       │  │             │  │             │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                 │                 │                 │
│  ┌──────┴─────────────────┴─────────────────┴──────┐        │
│  │              API 網關層 (API Gateway)              │        │
│  │              FastAPI + JWT 認證                     │        │
│  └──────┬──────────────────────────────────────────┘        │
│         │                                                 │
│  ┌──────┴──────────────────────────────────────────┐        │
│  │              業務邏輯層 (Service Layer)           │        │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │        │
│  │  │Proxy Service│  │Stats Service│  │ETL Service  │ │        │
│  │  │             │  │             │  │             │ │        │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │        │
│  │         │                 │                 │        │        │
│  │  ┌──────┴─────────────────┴─────────────────┴──────┐ │        │
│  │  │          ETL 數據處理層 (ETL Layer)              │ │        │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │ │        │
│  │  │  │Extraction   │  │Transformation │  │   Loading   │ │ │        │
│  │  │  │Coordinator │  │Coordinator  │  │Coordinator │ │ │        │
│  │  │  │             │  │             │  │             │ │ │        │
│  │  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │ │        │
│  │  │         │                 │                 │        │ │        │
│  │  │  ┌──────┴─────────────────┴─────────────────┴──────┐ │ │        │
│  │  │  │          數據存儲層 (Data Storage)              │ │ │        │
│  │  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │ │ │        │
│  │  │  │     Redis     │  │ PostgreSQL   │  │   MongoDB   │ │ │ │        │
│  │  │  │   (Cache)     │  │  (Primary)   │  │  (Backup)   │ │ │ │        │
│  │  │  └──────────────┴──────────────┴──────────────┘ │ │ │        │
│  │  └──────────────────────────────────────────────────┘ │        │
│  └─────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 架構分層說明

#### 5.2.1 前端展示層 (Frontend Layer)
- **技術棧**: Vue 3 + TypeScript + Vite + Element Plus
- **核心功能**: 
  - 代理IP管理界面
  - 實時監控面板
  - ETL流程可視化
  - 系統配置管理
- **架構特點**: 組件化設計、響應式佈局、TypeScript類型安全

#### 5.2.2 API 網關層 (API Gateway Layer)
- **技術棧**: FastAPI + JWT + CORS
- **核心功能**:
  - RESTful API接口
  - JWT身份認證
  - 請求限流與安全
  - API文檔自動生成
- **架構特點**: 異步處理、自動驗證、OpenAPI規範

#### 5.2.3 業務邏輯層 (Service Layer)
- **技術棧**: Python + asyncio + Pydantic
- **核心功能**:
  - 代理服務 (Proxy Service)
  - 統計服務 (Stats Service)  
  - ETL協調服務 (ETL Service)
- **架構特點**: 領域驅動設計、依賴注入、事務管理

#### 5.2.4 ETL 數據處理層 (ETL Layer)
- **技術棧**: Python + asyncio + 資料類
- **核心功能**:
  - **提取層**: 多源數據提取協調
  - **轉換層**: 數據清洗與標準化
  - **載入層**: 多目標數據載入
- **架構特點**: 管道模式、錯誤隔離、質量監控

#### 5.2.5 數據存儲層 (Data Storage Layer)
- **技術棧**: Redis + PostgreSQL + MongoDB
- **核心功能**:
  - Redis: 高速緩存與會話存儲
  - PostgreSQL: 結構化數據持久化
  - MongoDB: 日誌與備份存儲
- **架構特點**: 多層存儲策略、讀寫分離、數據冗餘

### 5.3 實施計劃與里程碑

根據新架構設計，開發階段重新劃分為：

#### 第一階段: 基礎架構與ETL (3週)
- **Week 1**: ETL架構實現
  - 提取協調器開發
  - 轉換協調器開發  
  - 載入協調器開發
- **Week 2**: 數據存儲層搭建
  - Redis集群配置
  - PostgreSQL數據庫設計
  - 數據訪問對象實現
- **Week 3**: ETL流程整合測試
  - 端到端ETL流程測試
  - 性能基準測試
  - 錯誤處理機制驗證

#### 第二階段: 後端核心服務 (2週)
- **Week 4**: API網關層實現
  - FastAPI框架搭建
  - JWT認證系統
  - API路由與中間件
- **Week 5**: 業務服務開發
  - 代理服務實現
  - 統計服務實現
  - 服務間通信機制

#### 第三階段: 前端界面開發 (2週)
- **Week 6**: 前端架構搭建
  - Vue 3項目初始化
  - Element Plus組件庫整合
  - TypeScript配置
- **Week 7**: 核心界面實現
  - 代理管理界面
  - 監控面板開發
  - API客戶端封裝

#### 第四階段: ETL流程完善 (1週)
- **Week 8**: 高級功能實現
  - 增量更新機制
  - 並行處理優化
  - 質量監控系統

#### 第五階段: 前後端整合 (1週)
- **Week 9**: 系統整合
  - API集成測試
  - 前端後端聯調
  - 端到端功能驗證

#### 第六階段: 測試與部署 (1週)
- **Week 10**: 測試與優化
  - 單元測試補充
  - 性能測試
  - 生產環境部署

### 5.4 技術債務管理

#### 高優先級技術債務
1. **ETL錯誤隔離機制**: 確保單個數據源故障不影響整體流程
2. **API限流保護**: 防止系統過載和惡意攻擊
3. **數據一致性保障**: 跨存儲層的數據同步機制

#### 中優先級技術債務  
1. **前端組件庫文檔**: 完整的組件使用文檔
2. **API版本管理**: 支持API向後兼容
3. **配置中心**: 集中化的配置管理

#### 低優先級技術債務
1. **代碼覆蓋率提升**: 從60%提升至80%
2. **性能監控優化**: 更細緻的性能指標
3. **自動化部署**: CI/CD流程完善

### 5.5 風險緩解策略

#### 技術風險
- **ETL流程複雜性**: 採用管道模式簡化流程，加強單元測試
- **多存儲層一致性**: 實現分佈式事務機制，定期數據校驗
- **前端後端集成**: 提前進行接口對接，使用Mock數據獨立開發

#### 進度風險
- **階段性交付**: 每個階段都有可演示的成果
- **關鍵路徑優化**: 識別並優化關鍵開發路徑
- **資源預留**: 為高風險任務預留緩衝時間

### 5.6 質量保證措施

#### 代碼質量
- **靜態代碼分析**: 使用pylint、eslint等工具
- **代碼審查流程**: 強制代碼Review機制
- **設計模式應用**: 統一的架構模式和編碼規範

#### 測試策略
- **單元測試**: 核心模組100%覆蓋
- **集成測試**: 關鍵路徑完整測試
- **端到端測試**: 用戶場景模擬測試

#### 性能保障
- **性能基準**: 建立性能測試基準
- **負載測試**: 模擬高併發場景
- **監控告警**: 實時性能監控和告警

## 6. 配置管理

### 6.1 配置文件結構

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

## 7. 監控與日誌

### 7.1 監控指標

- 代理 IP 池大小
- 有效 IP 比例
- 驗證成功率
- 爬取成功率
- 系統資源使用率

### 7.2 日誌級別

- **DEBUG**: 詳細的調試信息
- **INFO**: 一般操作記錄
- **WARNING**: 警告信息
- **ERROR**: 錯誤信息
- **CRITICAL**: 嚴重錯誤

## 8. 部署與運維

### 8.1 系統要求

- Python 3.8+
- Redis 6.0+
- 至少 2GB RAM
- 穩定的網路連接

### 8.2 部署方式

- Docker 容器化部署
- 支援多實例負載均衡
- 自動重啟機制

### 8.3 運維工具

- 健康檢查接口
- 性能監控面板
- 告警通知機制

## 9. 開發計劃

### 9.1 第一階段 (2 週)

- 基礎架構搭建
- 核心模組實現
- 基本爬取和驗證功能

### 9.2 第二階段 (2 週)

- 調度系統實現
- 儲存模組優化
- 配置管理完善

### 9.3 第三階段 (1 週)

- 監控和日誌系統
- 性能優化
- 測試和文檔完善

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
