# Proxy IP Pool Collector - ETL 架構規格書

## 1. 架構概述

### 1.1 設計理念
ETL（Extract-Transform-Load）架構採用流式處理設計，實現高吞吐量、低延遲的代理IP數據處理管道。架構核心目標是實現數據的實時提取、智能轉換和高效載入。

### 1.2 技術選型
- **流處理引擎**：Apache Kafka + Faust（Python流處理庫）
- **數據管道**：Redis Streams + 自定義異步管道
- **任務調度**：Celery + Redis
- **數據存儲**：PostgreSQL（主庫）+ Redis（快取）+ ClickHouse（分析）
- **監控系統**：Prometheus + Grafana + 自定義指標

## 2. 數據提取層（Extract）

### 2.1 多源數據提取架構
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import asyncio
import aiohttp
from datetime import datetime

@dataclass
class ExtractConfig:
    """提取配置"""
    source_type: str  # 'api', 'web_scraping', 'file', 'database'
    source_url: str
    extraction_method: str
    rate_limit: int = 100  # 每分鐘請求數
    timeout: int = 30
    retry_count: int = 3
    headers: Dict[str, str] = None
    auth_config: Dict[str, Any] = None

class BaseExtractor(ABC):
    """基礎提取器"""
    
    def __init__(self, config: ExtractConfig):
        self.config = config
        self.session = None
        self.rate_limiter = None
        
    @abstractmethod
    async def extract(self) -> List[Dict[str, Any]]:
        """提取數據"""
        pass
        
    @abstractmethod
    async def validate_source(self) -> bool:
        """驗證數據源"""
        pass
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers=self.config.headers or {}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

class APIExtractor(BaseExtractor):
    """API數據提取器"""
    
    async def extract(self) -> List[Dict[str, Any]]:
        """從API提取代理數據"""
        proxies = []
        
        async with self.session.get(self.config.source_url) as response:
            if response.status == 200:
                data = await response.json()
                
                # 根據不同API格式解析
                if isinstance(data, list):
                    proxies = data
                elif 'data' in data:
                    proxies = data['data']
                elif 'proxies' in data:
                    proxies = data['proxies']
                    
                # 標準化數據格式
                return self._normalize_proxy_data(proxies)
            else:
                raise Exception(f"API請求失敗: {response.status}")
    
    def _normalize_proxy_data(self, data: List[Dict]) -> List[Dict[str, Any]]:
        """標準化代理數據格式"""
        normalized_proxies = []
        
        for proxy in data:
            normalized_proxy = {
                'ip': proxy.get('ip') or proxy.get('host', ''),
                'port': int(proxy.get('port', 0)),
                'protocol': proxy.get('protocol', 'http'),
                'country': proxy.get('country', 'unknown'),
                'anonymity': proxy.get('anonymity', 'unknown'),
                'source': self.config.source_type,
                'extracted_at': datetime.now().isoformat(),
                'raw_data': proxy
            }
            normalized_proxies.append(normalized_proxy)
            
        return normalized_proxies
    
    async def validate_source(self) -> bool:
        """驗證API源"""
        try:
            async with self.session.get(
                self.config.source_url, 
                timeout=10
            ) as response:
                return response.status == 200
        except:
            return False

