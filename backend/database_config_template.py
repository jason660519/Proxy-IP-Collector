
# 數據庫配置模板
DATABASE_CONFIG = {
    # PostgreSQL配置
    "postgresql": {
        "host": "localhost",
        "port": 5432,
        "database": "proxy_collector",
        "username": "your_username",
        "password": "your_password",
        "ssl_mode": "prefer"
    },
    
    # SQLite配置（開發環境）
    "sqlite": {
        "database_path": "./data/proxy_collector.db"
    },
    
    # 連接池配置
    "pool_config": {
        "min_connections": 5,
        "max_connections": 20,
        "connection_timeout": 30,
        "idle_timeout": 300
    }
}

# 使用方式：
# 1. 複製此配置到 config.py
# 2. 根據實際環境修改參數
# 3. 安裝相應的數據庫驅動
