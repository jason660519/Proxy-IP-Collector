"""
SQLite配置和連接管理模塊
提供SQLite數據庫的連接池和配置管理
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class SQLiteConfig:
    """SQLite配置管理類"""
    
    def __init__(self):
        self.db_path: str = self._get_db_path()
        self.connection_timeout: int = int(os.getenv('SQLITE_TIMEOUT', '30'))
        self.check_same_thread: bool = False
        self.isolation_level: Optional[str] = None
        
    def _get_db_path(self) -> str:
        """獲取SQLite數據庫文件路徑"""
        # 優先使用環境變量指定的路徑
        env_path = os.getenv('SQLITE_DATABASE_URL')
        if env_path:
            # 處理 sqlite:/// 前綴
            if env_path.startswith('sqlite:///'):
                return env_path.replace('sqlite:///', '')
            return env_path
        
        # 默認使用項目目錄下的數據庫文件
        project_root = Path(__file__).parent.parent.parent
        db_dir = project_root / 'data'
        db_dir.mkdir(exist_ok=True)
        return str(db_dir / 'proxy_collector.db')
    
    def get_connection_params(self) -> Dict[str, Any]:
        """獲取數據庫連接參數"""
        return {
            'database': self.db_path,
            'timeout': self.connection_timeout,
            'check_same_thread': self.check_same_thread,
            'isolation_level': self.isolation_level
        }

class SQLiteManager:
    """SQLite數據庫管理器"""
    
    def __init__(self, config: Optional[SQLiteConfig] = None):
        self.config = config or SQLiteConfig()
        self._ensure_database_exists()
        self._initialize_schema()
    
    def _ensure_database_exists(self):
        """確保數據庫文件存在"""
        db_path = Path(self.config.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not db_path.exists():
            # 創建空數據庫文件
            db_path.touch()
            logger.info(f"創建SQLite數據庫文件: {db_path}")
    
    def _initialize_schema(self):
        """初始化數據庫架構"""
        try:
            schema_path = Path(__file__).parent.parent / 'database_schema.sql'
            if schema_path.exists():
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                
                with self.get_connection() as conn:
                    # 啟用外鍵支持
                    conn.execute('PRAGMA foreign_keys = ON')
                    # 執行架構腳本
                    conn.executescript(schema_sql)
                    logger.info("SQLite數據庫架構初始化完成")
            else:
                logger.warning(f"數據庫架構文件不存在: {schema_path}")
        except Exception as e:
            logger.error(f"SQLite數據庫初始化失敗: {e}")
            raise
    
    @contextmanager
    def get_connection(self) -> sqlite3.Connection:
        """獲取數據庫連接（上下文管理器）"""
        conn = None
        try:
            conn = sqlite3.connect(**self.config.get_connection_params())
            conn.row_factory = sqlite3.Row  # 啟用字典式行訪問
            conn.execute('PRAGMA foreign_keys = ON')  # 啟用外鍵約束
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"SQLite數據庫操作失敗: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """執行查詢語句"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """執行更新語句"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            return cursor.rowcount
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """批量執行語句"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """獲取表信息"""
        query = "PRAGMA table_info(?)"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (table_name,))
            columns = cursor.fetchall()
            
            return {
                'columns': [dict(col) for col in columns],
                'column_count': len(columns)
            }
    
    def get_database_stats(self) -> Dict[str, Any]:
        """獲取數據庫統計信息"""
        stats = {}
        
        # 獲取所有表
        tables_query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        tables = self.execute_query(tables_query)
        
        for table in tables:
            table_name = table['name']
            count_query = f"SELECT COUNT(*) as count FROM {table_name}"
            count_result = self.execute_query(count_query)
            stats[table_name] = count_result[0]['count'] if count_result else 0
        
        # 獲取數據庫文件信息
        db_path = self.config.db_path
        if os.path.exists(db_path):
            file_stats = os.stat(db_path)
            stats['database_size_bytes'] = file_stats.st_size
            stats['database_size_mb'] = round(file_stats.st_size / (1024 * 1024), 2)
            stats['last_modified'] = datetime.fromtimestamp(file_stats.st_mtime).isoformat()
        
        # 獲取SQLite版本信息
        version_query = "SELECT sqlite_version() as version"
        version_result = self.execute_query(version_query)
        if version_result:
            stats['sqlite_version'] = version_result[0]['version']
        
        return stats
    
    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """備份數據庫"""
        if not backup_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{self.config.db_path}.backup_{timestamp}"
        
        try:
            with self.get_connection() as conn:
                backup_conn = sqlite3.connect(backup_path)
                conn.backup(backup_conn)
                backup_conn.close()
            
            logger.info(f"SQLite數據庫備份成功: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"SQLite數據庫備份失敗: {e}")
            raise
    
    def vacuum_database(self):
        """清理數據庫"""
        try:
            with self.get_connection() as conn:
                conn.execute('VACUUM')
            logger.info("SQLite數據庫清理完成")
        except Exception as e:
            logger.error(f"SQLite數據庫清理失敗: {e}")
            raise
    
    def get_system_config(self, config_key: str, default_value: Any = None) -> Any:
        """獲取系統配置值"""
        query = "SELECT config_value, config_type FROM system_configs WHERE config_key = ?"
        result = self.execute_query(query, (config_key,))
        
        if not result:
            return default_value
        
        config_value = result[0]['config_value']
        config_type = result[0]['config_type']
        
        # 根據類型轉換值
        if config_type == 'int':
            return int(config_value)
        elif config_type == 'float':
            return float(config_value)
        elif config_type == 'boolean':
            return config_value.lower() in ('true', '1', 'yes', 'on')
        elif config_type == 'json':
            try:
                return json.loads(config_value)
            except json.JSONDecodeError:
                return default_value
        else:
            return config_value
    
    def set_system_config(self, config_key: str, config_value: Any, config_type: str = 'string', description: str = ''):
        """設置系統配置值"""
        # 根據類型轉換值為字符串
        if config_type == 'json' and isinstance(config_value, (dict, list)):
            config_value = json.dumps(config_value)
        else:
            config_value = str(config_value)
        
        query = """
        INSERT OR REPLACE INTO system_configs 
        (config_key, config_value, config_type, description, updated_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        """
        self.execute_update(query, (config_key, config_value, config_type, description))

# 全局SQLite管理器實例
sqlite_manager = SQLiteManager()

def get_sqlite_manager() -> SQLiteManager:
    """獲取全局SQLite管理器實例"""
    return sqlite_manager

def init_sqlite_database():
    """初始化SQLite數據庫（用於應用啟動時調用）"""
    global sqlite_manager
    sqlite_manager = SQLiteManager()
    logger.info("SQLite數據庫管理器初始化完成")

def get_database_stats() -> Dict[str, Any]:
    """獲取數據庫統計信息"""
    return sqlite_manager.get_database_stats()

def backup_database(backup_path: Optional[str] = None) -> str:
    """備份數據庫"""
    return sqlite_manager.backup_database(backup_path)