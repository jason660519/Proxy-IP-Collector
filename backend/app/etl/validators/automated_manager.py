"""
自動化IP驗證與評分管理器
管理代理驗證流程，提供自動化的驗證調度和監控
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
import aiofiles

from .validation_system import ProxyValidationSystem, ProxyValidationResult


@dataclass
class ValidationJob:
    """驗證任務數據類"""
    job_id: str
    proxies: List[Any]
    test_level: str
    priority: int
    created_at: datetime
    scheduled_at: Optional[datetime]
    completed_at: Optional[datetime]
    results: Optional[List[ProxyValidationResult]]
    status: str  # pending, running, completed, failed


class AutomatedValidationManager:
    """
    自動化IP驗證與評分管理器
    提供代理驗證的自動化調度和管理功能
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化自動化驗證管理器
        
        Args:
            config: 系統配置
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化驗證系統
        self.validation_system = ProxyValidationSystem(self.config.get('validation_system', {}))
        
        # 調度配置
        self.max_concurrent_jobs = self.config.get('max_concurrent_jobs', 3)
        self.job_queue_size = self.config.get('job_queue_size', 100)
        self.validation_interval = self.config.get('validation_interval', 3600)  # 1小時
        self.retry_failed_interval = self.config.get('retry_failed_interval', 1800)  # 30分鐘
        self.auto_cleanup_interval = self.config.get('auto_cleanup_interval', 86400)  # 24小時
        
        # 狀態管理
        self.job_queue: List[ValidationJob] = []
        self.running_jobs: Dict[str, ValidationJob] = {}
        self.completed_jobs: Dict[str, ValidationJob] = {}
        self.failed_jobs: Dict[str, ValidationJob] = {}
        
        # 統計數據
        self.stats = {
            'total_jobs_created': 0,
            'total_jobs_completed': 0,
            'total_jobs_failed': 0,
            'avg_job_duration': 0.0,
            'current_queue_size': 0,
            'active_workers': 0
        }
        
        # 控制標誌
        self.is_running = False
        self.stop_event = asyncio.Event()
        
        # 持久化配置
        self.persistence_enabled = self.config.get('persistence_enabled', True)
        self.persistence_path = Path(self.config.get('persistence_path', './validation_jobs'))
        
        if self.persistence_enabled:
            self.persistence_path.mkdir(exist_ok=True)
    
    async def start(self):
        """啟動自動化驗證管理器"""
        self.logger.info("啟動自動化IP驗證與評分管理器")
        self.is_running = True
        self.stop_event.clear()
        
        # 載入待處理任務
        await self._load_pending_jobs()
        
        # 啟動工作協程
        tasks = [
            self._job_scheduler(),
            self._job_processor(),
            self._cleanup_scheduler(),
            self._statistics_reporter()
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop(self):
        """停止自動化驗證管理器"""
        self.logger.info("停止自動化IP驗證與評分管理器")
        self.is_running = False
        self.stop_event.set()
        
        # 等待所有運行中的任務完成
        await self._wait_for_completion()
        
        # 保存未完成的任務
        await self._save_pending_jobs()
    
    async def add_validation_job(self, proxies: List[Any], test_level: str = 'standard', 
                                 priority: int = 5, schedule_delay: Optional[int] = None) -> str:
        """
        添加驗證任務
        
        Args:
            proxies: 代理列表
            test_level: 測試等級
            priority: 優先級 (1-10, 數字越大優先級越高)
            schedule_delay: 延遲執行秒數
            
        Returns:
            str: 任務ID
        """
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.job_queue)}"
        
        scheduled_at = None
        if schedule_delay:
            scheduled_at = datetime.now() + timedelta(seconds=schedule_delay)
        
        job = ValidationJob(
            job_id=job_id,
            proxies=proxies,
            test_level=test_level,
            priority=priority,
            created_at=datetime.now(),
            scheduled_at=scheduled_at,
            completed_at=None,
            results=None,
            status='pending'
        )
        
        # 根據優先級插入隊列
        insert_index = 0
        for i, existing_job in enumerate(self.job_queue):
            if job.priority > existing_job.priority:
                insert_index = i
                break
            elif job.priority == existing_job.priority:
                if job.created_at < existing_job.created_at:
                    insert_index = i
                    break
            insert_index = i + 1
        
        self.job_queue.insert(insert_index, job)
        self.stats['total_jobs_created'] += 1
        self.stats['current_queue_size'] = len(self.job_queue)
        
        self.logger.info(f"添加驗證任務: {job_id}, 代理數: {len(proxies)}, 優先級: {priority}")
        
        return job_id
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取任務狀態
        
        Args:
            job_id: 任務ID
            
        Returns:
            Dict: 任務狀態信息
        """
        # 在隊列中查找
        for job in self.job_queue:
            if job.job_id == job_id:
                return {
                    'job_id': job_id,
                    'status': 'pending',
                    'position': self.job_queue.index(job) + 1,
                    'queue_size': len(self.job_queue),
                    'created_at': job.created_at.isoformat(),
                    'scheduled_at': job.scheduled_at.isoformat() if job.scheduled_at else None,
                    'proxies_count': len(job.proxies)
                }
        
        # 在運行中查找
        if job_id in self.running_jobs:
            job = self.running_jobs[job_id]
            return {
                'job_id': job_id,
                'status': 'running',
                'started_at': datetime.now().isoformat(),
                'proxies_count': len(job.proxies),
                'test_level': job.test_level
            }
        
        # 在完成任務中查找
        if job_id in self.completed_jobs:
            job = self.completed_jobs[job_id]
            results = job.results or []
            return {
                'job_id': job_id,
                'status': 'completed',
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'proxies_count': len(job.proxies),
                'successful_validations': sum(1 for r in results if r.success),
                'failed_validations': sum(1 for r in results if not r.success),
                'avg_score': sum(r.overall_score for r in results) / len(results) if results else 0
            }
        
        # 在失敗任務中查找
        if job_id in self.failed_jobs:
            job = self.failed_jobs[job_id]
            return {
                'job_id': job_id,
                'status': 'failed',
                'failed_at': job.completed_at.isoformat() if job.completed_at else None,
                'proxies_count': len(job.proxies),
                'error': '任務執行失敗'
            }
        
        return None
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        獲取系統狀態
        
        Returns:
            Dict: 系統狀態信息
        """
        validation_stats = self.validation_system.get_system_stats()
        
        return {
            'is_running': self.is_running,
            'queue_size': len(self.job_queue),
            'running_jobs': len(self.running_jobs),
            'completed_jobs': len(self.completed_jobs),
            'failed_jobs': len(self.failed_jobs),
            'active_workers': self.stats['active_workers'],
            'statistics': {
                'total_jobs_created': self.stats['total_jobs_created'],
                'total_jobs_completed': self.stats['total_jobs_completed'],
                'total_jobs_failed': self.stats['total_jobs_failed'],
                'avg_job_duration': self.stats['avg_job_duration'],
                'validation_system_stats': validation_stats
            },
            'timestamp': datetime.now().isoformat()
        }
    
    async def _job_scheduler(self):
        """任務調度器協程"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # 檢查定時任務
                ready_jobs = []
                remaining_jobs = []
                
                for job in self.job_queue:
                    if job.scheduled_at is None or job.scheduled_at <= current_time:
                        ready_jobs.append(job)
                    else:
                        remaining_jobs.append(job)
                
                self.job_queue = remaining_jobs
                
                # 將就緒任務移動到運行狀態
                for job in ready_jobs:
                    if len(self.running_jobs) < self.max_concurrent_jobs:
                        job.status = 'running'
                        self.running_jobs[job.job_id] = job
                        self.logger.info(f"調度任務開始執行: {job.job_id}")
                    else:
                        # 如果沒有空閒工作槽，重新放回隊列
                        self.job_queue.insert(0, job)
                
                await asyncio.sleep(1)  # 每秒檢查一次
                
            except Exception as e:
                self.logger.error(f"任務調度器錯誤: {e}")
                await asyncio.sleep(5)
    
    async def _job_processor(self):
        """任務處理器協程"""
        while self.is_running:
            try:
                # 處理運行中的任務
                completed_job_ids = []
                
                for job_id, job in self.running_jobs.items():
                    try:
                        # 執行驗證任務
                        self.stats['active_workers'] += 1
                        
                        results = await self.validation_system.validate_proxies_batch(
                            job.proxies, job.test_level
                        )
                        
                        # 更新任務狀態
                        job.results = results
                        job.completed_at = datetime.now()
                        job.status = 'completed'
                        
                        # 移動到完成列表
                        self.completed_jobs[job_id] = job
                        completed_job_ids.append(job_id)
                        
                        # 更新統計
                        self.stats['total_jobs_completed'] += 1
                        job_duration = (job.completed_at - job.created_at).total_seconds()
                        
                        # 更新平均任務時長
                        total_duration = self.stats['avg_job_duration'] * (self.stats['total_jobs_completed'] - 1)
                        self.stats['avg_job_duration'] = (total_duration + job_duration) / self.stats['total_jobs_completed']
                        
                        self.logger.info(
                            f"任務完成: {job_id}, "
                            f"代理數: {len(job.proxies)}, "
                            f"耗時: {job_duration:.1f}s, "
                            f"成功: {sum(1 for r in results if r.success)}/{len(results)}"
                        )
                        
                    except Exception as e:
                        self.logger.error(f"任務處理失敗 {job_id}: {e}")
                        
                        # 標記任務為失敗
                        job.status = 'failed'
                        job.completed_at = datetime.now()
                        self.failed_jobs[job_id] = job
                        completed_job_ids.append(job_id)
                        
                        self.stats['total_jobs_failed'] += 1
                    
                    finally:
                        self.stats['active_workers'] = max(0, self.stats['active_workers'] - 1)
                
                # 移除完成的任務
                for job_id in completed_job_ids:
                    if job_id in self.running_jobs:
                        del self.running_jobs[job_id]
                
                await asyncio.sleep(0.5)  # 每0.5秒檢查一次
                
            except Exception as e:
                self.logger.error(f"任務處理器錯誤: {e}")
                await asyncio.sleep(5)
    
    async def _cleanup_scheduler(self):
        """清理調度器協程"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # 清理過期的完成任務（保留24小時）
                expired_jobs = []
                for job_id, job in self.completed_jobs.items():
                    if job.completed_at and (current_time - job.completed_at).total_seconds() > self.auto_cleanup_interval:
                        expired_jobs.append(job_id)
                
                for job_id in expired_jobs:
                    del self.completed_jobs[job_id]
                
                # 清理過期的失敗任務（保留48小時）
                expired_failed_jobs = []
                for job_id, job in self.failed_jobs.items():
                    if job.completed_at and (current_time - job.completed_at).total_seconds() > self.auto_cleanup_interval * 2:
                        expired_failed_jobs.append(job_id)
                
                for job_id in expired_failed_jobs:
                    del self.failed_jobs[job_id]
                
                # 保存持久化數據
                if self.persistence_enabled:
                    await self._save_system_state()
                
                self.logger.info(
                    f"清理完成 - 移除過期任務: {len(expired_jobs) + len(expired_failed_jobs)}, "
                    f"當前完成任務: {len(self.completed_jobs)}, 失敗任務: {len(self.failed_jobs)}"
                )
                
                await asyncio.sleep(3600)  # 每小時清理一次
                
            except Exception as e:
                self.logger.error(f"清理調度器錯誤: {e}")
                await asyncio.sleep(300)  # 5分鐘後重試
    
    async def _statistics_reporter(self):
        """統計報告器協程"""
        while self.is_running:
            try:
                # 每5分鐘報告一次統計
                await asyncio.sleep(300)
                
                system_status = await self.get_system_status()
                validation_stats = self.validation_system.get_system_stats()
                
                self.logger.info(
                    f"系統統計報告 - "
                    f"隊列: {system_status['queue_size']}, "
                    f"運行中: {system_status['running_jobs']}, "
                    f"完成: {system_status['completed_jobs']}, "
                    f"失敗: {system_status['failed_jobs']}, "
                    f"驗證成功率: {validation_stats['success_rate']:.1f}%, "
                    f"平均分數: {validation_stats['avg_score']:.1f}"
                )
                
            except Exception as e:
                self.logger.error(f"統計報告器錯誤: {e}")
    
    async def _load_pending_jobs(self):
        """載入待處理任務"""
        if not self.persistence_enabled:
            return
        
        try:
            pending_file = self.persistence_path / 'pending_jobs.json'
            if pending_file.exists():
                async with aiofiles.open(pending_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    jobs_data = json.loads(content)
                
                # 重建任務對象
                for job_data in jobs_data:
                    job = ValidationJob(
                        job_id=job_data['job_id'],
                        proxies=[],  # 需要重新獲取代理對象
                        test_level=job_data['test_level'],
                        priority=job_data['priority'],
                        created_at=datetime.fromisoformat(job_data['created_at']),
                        scheduled_at=datetime.fromisoformat(job_data['scheduled_at']) if job_data.get('scheduled_at') else None,
                        completed_at=None,
                        results=None,
                        status='pending'
                    )
                    self.job_queue.append(job)
                
                self.logger.info(f"載入 {len(jobs_data)} 個待處理任務")
                
        except Exception as e:
            self.logger.error(f"載入待處理任務失敗: {e}")
    
    async def _save_pending_jobs(self):
        """保存待處理任務"""
        if not self.persistence_enabled:
            return
        
        try:
            # 保存隊列中的任務和運行中的任務
            pending_jobs = []
            
            for job in self.job_queue:
                job_data = {
                    'job_id': job.job_id,
                    'test_level': job.test_level,
                    'priority': job.priority,
                    'created_at': job.created_at.isoformat(),
                    'scheduled_at': job.scheduled_at.isoformat() if job.scheduled_at else None
                }
                pending_jobs.append(job_data)
            
            for job in self.running_jobs.values():
                job_data = {
                    'job_id': job.job_id,
                    'test_level': job.test_level,
                    'priority': job.priority,
                    'created_at': job.created_at.isoformat(),
                    'scheduled_at': job.scheduled_at.isoformat() if job.scheduled_at else None
                }
                pending_jobs.append(job_data)
            
            pending_file = self.persistence_path / 'pending_jobs.json'
            async with aiofiles.open(pending_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(pending_jobs, ensure_ascii=False, indent=2))
            
            self.logger.info(f"保存 {len(pending_jobs)} 個待處理任務")
            
        except Exception as e:
            self.logger.error(f"保存待處理任務失敗: {e}")
    
    async def _save_system_state(self):
        """保存系統狀態"""
        if not self.persistence_enabled:
            return
        
        try:
            state_data = {
                'timestamp': datetime.now().isoformat(),
                'stats': self.stats,
                'system_stats': self.validation_system.get_system_stats()
            }
            
            state_file = self.persistence_path / 'system_state.json'
            async with aiofiles.open(state_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(state_data, ensure_ascii=False, indent=2))
                
        except Exception as e:
            self.logger.error(f"保存系統狀態失敗: {e}")
    
    async def _wait_for_completion(self):
        """等待所有任務完成"""
        self.logger.info("等待所有運行中的任務完成...")
        
        max_wait_time = 300  # 最多等待5分鐘
        start_time = datetime.now()
        
        while self.running_jobs and (datetime.now() - start_time).total_seconds() < max_wait_time:
            await asyncio.sleep(1)
        
        if self.running_jobs:
            self.logger.warning(f"超時，仍有 {len(self.running_jobs)} 個任務未完成")
        else:
            self.logger.info("所有任務已完成")


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    # 模擬代理對象
    class MockProxy:
        def __init__(self, ip, port, protocol='http'):
            self.ip = ip
            self.port = port
            self.protocol = protocol
            self.country = 'US'
            self.anonymity = 'elite'
    
    async def test_automated_manager():
        # 創建自動化管理器
        config = {
            'max_concurrent_jobs': 2,
            'validation_interval': 60,
            'persistence_enabled': False
        }
        
        manager = AutomatedValidationManager(config)
        
        # 添加測試任務
        test_proxies = [
            MockProxy('8.8.8.8', 8080),
            MockProxy('1.1.1.1', 3128),
            MockProxy('192.168.1.1', 8080)
        ]
        
        job_id = await manager.add_validation_job(
            test_proxies, 
            test_level='comprehensive',
            priority=8
        )
        
        print(f"添加驗證任務: {job_id}")
        
        # 獲取系統狀態
        status = await manager.get_system_status()
        print(f"系統狀態: {status}")
        
        # 啟動管理器（運行30秒後停止）
        manager_task = asyncio.create_task(manager.start())
        
        await asyncio.sleep(30)
        
        await manager.stop()
        manager_task.cancel()
        
        # 獲取任務狀態
        job_status = await manager.get_job_status(job_id)
        print(f"任務狀態: {job_status}")
    
    # 運行測試
    asyncio.run(test_automated_manager())