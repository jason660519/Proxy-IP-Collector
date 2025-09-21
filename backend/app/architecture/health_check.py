"""
統一健康檢查實現
提供標準化的健康檢查機制
"""
import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import aiohttp
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class HealthCheckResult:
    """健康檢查結果"""
    
    def __init__(self, name: str, status: str, message: str = "", 
                 response_time: Optional[float] = None, details: Optional[Dict] = None):
        self.name = name
        self.status = status
        self.message = message
        self.response_time = response_time
        self.details = details or {}
        self.checked_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "response_time": self.response_time,
            "details": self.details,
            "checked_at": self.checked_at
        }


class BaseHealthCheck:
    """基礎健康檢查類"""
    
    def __init__(self, name: str, timeout: float = 5.0, 
                 critical: bool = True, retry_count: int = 1):
        """
        初始化健康檢查
        
        Args:
            name: 檢查名稱
            timeout: 超時時間（秒）
            critical: 是否為關鍵檢查
            retry_count: 重試次數
        """
        self.name = name
        self.timeout = timeout
        self.critical = critical
        self.retry_count = retry_count
    
    async def check(self) -> HealthCheckResult:
        """執行健康檢查"""
        start_time = time.time()
        
        try:
            for attempt in range(self.retry_count):
                try:
                    result = await self._perform_check()
                    result.response_time = time.time() - start_time
                    return result
                    
                except Exception as e:
                    if attempt < self.retry_count - 1:
                        logger.warning(f"{self.name} 檢查失敗 (嘗試 {attempt + 1}/{self.retry_count}): {e}")
                        await asyncio.sleep(0.5)  # 短暫延遲後重試
                    else:
                        raise
            
        except asyncio.TimeoutError:
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                message=f"檢查超時 ({self.timeout}秒)",
                response_time=time.time() - start_time
            )
        
        except Exception as e:
            logger.error(f"{self.name} 健康檢查異常: {e}")
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                message=f"檢查異常: {str(e)}",
                response_time=time.time() - start_time
            )
    
    async def _perform_check(self) -> HealthCheckResult:
        """執行具體的檢查邏輯（子類實現）"""
        raise NotImplementedError("子類必須實現此方法")


class DatabaseHealthCheck(BaseHealthCheck):
    """數據庫健康檢查"""
    
    def __init__(self, timeout: float = 3.0):
        super().__init__("database", timeout, critical=True)
    
    async def _perform_check(self) -> HealthCheckResult:
        """檢查數據庫連接"""
        try:
            from app.core.database import get_db
            
            # 測試數據庫連接
            async for db in get_db():
                # 執行簡單的查詢測試
                result = await db.execute("SELECT 1")
                await result.fetchone()
                
                return HealthCheckResult(
                    name=self.name,
                    status="healthy",
                    message="數據庫連接正常",
                    details={"database_url": settings.DATABASE_URL.split("@")[-1]}  # 移除敏感信息
                )
                
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                message=f"數據庫連接失敗: {str(e)}",
                details={"error_type": type(e).__name__}
            )


class RedisHealthCheck(BaseHealthCheck):
    """Redis健康檢查"""
    
    def __init__(self, timeout: float = 2.0):
        super().__init__("redis", timeout, critical=False)
    
    async def _perform_check(self) -> HealthCheckResult:
        """檢查Redis連接"""
        try:
            import aioredis
            
            redis = aioredis.from_url(settings.REDIS_URL)
            
            # 測試Redis連接
            await redis.ping()
            
            # 獲取Redis信息
            info = await redis.info()
            
            await redis.close()
            
            return HealthCheckResult(
                name=self.name,
                status="healthy",
                message="Redis連接正常",
                details={
                    "redis_version": info.get("redis_version", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "unknown")
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                message=f"Redis連接失敗: {str(e)}",
                details={"error_type": type(e).__name__}
            )


class APIHealthCheck(BaseHealthCheck):
    """API服務健康檢查"""
    
    def __init__(self, timeout: float = 2.0):
        super().__init__("api", timeout, critical=True)
    
    async def _perform_check(self) -> HealthCheckResult:
        """檢查API服務狀態"""
        try:
            # 檢查API端點響應
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                # 測試根端點
                async with session.get(f"http://localhost:{settings.PORT}/") as response:
                    if response.status == 200:
                        return HealthCheckResult(
                            name=self.name,
                            status="healthy",
                            message="API服務響應正常",
                            details={"response_status": response.status}
                        )
                    else:
                        return HealthCheckResult(
                            name=self.name,
                            status="degraded",
                            message=f"API服務響應異常 (狀態碼: {response.status})",
                            details={"response_status": response.status}
                        )
                        
        except asyncio.TimeoutError:
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                message=f"API服務超時 ({self.timeout}秒)"
            )
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                message=f"API服務檢查失敗: {str(e)}",
                details={"error_type": type(e).__name__}
            )


