#!/usr/bin/env python3
"""
代理驗證系統快速測試腳本

這個腳本提供簡單的測試功能來驗證系統是否正常運行
"""

import asyncio
import sys
from pathlib import Path

# 添加父目錄到Python路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from validators import ProxyValidationService, ValidationConfigManager


async def test_basic_functionality():
    """測試基本功能"""
    print("測試代理驗證系統基本功能...")
    
    try:
        # 測試配置管理器
        print("1. 測試配置管理器...")
        config_manager = ValidationConfigManager()
        
        # 獲取預設配置
        default_config = await config_manager.get_preset_config("default")
        print(f"   ✓ 獲取預設配置成功: {len(default_config)} 個配置項")
        
        # 測試驗證服務
        print("2. 測試驗證服務...")
        service = ProxyValidationService()
        
        # 啟動服務
        await service.start_service()
        print("   ✓ 服務啟動成功")
        
        # 測試代理（使用無效代理來測試錯誤處理）
        test_proxy = {
            "ip": "192.168.255.255",  # 無效IP
            "port": 8080,
            "protocol": "http",
            "country": "US"
        }
        
        print("3. 測試代理驗證...")
        result = await service.quick_validate(test_proxy)
        
        if result:
            print(f"   ✓ 驗證完成 - 評分: {result.overall_score:.1f}")
            print(f"   ✓ 可用性: {'可用' if result.is_valid else '不可用'}")
        else:
            print("   ✓ 驗證返回None（預期行為）")
        
        # 停止服務
        await service.stop_service()
        print("   ✓ 服務停止成功")
        
        print("\n基本功能測試通過！✅")
        return True
        
    except Exception as e:
        print(f"\n測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_configuration_management():
    """測試配置管理"""
    print("\n測試配置管理功能...")
    
    try:
        config_manager = ValidationConfigManager()
        
        # 測試獲取所有預設配置
        presets = ["default", "strict", "fast", "comprehensive"]
        
        for preset in presets:
            config = await config_manager.get_preset_config(preset)
            if config:
                print(f"   ✓ {preset} 配置加載成功")
            else:
                print(f"   ⚠ {preset} 配置不可用")
        
        # 測試創建自定義配置
        custom_config = {
            "scoring_config": {"connectivity_weight": 0.5, "speed_weight": 0.5},
            "timeout": 10
        }
        
        await config_manager.save_config("test_custom", custom_config)
        print("   ✓ 自定義配置保存成功")
        
        # 測試加載自定義配置
        loaded_config = await config_manager.load_config("test_custom")
        if loaded_config:
            print("   ✓ 自定義配置加載成功")
        
        # 清理測試配置
        await config_manager.delete_config("test_custom")
        print("   ✓ 測試配置清理完成")
        
        print("配置管理測試通過！✅")
        return True
        
    except Exception as e:
        print(f"配置管理測試失敗: {e}")
        return False


async def test_service_integration():
    """測試服務集成"""
    print("\n測試服務集成功能...")
    
    try:
        # 使用自定義配置創建服務
        service = ProxyValidationService(config_name="default")
        
        # 獲取服務狀態
        status = service.get_service_status()
        print(f"   ✓ 服務狀態: {status}")
        
        # 測試批量驗證（小批量）
        test_proxies = [
            {"ip": "192.168.1.1", "port": 8080, "protocol": "http"},
            {"ip": "10.0.0.1", "port": 3128, "protocol": "https"}
        ]
        
        results = await service.validate_batch(test_proxies, max_concurrent=2)
        print(f"   ✓ 批量驗證完成: {len(results)} 個結果")
        
        # 測試統計數據
        stats = service.get_validation_stats()
        print(f"   ✓ 統計數據: {stats}")
        
        print("服務集成測試通過！✅")
        return True
        
    except Exception as e:
        print(f"服務集成測試失敗: {e}")
        return False


async def run_all_tests():
    """運行所有測試"""
    print("開始代理驗證系統測試...")
    print("=" * 50)
    
    test_results = []
    
    # 運行各個測試
    test_results.append(await test_basic_functionality())
    test_results.append(await test_configuration_management())
    test_results.append(await test_service_integration())
    
    # 總結結果
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 50)
    print(f"測試完成: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！系統運行正常")
        return True
    else:
        print("⚠️  部分測試失敗，請檢查錯誤信息")
        return False


if __name__ == "__main__":
    # 運行測試
    success = asyncio.run(run_all_tests())
    
    # 退出碼
    sys.exit(0 if success else 1)