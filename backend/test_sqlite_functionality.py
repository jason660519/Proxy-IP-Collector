#!/usr/bin/env python3
"""
SQLite功能測試腳本
測試SQLite數據庫的基本CRUD操作
"""

import asyncio
import sys
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.database_config import DatabaseConfig, DatabaseType
from app.core.database_manager import get_db_manager, init_db_manager, close_db_manager
from app.core.structured_logging import get_logger


async def test_sqlite_crud():
    """測試SQLite的CRUD操作"""
    logger = get_logger("sqlite_test")
    
    print("=== 測試SQLite CRUD功能 ===")
    
    # 創建SQLite配置
    config = DatabaseConfig(
        database_type=DatabaseType.SQLITE,
        database="./test_data/crud_test.db",
        echo=True  # 啟用SQL日誌
    )
    
    try:
        # 初始化數據庫管理器
        print("1. 初始化數據庫管理器...")
        success = await init_db_manager(config)
        if not success:
            print("❌ 數據庫初始化失敗")
            return False
        
        manager = get_db_manager()
        print("✅ 數據庫初始化成功")
        
        # 測試創建表（應該已經自動創建）
        print("\n2. 測試數據表...")
        
        # 插入測試數據
        print("3. 插入測試數據...")
        insert_sql = """
        INSERT INTO proxies (ip, port, protocol, country, anonymity_level)
        VALUES (?, ?, ?, ?, ?)
        """
        test_data = [
            ("192.168.1.1", 8080, "http", "US", "elite"),
            ("10.0.0.1", 3128, "https", "UK", "anonymous"),
            ("172.16.0.1", 8080, "socks5", "JP", "transparent")
        ]
        
        for data in test_data:
            await manager.engine.execute(insert_sql, data)
        print("✅ 插入數據成功")
        
        # 查詢數據
        print("\n4. 查詢數據...")
        select_sql = "SELECT * FROM proxies WHERE country = ?"
        result = await manager.engine.fetch_all(select_sql, ("US",))
        print(f"找到 {len(result)} 個美國代理:")
        for row in result:
            print(f"  - {row['ip']}:{row['port']} ({row['protocol']})")
        
        # 更新數據
        print("\n5. 更新數據...")
        update_sql = "UPDATE proxies SET is_active = ? WHERE country = ?"
        await manager.engine.execute(update_sql, (False, "UK"))
        print("✅ 更新數據成功")
        
        # 刪除數據
        print("\n6. 刪除數據...")
        delete_sql = "DELETE FROM proxies WHERE anonymity_level = ?"
        await manager.engine.execute(delete_sql, ("transparent",))
        print("✅ 刪除數據成功")
        
        # 統計數據
        print("\n7. 統計數據...")
        count_sql = "SELECT COUNT(*) as count FROM proxies"
        result = await manager.engine.fetch_one(count_sql)
        print(f"剩餘代理數量: {result['count']}")
        
        # 健康檢查
        print("\n8. 健康檢查...")
        health = await manager.health_check()
        print(f"數據庫狀態: {health['status']}")
        print(f"連接統計: {health['connection_stats']}")
        
        print("\n✅ 所有SQLite測試通過!")
        return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        logger.error(f"SQLite測試失敗: {e}", exc_info=True)
        return False
        
    finally:
        # 清理資源
        print("\n9. 清理資源...")
        await close_db_manager()
        print("✅ 資源清理完成")


async def main():
    """主函數"""
    success = await test_sqlite_crud()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())