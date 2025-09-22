-- SQLite Database Schema for Proxy Collector
-- 增強版架構，支持完整功能

-- 代理服務器表（增強版）
CREATE TABLE IF NOT EXISTS proxies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT NOT NULL,
    port INTEGER NOT NULL,
    protocol TEXT NOT NULL,
    country TEXT,
    region TEXT,
    city TEXT,
    anonymity_level TEXT,
    response_time_ms INTEGER,
    reliability_score REAL DEFAULT 0.00,
    last_verified TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    source_name TEXT,
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

-- 代理驗證結果表
CREATE TABLE IF NOT EXISTS proxy_validation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proxy_id INTEGER NOT NULL,
    is_valid BOOLEAN NOT NULL,
    response_time_ms INTEGER,
    anonymity_check BOOLEAN,
    location_check BOOLEAN,
    speed_test_result REAL,
    error_message TEXT,
    tested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proxy_id) REFERENCES proxies(id) ON DELETE CASCADE
);

-- 代理使用統計表
CREATE TABLE IF NOT EXISTS proxy_usage_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proxy_id INTEGER NOT NULL,
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    average_response_time_ms INTEGER,
    last_used TIMESTAMP,
    date DATE NOT NULL,
    FOREIGN KEY (proxy_id) REFERENCES proxies(id) ON DELETE CASCADE,
    UNIQUE(proxy_id, date)
);

-- 代理來源表
CREATE TABLE IF NOT EXISTS proxy_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_url TEXT,
    api_key TEXT,
    request_config TEXT,
    is_active BOOLEAN DEFAULT 1,
    last_sync TIMESTAMP,
    sync_interval_minutes INTEGER DEFAULT 60,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_name)
);

-- 系統配置表
CREATE TABLE IF NOT EXISTS system_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT NOT NULL,
    config_value TEXT,
    config_type TEXT DEFAULT 'string',
    description TEXT,
    is_secret BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(config_key)
);

-- 性能指標表
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL,
    metric_unit TEXT,
    metric_type TEXT NOT NULL,
    labels TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 任務管理表（增強版）
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

-- 插入默認系統配置
INSERT OR IGNORE INTO system_configs (config_key, config_value, config_type, description) VALUES
('proxy_validation_timeout', '30', 'int', '代理驗證超時時間（秒）'),
('proxy_pool_min_size', '50', 'int', '代理池最小數量'),
('proxy_validation_interval', '300', 'int', '代理驗證間隔（秒）'),
('scraping_max_retries', '3', 'int', '爬蟲最大重試次數'),
('scraping_retry_delay', '5', 'int', '爬蟲重試延遲（秒）'),
('monitoring_enabled', 'true', 'boolean', '是否啟用監控'),
('logging_level', 'INFO', 'string', '日誌級別'),
('rate_limit_requests_per_minute', '100', 'int', '每分鐘請求限制'),
('proxy_rotation_enabled', 'true', 'boolean', '是否啟用代理輪換'),
('data_retention_days', '30', 'int', '數據保留天數'),
('prometheus_enabled', 'true', 'boolean', '是否啟用Prometheus監控'),
('redis_enabled', 'false', 'boolean', '是否啟用Redis緩存'),
('database_connection_pool_size', '10', 'int', '數據庫連接池大小');

-- 插入默認代理來源
INSERT OR IGNORE INTO proxy_sources (source_name, source_type, source_url, is_active, sync_interval_minutes) VALUES
('FreeProxyList', 'web_scraping', 'https://www.freeproxy-list.net/', 1, 60),
('ProxyScrapeAPI', 'api', 'https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all&simplified=true', 1, 30),
('GeonodeAPI', 'api', 'https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc', 1, 30);

-- 創建視圖：活躍代理統計
CREATE VIEW IF NOT EXISTS active_proxy_stats AS
SELECT 
    country,
    protocol,
    anonymity_level,
    COUNT(*) as proxy_count,
    AVG(reliability_score) as avg_reliability,
    AVG(response_time_ms) as avg_speed,
    MAX(last_verified) as last_verified
FROM proxies 
WHERE is_active = 1 
GROUP BY country, protocol, anonymity_level;

-- 創建視圖：代理使用統計摘要
CREATE VIEW IF NOT EXISTS proxy_usage_summary AS
SELECT 
    p.id,
    p.ip_address,
    p.port,
    p.protocol,
    p.country,
    COALESCE(SUM(us.total_requests), 0) as total_requests,
    COALESCE(SUM(us.successful_requests), 0) as successful_requests,
    COALESCE(ROUND(CAST(SUM(us.successful_requests) AS REAL) * 100.0 / NULLIF(SUM(us.total_requests), 0), 2), 0) as success_rate,
    COALESCE(AVG(us.average_response_time_ms), 0) as avg_response_time,
    MAX(us.last_used) as last_used
FROM proxies p
LEFT JOIN proxy_usage_stats us ON p.id = us.proxy_id
WHERE p.is_active = 1
GROUP BY p.id, p.ip_address, p.port, p.protocol, p.country;

-- 創建索引
CREATE INDEX IF NOT EXISTS idx_proxies_composite ON proxies(ip, port, protocol, is_active);
CREATE INDEX IF NOT EXISTS idx_proxies_reliability ON proxies(reliability_score);
CREATE INDEX IF NOT EXISTS idx_proxies_response_time ON proxies(response_time_ms);
CREATE INDEX IF NOT EXISTS idx_proxies_source ON proxies(source_name);
CREATE INDEX IF NOT EXISTS idx_proxies_location ON proxies(country, region, city);

CREATE INDEX IF NOT EXISTS idx_proxy_validation_proxy_id ON proxy_validation_results(proxy_id);
CREATE INDEX IF NOT EXISTS idx_proxy_validation_valid ON proxy_validation_results(is_valid);
CREATE INDEX IF NOT EXISTS idx_proxy_validation_tested_at ON proxy_validation_results(tested_at);

CREATE INDEX IF NOT EXISTS idx_proxy_usage_proxy_id ON proxy_usage_stats(proxy_id);
CREATE INDEX IF NOT EXISTS idx_proxy_usage_date ON proxy_usage_stats(date);

CREATE INDEX IF NOT EXISTS idx_performance_metrics_name ON performance_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_task_type ON tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_tasks_worker_id ON tasks(worker_id);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_started ON tasks(started_at);
