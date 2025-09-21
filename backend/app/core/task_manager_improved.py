"""
改進的任務狀態管理器

這個模塊提供高效的任務狀態管理和執行流程優化
"""

import asyncio
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import json

from .database_manager import get_db_manager
from .config_improved import get_settings

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任務狀態枚舉"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskType(Enum):
    """任務類型枚舉"""
    PROXY_SCRAPING = "proxy_scraping"
    PROXY_VALIDATION = "proxy_validation"
    PROXY_CLEANUP = "proxy_cleanup"
    SYSTEM_MAINTENANCE = "system_maintenance"
    DATA_EXPORT = "data_export"


@dataclass
class TaskConfig:
    """任務配置類"""
    timeout: int = 300  # 5分鐘
    max_retries: int = 3
    retry_delay: int = 60  # 1分鐘
    priority: int = 1  # 1-10，數字越大優先級越高
    worker_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    max_parallel: int = 1
    tags: List[str] = field(default_factory=list)


@dataclass
class Task:
    """任務數據類"""
    id: str
    name: str
    task_type: TaskType
    status: TaskStatus
    config: TaskConfig
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    worker_id: Optional[str] = None
    retry_count: int = 0
    execution_time: Optional[float] = None


class TaskQueue:
    """任務隊列"""
    
    def __init__(self, max_size: int = 1000):
        self.queue = asyncio.PriorityQueue(maxsize=max_size)
        self.pending_tasks: Dict[str, Task] = {}
        self.task_priorities: Dict[str, int] = {}
        self._lock = asyncio.Lock()
    
    async def put(self, task: Task) -> bool:
        """添加任務到隊列"""
        try:
            priority = -task.config.priority  # 優先級隊列使用負數，數字越小優先級越高
            await self.queue.put((priority, task.id))
            
            async with self._lock:
                self.pending_tasks[task.id] = task
                self.task_priorities[task.id] = priority
            
            logger.debug(f"任務已加入隊列: {task.id} (優先級: {task.config.priority})")
            return True
            
        except asyncio.QueueFull:
            logger.warning(f"任務隊列已滿，無法添加任務: {task.id}")
            return False
    
    async def get(self, timeout: Optional[float] = None) -> Optional[Task]:
        """從隊列獲取任務"""
        try:
            if timeout:
                priority, task_id = await asyncio.wait_for(self.queue.get(), timeout=timeout)
            else:
                priority, task_id = await self.queue.get()
            
            async with self._lock:
                task = self.pending_tasks.pop(task_id, None)
                self.task_priorities.pop(task_id, None)
            
            if task:
                logger.debug(f"從隊列獲取任務: {task.id}")
            
            return task
            
        except asyncio.TimeoutError:
            return None
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """獲取隊列統計信息"""
        return {
            'queue_size': self.queue.qsize(),
            'pending_count': len(self.pending_tasks),
            'priorities': list(self.task_priorities.values())
        }


