"""
數據庫架構定義和初始化腳本
Database schema definitions and initialization script
"""

import sqlite3
import asyncio
from typing import Dict, Any, List
from datetime import datetime
import json
from pathlib import Path

# SQL 架構定義
SQLITE_SCHEMA = """
-- 代理服務器表
CREATE TABLE IF NOT EXISTS proxies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT NOT NULL,
    port INTEGER NOT NULL,
    protocol TEXT NOT NULL,
    country TEXT,
    anonymity_level TEXT,
    response_time REAL,
    is_active BOOLEAN DEFAULT 1,
    last_verified TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ip, port, protocol)
);

-- 爬蟲任務表
CREATE TABLE IF NOT EXISTS crawler_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT UNIQUE NOT NULL,
    source_name TEXT NOT NULL,
    status TEXT NOT NULL,
    task_type TEXT NOT NULL,
    config TEXT,
    progress REAL DEFAULT 0,
    results_count INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 爬蟲統計表
CREATE TABLE IF NOT EXISTS crawler_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    total_proxies INTEGER DEFAULT 0,
    active_proxies INTEGER DEFAULT 0,
    last_crawl_time TIMESTAMP,
    success_rate REAL DEFAULT 0,
    average_response_time REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_name)
);

-- 系統日誌表
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    module TEXT,
    function TEXT,
    line_number INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extra_data TEXT
);

-- 任務管理表
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    task_type TEXT NOT NULL,
    status TEXT NOT NULL,
    config TEXT,
    result TEXT,
    error_message TEXT,
    worker_id TEXT,
    retry_count INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建索引
CREATE INDEX IF NOT EXISTS idx_proxies_ip_port ON proxies(ip, port);
CREATE INDEX IF NOT EXISTS idx_proxies_protocol ON proxies(protocol);
CREATE INDEX IF NOT EXISTS idx_proxies_country ON proxies(country);
CREATE INDEX IF NOT EXISTS idx_proxies_active ON proxies(is_active);
CREATE INDEX IF NOT EXISTS idx_proxies_created ON proxies(created_at);

CREATE INDEX IF NOT EXISTS idx_crawler_tasks_task_id ON crawler_tasks(task_id);
CREATE INDEX IF NOT EXISTS idx_crawler_tasks_status ON crawler_tasks(status);
CREATE INDEX IF NOT EXISTS idx_crawler_tasks_source ON crawler_tasks(source_name);
CREATE INDEX IF NOT EXISTS idx_crawler_tasks_created ON crawler_tasks(created_at);

CREATE INDEX IF NOT EXISTS idx_crawler_stats_source ON crawler_stats(source_name);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);

-- 任務管理表
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    task_type TEXT NOT NULL,
    status TEXT NOT NULL,
    config TEXT,
    result TEXT,
    error_message TEXT,
    worker_id TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 任務表索引
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_task_type ON tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_tasks_worker_id ON tasks(worker_id);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at);
"""

# PostgreSQL 架構（參考）
POSTGRESQL_SCHEMA = """
-- 代理服務器表
CREATE TABLE IF NOT EXISTS proxies (
    id SERIAL PRIMARY KEY,
    ip INET NOT NULL,
    port INTEGER NOT NULL CHECK (port > 0 AND port <= 65535),
    protocol VARCHAR(10) NOT NULL,
    country VARCHAR(2),
    anonymity_level VARCHAR(20),
    response_time REAL,
    is_active BOOLEAN DEFAULT TRUE,
    last_verified TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ip, port, protocol)
);

-- 爬蟲任務表
CREATE TABLE IF NOT EXISTS crawler_tasks (
    id SERIAL PRIMARY KEY,
    task_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    source_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    config JSONB,
    progress REAL DEFAULT 0,
    results_count INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 爬蟲統計表
CREATE TABLE IF NOT EXISTS crawler_stats (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) UNIQUE NOT NULL,
    total_proxies INTEGER DEFAULT 0,
    active_proxies INTEGER DEFAULT 0,
    last_crawl_time TIMESTAMP,
    success_rate REAL DEFAULT 0,
    average_response_time REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 系統日誌表
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    module VARCHAR(100),
    function VARCHAR(100),
    line_number INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extra_data JSONB
);

-- 創建索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_proxies_ip_port ON proxies(ip, port);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_proxies_protocol ON proxies(protocol);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_proxies_country ON proxies(country);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_proxies_active ON proxies(is_active);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_proxies_created ON proxies(created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_crawler_tasks_task_id ON crawler_tasks(task_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_crawler_tasks_status ON crawler_tasks(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_crawler_tasks_source ON crawler_tasks(source_name);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_crawler_tasks_created ON crawler_tasks(created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_crawler_stats_source ON crawler_stats(source_name);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);
"""