class WebScrapingExtractor(BaseExtractor):
    """網頁爬蟲提取器"""
    
    def __init__(self, config: ExtractConfig):
        super().__init__(config)
        from playwright.async_api import async_playwright
        self.playwright = None
        self.browser = None
        
    async def extract(self) -> List[Dict[str, Any]]:
        """從網頁提取代理數據"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            
        page = await self.browser.new_page()
        
        try:
            await page.goto(self.config.source_url)
            await page.wait_for_load_state('networkidle')
            
            # 根據配置提取數據
            if self.config.extraction_method == 'table':
                proxies = await self._extract_from_table(page)
            elif self.config.extraction_method == 'api_call':
                proxies = await self._extract_from_api_call(page)
            else:
                proxies = await self._extract_with_selectors(page)
                
            return self._normalize_proxy_data(proxies)
            
        finally:
            await page.close()
    
    async def _extract_from_table(self, page) -> List[Dict[str, Any]]:
        """從表格提取數據"""
        rows = await page.query_selector_all('table tr')
        proxies = []
        
        for row in rows[1:]:  # 跳過表頭
            cells = await row.query_selector_all('td')
            if len(cells) >= 2:
                proxy = {
                    'ip': await cells[0].inner_text(),
                    'port': await cells[1].inner_text(),
                }
                proxies.append(proxy)
                
        return proxies
    
    async def validate_source(self) -> bool:
        """驗證網頁源"""
        try:
            if not self.browser:
                return False
                
            page = await self.browser.new_page()
            await page.goto(self.config.source_url, timeout=10000)
            content = await page.content()
            await page.close()
            
            return len(content) > 100  # 基本驗證
        except:
            return False
```

### 2.2 提取協調器
```python
class ExtractionCoordinator:
    """提取協調器"""
    
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.extractors = []
        self.extracted_data_queue = asyncio.Queue()
        self.metrics_collector = MetricsCollector()
        
    async def initialize_extractors(self):
        """初始化所有提取器"""
        configs = self._load_configs()
        
        for config_data in configs:
            config = ExtractConfig(**config_data)
            
            if config.source_type == 'api':
                extractor = APIExtractor(config)
            elif config.source_type == 'web_scraping':
                extractor = WebScrapingExtractor(config)
            else:
                continue
                
            self.extractors.append(extractor)
    
    async def start_extraction(self):
        """開始提取流程"""
        await self.initialize_extractors()
        
        # 創建提取任務
        tasks = []
        for extractor in self.extractors:
            task = asyncio.create_task(self._extract_with_metrics(extractor))
            tasks.append(task)
        
        # 並行執行提取
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果
        all_proxies = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"提取失敗: {result}")
            else:
                all_proxies.extend(result)
                
        return all_proxies
    
    async def _extract_with_metrics(self, extractor: BaseExtractor):
        """帶指標收集的提取"""
        start_time = datetime.now()
        
        try:
            async with extractor:
                # 驗證源
                is_valid = await extractor.validate_source()
                if not is_valid:
                    logger.warning(f"提取源無效: {extractor.config.source_url}")
                    return []
                
                # 執行提取
                data = await extractor.extract()
                
                # 記錄指標
                extraction_time = (datetime.now() - start_time).total_seconds()
                self.metrics_collector.record_extraction(
                    source=extractor.config.source_type,
                    proxy_count=len(data),
                    extraction_time=extraction_time,
                    success=True
                )
                
                return data
                
        except Exception as e:
            # 記錄失敗指標
            self.metrics_collector.record_extraction(
                source=extractor.config.source_type,
                proxy_count=0,
                extraction_time=(datetime.now() - start_time).total_seconds(),
                success=False,
                error=str(e)
            )
            raise e
```

## 3. 數據轉換層（Transform）

### 3.1 數據清洗與驗證
```python
from pydantic import BaseModel, validator
from typing import Optional, Literal
import ipaddress

class ProxyData(BaseModel):
    """標準化代理數據模型"""
    
    ip: str
    port: int
    protocol: Literal['http', 'https', 'socks4', 'socks5'] = 'http'
    country: str = 'unknown'
    anonymity: Literal['transparent', 'anonymous', 'elite'] = 'transparent'
    source: str
    extracted_at: str
    
    @validator('ip')
    def validate_ip(cls, v):
        """驗證IP地址"""
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f'無效的IP地址: {v}')
    
    @validator('port')
    def validate_port(cls, v):
        """驗證端口"""
        if not 1 <= v <= 65535:
            raise ValueError(f'端口必須在1-65535之間: {v}')
        return v
    
    @validator('protocol')
    def validate_protocol(cls, v):
        """驗證協議"""
        valid_protocols = ['http', 'https', 'socks4', 'socks5']
        if v not in valid_protocols:
            raise ValueError(f'無效的協議: {v}')
        return v

class DataTransformer:
    """數據轉換器"""
    
    def __init__(self):
        self.validation_rules = []
        self.transformation_rules = []
        self.enrichment_services = []
    
    async def transform(self, raw_data: List[Dict[str, Any]]) -> List[ProxyData]:
        """轉換原始數據"""
        transformed_data = []
        
        for item in raw_data:
            try:
                # 1. 數據清洗
                cleaned_data = self._clean_data(item)
                
                # 2. 數據驗證
                validated_data = self._validate_data(cleaned_data)
                
                # 3. 數據豐富化
                enriched_data = await self._enrich_data(validated_data)
                
                # 4. 創建標準化模型
                proxy_data = ProxyData(**enriched_data)
                transformed_data.append(proxy_data)
                
            except Exception as e:
                logger.error(f"數據轉換失敗: {e}, 數據: {item}")
                continue
        
        return transformed_data
    
    def _clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗數據"""
        # 移除空值和多餘空格
        cleaned = {}
        for key, value in data.items():
            if value is not None and str(value).strip():
                cleaned[key] = str(value).strip()
        
        # 標準化字段名稱
        field_mapping = {
            'host': 'ip',
            'hostname': 'ip',
            'proxy_ip': 'ip',
            'proxy_port': 'port',
            'type': 'protocol',
            'proxy_type': 'protocol'
        }
        
        for old_key, new_key in field_mapping.items():
            if old_key in cleaned:
                cleaned[new_key] = cleaned.pop(old_key)
        
        return cleaned
    
    def _validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證數據完整性"""
        # 必需字段檢查
        required_fields = ['ip', 'port']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"缺少必需字段: {field}")
        
        # 端口格式轉換
        if isinstance(data['port'], str):
            try:
                data['port'] = int(data['port'])
            except ValueError:
                raise ValueError(f"無效的端口格式: {data['port']}")
        
        return data
    
    async def _enrich_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """豐富化數據"""
        # IP地理位置查詢
        if data.get('country', 'unknown') == 'unknown':
            geo_info = await self._get_geo_info(data['ip'])
            data.update(geo_info)
        
        # 匿名等級標準化
        if 'anonymity' in data:
            data['anonymity'] = self._normalize_anonymity(data['anonymity'])
        
        return data
    
    async def _get_geo_info(self, ip: str) -> Dict[str, str]:
        """獲取IP地理位置"""
        try:
            # 使用IP地理位置服務
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://ip-api.com/json/{ip}") as response:
                    if response.status == 200:
                        geo_data = await response.json()
                        return {
                            'country': geo_data.get('country', 'unknown'),
                            'city': geo_data.get('city', 'unknown'),
                            'isp': geo_data.get('isp', 'unknown')
                        }
        except Exception as e:
            logger.warning(f"地理位置查詢失敗: {e}")
        
        return {'country': 'unknown', 'city': 'unknown', 'isp': 'unknown'}
    
    def _normalize_anonymity(self, anonymity: str) -> str:
        """標準化匿名等級"""
        anonymity_lower = anonymity.lower()
        
        if 'elite' in anonymity_lower or 'high' in anonymity_lower:
            return 'elite'
        elif 'anonymous' in anonymity_lower or 'medium' in anonymity_lower:
            return 'anonymous'
        else:
            return 'transparent'
```

### 3.2 數據質量評分
```python
class DataQualityScorer:
    """數據質量評分器"""
    
    def __init__(self):
        self.scoring_weights = {
            'completeness': 0.3,    # 完整性
            'accuracy': 0.3,      # 準確性
            'consistency': 0.2,     # 一致性
            'timeliness': 0.2     # 時效性
        }
    
    def calculate_quality_score(self, proxy_data: ProxyData) -> float:
        """計算數據質量評分"""
        scores = {}
        
        # 完整性評分
        scores['completeness'] = self._score_completeness(proxy_data)
        
        # 準確性評分
        scores['accuracy'] = self._score_accuracy(proxy_data)
        
        # 一致性評分
        scores['consistency'] = self._score_consistency(proxy_data)
        
        # 時效性評分
        scores['timeliness'] = self._score_timeliness(proxy_data)
        
        # 加權平均
        total_score = sum(
            scores[dimension] * weight 
            for dimension, weight in self.scoring_weights.items()
        )
        
        return min(1.0, max(0.0, total_score))
    
    def _score_completeness(self, proxy_data: ProxyData) -> float:
        """完整性評分"""
        required_fields = ['ip', 'port', 'protocol']
        optional_fields = ['country', 'anonymity', 'source']
        
        required_complete = all(
            getattr(proxy_data, field) is not None 
            for field in required_fields
        )
        
        optional_complete = sum(
            1 for field in optional_fields 
            if getattr(proxy_data, field) != 'unknown'
        ) / len(optional_fields)
        
        return (1.0 if required_complete else 0.0) * 0.7 + optional_complete * 0.3
    
    def _score_accuracy(self, proxy_data: ProxyData) -> float:
        """準確性評分"""
        score = 1.0
        
        # IP格式驗證
        try:
            ipaddress.ip_address(proxy_data.ip)
        except ValueError:
            score -= 0.5
        
        # 端口範圍驗證
        if not (1 <= proxy_data.port <= 65535):
            score -= 0.3
        
        # 協議格式驗證
        valid_protocols = ['http', 'https', 'socks4', 'socks5']
        if proxy_data.protocol not in valid_protocols:
            score -= 0.2
        
        return max(0.0, score)
    
    def _score_consistency(self, proxy_data: ProxyData) -> float:
        """一致性評分"""
        # 檢查數據格式一致性
        score = 1.0
        
        # IP格式一致性
        if not self._is_valid_ip_format(proxy_data.ip):
            score -= 0.3
        
        # 端口格式一致性
        if not isinstance(proxy_data.port, int):
            score -= 0.2
        
        return max(0.0, score)
    
    def _score_timeliness(self, proxy_data: ProxyData) -> float:
        """時效性評分"""
        try:
            extracted_time = datetime.fromisoformat(proxy_data.extracted_at)
            time_diff = datetime.now() - extracted_time
            
            # 超過24小時的數據扣分
            if time_diff.total_seconds() > 86400:
                return 0.5
            elif time_diff.total_seconds() > 3600:  # 超過1小時
                return 0.8
            else:
                return 1.0
        except:
            return 0.0
    
    def _is_valid_ip_format(self, ip: str) -> bool:
        """檢查IP格式"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False
