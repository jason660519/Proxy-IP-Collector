"""
SQLite數據庫適配器

這個模塊提供SQLite數據庫連接和操作功能，作為PostgreSQL的替代方案
"""

import sqlite3
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class SQLiteAdapter:
    """SQLite數據庫適配器"""
    
    def __init__(self, db_path: str = None):
        # 使用絕對路徑，默認在項目根目錄的data文件夾
        if db_path is None:
            # 獲取當前文件的絕對路徑，然後找到項目根目錄
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent  # backend目錄
            self.db_path = project_root / "data" / "proxy_collector.db"
        else:
            self.db_path = Path(db_path).resolve()
        
        # 確保數據目錄存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = None
        
    def get_connection(self) -> sqlite3.Connection:
        """獲取數據庫連接"""
        if self._connection is None:
            self._connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,  # 允許多線程使用
                timeout=30.0  # 超時時間
            )
            # 設置行工廠，返回字典格式的結果
            self._connection.row_factory = self._dict_factory
            # 啟用外鍵支持
            self._connection.execute("PRAGMA foreign_keys = ON")
            # 設置同步模式
            self._connection.execute("PRAGMA synchronous = NORMAL")
            # 設置日誌模式
            self._connection.execute("PRAGMA journal_mode = WAL")
            
        return self._connection
    
    def _dict_factory(self, cursor, row):
        """將行轉換為字典"""
        fields = [column[0] for column in cursor.description]
        return {key: value for key, value in zip(fields, row)}
    
    def execute(self, query: str, params: tuple = None) -> sqlite3.Cursor:
        """執行SQL查詢"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor
        except Exception as e:
            conn.rollback()
            logger.error(f"SQL執行錯誤: {query}, 參數: {params}, 錯誤: {str(e)}")
            raise
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """獲取單條記錄"""
        cursor = self.execute(query, params)
        result = cursor.fetchone()
        cursor.close()
        return result
    
    def fetch_all(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """獲取所有記錄"""
        cursor = self.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        return results
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """插入數據"""
        columns = list(data.keys())
        placeholders = ', '.join(['?' for _ in columns])
        column_names = ', '.join(columns)
        
        query = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"
        params = tuple(data.values())
        
        cursor = self.execute(query, params)
        last_id = cursor.lastrowid
        cursor.close()
        
        return last_id
    
    def update(self, table: str, data: Dict[str, Any], where_clause: str, where_params: tuple = None) -> int:
        """更新數據"""
        set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        params = tuple(data.values())
        if where_params:
            params += where_params
        
        cursor = self.execute(query, params)
        affected_rows = cursor.rowcount
        cursor.close()
        
        return affected_rows
    
    def delete(self, table: str, where_clause: str, where_params: tuple = None) -> int:
        """刪除數據"""
        query = f"DELETE FROM {table} WHERE {where_clause}"
        cursor = self.execute(query, where_params)
        affected_rows = cursor.rowcount
        cursor.close()
        
        return affected_rows
    
    def close(self):
        """關閉數據庫連接"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("SQLite連接已關閉")
    
    def __enter__(self):
        """上下文管理器進入"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()


class AsyncSQLiteAdapter:
    """異步SQLite適配器"""
    
    def __init__(self, db_path: str = None):
        # 使用與同步適配器相同的邏輯
        self.sync_adapter = SQLiteAdapter(db_path)
    
    async def execute(self, query: str, params: tuple = None) -> sqlite3.Cursor:
        """異步執行SQL查詢"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.sync_adapter.execute, query, params)
    
    async def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """異步獲取單條記錄"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.sync_adapter.fetch_one, query, params)
    
    async def fetch_all(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """異步獲取所有記錄"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.sync_adapter.fetch_all, query, params)
    
    async def insert(self, table: str, data: Dict[str, Any]) -> int:
        """異步插入數據"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.sync_adapter.insert, table, data)
    
    async def update(self, table: str, data: Dict[str, Any], where_clause: str, where_params: tuple = None) -> int:
        """異步更新數據"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.sync_adapter.update, table, data, where_clause, where_params)
    
    async def delete(self, table: str, where_clause: str, where_params: tuple = None) -> int:
        """異步刪除數據"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.sync_adapter.delete, table, where_clause, where_params)
    
    async def close(self):
        """異步關閉連接"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.sync_adapter.close)


