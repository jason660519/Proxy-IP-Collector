#!/bin/bash
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