```

## 4. 數據載入層（Load）

### 4.1 多目標載入策略
```python
class LoadTarget:
    """載入目標配置"""
    
    def __init__(self, target_type: str, connection_config: Dict[str, Any]):
        self.target_type = target_type  # 'redis', 'postgresql', 'clickhouse'
        self.connection_config = connection_config
        self.connection = None
    
    async def connect(self):
        """建立連接"""
        if self.target_type == 'redis':
            import aioredis
            self.connection = await aioredis.create_redis_pool(
                f"redis://{self.connection_config['host']}:{self.connection_config['port']}"
            )
        elif self.target_type == 'postgresql':
            import asyncpg
            self.connection = await asyncpg.connect(
                host=self.connection_config['host'],
                port=self.connection_config['port'],
                user=self.connection_config['user'],
                password=self.connection_config['password'],
                database=self.connection_config['database']
            )
        elif self.target_type == 'clickhouse':
            # ClickHouse連接邏輯
            pass
    
    async def disconnect(self):
        """斷開連接"""
        if self.connection:
            if self.target_type == 'redis':
                self.connection.close()
                await self.connection.wait_closed()
            elif self.target_type == 'postgresql':
                await self.connection.close()

class BaseLoader(ABC):
    """基礎載入器"""
    
    def __init__(self, load_target: LoadTarget):
        self.load_target = load_target
        self.batch_size = 1000
        self.metrics_collector = MetricsCollector()
    
    @abstractmethod
    async def load(self, data: List[ProxyData]) -> bool:
        """載入數據"""
        pass
    
    @abstractmethod
    async def create_schema(self):
        """創建數據架構"""
        pass