# 代理數據庫操作類
class ProxyDatabase:
    """代理數據庫操作類"""
    
    def __init__(self, adapter: Union[SQLiteAdapter, AsyncSQLiteAdapter]):
        self.adapter = adapter
    
    async def create_proxy(self, proxy_data: Dict[str, Any]) -> int:
        """創建代理記錄"""
        proxy_data['created_at'] = datetime.now()
        proxy_data['updated_at'] = datetime.now()
        return await self.adapter.insert('proxies', proxy_data)
    
    async def get_proxy_by_id(self, proxy_id: int) -> Optional[Dict[str, Any]]:
        """根據ID獲取代理"""
        return await self.adapter.fetch_one(
            "SELECT * FROM proxies WHERE id = ?",
            (proxy_id,)
        )
    
    async def get_active_proxies(self, protocol: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """獲取活動代理列表"""
        query = "SELECT * FROM proxies WHERE is_active = 1"
        params = []
        
        if protocol:
            query += " AND protocol = ?"
            params.append(protocol)
        
        query += " ORDER BY success_rate DESC, response_time ASC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        return await self.adapter.fetch_all(query, tuple(params) if params else None)
    
    async def update_proxy_status(self, proxy_id: int, is_active: bool, success_rate: float = None, response_time: float = None) -> int:
        """更新代理狀態"""
        update_data = {
            'is_active': is_active,
            'updated_at': datetime.now()
        }
        
        if success_rate is not None:
            update_data['success_rate'] = success_rate
        
        if response_time is not None:
            update_data['response_time'] = response_time
        
        return await self.adapter.update(
            'proxies',
            update_data,
            'id = ?',
            (proxy_id,)
        )
    
    async def delete_proxy(self, proxy_id: int) -> int:
        """刪除代理"""
        return await self.adapter.delete('proxies', 'id = ?', (proxy_id,))
    
    async def get_proxy_stats(self) -> Dict[str, Any]:
        """獲取代理統計信息"""
        total = await self.adapter.fetch_one("SELECT COUNT(*) as count FROM proxies")
        active = await self.adapter.fetch_one("SELECT COUNT(*) as count FROM proxies WHERE is_active = 1")
        by_protocol = await self.adapter.fetch_all(
            "SELECT protocol, COUNT(*) as count FROM proxies GROUP BY protocol"
        )
        
        return {
            'total': total['count'] if total else 0,
            'active': active['count'] if active else 0,
            'by_protocol': {row['protocol']: row['count'] for row in by_protocol}
        }


# 任務數據庫操作類
class TaskDatabase:
    """任務數據庫操作類"""
    
    def __init__(self, adapter: Union[SQLiteAdapter, AsyncSQLiteAdapter]):
        self.adapter = adapter
    
    async def create_task(self, task_data: Dict[str, Any]) -> int:
        """創建任務"""
        task_data['created_at'] = datetime.now()
        task_data['updated_at'] = datetime.now()
        task_data['status'] = task_data.get('status', 'pending')
        
        # 序列化配置和結果
        if 'config' in task_data and isinstance(task_data['config'], dict):
            task_data['config'] = json.dumps(task_data['config'])
        
        if 'result' in task_data and isinstance(task_data['result'], dict):
            task_data['result'] = json.dumps(task_data['result'])
        
        return await self.adapter.insert('tasks', task_data)
    
    async def get_task_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """根據ID獲取任務"""
        task = await self.adapter.fetch_one(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,)
        )
        
        # 反序列化配置和結果
        if task and task.get('config'):
            try:
                task['config'] = json.loads(task['config'])
            except (json.JSONDecodeError, TypeError):
                pass
        
        if task and task.get('result'):
            try:
                task['result'] = json.loads(task['result'])
            except (json.JSONDecodeError, TypeError):
                pass
        
        return task
    
    async def get_tasks_by_status(self, status: str, limit: int = None) -> List[Dict[str, Any]]:
        """根據狀態獲取任務"""
        query = "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC"
        params = [status]
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        tasks = await self.adapter.fetch_all(query, tuple(params))
        
        # 反序列化配置和結果
        for task in tasks:
            if task.get('config'):
                try:
                    task['config'] = json.loads(task['config'])
                except (json.JSONDecodeError, TypeError):
                    pass
            
            if task.get('result'):
                try:
                    task['result'] = json.loads(task['result'])
                except (json.JSONDecodeError, TypeError):
                    pass
        
        return tasks
    
    async def update_task_status(self, task_id: int, status: str, result: Dict[str, Any] = None, error_message: str = None) -> int:
        """更新任務狀態"""
        update_data = {
            'status': status,
            'updated_at': datetime.now()
        }
        
        if result:
            update_data['result'] = json.dumps(result)
        
        if error_message:
            update_data['error_message'] = error_message
        
        if status == 'running':
            update_data['started_at'] = datetime.now()
        elif status in ['completed', 'failed']:
            update_data['completed_at'] = datetime.now()
        
        return await self.adapter.update(
            'tasks',
            update_data,
            'id = ?',
            (task_id,)
        )
    
    async def delete_task(self, task_id: int) -> int:
        """刪除任務"""
        return await self.adapter.delete('tasks', 'id = ?', (task_id,))
    
    async def get_task_stats(self) -> Dict[str, Any]:
        """獲取任務統計信息"""
        total = await self.adapter.fetch_one("SELECT COUNT(*) as count FROM tasks")
        by_status = await self.adapter.fetch_all(
            "SELECT status, COUNT(*) as count FROM tasks GROUP BY status"
        )
        
        return {
            'total': total['count'] if total else 0,
            'by_status': {row['status']: row['count'] for row in by_status}
        }


