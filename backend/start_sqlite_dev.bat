@echo off
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