class RedisLoader(BaseLoader):
    """Redis載入器"""
    
    async def load(self, data: List[ProxyData]) -> bool:
        """載入數據到Redis"""
        try:
            # 批次處理
            for i in range(0, len(data), self.batch_size):
                batch = data[i:i + self.batch_size]
                await self._load_batch(batch)
            
            return True
        except Exception as e:
            logger.error(f"Redis載入失敗: {e}")
            return False
    
    async def _load_batch(self, batch: List[ProxyData]):
        """載入批次數據"""
        pipe = self.load_target.connection.pipeline()
        
        for proxy in batch:
            # 存儲代理信息
            proxy_key = f"proxy:{proxy.ip}:{proxy.port}"
            proxy_data = proxy.dict()
            
            # 設置代理詳細信息
            pipe.hmset_dict(proxy_key, proxy_data)
            pipe.expire(proxy_key, 3600)  # 1小時過期
            
            # 添加到協議集合
            pipe.sadd(f"proxies:{proxy.protocol}", f"{proxy.ip}:{proxy.port}")
            
            # 添加到國家集合
            if proxy.country != 'unknown':
                pipe.sadd(f"proxies:country:{proxy.country}", f"{proxy.ip}:{proxy.port}")
            
            # 添加到匿名等級集合
            pipe.sadd(f"proxies:anonymity:{proxy.anonymity}", f"{proxy.ip}:{proxy.port}")
        
        await pipe.execute()
    
    async def create_schema(self):
        """Redis不需要預創建架構"""
        pass

