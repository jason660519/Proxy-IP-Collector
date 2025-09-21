"""
SQLite配置方案 - 為開發環境提供數據庫支持

這個腳本會創建一個SQLite版本的配置文件，讓系統可以在沒有PostgreSQL的情況下運行
"""

import os
import sqlite3
from pathlib import Path
import shutil
from datetime import datetime


def create_sqlite_config():
    """創建SQLite配置文件"""
    
    # 創建數據目錄
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # 創建SQLite數據庫文件
    db_path = data_dir / "proxy_collector.db"
    
    print(f"🚀 創建SQLite數據庫配置...")
    print(f"   數據庫路徑: {db_path}")
    
    try:
        # 連接到SQLite數據庫
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 創建代理表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proxies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                port INTEGER NOT NULL,
                protocol TEXT DEFAULT 'http',
                country TEXT,
                anonymity_level TEXT,
                response_time REAL,
                success_rate REAL DEFAULT 0.0,
                last_checked TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 創建任務表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                config TEXT,
                result TEXT,
                error_message TEXT,
                scheduled_at TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 創建爬蟲結果表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crawler_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                proxy_count INTEGER DEFAULT 0,
                new_proxies INTEGER DEFAULT 0,
                failed_proxies INTEGER DEFAULT 0,
                execution_time REAL,
                status TEXT DEFAULT 'success',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 創建系統日誌表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                module TEXT,
                function TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 創建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_proxies_ip_port ON proxies(ip, port)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_proxies_active ON proxies(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_proxies_protocol ON proxies(protocol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(task_type)")
        
        # 插入測試數據
        cursor.execute("""
            INSERT OR IGNORE INTO proxies (ip, port, protocol, country, anonymity_level, response_time, is_active)
            VALUES 
                ('127.0.0.1', 8080, 'http', 'US', 'elite', 0.5, TRUE),
                ('192.168.1.1', 3128, 'http', 'US', 'anonymous', 1.2, TRUE)
        """)
        
        cursor.execute("""
            INSERT OR IGNORE INTO tasks (name, task_type, status, config)
            VALUES 
                ('測試任務1', 'proxy_validation', 'completed', '{"timeout": 10}'),
                ('測試任務2', 'proxy_crawling', 'pending', '{"source": "free-proxy-list"}')
        """)
        
        conn.commit()
        
        # 獲取表信息
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        # 獲取每個表的記錄數
        table_stats = {}
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            table_stats[table_name] = count
        
        conn.close()
        
        print(f"✅ SQLite數據庫創建成功！")
        print(f"   表數量: {len(tables)}")
        for table, count in table_stats.items():
            print(f"   - {table}: {count} 條記錄")
        
        return {
            "status": "success",
            "database_path": str(db_path),
            "tables": table_stats,
            "message": "SQLite數據庫配置完成"
        }
        
    except Exception as e:
        print(f"❌ SQLite數據庫創建失敗: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
            "message": f"SQLite數據庫創建失敗: {str(e)}"
        }


def create_sqlite_env_file():
    """創建SQLite環境變量文件"""
    
    env_content = """# SQLite配置 - 開發環境使用
DATABASE_URL=sqlite:///data/proxy_collector.db
REDIS_URL=memory://  # 使用內存存儲代替Redis

# 應用配置
APP_NAME=代理收集器 (開發模式)
APP_VERSION=1.0.0
DEBUG=true
ENVIRONMENT=development

# 服務器配置
HOST=0.0.0.0
PORT=8000
WORKERS=1

# 日誌配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
MAX_LOG_SIZE=10485760
BACKUP_COUNT=5

# 爬蟲配置
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
RETRY_ATTEMPTS=3
RETRY_DELAY=1

# 代理驗證配置
VALIDATION_TIMEOUT=10
MAX_VALIDATION_THREADS=5

# 速率限制
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10
"""
    
    try:
        with open(".env.sqlite", "w", encoding="utf-8") as f:
            f.write(env_content)
        
        print(f"✅ SQLite環境文件創建成功: .env.sqlite")
        return {"status": "success", "file": ".env.sqlite"}
        
    except Exception as e:
        print(f"❌ 環境文件創建失敗: {str(e)}")
        return {"status": "failed", "error": str(e)}


def create_startup_script():
    """創建啟動腳本"""
    
    startup_script = """#!/bin/bash
# SQLite開發環境啟動腳本

echo "🚀 啟動代理收集器 (SQLite開發模式)..."

# 檢查Python虛擬環境
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  警告: 未檢測到虛擬環境，建議使用 uv shell 激活"
fi

# 創建必要的目錄
mkdir -p logs data

# 複製SQLite配置
cp .env.sqlite .env

# 運行數據庫初始化
echo "📊 初始化SQLite數據庫..."
python -c "
import sqlite3
from pathlib import Path

# 確保數據目錄存在
Path('data').mkdir(exist_ok=True)

# 連接數據庫（如果不存在會自動創建）
conn = sqlite3.connect('data/proxy_collector.db')
print('✅ SQLite數據庫連接成功')
conn.close()
"

# 啟動服務器
echo "🌐 啟動Web服務器..."
python unified_server.py
"""
    
    try:
        with open("start_sqlite_dev.sh", "w", encoding="utf-8") as f:
            f.write(startup_script)
        
        # Windows批處理文件
        windows_script = """@echo off
echo 正在啟動代理收集器 (SQLite開發模式)...

rem 檢查Python虛擬環境
if "%VIRTUAL_ENV%"=="" (
    echo ⚠️ 警告: 未檢測到虛擬環境，建議使用 uv shell 激活
)

rem 創建必要的目錄
if not exist logs mkdir logs
if not exist data mkdir data

rem 複製SQLite配置
copy .env.sqlite .env

rem 運行數據庫初始化
echo 📊 初始化SQLite數據庫...
python -c "import sqlite3; from pathlib import Path; Path('data').mkdir(exist_ok=True); conn = sqlite3.connect('data/proxy_collector.db'); print('✅ SQLite數據庫連接成功'); conn.close()"

rem 啟動服務器
echo 🌐 啟動Web服務器...
python unified_server.py
pause
"""
        
        with open("start_sqlite_dev.bat", "w", encoding="utf-8") as f:
            f.write(windows_script)
        
        print(f"✅ 啟動腳本創建成功:")
        print(f"   - Linux/macOS: start_sqlite_dev.sh")
        print(f"   - Windows: start_sqlite_dev.bat")
        
        return {"status": "success", "scripts": ["start_sqlite_dev.sh", "start_sqlite_dev.bat"]}
        
    except Exception as e:
        print(f"❌ 啟動腳本創建失敗: {str(e)}")
        return {"status": "failed", "error": str(e)}


def main():
    """主函數"""
    print("🚀 設置SQLite開發環境...")
    print("=" * 50)
    
    # 1. 創建SQLite數據庫
    print("\n1️⃣ 創建SQLite數據庫結構...")
    db_result = create_sqlite_config()
    
    if db_result["status"] == "failed":
        print(f"❌ 數據庫創建失敗，停止設置")
        return
    
    # 2. 創建環境文件
    print("\n2️⃣ 創建SQLite環境配置...")
    env_result = create_sqlite_env_file()
    
    # 3. 創建啟動腳本
    print("\n3️⃣ 創建啟動腳本...")
    script_result = create_startup_script()
    
    print("\n" + "=" * 50)
    print("✅ SQLite開發環境設置完成！")
    print("\n📋 使用說明：")
    print("1. 使用 .env.sqlite 文件作為開發環境配置")
    print("2. 運行 start_sqlite_dev.bat (Windows) 或 start_sqlite_dev.sh (Linux/macOS)")
    print("3. 系統將使用SQLite數據庫運行")
    print("\n🔧 文件說明：")
    print(f"   - .env.sqlite: SQLite環境配置")
    print(f"   - data/proxy_collector.db: SQLite數據庫文件")
    print(f"   - start_sqlite_dev.bat: Windows啟動腳本")
    print(f"   - start_sqlite_dev.sh: Linux/macOS啟動腳本")
    
    print("\n⚠️ 注意事項：")
    print("   - SQLite適合開發環境使用")
    print("   - 生產環境建議使用PostgreSQL")
    print("   - 數據庫文件會自動創建在 data/ 目錄下")


if __name__ == "__main__":
    main()