class TaskWorker:
    """任務工作器"""
    
    def __init__(self, worker_id: str, task_manager: 'TaskManager'):
        self.worker_id = worker_id
        self.task_manager = task_manager
        self.current_task: Optional[Task] = None
        self.is_running = False
        self.task_count = 0
        self.error_count = 0
        self._lock = asyncio.Lock()
    
    async def start(self):
        """啟動工作器"""
        self.is_running = True
        logger.info(f"工作器 {self.worker_id} 已啟動")
        
        try:
            while self.is_running:
                # 從隊列獲取任務
                task = await self.task_manager.task_queue.get(timeout=5.0)
                
                if task:
                    async with self._lock:
                        self.current_task = task
                    
                    # 執行任務
                    await self.execute_task(task)
                    
                    async with self._lock:
                        self.current_task = None
                        self.task_count += 1
                
                # 短暫休眠，避免CPU佔用過高
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"工作器 {self.worker_id} 發生錯誤: {str(e)}")
            self.error_count += 1
        finally:
            logger.info(f"工作器 {self.worker_id} 已停止")
    
    async def execute_task(self, task: Task):
        """執行任務"""
        logger.info(f"工作器 {self.worker_id} 開始執行任務: {task.id}")
        
        try:
            # 更新任務狀態
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            task.worker_id = self.worker_id
            
            # 保存狀態到數據庫
            await self.task_manager.update_task_in_db(task)
            
            # 獲取任務執行器
            executor = self.task_manager.get_executor(task.task_type)
            
            if not executor:
                raise ValueError(f"未找到任務執行器: {task.task_type}")
            
            # 設置超時
            timeout = task.config.timeout
            
            # 執行任務
            if timeout > 0:
                result = await asyncio.wait_for(
                    executor(task),
                    timeout=timeout
                )
            else:
                result = await executor(task)
            
            # 任務成功完成
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            task.execution_time = (task.completed_at - task.started_at).total_seconds()
            
            logger.info(f"任務 {task.id} 執行成功，耗時: {task.execution_time:.2f}秒")
            
        except asyncio.TimeoutError:
            # 任務超時
            task.status = TaskStatus.TIMEOUT
            task.completed_at = datetime.now()
            task.error_message = f"任務超時 (>{task.config.timeout}秒)"
            task.execution_time = (task.completed_at - task.started_at).total_seconds() if task.started_at else None
            
            logger.warning(f"任務 {task.id} 超時")
            
        except Exception as e:
            # 任務失敗
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error_message = str(e)
            task.execution_time = (task.completed_at - task.started_at).total_seconds() if task.started_at else None
            
            self.error_count += 1
            logger.error(f"任務 {task.id} 執行失敗: {str(e)}")
            
            # 檢查是否需要重試
            if task.retry_count < task.config.max_retries:
                await self.retry_task(task)
        
        finally:
            # 更新任務到數據庫
            await self.task_manager.update_task_in_db(task)
    
    async def retry_task(self, task: Task):
        """重試任務"""
        task.retry_count += 1
        logger.info(f"任務 {task.id} 將重試 (第{task.retry_count}次)")
        
        # 等待重試延遲
        await asyncio.sleep(task.config.retry_delay)
        
        # 重置任務狀態
        task.status = TaskStatus.PENDING
        task.started_at = None
        task.completed_at = None
        task.error_message = None
        
        # 重新加入隊列
        await self.task_manager.add_task_to_queue(task)
    
    def stop(self):
        """停止工作器"""
        self.is_running = False
        logger.info(f"工作器 {self.worker_id} 正在停止...")
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取工作器統計"""
        return {
            'worker_id': self.worker_id,
            'is_running': self.is_running,
            'current_task': self.current_task.id if self.current_task else None,
            'task_count': self.task_count,
            'error_count': self.error_count
        }


class TaskManager:
    """任務管理器"""
    
    def __init__(self, worker_count: int = 4):
        self.settings = get_settings()
        self.db_manager = None
        self.task_queue = TaskQueue(max_size=self.settings.TASK_QUEUE_SIZE)
        self.workers: List[TaskWorker] = []
        self.executors: Dict[TaskType, Callable] = {}
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self._lock = asyncio.Lock()
        
        # 初始化工作器
        for i in range(worker_count):
            worker_id = f"worker-{i+1}"
            worker = TaskWorker(worker_id, self)
            self.workers.append(worker)
    
    async def initialize(self) -> bool:
        """初始化任務管理器"""
        try:
            logger.info("正在初始化任務管理器...")
            
            # 獲取數據庫管理器
            self.db_manager = await get_db_manager()
            
            # 註冊任務執行器
            await self.register_executors()
            
            # 恢復未完成的任務
            await self.recover_tasks()
            
            logger.info("任務管理器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"任務管理器初始化失敗: {str(e)}")
            return False
    
    async def register_executors(self):
        """註冊任務執行器"""
        # 這裡可以註冊具體的任務執行器
        # 例如：
        # self.executors[TaskType.PROXY_SCRAPING] = self.execute_proxy_scraping
        # self.executors[TaskType.PROXY_VALIDATION] = self.execute_proxy_validation
        
        logger.info(f"已註冊 {len(self.executors)} 個任務執行器")
    
    def get_executor(self, task_type: TaskType) -> Optional[Callable]:
        """獲取任務執行器"""
        return self.executors.get(task_type)
    
    async def start(self):
        """啟動任務管理器"""
        if self.is_running:
            logger.warning("任務管理器已在運行中")
            return
        
        try:
            logger.info("正在啟動任務管理器...")
            self.is_running = True
            self.start_time = datetime.now()
            
            # 啟動所有工作器
            worker_tasks = []
            for worker in self.workers:
                task = asyncio.create_task(worker.start())
                worker_tasks.append(task)
            
            # 等待所有工作器完成
            await asyncio.gather(*worker_tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"任務管理器啟動失敗: {str(e)}")
            self.is_running = False
    
    async def stop(self):
        """停止任務管理器"""
        if not self.is_running:
            return
        
        logger.info("正在停止任務管理器...")
        self.is_running = False
        
        # 停止所有工作器
        for worker in self.workers:
            worker.stop()
        
        # 等待當前任務完成
        await asyncio.sleep(2)
        
        logger.info("任務管理器已停止")
    
    async def create_task(self, name: str, task_type: TaskType, config: Optional[TaskConfig] = None) -> str:
        """創建新任務"""
        task_id = str(uuid.uuid4())
        
        if config is None:
            config = TaskConfig()
        
        task = Task(
            id=task_id,
            name=name,
            task_type=task_type,
            status=TaskStatus.PENDING,
            config=config,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 保存到數據庫
        await self.save_task_to_db(task)
        
        # 添加到隊列
        await self.add_task_to_queue(task)
        
        logger.info(f"任務已創建: {task_id} ({name})")
        return task_id
    
    async def save_task_to_db(self, task: Task):
        """保存任務到數據庫"""
        if self.db_manager and self.db_manager.settings.is_sqlite:
            try:
                task_data = {
                    'id': task.id,
                    'name': task.name,
                    'task_type': task.task_type.value,
                    'status': task.status.value,
                    'config': {
                        'timeout': task.config.timeout,
                        'max_retries': task.config.max_retries,
                        'retry_delay': task.config.retry_delay,
                        'priority': task.config.priority,
                        'worker_id': task.config.worker_id,
                        'dependencies': task.config.dependencies,
                        'max_parallel': task.config.max_parallel,
                        'tags': task.config.tags
                    },
                    'result': task.result,
                    'error_message': task.error_message,
                    'worker_id': task.worker_id,
                    'retry_count': task.retry_count
                }
                
                await self.db_manager.task_db.create_task(task_data)
                
            except Exception as e:
                logger.error(f"保存任務到數據庫失敗: {str(e)}")
    
    async def update_task_in_db(self, task: Task):
        """更新任務到數據庫"""
        if self.db_manager and self.db_manager.settings.is_sqlite:
            try:
                await self.db_manager.task_db.update_task_status(
                    task.id,
                    task.status.value,
                    task.result,
                    task.error_message
                )
                
            except Exception as e:
                logger.error(f"更新任務到數據庫失敗: {str(e)}")
    
    async def add_task_to_queue(self, task: Task):
        """添加任務到隊列"""
        success = await self.task_queue.put(task)
        if success:
            task.status = TaskStatus.QUEUED
            task.updated_at = datetime.now()
            await self.update_task_in_db(task)
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """獲取任務"""
        if self.db_manager and self.db_manager.settings.is_sqlite:
            try:
                task_data = await self.db_manager.task_db.get_task_by_id(task_id)
                if task_data:
                    return self._task_from_db_data(task_data)
            except Exception as e:
                logger.error(f"獲取任務失敗: {str(e)}")
        
        return None
    
    def _task_from_db_data(self, data: Dict[str, Any]) -> Task:
        """從數據庫數據創建任務對象"""
        try:
            config_data = data.get('config', {})
            config = TaskConfig(
                timeout=config_data.get('timeout', 300),
                max_retries=config_data.get('max_retries', 3),
                retry_delay=config_data.get('retry_delay', 60),
                priority=config_data.get('priority', 1),
                worker_id=config_data.get('worker_id'),
                dependencies=config_data.get('dependencies', []),
                max_parallel=config_data.get('max_parallel', 1),
                tags=config_data.get('tags', [])
            )
            
            # 安全地獲取任務類型和狀態
            try:
                task_type = TaskType(data['task_type'])
            except ValueError:
                # 如果任務類型無效，默認為代理爬取
                logger.warning(f"無效的任務類型: {data['task_type']}，使用默認值")
                task_type = TaskType.PROXY_SCRAPING
            
            try:
                status = TaskStatus(data['status'])
            except ValueError:
                # 如果狀態無效，默認為待處理
                logger.warning(f"無效的任務狀態: {data['status']}，使用默認值")
                status = TaskStatus.PENDING
            
            return Task(
                id=data['id'],
                name=data['name'],
                task_type=task_type,
                status=status,
                config=config,
                created_at=data['created_at'],
                updated_at=data['updated_at'],
                started_at=data.get('started_at'),
                completed_at=data.get('completed_at'),
                result=data.get('result'),
                error_message=data.get('error_message'),
                worker_id=data.get('worker_id'),
                retry_count=data.get('retry_count', 0),
                execution_time=data.get('execution_time')
            )
            
        except Exception as e:
            logger.error(f"從數據庫數據創建任務對象失敗: {str(e)}")
            raise
    
    async def get_tasks_by_status(self, status: TaskStatus, limit: int = 100) -> List[Task]:
        """根據狀態獲取任務"""
        if self.db_manager and self.db_manager.settings.is_sqlite:
            try:
                tasks_data = await self.db_manager.task_db.get_tasks_by_status(status.value, limit)
                return [self._task_from_db_data(task_data) for task_data in tasks_data]
            except Exception as e:
                logger.error(f"獲取任務失敗: {str(e)}")
        
        return []
    
    async def recover_tasks(self):
        """恢復未完成的任務"""
        logger.info("正在恢復未完成的任務...")
        
        # 獲取運行中的任務
        running_tasks = await self.get_tasks_by_status(TaskStatus.RUNNING)
        
        for task in running_tasks:
            # 將運行中的任務重置為待處理
            task.status = TaskStatus.PENDING
            task.worker_id = None
            task.started_at = None
            
            # 重新加入隊列
            await self.add_task_to_queue(task)
            
            logger.info(f"已恢復任務: {task.id}")
        
        logger.info(f"已恢復 {len(running_tasks)} 個任務")
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        worker_stats = [worker.get_stats() for worker in self.workers]
        queue_stats = self.task_queue.get_queue_stats()
        
        return {
            'is_running': self.is_running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'worker_count': len(self.workers),
            'workers': worker_stats,
            'queue': queue_stats,
            'uptime': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }


# 全局任務管理器實例
task_manager = TaskManager()


async def get_task_manager() -> TaskManager:
    """獲取任務管理器實例"""
    if not task_manager.is_running:
        await task_manager.initialize()
    return task_manager


# 測試函數
async def test_task_manager():
    """測試任務管理器"""
    print("🚀 測試任務管理器...")
    
    try:
        # 獲取任務管理器
        manager = await get_task_manager()
        
        # 創建測試任務
        task_id = await manager.create_task(
            name="測試任務",
            task_type=TaskType.PROXY_SCRAPING,
            config=TaskConfig(timeout=60, priority=5)
        )
        print(f"✅ 創建任務成功: {task_id}")
        
        # 獲取任務
        task = await manager.get_task(task_id)
        print(f"✅ 獲取任務成功: {task.name} (狀態: {task.status.value})")
        
        # 獲取統計信息
        stats = manager.get_stats()
        print(f"✅ 統計信息: {stats}")
        
        print("✅ 任務管理器測試完成！")
        
    except Exception as e:
        print(f"❌ 任務管理器測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_task_manager())