class PostgreSQLLoader(BaseLoader):
    """PostgreSQL載入器"""
    
    async def load(self, data: List[ProxyData]) -> bool:
        """載入數據到PostgreSQL"""
        try:
            # 批次插入
            for i in range(0, len(data), self.batch_size):
                batch = data[i:i + self.batch_size]
                await self._insert_batch(batch)
            
            return True
        except Exception as e:
            logger.error(f"PostgreSQL載入失敗: {e}")
            return False
    
    async def _insert_batch(self, batch: List[ProxyData]):
        """批次插入數據"""
        values = [
            (
                proxy.ip,
                proxy.port,
                proxy.protocol,
                proxy.country,
                proxy.anonymity,
                proxy.source,
                proxy.extracted_at
            )
            for proxy in batch
        ]
        
        await self.load_target.connection.executemany("""
            INSERT INTO proxies (ip, port, protocol, country, anonymity, source, extracted_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (ip, port) DO UPDATE SET
                protocol = EXCLUDED.protocol,
                country = EXCLUDED.country,
                anonymity = EXCLUDED.anonymity,
                source = EXCLUDED.source,
                extracted_at = EXCLUDED.extracted_at,
                updated_at = NOW()
        """, values)
    
    async def create_schema(self):
        """創建數據表"""
        await self.load_target.connection.execute("""
            CREATE TABLE IF NOT EXISTS proxies (
                id SERIAL PRIMARY KEY,
                ip INET NOT NULL,
                port INTEGER NOT NULL,
                protocol VARCHAR(10) NOT NULL,
                country VARCHAR(50),
                anonymity VARCHAR(20),
                source VARCHAR(50),
                extracted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(ip, port)
            )
        """)
        
        # 創建索引
        await self.load_target.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_proxies_protocol ON proxies(protocol);
            CREATE INDEX IF NOT EXISTS idx_proxies_country ON proxies(country);
            CREATE INDEX IF NOT EXISTS idx_proxies_anonymity ON proxies(anonymity);
            CREATE INDEX IF NOT EXISTS idx_proxies_extracted_at ON proxies(extracted_at);
        """)
```

### 4.2 載入協調器
```python
class LoadCoordinator:
    """載入協調器"""
    
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.loaders = []
        self.load_balancer = LoadBalancer()
    
    async def initialize_loaders(self):
        """初始化所有載入器"""
        configs = self._load_configs()
        
        for config in configs:
            load_target = LoadTarget(
                target_type=config['type'],
                connection_config=config['connection']
            )
            await load_target.connect()
            
            if config['type'] == 'redis':
                loader = RedisLoader(load_target)
            elif config['type'] == 'postgresql':
                loader = PostgreSQLLoader(load_target)
            else:
                continue
            
            self.loaders.append(loader)
    
    async def load_data(self, data: List[ProxyData]) -> Dict[str, bool]:
        """載入數據到所有目標"""
        results = {}
        
        # 根據負載均衡策略分配數據
        distribution = self.load_balancer.distribute_data(data, len(self.loaders))
        
        # 並行載入
        tasks = []
        for i, loader in enumerate(self.loaders):
            if i < len(distribution):
                task = asyncio.create_task(self._load_with_metrics(loader, distribution[i]))
                tasks.append(task)
        
        load_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 收集結果
        for i, result in enumerate(load_results):
            loader_type = self.loaders[i].load_target.target_type
            if isinstance(result, Exception):
                results[loader_type] = False
                logger.error(f"載入器 {loader_type} 失敗: {result}")
            else:
                results[loader_type] = result
        
        return results
    
    async def _load_with_metrics(self, loader: BaseLoader, data: List[ProxyData]) -> bool:
        """帶指標收集的載入"""
        start_time = datetime.now()
        
        try:
            success = await loader.load(data)
            
            # 記錄指標
            load_time = (datetime.now() - start_time).total_seconds()
            loader.metrics_collector.record_load(
                target_type=loader.load_target.target_type,
                proxy_count=len(data),
                load_time=load_time,
                success=success
            )
            
            return success
            
        except Exception as e:
            logger.error(f"載入異常: {e}")
            return False
```

## 5. ETL 流程編排

### 5.1 主ETL流程
```python
class ETLPipeline:
    """ETL管道主控制器"""
    
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.extraction_coordinator = ExtractionCoordinator(config_file)
        self.data_transformer = DataTransformer()
        self.load_coordinator = LoadCoordinator(config_file)
        self.quality_scorer = DataQualityScorer()
        self.pipeline_metrics = PipelineMetrics()
        self.is_running = False
    
    async def initialize(self):
        """初始化ETL管道"""
        # 初始化提取層
        await self.extraction_coordinator.initialize_extractors()
        
        # 初始化轉換層
        # DataTransformer 不需要額外初始化
        
        # 初始化載入層
        await self.load_coordinator.initialize_loaders()
        
        logger.info("ETL管道初始化完成")
    
    async def run_etl_cycle(self) -> Dict[str, Any]:
        """執行一個ETL週期"""
        start_time = datetime.now()
        cycle_metrics = {
            'start_time': start_time,
            'status': 'running',
            'extraction': {},
            'transformation': {},
            'loading': {},
            'quality_scores': []
        }
        
        try:
            # 1. 提取階段
            logger.info("開始數據提取...")
            raw_data = await self.extraction_coordinator.start_extraction()
            cycle_metrics['extraction'] = {
                'raw_proxy_count': len(raw_data),
                'sources_processed': len(self.extraction_coordinator.extractors),
                'extraction_time': (datetime.now() - start_time).total_seconds()
            }
            
            # 2. 轉換階段
            logger.info("開始數據轉換...")
            transform_start = datetime.now()
            transformed_data = await self.data_transformer.transform(raw_data)
            cycle_metrics['transformation'] = {
                'transformed_proxy_count': len(transformed_data),
                'transformation_time': (datetime.now() - transform_start).total_seconds(),
                'transformation_success_rate': len(transformed_data) / len(raw_data) if raw_data else 0
            }
            
            # 3. 質量評分
            logger.info("開始質量評分...")
            quality_scores = []
            for proxy_data in transformed_data:
                score = self.quality_scorer.calculate_quality_score(proxy_data)
                quality_scores.append(score)
            
            cycle_metrics['quality_scores'] = {
                'scores': quality_scores,
                'average_score': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
                'high_quality_count': sum(1 for s in quality_scores if s >= 0.8)
            }
            
            # 4. 載入階段
            logger.info("開始數據載入...")
            load_start = datetime.now()
            load_results = await self.load_coordinator.load_data(transformed_data)
            cycle_metrics['loading'] = {
                'load_results': load_results,
                'load_time': (datetime.now() - load_start).total_seconds(),
                'successful_loads': sum(1 for success in load_results.values() if success)
            }
            
            # 5. 更新總體指標
            cycle_metrics['status'] = 'completed'
            cycle_metrics['total_time'] = (datetime.now() - start_time).total_seconds()
            
            # 記錄管道指標
            self.pipeline_metrics.record_cycle(cycle_metrics)
            
            logger.info(f"ETL週期完成，耗時: {cycle_metrics['total_time']:.2f}秒")
            return cycle_metrics
            
        except Exception as e:
            cycle_metrics['status'] = 'failed'
            cycle_metrics['error'] = str(e)
            cycle_metrics['total_time'] = (datetime.now() - start_time).total_seconds()
            
            logger.error(f"ETL週期失敗: {e}")
            return cycle_metrics
    
    async def start_continuous_etl(self, interval_minutes: int = 30):
        """啟動持續ETL流程"""
        self.is_running = True
        logger.info(f"啟動持續ETL流程，間隔: {interval_minutes}分鐘")
        
        while self.is_running:
            try:
                # 執行ETL週期
                metrics = await self.run_etl_cycle()
                
                # 記錄性能指標
                logger.info(f"ETL週期完成: {metrics}")
                
                # 等待下一個週期
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"ETL週期異常: {e}")
                await asyncio.sleep(60)  # 等待1分鐘後重試
    
    def stop_continuous_etl(self):
        """停止持續ETL流程"""
        self.is_running = False
        logger.info("ETL流程已停止")
```

### 5.2 監控與告警
```python
class PipelineMetrics:
    """管道指標收集器"""
    
    def __init__(self):
        self.metrics = {
            'total_cycles': 0,
            'successful_cycles': 0,
            'failed_cycles': 0,
            'average_extraction_time': 0,
            'average_transformation_time': 0,
            'average_load_time': 0,
            'total_proxies_extracted': 0,
            'total_proxies_loaded': 0,
            'average_quality_score': 0
        }
    
    def record_cycle(self, cycle_metrics: Dict[str, Any]):
        """記錄ETL週期指標"""
        self.metrics['total_cycles'] += 1
        
        if cycle_metrics['status'] == 'completed':
            self.metrics['successful_cycles'] += 1
        else:
            self.metrics['failed_cycles'] += 1
        
        # 更新平均時間
        if 'extraction_time' in cycle_metrics['extraction']:
            self._update_average('average_extraction_time', 
                               cycle_metrics['extraction']['extraction_time'])
        
        if 'transformation_time' in cycle_metrics['transformation']:
            self._update_average('average_transformation_time',
                               cycle_metrics['transformation']['transformation_time'])
        
        if 'load_time' in cycle_metrics['loading']:
            self._update_average('average_load_time',
                               cycle_metrics['loading']['load_time'])
        
        # 更新數據量指標
        self.metrics['total_proxies_extracted'] += \
            cycle_metrics['extraction'].get('raw_proxy_count', 0)
        self.metrics['total_proxies_loaded'] += \
            cycle_metrics['transformation'].get('transformed_proxy_count', 0)
        
        # 更新質量評分
        if 'quality_scores' in cycle_metrics:
            avg_score = cycle_metrics['quality_scores'].get('average_score', 0)
            self._update_average('average_quality_score', avg_score)
    
    def _update_average(self, metric_name: str, new_value: float):
        """更新平均值"""
        if self.metrics['total_cycles'] == 1:
            self.metrics[metric_name] = new_value
        else:
            # 移動平均
            old_avg = self.metrics[metric_name]
            n = self.metrics['total_cycles']
            self.metrics[metric_name] = old_avg + (new_value - old_avg) / n
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """獲取指標摘要"""
        success_rate = (self.metrics['successful_cycles'] / 
                       self.metrics['total_cycles'] * 100 
                       if self.metrics['total_cycles'] > 0 else 0)
        
        return {
            'success_rate': success_rate,
            'total_cycles': self.metrics['total_cycles'],
            'performance_metrics': {
                'average_extraction_time': self.metrics['average_extraction_time'],
                'average_transformation_time': self.metrics['average_transformation_time'],
                'average_load_time': self.metrics['average_load_time'],
                'total_processing_time': (self.metrics['average_extraction_time'] + 
                                        self.metrics['average_transformation_time'] + 
                                        self.metrics['average_load_time'])
            },
            'data_metrics': {
                'total_proxies_extracted': self.metrics['total_proxies_extracted'],
                'total_proxies_loaded': self.metrics['total_proxies_loaded'],
                'extraction_to_load_ratio': (self.metrics['total_proxies_loaded'] / 
                                           self.metrics['total_proxies_extracted'] * 100
                                           if self.metrics['total_proxies_extracted'] > 0 else 0),
                'average_quality_score': self.metrics['average_quality_score']
            }
        }
```

## 6. 配置管理

### 6.1 ETL配置文件
```yaml
# etl_config.yaml
etl:
  cycle_interval_minutes: 30
  batch_size: 1000
  
extraction:
  sources:
    - name: "free-proxy-list"
      type: "api"
      url: "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
      rate_limit: 60
      timeout: 30
      retry_count: 3
      
    - name: "proxy-daily"
      type: "web_scraping"
      url: "https://www.proxy-list.download/HTTP"
      method: "table"
      rate_limit: 30
      timeout: 45
      
    - name: "geonode-proxy"
      type: "api"
      url: "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"
      rate_limit: 120
      timeout: 30

transformation:
  validation_rules:
    - required_fields: ["ip", "port"]
    - ip_format_validation: true
    - port_range_validation: [1, 65535]
    - protocol_validation: ["http", "https", "socks4", "socks5"]
  
  enrichment:
    geo_location: true
    anonymity_normalization: true
    
  quality_scoring:
    weights:
      completeness: 0.3
      accuracy: 0.3
      consistency: 0.2
      timeliness: 0.2

loading:
  targets:
    - type: "redis"
      connection:
        host: "localhost"
        port: 6379
        db: 0
      enabled: true
      
    - type: "postgresql"
      connection:
        host: "localhost"
        port: 5432
        database: "proxy_pool"
        user: "postgres"
        password: "password"
      enabled: true
      
    - type: "clickhouse"
      connection:
        host: "localhost"
        port: 8123
        database: "proxy_analytics"
      enabled: false

monitoring:
  metrics_collection: true
  alerting:
    enabled: true
    thresholds:
      success_rate: 0.8
      quality_score: 0.6
      processing_time: 300  # 秒
```

## 7. 錯誤處理與恢復

### 7.1 錯誤分類與處理策略
```python
class ETLExceptionHandler:
    """ETL異常處理器"""
    
    def __init__(self):
        self.error_strategies = {
            'network_error': self._handle_network_error,
            'data_validation_error': self._handle_validation_error,
            'database_error': self._handle_database_error,
            'rate_limit_error': self._handle_rate_limit_error,
            'timeout_error': self._handle_timeout_error
        }
        self.error_counts = defaultdict(int)
        self.circuit_breakers = {}
    
    async def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """處理ETL錯誤"""
        error_type = self._classify_error(error)
        self.error_counts[error_type] += 1
        
        # 檢查熔斷器
        if self._should_circuit_break(error_type):
            return {
                'action': 'circuit_break',
                'message': f'{error_type} 觸發熔斷器',
                'retry_after': 300  # 5分鐘後重試
            }
        
        # 執行錯誤處理策略
        handler = self.error_strategies.get(error_type)
        if handler:
            return await handler(error, context)
        else:
            return await self._handle_unknown_error(error, context)
    
    def _classify_error(self, error: Exception) -> str:
        """分類錯誤"""
        error_msg = str(error).lower()
        
        if any(keyword in error_msg for keyword in ['connection', 'network', 'timeout']):
            return 'network_error'
        elif any(keyword in error_msg for keyword in ['validation', 'invalid', 'format']):
            return 'data_validation_error'
        elif any(keyword in error_msg for keyword in ['database', 'sql', 'constraint']):
            return 'database_error'
        elif any(keyword in error_msg for keyword in ['rate limit', 'too many', 'quota']):
            return 'rate_limit_error'
        else:
            return 'unknown_error'
    
    def _should_circuit_break(self, error_type: str) -> bool:
        """檢查是否需要熔斷"""
        error_count = self.error_counts[error_type]
        
        # 同一類型錯誤超過10次觸發熔斷
        return error_count >= 10
    
    async def _handle_network_error(self, error: Exception, context: Dict) -> Dict:
        """處理網絡錯誤"""
        return {
            'action': 'retry_with_backoff',
            'retry_count': 3,
            'backoff_strategy': 'exponential',
            'message': '網絡錯誤，將使用指數退避重試'
        }
    
    async def _handle_validation_error(self, error: Exception, context: Dict) -> Dict:
        """處理驗證錯誤"""
        return {
            'action': 'skip_and_log',
            'message': '數據驗證失敗，跳過該記錄並記錄日誌',
            'log_level': 'warning'
        }
    
    async def _handle_database_error(self, error: Exception, context: Dict) -> Dict:
        """處理數據庫錯誤"""
        return {
            'action': 'retry_with_delay',
            'retry_count': 2,
            'delay': 30,  # 30秒後重試
            'message': '數據庫錯誤，將延遲重試'
        }
    
    async def _handle_rate_limit_error(self, error: Exception, context: Dict) -> Dict:
        """處理速率限制錯誤"""
        return {
            'action': 'delay_and_retry',
            'delay': 600,  # 10分鐘後重試
            'message': '觸發速率限制，將延遲後重試'
        }
    
    async def _handle_timeout_error(self, error: Exception, context: Dict) -> Dict:
        """處理超時錯誤"""
        return {
            'action': 'increase_timeout_and_retry',
            'timeout_multiplier': 1.5,
            'retry_count': 2,
            'message': '請求超時，將增加超時時間後重試'
        }
    
    async def _handle_unknown_error(self, error: Exception, context: Dict) -> Dict:
        """處理未知錯誤"""
        return {
            'action': 'log_and_continue',
            'message': f'未知錯誤: {str(error)}，記錄後繼續',
            'log_level': 'error'
        }
```

## 8. 性能優化

### 8.1 並行處理優化
```python
class ParallelProcessor:
    """並行處理器"""
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)
        
    async def process_batch(self, items: List[Any], process_func) -> List[Any]:
        """並行處理批次"""
        tasks = []
        
        for item in items:
            task = asyncio.create_task(self._process_with_semaphore(item, process_func))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 過濾異常結果
        valid_results = [r for r in results if not isinstance(r, Exception)]
        
        return valid_results
    
    async def _process_with_semaphore(self, item: Any, process_func):
        """使用信號量控制並行度"""
        async with self.semaphore:
            return await process_func(item)
```

### 8.2 內存管理
```python
class MemoryManager:
    """內存管理器"""
    
    def __init__(self, max_memory_mb: int = 500):
        self.max_memory_mb = max_memory_mb
        self.cleanup_threshold = 0.8
        
    def should_cleanup(self) -> bool:
        """檢查是否需要清理內存"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        return memory_mb > self.max_memory_mb * self.cleanup_threshold
    
    def cleanup_memory(self):
        """清理內存"""
        import gc
        gc.collect()
        logger.info("執行內存清理")
```

這個ETL架構規格書提供了完整的數據處理流程設計，從多源數據提取到智能轉換，再到多目標載入，並包含了完整的監控、錯誤處理和性能優化機制。架構支持高併發、容錯處理和可擴展性設計。