class DatabaseInitializer:
    """數據庫初始化器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or "data/proxy_collector.db"
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """確保數據目錄存在"""
        data_dir = Path(self.db_path).parent
        data_dir.mkdir(parents=True, exist_ok=True)
    
    def init_sqlite_database(self) -> bool:
        """初始化 SQLite 數據庫"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 執行架構創建
            cursor.executescript(SQLITE_SCHEMA)
            
            # 插入一些測試數據
            self.insert_test_data(cursor)
            
            conn.commit()
            conn.close()
            
            print(f"✅ SQLite 數據庫初始化成功: {self.db_path}")
            return True
            
        except Exception as e:
            print(f"❌ SQLite 數據庫初始化失敗: {e}")
            return False
    
    def insert_test_data(self, cursor: sqlite3.Cursor):
        """插入測試數據"""
        try:
            # 插入測試代理數據
            test_proxies = [
                ('192.168.1.100', 8080, 'http', 'US', 'elite', 0.5),
                ('10.0.0.1', 3128, 'https', 'GB', 'anonymous', 1.2),
                ('203.0.113.45', 8080, 'socks5', 'JP', 'transparent', 2.1),
            ]
            
            cursor.executemany("""
                INSERT OR IGNORE INTO proxies (ip, port, protocol, country, anonymity_level, response_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, test_proxies)
            
            print("✅ 代理測試數據插入成功")
            
            # 插入測試任務數據（crawler_tasks表）
            test_tasks = [
                ('test_task_1', 'free_proxy_list', 'completed', 'crawl', '{"url": "https://example.com"}', 100.0, 150),
                ('test_task_2', 'proxy_daily', 'running', 'crawl', '{"url": "https://proxydaily.com"}', 65.0, 89),
            ]
            
            cursor.executemany("""
                INSERT OR IGNORE INTO crawler_tasks (task_id, source_name, status, task_type, config, progress, results_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, test_tasks)
            
            print("✅ 爬蟲任務測試數據插入成功")
            
            # 插入測試統計數據
            test_stats = [
                ('free_proxy_list', 150, 120, datetime.now(), 85.5, 0.8),
                ('proxy_daily', 89, 67, datetime.now(), 78.2, 1.1),
            ]
            
            cursor.executemany("""
                INSERT OR IGNORE INTO crawler_stats (source_name, total_proxies, active_proxies, last_crawl_time, success_rate, average_response_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, test_stats)
            
            print("✅ 統計測試數據插入成功")
            
            # 插入測試任務管理數據（tasks表）
            test_management_tasks = [
                ('task_1', '代理爬取任務', 'crawl', 'pending', '{"source": "free_proxy_list"}', None, None, 'worker_1', 0),
                ('task_2', '代理驗證任務', 'validate', 'running', '{"proxy_ids": [1,2,3]}', None, None, 'worker_2', 1),
                ('task_3', '統計生成任務', 'stats', 'completed', '{"generate_report": true}', '{"total": 150, "active": 120}', None, 'worker_1', 0),
            ]
            
            cursor.executemany("""
                INSERT OR IGNORE INTO tasks (id, name, task_type, status, config, result, error_message, worker_id, retry_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, test_management_tasks)
            
            print("✅ 任務管理測試數據插入成功")
            
        except Exception as e:
            print(f"⚠️ 測試數據插入失敗: {e}")
    
    def verify_database(self) -> Dict[str, Any]:
        """驗證數據庫狀態"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 檢查表是否存在
            tables = ['proxies', 'crawler_tasks', 'crawler_stats', 'system_logs', 'tasks']
            results = {}
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                results[table] = {
                    'exists': True,
                    'row_count': count
                }
            
            conn.close()
            return {
                'status': 'healthy',
                'tables': results,
                'db_path': self.db_path
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'db_path': self.db_path
            }
    
    def export_schema_to_file(self, output_path: str = "database_schema.sql"):
        """導出架構到文件"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("-- SQLite Database Schema for Proxy Collector\n")
                f.write("-- Generated at: " + datetime.now().isoformat() + "\n\n")
                f.write(SQLITE_SCHEMA)
            
            print(f"✅ 架構導出成功: {output_path}")
            
        except Exception as e:
            print(f"❌ 架構導出失敗: {e}")

def main():
    """主函數"""
    print("🚀 開始初始化數據庫...")
    
    # 創建初始化器
    initializer = DatabaseInitializer()
    
    # 初始化 SQLite 數據庫
    if initializer.init_sqlite_database():
        # 驗證數據庫
        verification = initializer.verify_database()
        print(f"📊 數據庫驗證結果:")
        print(json.dumps(verification, indent=2, ensure_ascii=False))
        
        # 導出架構
        initializer.export_schema_to_file()
        
        print("\n✅ 數據庫初始化完成！")
        print("📁 數據文件位置:", initializer.db_path)
        
    else:
        print("\n❌ 數據庫初始化失敗！")

if __name__ == "__main__":
    main()