# 創建數據庫連接工廠
class DatabaseFactory:
    """數據庫連接工廠"""
    
    @staticmethod
    def create_adapter(database_url: str) -> Union[SQLiteAdapter, AsyncSQLiteAdapter]:
        """根據數據庫URL創建適配器"""
        
        if database_url.startswith('sqlite'):
            # 解析SQLite URL
            db_path = database_url.replace('sqlite:///', '')
            if database_url.startswith('sqlite:///./'):
                db_path = database_url.replace('sqlite:///./', '')
            
            return AsyncSQLiteAdapter(db_path)
        else:
            # 對於PostgreSQL，返回None，由應用程序處理
            return None


# 測試函數
async def test_sqlite_adapter():
    """測試SQLite適配器"""
    print("🚀 測試SQLite適配器...")
    
    try:
        # 創建適配器 - 使用已經初始化的數據庫
        adapter = AsyncSQLiteAdapter()  # 使用默認路徑
        
        # 測試代理數據庫
        proxy_db = ProxyDatabase(adapter)
        
        # 創建測試代理
        proxy_data = {
            'ip': '192.168.1.100',
            'port': 8080,
            'protocol': 'http',
            'country': 'US',
            'anonymity_level': 'elite',
            'response_time': 0.5,
            'is_active': True,
            'success_rate': 0.95
        }
        
        proxy_id = await proxy_db.create_proxy(proxy_data)
        print(f"✅ 創建代理成功，ID: {proxy_id}")
        
        # 獲取代理
        proxy = await proxy_db.get_proxy_by_id(proxy_id)
        print(f"✅ 獲取代理成功: {proxy}")
        
        # 獲取活動代理
        active_proxies = await proxy_db.get_active_proxies(limit=10)
        print(f"✅ 獲取活動代理成功，數量: {len(active_proxies)}")
        
        # 獲取統計信息
        stats = await proxy_db.get_proxy_stats()
        print(f"✅ 代理統計: {stats}")
        
        # 測試任務數據庫
        task_db = TaskDatabase(adapter)
        
        # 創建任務
        task_data = {
            'name': '測試任務',
            'task_type': 'proxy_validation',
            'config': {'timeout': 30, 'retry_count': 3},
            'status': 'pending'
        }
        
        task_id = await task_db.create_task(task_data)
        print(f"✅ 創建任務成功，ID: {task_id}")
        
        # 獲取任務
        task = await task_db.get_task_by_id(task_id)
        print(f"✅ 獲取任務成功: {task}")
        
        # 更新任務狀態
        await task_db.update_task_status(task_id, 'completed', {'validated': 10, 'failed': 2})
        print(f"✅ 更新任務狀態成功")
        
        # 獲取任務統計
        task_stats = await task_db.get_task_stats()
        print(f"✅ 任務統計: {task_stats}")
        
        # 關閉連接
        await adapter.close()
        
        print("✅ SQLite適配器測試完成！")
        
    except Exception as e:
        print(f"❌ SQLite適配器測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_sqlite_adapter())