#!/usr/bin/env python3
"""
系統狀態檢查腳本
用於檢查代理收集器系統的核心組件運行狀態
"""

import sys
import os

# 添加後端路徑到Python路徑
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.append(backend_path)

def check_system_status():
    """檢查系統核心組件的運行狀態"""
    print("=== 系統狀態檢查 ===\n")
    
    all_passed = True
    
    # 檢查配置管理器
    try:
        from app.core.config_manager import get_config
        config = get_config()
        print("✅ 配置管理器: 正常")
        print(f"   環境: {config.environment}")
        print(f"   主機: {config.host}:{config.port}")
        print(f"   調試模式: {config.debug}")
        print(f"   數據庫類型: {config.database.type}")
        print(f"   數據庫URL: {config.database.url or config.database.database}")
        print()
    except Exception as e:
        print(f"❌ 配置管理器: 失敗 - {e}")
        all_passed = False
        print()
    
    # 檢查數據庫管理器
    try:
        from app.core.database_manager import get_db_manager
        db_manager = get_db_manager()
        print("✅ 數據庫管理器: 正常")
        print(f"   數據庫類型: {type(db_manager).__name__}")
        print()
    except Exception as e:
        print(f"❌ 數據庫管理器: 失敗 - {e}")
        all_passed = False
        print()
    
    # 檢查健康檢查管理器
    try:
        from app.core.health_check import get_health_manager
        health_manager = get_health_manager()
        print("✅ 健康檢查管理器: 正常")
        print(f"   管理器類型: {type(health_manager).__name__}")
        print()
    except Exception as e:
        print(f"❌ 健康檢查管理器: 失敗 - {e}")
        all_passed = False
        print()
    
    # 檢查監控系統
    try:
        from app.core.monitoring import get_metrics_exporter
        metrics_exporter = get_metrics_exporter()
        print("✅ 監控系統: 正常")
        print(f"   導出器類型: {type(metrics_exporter).__name__}")
        print()
    except Exception as e:
        print(f"❌ 監控系統: 失敗 - {e}")
        all_passed = False
        print()
    
    # 檢查代理池管理器
    try:
        import asyncio
        from app.core.proxy_pool import get_proxy_pool_manager
        proxy_pool = asyncio.run(get_proxy_pool_manager())
        print("✅ 代理池管理器: 正常")
        print(f"   管理器類型: {type(proxy_pool).__name__}")
        print()
    except Exception as e:
        print(f"❌ 代理池管理器: 失敗 - {e}")
        all_passed = False
        print()
    
    print("=== 檢查完成 ===")
    
    if all_passed:
        print("✅ 所有核心組件運行正常！")
        return True
    else:
        print("⚠️  部分組件存在問題，請查看詳細錯誤信息")
        return False

if __name__ == "__main__":
    check_system_status()