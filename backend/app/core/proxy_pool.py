"""
代理池管理器
提供代理服務器的收集、驗證、管理和分發功能
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import random
import json
from pathlib import Path
import aiohttp
from sqlalchemy import text

from .database_manager import get_db_manager, DatabaseType
from .config_manager import get_config
from .metrics_collector import get_metrics_collector


@dataclass
class ProxyInfo:
    """代理服務器信息"""
    id: Optional[int] = None
    host: str = ""
    port: int = 0
    protocol: str = "http"  # http, https, socks4, socks5
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    anonymity: str = "transparent"  # transparent, anonymous, elite
    speed: Optional[float] = None  # 響應時間（秒）
    uptime: float = 0.0  # 可用性百分比
    last_checked: Optional[datetime] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source: str = "unknown"  # 來源標識
    tags: Set[str] = field(default_factory=set)


@dataclass
class ProxyValidationResult:
    """代理驗證結果"""
    proxy: ProxyInfo
    is_valid: bool
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    checked_at: datetime = field(default_factory=datetime.now)


class ProxyPoolManager:
    """代理池管理器"""
    
    def __init__(self):
        self.config = get_config()
        self.db_manager = None
        self.metrics = get_metrics_collector()
        self.logger = logging.getLogger(__name__)
        
        # 內存中的代理緩存
        self._proxy_cache: Dict[str, ProxyInfo] = {}
        self._active_proxies: List[ProxyInfo] = []
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=5)
        
        # 延遲初始化數據庫管理器
        self._initialized = False
    
    async def _init_database(self):
        """初始化代理池數據庫表"""
        try:
            # 獲取數據庫管理器
            self.db_manager = get_db_manager()
            
            if self.config.database.type == "sqlite":
                await self._init_sqlite_tables()
            elif self.config.database.type == "postgresql":
                await self._init_postgresql_tables()
            
            self.logger.info("代理池數據庫表初始化完成")
        except Exception as e:
            self.logger.error(f"初始化代理池數據庫表失敗: {e}")
            raise
    
    async def _init_sqlite_tables(self):
        """初始化SQLite表"""
        async with self.db_manager.get_session() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS proxy_servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    protocol TEXT DEFAULT 'http',
                    country TEXT,
                    region TEXT,
                    city TEXT,
                    anonymity TEXT DEFAULT 'transparent',
                    speed REAL,
                    uptime REAL DEFAULT 0.0,
                    last_checked TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source TEXT DEFAULT 'unknown',
                    tags TEXT DEFAULT '[]',
                    UNIQUE(host, port)
                )
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_proxy_active ON proxy_servers(is_active);
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_proxy_protocol ON proxy_servers(protocol);
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_proxy_country ON proxy_servers(country);
            """))
            
            await session.commit()
    
    async def _init_postgresql_tables(self):
        """初始化PostgreSQL表"""
        async with self.db_manager.get_session() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS proxy_servers (
                    id SERIAL PRIMARY KEY,
                    host VARCHAR(255) NOT NULL,
                    port INTEGER NOT NULL,
                    protocol VARCHAR(10) DEFAULT 'http',
                    country VARCHAR(2),
                    region VARCHAR(100),
                    city VARCHAR(100),
                    anonymity VARCHAR(20) DEFAULT 'transparent',
                    speed NUMERIC(8,3),
                    uptime NUMERIC(5,2) DEFAULT 0.0,
                    last_checked TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source VARCHAR(50) DEFAULT 'unknown',
                    tags JSONB DEFAULT '[]'::jsonb,
                    UNIQUE(host, port)
                )
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_proxy_active ON proxy_servers(is_active);
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_proxy_protocol ON proxy_servers(protocol);
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_proxy_country ON proxy_servers(country);
            """))
            
            await session.commit()
    
    async def add_proxy(self, proxy: ProxyInfo) -> bool:
        """添加代理到池中"""
        try:
            # 延遲初始化數據庫
            if not self._initialized:
                await self._init_database()
                self._initialized = True
            
            # 檢查是否已存在
            if await self._proxy_exists(proxy.host, proxy.port):
                self.logger.warning(f"代理已存在: {proxy.host}:{proxy.port}")
                return False
            
            # 插入數據庫
            success = await self._insert_proxy(proxy)
            if success:
                self.logger.info(f"添加代理成功: {proxy.host}:{proxy.port}")
                self.metrics.increment("proxy_added_total", {"source": proxy.source})
                # 清除緩存
                self._clear_cache()
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"添加代理失敗: {e}")
            return False
    
    async def _proxy_exists(self, host: str, port: int) -> bool:
        """檢查代理是否已存在"""
        try:
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    text("SELECT COUNT(*) FROM proxy_servers WHERE host = :host AND port = :port"),
                    {"host": host, "port": port}
                )
                count = result.scalar()
                return count > 0
        except Exception as e:
            self.logger.error(f"檢查代理存在性失敗: {e}")
            return False
    
    async def _insert_proxy(self, proxy: ProxyInfo) -> bool:
        """插入代理到數據庫"""
        try:
            async with self.db_manager.get_session() as session:
                tags_json = json.dumps(list(proxy.tags)) if proxy.tags else "[]"
                
                if self.config.database.type == "sqlite":
                    await session.execute(
                        text("""
                            INSERT INTO proxy_servers 
                            (host, port, protocol, country, region, city, anonymity, 
                             speed, uptime, last_checked, is_active, source, tags)
                            VALUES (:host, :port, :protocol, :country, :region, :city, :anonymity, 
                                    :speed, :uptime, :last_checked, :is_active, :source, :tags)
                        """),
                        {
                            "host": proxy.host, "port": proxy.port, "protocol": proxy.protocol,
                            "country": proxy.country, "region": proxy.region, "city": proxy.city,
                            "anonymity": proxy.anonymity, "speed": proxy.speed,
                            "uptime": proxy.uptime, "last_checked": proxy.last_checked,
                            "is_active": proxy.is_active, "source": proxy.source, "tags": tags_json
                        }
                    )
                else:  # postgresql
                    await session.execute(
                        text("""
                            INSERT INTO proxy_servers 
                            (host, port, protocol, country, region, city, anonymity, 
                             speed, uptime, last_checked, is_active, source, tags)
                            VALUES (:host, :port, :protocol, :country, :region, :city, :anonymity, 
                                    :speed, :uptime, :last_checked, :is_active, :source, :tags)
                        """),
                        {
                            "host": proxy.host, "port": proxy.port, "protocol": proxy.protocol,
                            "country": proxy.country, "region": proxy.region, "city": proxy.city,
                            "anonymity": proxy.anonymity, "speed": proxy.speed,
                            "uptime": proxy.uptime, "last_checked": proxy.last_checked,
                            "is_active": proxy.is_active, "source": proxy.source, "tags": tags_json
                        }
                    )
                
                await session.commit()
                return True
        except Exception as e:
            self.logger.error(f"插入代理失敗: {e}")
            return False
    
    async def get_proxy(self, protocol: str = "http", country: str = None, 
                       anonymity: str = None) -> Optional[ProxyInfo]:
        """獲取一個代理"""
        try:
            # 獲取活動代理列表
            proxies = await self.get_active_proxies(protocol, country, anonymity)
            
            if not proxies:
                self.logger.warning(f"沒有可用的代理: protocol={protocol}, country={country}")
                return None
            
            # 隨機選擇一個代理
            proxy = random.choice(proxies)
            
            # 更新使用統計
            self.metrics.increment("proxy_used_total", {
                "protocol": protocol,
                "country": country or "any",
                "anonymity": anonymity or "any"
            })
            
            return proxy
        except Exception as e:
            self.logger.error(f"獲取代理失敗: {e}")
            return None
    
    async def get_proxy_by_host_port(self, host: str, port: int) -> Optional[ProxyInfo]:
        """根據 host 和 port 獲取指定代理
        
        Args:
            host: 主機地址
            port: 端口
            
        Returns:
            Optional[ProxyInfo]: 代理信息，不存在則返回 None
        """
        try:
            # 確保數據庫已初始化
            if not self._initialized:
                await self._init_database()
            
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    text("SELECT * FROM proxy_servers WHERE host = :host AND port = :port"),
                    {"host": host, "port": port}
                )
                row = result.fetchone()
                if row:
                    return self._row_to_proxy(row)
                
                return None
            
        except Exception as e:
            self.logger.error(f"根據 host/port 獲取代理失敗: {e}")
            return None
    
    async def get_active_proxies(self, protocol: str = None, country: str = None, 
                                anonymity: str = None) -> List[ProxyInfo]:
        """獲取活動代理列表
        
        Args:
            protocol: 協議過濾 (http, https, socks4, socks5)
            country: 國家過濾
            anonymity: 匿名級別過濾
            
        Returns:
            List[ProxyInfo]: 活動代理列表
        """
        try:
            # 確保數據庫已初始化
            if not self._initialized:
                await self._init_database()
                self._initialized = True
            
            # 檢查緩存是否有效
            if self._is_cache_valid() and not any([protocol, country, anonymity]):
                return self._active_proxies.copy()
            
            # 從數據庫查詢
            proxies = await self._query_proxies(protocol, country, anonymity)
            
            # 更新緩存
            if not any([protocol, country, anonymity]):
                self._active_proxies = proxies.copy()
                self._cache_timestamp = datetime.now()
            
            return proxies
        except Exception as e:
            self.logger.error(f"獲取活動代理列表失敗: {e}")
            return []
    
    def _is_cache_valid(self) -> bool:
        """檢查緩存是否有效"""
        if self._cache_timestamp is None:
            return False
        return datetime.now() - self._cache_timestamp < self._cache_ttl
    
    def _clear_cache(self):
        """清除緩存"""
        self._active_proxies.clear()
        self._cache_timestamp = None
    
    async def _query_proxies(self, protocol: str = None, country: str = None, 
                           anonymity: str = None) -> List[ProxyInfo]:
        """從數據庫查詢代理"""
        try:
            async with self.db_manager.get_session() as session:
                # 構建查詢
                query = "SELECT * FROM proxy_servers WHERE is_active = 1"
                params = {}
                
                if protocol:
                    query += " AND protocol = :protocol"
                    params["protocol"] = protocol
                
                if country:
                    query += " AND country = :country"
                    params["country"] = country
                
                if anonymity:
                    query += " AND anonymity = :anonymity"
                    params["anonymity"] = anonymity
                
                query += " ORDER BY uptime DESC, speed ASC"
                
                result = await session.execute(text(query), params)
                rows = result.fetchall()
                
                # 轉換為ProxyInfo對象
                proxies = []
                for row in rows:
                    proxy = self._row_to_proxy(row)
                    if proxy:
                        proxies.append(proxy)
                
                return proxies
        except Exception as e:
            self.logger.error(f"查詢代理失敗: {e}")
            return []
    
    def _row_to_proxy(self, row) -> Optional[ProxyInfo]:
        """將數據庫行轉換為ProxyInfo對象"""
        try:
            # 根據數據庫類型處理不同的列順序
            if self.config.database.type == "sqlite":
                return ProxyInfo(
                    id=row[0],
                    host=row[1],
                    port=row[2],
                    protocol=row[3],
                    country=row[4],
                    region=row[5],
                    city=row[6],
                    anonymity=row[7],
                    speed=row[8],
                    uptime=row[9] or 0.0,
                    last_checked=row[10],
                    is_active=bool(row[11]),
                    created_at=row[12],
                    updated_at=row[13],
                    source=row[14],
                    tags=set(json.loads(row[15]) if row[15] else [])
                )
            else:  # postgresql
                return ProxyInfo(
                    id=row[0],
                    host=row[1],
                    port=row[2],
                    protocol=row[3],
                    country=row[4],
                    region=row[5],
                    city=row[6],
                    anonymity=row[7],
                    speed=row[8],
                    uptime=row[9] or 0.0,
                    last_checked=row[10],
                    is_active=bool(row[11]),
                    created_at=row[12],
                    updated_at=row[13],
                    source=row[14],
                    tags=set(row[15]) if row[15] else set()
                )
        except Exception as e:
            self.logger.error(f"轉換代理數據失敗: {e}")
            return None
    
    async def validate_proxy(self, proxy: ProxyInfo, test_url: str = "http://httpbin.org/ip") -> ProxyValidationResult:
        """驗證代理的有效性"""
        import aiohttp
        import asyncio
        
        start_time = datetime.now()
        
        try:
            # 設置代理
            proxy_url = f"{proxy.protocol}://{proxy.host}:{proxy.port}"
            
            # 創建連接器
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(timeout=timeout, connector=connector, trust_env=True) as session:
                # 測試請求
                test_urls = ["http://httpbin.org/ip", "https://httpbin.org/ip"]
                
                for test_url in test_urls:
                    try:
                        async with session.get(
                            test_url,
                            proxy=proxy_url,
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                response_time = (datetime.now() - start_time).total_seconds()
                                
                                # 更新代理信息
                                proxy.speed = response_time
                                proxy.last_checked = datetime.now()
                                proxy.is_active = True
                                
                                # 更新數據庫
                                await self._update_proxy_status(proxy)
                                
                                self.logger.info(f"代理驗證成功: {proxy.host}:{proxy.port} ({response_time:.2f}s)")
                                self.metrics.increment("proxy_validation_success_total")
                                
                                return ProxyValidationResult(proxy, True, response_time)
                    except Exception:
                        continue
                
                # 所有測試都失敗
                proxy.is_active = False
                await self._update_proxy_status(proxy)
                
                self.logger.warning(f"代理驗證失敗: {proxy.host}:{proxy.port} (所有測試請求都失敗)")
                self.metrics.increment("proxy_validation_failure_total")
                
                return ProxyValidationResult(proxy, False, None, "所有測試請求都失敗")
        
        except Exception as e:
            proxy.is_active = False
            await self._update_proxy_status(proxy)
            
            error_message = f"代理驗證錯誤: {proxy.host}:{proxy.port} - {e}"
            self.logger.error(error_message)
            self.metrics.increment("proxy_validation_error_total")
            
            return ProxyValidationResult(proxy, False, None, error_message)
    
    async def update_proxy_status(self, proxy_info: ProxyInfo) -> bool:
        """更新代理狀態
        
        Args:
            proxy_info: 代理信息
            
        Returns:
            bool: 是否更新成功
        """
        try:
            # 確保數據庫已初始化
            if not self._initialized:
                await self._init_database()
            
            async with self.db_manager.get_session() as session:
                await session.execute(
                    text("""UPDATE proxy_pool 
                           SET is_active = :is_active, success_rate = :success_rate, 
                               response_time = :response_time, last_checked = :last_checked, 
                               updated_at = :updated_at
                           WHERE ip = :ip AND port = :port"""),
                    {
                        'is_active': proxy_info.is_active, 'success_rate': proxy_info.success_rate,
                        'response_time': proxy_info.response_time, 'last_checked': proxy_info.last_checked,
                        'updated_at': datetime.now(), 'ip': proxy_info.ip, 'port': proxy_info.port
                    }
                )
                await session.commit()
            
            logger.info(f"更新代理狀態成功: {proxy_info.ip}:{proxy_info.port}")
            return True
            
        except Exception as e:
            logger.error(f"更新代理狀態失敗: {str(e)}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """獲取代理池統計信息"""
        try:
            # 確保數據庫已初始化
            if not self._initialized:
                await self._init_database()
            
            async with self.db_manager.get_session() as session:
                # 總代理數
                result = await session.execute(text("SELECT COUNT(*) FROM proxy_servers"))
                total_proxies = result.scalar()
                
                # 活動代理數
                result = await session.execute(text("SELECT COUNT(*) FROM proxy_servers WHERE is_active = 1"))
                active_proxies = result.scalar()
                
                # 按協議統計
                result = await session.execute(text("""
                    SELECT protocol, COUNT(*) as count 
                    FROM proxy_servers 
                    WHERE is_active = 1 
                    GROUP BY protocol
                """))
                protocol_stats = dict(result.fetchall())
                
                # 按國家統計
                result = await session.execute(text("""
                    SELECT country, COUNT(*) as count 
                    FROM proxy_servers 
                    WHERE is_active = 1 AND country IS NOT NULL
                    GROUP BY country
                    ORDER BY count DESC
                    LIMIT 10
                """))
                country_stats = dict(result.fetchall())
                
                # 平均速度
                result = await session.execute(text("SELECT AVG(speed) FROM proxy_servers WHERE is_active = 1 AND speed IS NOT NULL"))
                avg_speed = result.scalar() or 0
                
                return {
                    "total_proxies": total_proxies,
                    "active_proxies": active_proxies,
                    "inactive_proxies": total_proxies - active_proxies,
                    "availability_rate": (active_proxies / total_proxies * 100) if total_proxies > 0 else 0,
                    "protocol_distribution": protocol_stats,
                    "top_countries": country_stats,
                    "average_speed": round(avg_speed, 3) if avg_speed else None
                }
        except Exception as e:
            self.logger.error(f"獲取代理統計失敗: {e}")
            return {}
    
    async def cleanup_inactive_proxies(self, days: int = 7) -> int:
        """清理不活動的代理"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            async with self.db_manager.get_session() as session:
                if self.config.database.type == "sqlite":
                    result = await session.execute(
                        text("""
                            DELETE FROM proxy_servers 
                            WHERE is_active = 0 AND (last_checked < :cutoff_date OR last_checked IS NULL)
                        """),
                        {'cutoff_date': cutoff_date}
                    )
                else:  # postgresql
                    result = await session.execute(
                        text("""
                            DELETE FROM proxy_servers 
                            WHERE is_active = FALSE AND (last_checked < :cutoff_date OR last_checked IS NULL)
                        """),
                        {'cutoff_date': cutoff_date}
                    )
                
                deleted_count = result.rowcount
                await session.commit()
            
            self.logger.info(f"清理了 {deleted_count} 個不活動代理")
            self._clear_cache()
            
            return deleted_count
        except Exception as e:
            self.logger.error(f"清理不活動代理失敗: {e}")
            return 0


# 全局代理池管理器實例
_proxy_pool_manager: Optional[ProxyPoolManager] = None


async def get_proxy_pool_manager() -> ProxyPoolManager:
    """獲取全局代理池管理器實例
    
    Returns:
        ProxyPoolManager: 代理池管理器實例
    """
    global _proxy_pool_manager
    if _proxy_pool_manager is None:
        _proxy_pool_manager = ProxyPoolManager()
        # 確保數據庫管理器已初始化
        db_manager = get_db_manager()
        if not db_manager._initialized:
            await db_manager.initialize()
        await _proxy_pool_manager._init_database()
    return _proxy_pool_manager