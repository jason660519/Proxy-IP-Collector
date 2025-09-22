#!/usr/bin/env python3
"""
數據庫配置系統測試腳本
測試新的統一數據庫配置和連接管理功能
"""

import asyncio
import sys
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database_config import DatabaseConfig, DatabaseType
from app.core.database_manager import get_db_manager, init_db_manager, close_db_manager
from app.core.structured_logging import get_logger


async def test_database_config():
    """測試數據庫配置系統"""
    print("=== 測試數據庫配置系統 ===")
    
    # 測試默認配置
    print("\n1. 測試默認配置...")
    config = DatabaseConfig.from_env("DATABASE_")
    print(f"數據庫類型: {config.database_type}")
    print(f"數據庫路徑: {config.database}")
    print(f"主機: {config.host}:{config.port}")
    print(f"用戶名: {config.username}")
    
    # 測試SQLite配置
    print("\n2. 測試SQLite配置...")
    sqlite_config = DatabaseConfig(
        database_type=DatabaseType.SQLITE,
        database="./test_data/test.db"
    )
    print(f"SQLite配置: {sqlite_config.database}")
    
    # 測試PostgreSQL配置
    print("\n3. 測試PostgreSQL配置...")
    postgres_config = DatabaseConfig(
        database_type=DatabaseType.POSTGRESQL,
        host="localhost",
        port=5432,
        database="test_db",
        username="test_user",
        password="test_pass"
    )
    print(f"PostgreSQL配置: {postgres_config.host}:{postgres_config.port}/{postgres_config.database}")


async def test_database_manager():
    """測試數據庫管理器"""
    print("\n=== 測試數據庫管理器 ===")
    
    # 使用SQLite進行測試
    print("\n1. 測試SQLite連接...")
    sqlite_config = DatabaseConfig(
        database_type=DatabaseType.SQLITE,
        database="./test_data/test_manager.db"
    )
    
    # 初始化數據庫管理器
    success = await init_db_manager(sqlite_config)
    print(f"數據庫初始化: {'成功' if success else '失敗'}")
    
    if success:
        manager = get_db_manager()
        
        # 測試健康檢查
        print("\n2. 測試健康檢查...")
        health = await manager.health_check()
        print(f"健康狀態: {health}")
        
        # 測試數據庫信息
        print("\n3. 測試數據庫信息...")
        db_info = await manager.get_database_info()
        print(f"數據庫信息: {db_info}")
        
        # 測試連接統計
        print("\n4. 測試連接統計...")
        stats = manager.get_connection_stats()
        print(f"連接統計: {stats}")
        
        # 測試數據庫操作
        print("\n5. 測試數據庫操作...")
        try:
            if manager.config.database_type.value == "postgresql":
                # PostgreSQL 使用 SQLAlchemy 會話
                async with manager.get_session() as session:
                    result = await session.execute("SELECT 1")
                    value = result.scalar()
                    print(f"測試查詢結果: {value}")
            else:
                # SQLite 使用原生適配器
                result = await manager.engine.fetch_one("SELECT 1")
                print(f"測試查詢結果: {result}")
        except Exception as e:
            print(f"數據庫操作錯誤: {e}")
        
        # 關閉連接
        print("\n6. 關閉數據庫連接...")
        await close_db_manager()
        print("數據庫連接已關閉")


async def test_postgresql_connection():
    """測試PostgreSQL連接（如果可用）"""
    print("\n=== 測試PostgreSQL連接 ===")
    
    # 嘗試連接到PostgreSQL
    postgres_config = DatabaseConfig(
        database_type=DatabaseType.POSTGRESQL,
        host="localhost",
        port=5432,
        database="proxy_collector",
        username="postgres",
        password="password"
    )
    
    try:
        success = await init_db_manager(postgres_config)
        if success:
            print("PostgreSQL連接成功!")
            manager = get_db_manager()
            
            # 測試健康檢查
            health = await manager.health_check()
            print(f"PostgreSQL健康狀態: {health}")
            
            await close_db_manager()
        else:
            print("PostgreSQL連接失敗，請檢查配置和服務狀態")
    except Exception as e:
        print(f"PostgreSQL連接失敗: {e}")


async def main():
    """主測試函數"""
    # 設置日誌
    logger = get_logger("test_database")
    logger.info("開始數據庫配置測試")
    
    try:
        # 測試配置系統
        await test_database_config()
        
        # 測試SQLite管理器
        await test_database_manager()
        
        # 測試PostgreSQL（可選）
        await test_postgresql_connection()
        
        print("\n=== 所有測試完成 ===")
        
    except KeyboardInterrupt:
        print("\n測試被用戶中斷")
    except Exception as e:
        print(f"測試過程中發生錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())