class MemoryHealthCheck(BaseHealthCheck):
    """內存使用健康檢查"""
    
    def __init__(self, timeout: float = 1.0, max_memory_percent: float = 90.0):
        super().__init__("memory", timeout, critical=False)
        self.max_memory_percent = max_memory_percent
    
    async def _perform_check(self) -> HealthCheckResult:
        """檢查內存使用情況"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            if memory_percent < self.max_memory_percent:
                status = "healthy"
                message = f"內存使用正常 ({memory_percent:.1f}%)"
            else:
                status = "warning"
                message = f"內存使用過高 ({memory_percent:.1f}%)"
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details={
                    "memory_percent": memory_percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "memory_total_gb": memory.total / (1024**3),
                    "threshold_percent": self.max_memory_percent
                }
            )
            
        except ImportError:
            return HealthCheckResult(
                name=self.name,
                status="unknown",
                message="無法檢查內存使用 (缺少psutil庫)"
            )
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                message=f"內存檢查失敗: {str(e)}"
            )


class DiskHealthCheck(BaseHealthCheck):
    """磁盤空間健康檢查"""
    
    def __init__(self, timeout: float = 1.0, max_disk_percent: float = 85.0):
        super().__init__("disk", timeout, critical=False)
        self.max_disk_percent = max_disk_percent
    
    async def _perform_check(self) -> HealthCheckResult:
        """檢查磁盤空間"""
        try:
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            if disk_percent < self.max_disk_percent:
                status = "healthy"
                message = f"磁盤空間正常 ({disk_percent:.1f}%)"
            else:
                status = "warning"
                message = f"磁盤空間不足 ({disk_percent:.1f}%)"
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details={
                    "disk_percent": disk_percent,
                    "disk_free_gb": disk.free / (1024**3),
                    "disk_total_gb": disk.total / (1024**3),
                    "threshold_percent": self.max_disk_percent
                }
            )
            
        except ImportError:
            return HealthCheckResult(
                name=self.name,
                status="unknown",
                message="無法檢查磁盤空間 (缺少psutil庫)"
            )
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                message=f"磁盤檢查失敗: {str(e)}"
            )


class UnifiedHealthChecker:
    """統一健康檢查器"""
    
    def __init__(self):
        self.checks: List[BaseHealthCheck] = []
        self._setup_default_checks()
    
    def _setup_default_checks(self):
        """設置默認檢查項"""
        # 添加關鍵檢查項
        self.add_check(DatabaseHealthCheck())
        self.add_check(APIHealthCheck())
        
        # 添加可選檢查項
        self.add_check(RedisHealthCheck())
        
        # 添加系統資源檢查（如果可用）
        try:
            import psutil
            self.add_check(MemoryHealthCheck())
            self.add_check(DiskHealthCheck())
        except ImportError:
            logger.warning("psutil庫未安裝，跳過系統資源檢查")
    
    def add_check(self, check: BaseHealthCheck):
        """添加健康檢查"""
        self.checks.append(check)
        logger.info(f"添加健康檢查: {check.name}")
    
    async def perform_health_check(self) -> Dict[str, Any]:
        """執行完整的健康檢查"""
        start_time = time.time()
        
        logger.info("開始執行健康檢查...")
        
        # 並行執行所有檢查
        tasks = [check.check() for check in self.checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果
        check_results = []
        critical_failures = 0
        warnings = 0
        
        for i, result in enumerate(results):
            check_name = self.checks[i].name
            
            if isinstance(result, Exception):
                # 檢查異常
                logger.error(f"{check_name} 檢查異常: {result}")
                result = HealthCheckResult(
                    name=check_name,
                    status="unhealthy",
                    message=f"檢查異常: {str(result)}"
                )
            
            check_results.append(result.to_dict())
            
            # 統計失敗和警告
            if result.status == "unhealthy":
                if self.checks[i].critical:
                    critical_failures += 1
            elif result.status == "warning":
                warnings += 1
        
        # 確定整體狀態
        if critical_failures > 0:
            overall_status = "unhealthy"
            message = f"發現 {critical_failures} 個關鍵服務異常"
        elif warnings > 0:
            overall_status = "degraded"
            message = f"發現 {warnings} 個警告"
        else:
            overall_status = "healthy"
            message = "所有服務運行正常"
        
        total_time = time.time() - start_time
        
        logger.info(f"健康檢查完成 - 狀態: {overall_status}, 耗時: {total_time:.2f}秒")
        
        return {
            "status": overall_status,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "mode": "full",  # 可以從配置獲取
            "checks": check_results,
            "summary": {
                "total_checks": len(check_results),
                "healthy": sum(1 for r in check_results if r["status"] == "healthy"),
                "unhealthy": sum(1 for r in check_results if r["status"] == "unhealthy"),
                "warning": sum(1 for r in check_results if r["status"] == "warning"),
                "unknown": sum(1 for r in check_results if r["status"] == "unknown"),
                "total_time": total_time
            }
        }


# 全局健康檢查器實例
health_checker = UnifiedHealthChecker()


async def get_health_status() -> Dict[str, Any]:
    """獲取健康狀態（供API使用）"""
    return await health_checker.perform_health_check()