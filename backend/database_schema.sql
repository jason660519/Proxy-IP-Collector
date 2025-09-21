-- SQLite Database Schema for Proxy Collector
-- Generated at: 2025-09-21T23:51:17.337327


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
