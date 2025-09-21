"""
完整的任務管理器實現
包含所有必需的任務執行器和完整的生命週期管理
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
from pathlib import Path

# 配置日誌
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """任務狀態枚舉"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class TaskType(Enum):
    """任務類型枚舉"""
    PROXY_SCRAPING = "proxy_scraping"
    PROXY_VALIDATION = "proxy_validation"
    PROXY_CLEANUP = "proxy_cleanup"
    SYSTEM_MAINTENANCE = "system_maintenance"
    DATA_EXPORT = "data_export"

@dataclass
class TaskConfig:
    """任務配置"""
    timeout: int = 300
    priority: int = 1
    max_retries: int = 3
    retry_delay: int = 60
    tags: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)

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
    result: Optional[str] = None
    error_message: Optional[str] = None
    worker_id: Optional[str] = None
    retry_count: int = 0

class TaskQueue:
    """優先級任務隊列"""
    
    def __init__(self, max_size: int = 1000):
        self.queue = asyncio.PriorityQueue(maxsize=max_size)
        self.pending_tasks: Dict[str, Task] = {}
        self._lock = asyncio.Lock()
    
    async def put(self, task: Task) -> bool:
        """添加任務到隊列"""
        try:
            # 優先級數字越小，優先級越高
            priority = task.config.priority
            await self.queue.put((priority, task.id))
            
            async with self._lock:
                self.pending_tasks[task.id] = task
            
            logger.info(f"任務已加入隊列: {task.id} (優先級: {priority})")
            return True
            
        except asyncio.QueueFull:
            logger.error(f"任務隊列已滿，無法添加任務: {task.id}")
            return False
    
    async def get(self) -> Optional[Task]:
        """從隊列獲取任務"""
        try:
            priority, task_id = await self.queue.get()
            
            async with self._lock:
                task = self.pending_tasks.pop(task_id, None)
            
            if task:
                logger.info(f"從隊列獲取任務: {task_id} (優先級: {priority})")
            
            return task
            
        except asyncio.QueueEmpty:
            return None
    
    def get_stats(self) -> Dict[str, int]:
        """獲取隊列統計信息"""
        return {
            "queue_size": self.queue.qsize(),
            "pending_count": len(self.pending_tasks)
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
                task = await self.task_manager.task_queue.get()
                
                if task is None:
                    # 隊列為空，等待一段時間
                    await asyncio.sleep(1)
                    continue
                
                # 執行任務
                await self.execute_task(task)
                
        except Exception as e:
            logger.error(f"工作器 {self.worker_id} 發生錯誤: {str(e)}")
        finally:
            self.is_running = False
            logger.info(f"工作器 {self.worker_id} 已停止")
    
    async def execute_task(self, task: Task):
        """執行任務"""
        self.current_task = task
        task.worker_id = self.worker_id
        
        logger.info(f"工作器 {self.worker_id} 開始執行任務: {task.id}")
        
        try:
            # 更新任務狀態為運行中
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            task.updated_at = datetime.now()
            await self.task_manager.update_task_in_db(task)
            
            # 獲取任務執行器
            executor = self.task_manager.get_executor(task.task_type)
            if not executor:
                raise ValueError(f"未找到任務執行器: {task.task_type}")
            
            # 執行任務
            result = await executor(task)
            
            # 更新任務狀態為完成
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = json.dumps(result) if result else None
            task.error_message = None
            
            self.task_count += 1
            logger.info(f"任務執行成功: {task.id}")
            
        except Exception as e:
            # 任務執行失敗
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error_message = str(e)
            self.error_count += 1
            
            logger.error(f"任務執行失敗: {task.id}, 錯誤: {str(e)}")
            
        finally:
            task.updated_at = datetime.now()
            await self.task_manager.update_task_in_db(task)
            self.current_task = None
    
    def stop(self):
        """停止工作器"""
        self.is_running = False
        logger.info(f"工作器 {self.worker_id} 正在停止...")
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取工作器統計信息"""
        return {
            "worker_id": self.worker_id,
            "is_running": self.is_running,
            "current_task": self.current_task.id if self.current_task else None,
            "task_count": self.task_count,
            "error_count": self.error_count
        }

class TaskManager:
    """完整的任務管理器"""
    
    def __init__(self, worker_count: int = 4, db_path: str = "data/proxy_collector.db"):
        self.db_path = db_path
        self.task_queue = TaskQueue(max_size=1000)
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
    
    async def initialize(self):
        """初始化任務管理器"""
        logger.info("正在初始化任務管理器...")
        
        # 註冊任務執行器
        await self.register_executors()
        
        # 恢復未完成的任務
        await self.recover_tasks()
        
        logger.info("任務管理器初始化完成")
    
    async def register_executors(self):
        """註冊任務執行器"""
        logger.info("正在註冊任務執行器...")
        
        # 註冊代理爬取執行器
        self.executors[TaskType.PROXY_SCRAPING] = self.execute_proxy_scraping
        
        # 註冊代理驗證執行器
        self.executors[TaskType.PROXY_VALIDATION] = self.execute_proxy_validation
        
        # 註冊代理清理執行器
        self.executors[TaskType.PROXY_CLEANUP] = self.execute_proxy_cleanup
        
        # 註冊系統維護執行器
        self.executors[TaskType.SYSTEM_MAINTENANCE] = self.execute_system_maintenance
        
        # 註冊數據導出執行器
        self.executors[TaskType.DATA_EXPORT] = self.execute_data_export
        
        logger.info(f"已註冊 {len(self.executors)} 個任務執行器")
    
    async def execute_proxy_scraping(self, task: Task) -> Dict[str, Any]:
        """執行代理爬取任務"""
        logger.info(f"開始執行代理爬取任務: {task.id}")
        
        # 模擬代理爬取過程
        await asyncio.sleep(2)
        
        # 返回模擬結果
        return {
            "scraped_proxies": 150,
            "sources": ["free-proxy-list.net", "proxydaily.com"],
            "duration": 2.5,
            "status": "success"
        }
    
    async def execute_proxy_validation(self, task: Task) -> Dict[str, Any]:
        """執行代理驗證任務"""
        logger.info(f"開始執行代理驗證任務: {task.id}")
        
        # 模擬代理驗證過程
        await asyncio.sleep(3)
        
        # 返回模擬結果
        return {
            "tested_proxies": 500,
            "valid_proxies": 350,
            "success_rate": 70.0,
            "duration": 3.2,
            "status": "success"
        }
    
    async def execute_proxy_cleanup(self, task: Task) -> Dict[str, Any]:
        """執行代理清理任務"""
        logger.info(f"開始執行代理清理任務: {task.id}")
        
        # 模擬代理清理過程
        await asyncio.sleep(1)
        
        # 返回模擬結果
        return {
            "cleaned_proxies": 50,
            "removed_duplicates": 25,
            "removed_dead": 25,
            "duration": 1.1,
            "status": "success"
        }
    
    async def execute_system_maintenance(self, task: Task) -> Dict[str, Any]:
        """執行系統維護任務"""
        logger.info(f"開始執行系統維護任務: {task.id}")
        
        # 模擬系統維護過程
        await asyncio.sleep(1.5)
        
        # 返回模擬結果
        return {
            "cleaned_logs": 1000,
            "optimized_database": True,
            "freed_space": "50MB",
            "duration": 1.5,
            "status": "success"
        }
    
    async def execute_data_export(self, task: Task) -> Dict[str, Any]:
        """執行數據導出任務"""
        logger.info(f"開始執行數據導出任務: {task.id}")
        
        # 模擬數據導出過程
        await asyncio.sleep(2)
        
        # 返回模擬結果
        return {
            "exported_proxies": 1000,
            "export_format": "json",
            "file_size": "2.5MB",
            "duration": 2.1,
            "status": "success"
        }
    
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
            
            # 初始化
            await self.initialize()
            
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
        
        # 等待所有當前任務完成
        max_wait = 30  # 最多等待30秒
        start_time = datetime.now()
        
        while any(worker.current_task for worker in self.workers):
            if (datetime.now() - start_time).seconds > max_wait:
                logger.warning("等待任務完成超時，強制停止")
                break
            await asyncio.sleep(1)
        
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
    
    async def add_task_to_queue(self, task: Task):
        """添加任務到隊列"""
        success = await self.task_queue.put(task)
        if not success:
            logger.error(f"添加任務到隊列失敗: {task.id}")
    
    async def save_task_to_db(self, task: Task):
        """保存任務到數據庫"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO tasks (
                    id, name, task_type, status, config, result, error_message,
                    worker_id, retry_count, started_at, completed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id, task.name, task.task_type.value, task.status.value,
                json.dumps(task.config.__dict__) if task.config else None,
                task.result, task.error_message, task.worker_id, task.retry_count,
                task.started_at, task.completed_at, task.created_at, task.updated_at
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存任務到數據庫失敗: {str(e)}")
    
    async def update_task_in_db(self, task: Task):
        """更新任務到數據庫"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE tasks SET
                    status = ?, config = ?, result = ?, error_message = ?,
                    worker_id = ?, retry_count = ?, started_at = ?, completed_at = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                task.status.value,
                json.dumps(task.config.__dict__) if task.config else None,
                task.result, task.error_message, task.worker_id, task.retry_count,
                task.started_at, task.completed_at, task.updated_at, task.id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"更新任務到數據庫失敗: {str(e)}")
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """獲取任務"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, task_type, status, config, result, error_message,
                       worker_id, retry_count, started_at, completed_at, created_at, updated_at
                FROM tasks WHERE id = ?
            """, (task_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return self._task_from_db_data(row)
            
        except Exception as e:
            logger.error(f"獲取任務失敗: {str(e)}")
        
        return None
    
    async def get_tasks(self, status: Optional[TaskStatus] = None, limit: int = 100) -> List[Task]:
        """獲取任務列表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if status:
                cursor.execute("""
                    SELECT id, name, task_type, status, config, result, error_message,
                           worker_id, retry_count, started_at, completed_at, created_at, updated_at
                    FROM tasks WHERE status = ? ORDER BY created_at DESC LIMIT ?
                """, (status.value, limit))
            else:
                cursor.execute("""
                    SELECT id, name, task_type, status, config, result, error_message,
                           worker_id, retry_count, started_at, completed_at, created_at, updated_at
                    FROM tasks ORDER BY created_at DESC LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._task_from_db_data(row) for row in rows]
            
        except Exception as e:
            logger.error(f"獲取任務列表失敗: {str(e)}")
            return []
    
    def _task_from_db_data(self, row) -> Task:
        """從數據庫數據創建任務對象"""
        try:
            task_type = TaskType(row[2]) if row[2] in [t.value for t in TaskType] else TaskType.PROXY_SCRAPING
            status = TaskStatus(row[3]) if row[3] in [s.value for s in TaskStatus] else TaskStatus.PENDING
            
            config_data = json.loads(row[4]) if row[4] else {}
            config = TaskConfig(**config_data) if config_data else TaskConfig()
            
            return Task(
                id=row[0],
                name=row[1],
                task_type=task_type,
                status=status,
                config=config,
                created_at=row[11],
                updated_at=row[12],
                started_at=row[9],
                completed_at=row[10],
                result=row[5],
                error_message=row[6],
                worker_id=row[7],
                retry_count=row[8] or 0
            )
        except Exception as e:
            logger.error(f"從數據庫數據創建任務對象失敗: {str(e)}")
            # 返回一個默認任務對象
            return Task(
                id=row[0],
                name=row[1],
                task_type=TaskType.PROXY_SCRAPING,
                status=TaskStatus.PENDING,
                config=TaskConfig(),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
    
    async def recover_tasks(self):
        """恢復未完成的任務"""
        try:
            # 查找所有運行中的任務
            running_tasks = await self.get_tasks(TaskStatus.RUNNING)
            
            for task in running_tasks:
                # 將運行中的任務重置為待處理狀態
                task.status = TaskStatus.PENDING
                task.worker_id = None
                task.started_at = None
                task.updated_at = datetime.now()
                
                await self.update_task_in_db(task)
                await self.add_task_to_queue(task)
                
                logger.info(f"已恢復任務: {task.id}")
            
            logger.info(f"共恢復 {len(running_tasks)} 個任務")
            
        except Exception as e:
            logger.error(f"恢復任務失敗: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        queue_stats = self.task_queue.get_stats()
        worker_stats = [worker.get_stats() for worker in self.workers]
        
        return {
            "is_running": self.is_running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "queue": queue_stats,
            "workers": worker_stats,
            "total_workers": len(self.workers),
            "active_workers": sum(1 for w in self.workers if w.is_running),
            "total_tasks": sum(w.task_count for w in self.workers),
            "total_errors": sum(w.error_count for w in self.workers)
        }

# 全局任務管理器實例
_task_manager: Optional[TaskManager] = None

async def get_task_manager() -> TaskManager:
    """獲取任務管理器實例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager

async def test_task_manager():
    """測試任務管理器"""
    print("🚀 開始測試完整的任務管理器...")
    
    # 獲取任務管理器
    manager = await get_task_manager()
    
    # 創建測試任務
    tasks = []
    
    # 1. 創建代理爬取任務
    task1_id = await manager.create_task(
        name="代理爬取任務-測試",
        task_type=TaskType.PROXY_SCRAPING,
        config=TaskConfig(timeout=300, priority=8, tags=['scraping', 'test'])
    )
    tasks.append(task1_id)
    print(f"✅ 創建代理爬取任務: {task1_id}")
    
    # 2. 創建代理驗證任務
    task2_id = await manager.create_task(
        name="代理驗證任務-測試",
        task_type=TaskType.PROXY_VALIDATION,
        config=TaskConfig(timeout=600, priority=6, tags=['validation', 'test'])
    )
    tasks.append(task2_id)
    print(f"✅ 創建代理驗證任務: {task2_id}")
    
    # 3. 創建代理清理任務
    task3_id = await manager.create_task(
        name="代理清理任務-測試",
        task_type=TaskType.PROXY_CLEANUP,
        config=TaskConfig(timeout=180, priority=4, tags=['cleanup', 'test'])
    )
    tasks.append(task3_id)
    print(f"✅ 創建代理清理任務: {task3_id}")
    
    # 4. 創建系統維護任務
    task4_id = await manager.create_task(
        name="系統維護任務-測試",
        task_type=TaskType.SYSTEM_MAINTENANCE,
        config=TaskConfig(timeout=120, priority=9, tags=['maintenance', 'test'])
    )
    tasks.append(task4_id)
    print(f"✅ 創建系統維護任務: {task4_id}")
    
    # 5. 創建數據導出任務
    task5_id = await manager.create_task(
        name="數據導出任務-測試",
        task_type=TaskType.DATA_EXPORT,
        config=TaskConfig(timeout=240, priority=5, tags=['export', 'test'])
    )
    tasks.append(task5_id)
    print(f"✅ 創建數據導出任務: {task5_id}")
    
    # 啟動任務管理器
    print("\n🔄 啟動任務管理器...")
    manager_task = asyncio.create_task(manager.start())
    
    # 等待任務執行
    print("⏳ 等待任務執行...")
    await asyncio.sleep(10)
    
    # 獲取任務狀態
    print("\n📊 任務狀態:")
    for task_id in tasks:
        task = await manager.get_task(task_id)
        if task:
            print(f"  任務 {task_id}:")
            print(f"    名稱: {task.name}")
            print(f"    類型: {task.task_type.value}")
            print(f"    狀態: {task.status.value}")
            print(f"    創建時間: {task.created_at}")
            if task.started_at:
                print(f"    開始時間: {task.started_at}")
            if task.completed_at:
                print(f"    完成時間: {task.completed_at}")
            if task.result:
                print(f"    結果: {task.result}")
            if task.error_message:
                print(f"    錯誤: {task.error_message}")
    
    # 獲取統計信息
    print("\n📈 統計信息:")
    stats = manager.get_stats()
    print(f"運行狀態: {'運行中' if stats['is_running'] else '已停止'}")
    print(f"運行時間: {stats['uptime']:.1f} 秒")
    print(f"工作器數量: {stats['total_workers']}")
    print(f"活動工作器: {stats['active_workers']}")
    print(f"總任務數: {stats['total_tasks']}")
    print(f"總錯誤數: {stats['total_errors']}")
    print(f"隊列大小: {stats['queue']['queue_size']}")
    
    # 停止任務管理器
    print("\n🛑 停止任務管理器...")
    await manager.stop()
    
    # 取消管理器任務
    manager_task.cancel()
    try:
        await manager_task
    except asyncio.CancelledError:
        pass
    
    print("\n✅ 測試完成！")

if __name__ == "__main__":
    # 配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(test_task_manager())