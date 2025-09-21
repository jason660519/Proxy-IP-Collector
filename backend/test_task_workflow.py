#!/usr/bin/env python3
"""
任務狀態管理和執行流程測試

這個腳本測試改進的任務管理器的完整工作流程
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# 添加項目根目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.task_manager_improved import (
    TaskManager, TaskType, TaskStatus, TaskConfig, 
    get_task_manager, Task
)
from app.core.database_manager import get_db_manager


class MockTaskExecutor:
    """模擬任務執行器"""
    
    def __init__(self):
        self.execution_log = []
    
    async def execute_proxy_scraping(self, task: Task) -> Dict[str, Any]:
        """執行代理爬取任務"""
        print(f"🕷️  開始執行代理爬取任務: {task.name}")
        
        # 模擬任務執行
        await asyncio.sleep(2)
        
        result = {
            'scraped_count': 100,
            'valid_count': 85,
            'invalid_count': 15,
            'sources': ['source1', 'source2', 'source3']
        }
        
        print(f"✅ 代理爬取任務完成: {task.name}")
        return result
    
    async def execute_proxy_validation(self, task: Task) -> Dict[str, Any]:
        """執行代理驗證任務"""
        print(f"🔍 開始執行代理驗證任務: {task.name}")
        
        # 模擬任務執行
        await asyncio.sleep(1)
        
        result = {
            'tested_count': 50,
            'valid_count': 42,
            'invalid_count': 8,
            'test_time': 1.2
        }
        
        print(f"✅ 代理驗證任務完成: {task.name}")
        return result
    
    async def execute_proxy_cleanup(self, task: Task) -> Dict[str, Any]:
        """執行代理清理任務"""
        print(f"🧹 開始執行代理清理任務: {task.name}")
        
        # 模擬任務執行
        await asyncio.sleep(0.5)
        
        result = {
            'cleaned_count': 25,
            'freed_space': '10MB',
            'duration': 0.5
        }
        
        print(f"✅ 代理清理任務完成: {task.name}")
        return result
    
    async def execute_system_maintenance(self, task: Task) -> Dict[str, Any]:
        """執行系統維護任務"""
        print(f"🔧 開始執行系統維護任務: {task.name}")
        
        # 模擬任務執行
        await asyncio.sleep(3)
        
        result = {
            'maintenance_type': 'database_cleanup',
            'cleaned_tables': ['logs', 'stats'],
            'freed_space': '50MB',
            'duration': 3.0
        }
        
        print(f"✅ 系統維護任務完成: {task.name}")
        return result
    
    async def execute_data_export(self, task: Task) -> Dict[str, Any]:
        """執行數據導出任務"""
        print(f"📊 開始執行數據導出任務: {task.name}")
        
        # 模擬任務執行
        await asyncio.sleep(1.5)
        
        result = {
            'export_format': 'json',
            'exported_count': 500,
            'file_size': '2MB',
            'file_path': '/exports/data_20241201.json',
            'duration': 1.5
        }
        
        print(f"✅ 數據導出任務完成: {task.name}")
        return result


async def test_task_lifecycle():
    """測試任務完整生命週期"""
    print("🚀 開始測試任務生命週期...")
    
    # 獲取任務管理器
    manager = await get_task_manager()
    
    # 啟動任務管理器（這會啟動工作器）
    manager_task = asyncio.create_task(manager.start())
    
    # 等待管理器啟動
    await asyncio.sleep(1)
    
    # 註冊模擬執行器
    executor = MockTaskExecutor()
    
    # 註冊不同類型的任務執行器
    manager.executors = {
        TaskType.PROXY_SCRAPING: executor.execute_proxy_scraping,
        TaskType.PROXY_VALIDATION: executor.execute_proxy_validation,
        TaskType.PROXY_CLEANUP: executor.execute_proxy_cleanup,
        TaskType.SYSTEM_MAINTENANCE: executor.execute_system_maintenance,
        TaskType.DATA_EXPORT: executor.execute_data_export,
    }
    
    # 創建不同類型的任務
    tasks = []
    
    # 1. 創建代理爬取任務（高優先級）
    task1_id = await manager.create_task(
        name="代理爬取任務-測試",
        task_type=TaskType.PROXY_SCRAPING,
        config=TaskConfig(timeout=300, priority=8, tags=['scraping', 'test'])
    )
    tasks.append(task1_id)
    print(f"✅ 創建代理爬取任務: {task1_id}")
    
    # 2. 創建代理驗證任務（中優先級）
    task2_id = await manager.create_task(
        name="代理驗證任務-測試",
        task_type=TaskType.PROXY_VALIDATION,
        config=TaskConfig(timeout=180, priority=5, tags=['validation', 'test'])
    )
    tasks.append(task2_id)
    print(f"✅ 創建代理驗證任務: {task2_id}")
    
    # 3. 創建代理清理任務（低優先級）
    task3_id = await manager.create_task(
        name="代理清理任務-測試",
        task_type=TaskType.PROXY_CLEANUP,
        config=TaskConfig(timeout=120, priority=2, tags=['cleanup', 'test'])
    )
    tasks.append(task3_id)
    print(f"✅ 創建代理清理任務: {task3_id}")
    
    # 4. 創建系統維護任務（最高優先級）
    task4_id = await manager.create_task(
        name="系統維護任務-測試",
        task_type=TaskType.SYSTEM_MAINTENANCE,
        config=TaskConfig(timeout=600, priority=10, tags=['maintenance', 'system'])
    )
    tasks.append(task4_id)
    print(f"✅ 創建系統維護任務: {task4_id}")
    
    # 5. 創建數據導出任務（中優先級）
    task5_id = await manager.create_task(
        name="數據導出任務-測試",
        task_type=TaskType.DATA_EXPORT,
        config=TaskConfig(timeout=240, priority=6, tags=['export', 'data'])
    )
    tasks.append(task5_id)
    print(f"✅ 創建數據導出任務: {task5_id}")
    
    print(f"\n📊 總共創建了 {len(tasks)} 個任務")
    
    # 等待一段時間讓任務執行
    print("\n⏳ 等待任務執行...")
    await asyncio.sleep(15)
    
    # 檢查任務狀態
    print("\n📋 檢查任務狀態:")
    for task_id in tasks:
        task = await manager.get_task(task_id)
        if task:
            status_emoji = {
                TaskStatus.PENDING: "⏳",
                TaskStatus.QUEUED: "📋",
                TaskStatus.RUNNING: "🔄",
                TaskStatus.COMPLETED: "✅",
                TaskStatus.FAILED: "❌",
                TaskStatus.CANCELLED: "🚫",
                TaskStatus.TIMEOUT: "⏰"
            }.get(task.status, "❓")
            
            print(f"{status_emoji} {task.name}: {task.status.value}")
            if task.result:
                print(f"   結果: {task.result}")
            if task.error_message:
                print(f"   錯誤: {task.error_message}")
    
    # 獲取統計信息
    print("\n📈 系統統計信息:")
    stats = manager.get_stats()
    print(f"運行狀態: {'運行中' if stats['is_running'] else '已停止'}")
    print(f"工作器數量: {stats['worker_count']}")
    print(f"運行時間: {stats['uptime']:.1f} 秒")
    print(f"隊列大小: {stats['queue']['queue_size']}")
    print(f"待處理任務: {stats['queue']['pending_count']}")
    
    # 顯示工作器狀態
    print("\n👷 工作器狀態:")
    for i, worker_stat in enumerate(stats['workers']):
        status = "🟢 運行中" if worker_stat['is_running'] else "🔴 停止"
        current_task = worker_stat['current_task'] or "空閒"
        print(f"工作器 {i+1}: {status} - 當前任務: {current_task}")
        print(f"  已完成任務: {worker_stat['task_count']} | 錯誤次數: {worker_stat['error_count']}")
    
    print("\n✅ 任務生命週期測試完成！")
    
    # 停止任務管理器
    await manager.stop()
    manager_task.cancel()
    try:
        await manager_task
    except asyncio.CancelledError:
        pass


async def test_task_priorities():
    """測試任務優先級處理"""
    print("\n🎯 開始測試任務優先級...")
    
    manager = await get_task_manager()
    
    # 創建不同優先級的任務
    priorities = [1, 3, 5, 7, 9]
    task_ids = []
    
    for i, priority in enumerate(priorities):
        task_id = await manager.create_task(
            name=f"優先級測試任務-{priority}",
            task_type=TaskType.PROXY_VALIDATION,
            config=TaskConfig(timeout=60, priority=priority, tags=['priority_test'])
        )
        task_ids.append((priority, task_id))
        print(f"✅ 創建優先級 {priority} 的任務: {task_id}")
    
    # 等待任務處理
    await asyncio.sleep(8)
    
    # 檢查任務完成順序
    print("\n📊 任務完成情況:")
    for priority, task_id in task_ids:
        task = await manager.get_task(task_id)
        if task:
            print(f"優先級 {priority}: {task.status.value}")
    
    print("✅ 任務優先級測試完成！")


async def test_task_recovery():
    """測試任務恢復功能"""
    print("\n🔄 開始測試任務恢復...")
    
    manager = await get_task_manager()
    
    # 創建一些任務
    task_id = await manager.create_task(
        name="恢復測試任務",
        task_type=TaskType.PROXY_SCRAPING,
        config=TaskConfig(timeout=300, priority=5)
    )
    
    # 模擬系統崩潰，將任務狀態設置為運行中
    task = await manager.get_task(task_id)
    if task:
        task.status = TaskStatus.RUNNING
        # 這裡應該更新數據庫，但我們只是模擬
        print(f"📝 模擬任務 {task_id} 在運行中")
    
    # 測試恢復功能
    await manager.recover_tasks()
    
    # 檢查任務是否被恢復
    recovered_task = await manager.get_task(task_id)
    if recovered_task:
        print(f"✅ 任務狀態: {recovered_task.status.value}")
    
    print("✅ 任務恢復測試完成！")


async def main():
    """主測試函數"""
    print("🚀 開始任務狀態管理和執行流程測試")
    print("=" * 60)
    
    try:
        # 測試1: 任務生命週期
        await test_task_lifecycle()
        
        # 等待一下
        await asyncio.sleep(2)
        
        # 測試2: 任務優先級
        await test_task_priorities()
        
        # 等待一下
        await asyncio.sleep(2)
        
        # 測試3: 任務恢復
        await test_task_recovery()
        
        print("\n" + "=" * 60)
        print("🎉 所有測試完成！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())