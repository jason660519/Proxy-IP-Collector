#!/usr/bin/env python3
"""
代理驗證系統演示腳本

這個腳本展示了完整的代理驗證系統功能，包括：
1. 配置管理
2. 單個代理驗證
3. 批量代理驗證
4. 自動化任務調度
5. 統計數據分析
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

from . import (
    ProxyValidationService,
    ValidationConfigManager,
    ProxyValidationResult
)


async def demo_single_proxy_validation():
    """演示單個代理驗證"""
    print("=== 單個代理驗證演示 ===")
    
    # 創建驗證服務
    service = ProxyValidationService()
    
    # 啟動服務
    await service.start_service()
    
    # 測試代理列表（請替換為實際可用的代理）
    test_proxies = [
        {
            "ip": "8.8.8.8",
            "port": 8080,
            "protocol": "http",
            "country": "US",
            "source": "test"
        },
        {
            "ip": "1.1.1.1", 
            "port": 3128,
            "protocol": "https",
            "country": "US",
            "source": "test"
        }
    ]
    
    for proxy in test_proxies:
        print(f"\n驗證代理: {proxy['ip']}:{proxy['port']}")
        
        # 執行快速驗證
        result = await service.quick_validate(proxy)
        
        if result:
            print(f"驗證結果:")
            print(f"  - 可用性: {'可用' if result.is_valid else '不可用'}")
            print(f"  - 綜合評分: {result.overall_score:.2f}/100")
            print(f"  - 連接成功率: {result.connectivity_score:.1f}%")
            print(f"  - 響應時間: {result.response_time:.2f}ms")
            print(f"  - 匿名等級: {result.anonymity_level}")
            print(f"  - 地理位置: {result.geolocation}")
            print(f"  - 建議: {result.recommendations}")
        else:
            print("驗證失敗")
    
    # 停止服務
    await service.stop_service()


async def demo_batch_validation():
    """演示批量代理驗證"""
    print("\n=== 批量代理驗證演示 ===")
    
    service = ProxyValidationService()
    await service.start_service()
    
    # 生成更多測試代理
    batch_proxies = []
    for i in range(10):
        batch_proxies.append({
            "ip": f"192.168.1.{i+1}",
            "port": 8080 + i,
            "protocol": "http" if i % 2 == 0 else "https",
            "country": "US" if i % 3 == 0 else "CN" if i % 3 == 1 else "JP",
            "source": f"batch_{i}"
        })
    
    print(f"開始批量驗證 {len(batch_proxies)} 個代理...")
    
    # 執行批量驗證
    results = await service.validate_batch(batch_proxies, max_concurrent=5)
    
    # 統計結果
    valid_count = sum(1 for r in results if r and r.is_valid)
    total_score = sum(r.overall_score for r in results if r) / len(results) if results else 0
    
    print(f"\n批量驗證完成:")
    print(f"  - 總數: {len(results)}")
    print(f"  - 有效: {valid_count}")
    print(f"  - 無效: {len(results) - valid_count}")
    print(f"  - 平均評分: {total_score:.2f}")
    
    # 顯示前5個結果
    print("\n前5個代理的詳細結果:")
    for i, result in enumerate(results[:5]):
        if result:
            print(f"  {i+1}. {result.proxy_info.get('ip', 'Unknown')}:{result.proxy_info.get('port', 'Unknown')} "
                  f"- 評分: {result.overall_score:.1f} - {'有效' if result.is_valid else '無效'}")
    
    await service.stop_service()


async def demo_automated_scheduling():
    """演示自動化任務調度"""
    print("\n=== 自動化任務調度演示 ===")
    
    service = ProxyValidationService()
    await service.start_service()
    
    # 創建定期驗證任務
    test_proxies = [
        {"ip": "8.8.8.8", "port": 8080, "protocol": "http", "country": "US"},
        {"ip": "1.1.1.1", "port": 3128, "protocol": "https", "country": "US"}
    ]
    
    # 添加定期任務（每30秒執行一次）
    job_id = await service.schedule_validation(
        proxies=test_proxies,
        interval_seconds=30,
        job_name="demo_scheduled_validation"
    )
    
    print(f"已創建定期驗證任務: {job_id}")
    print("任務將在後台運行，按 Ctrl+C 停止...")
    
    try:
        # 讓任務運行一段時間
        await asyncio.sleep(120)  # 2分鐘
        
        # 獲取任務狀態
        status = service.get_job_status(job_id)
        print(f"\n任務狀態:")
        print(f"  - 運行狀態: {status.get('status', 'unknown')}")
        print(f"  - 執行次數: {status.get('execution_count', 0)}")
        print(f"  - 最後執行: {status.get('last_execution', 'never')}")
        
        # 獲取統計數據
        stats = service.get_validation_stats()
        print(f"\n驗證統計:")
        print(f"  - 總驗證數: {stats.get('total_validations', 0)}")
        print(f"  - 有效代理: {stats.get('valid_proxies', 0)}")
        print(f"  - 成功率: {stats.get('success_rate', 0):.1%}")
        
    except KeyboardInterrupt:
        print("\n停止演示...")
    
    # 停止任務和服務
    await service.stop_scheduled_job(job_id)
    await service.stop_service()


async def demo_configuration_management():
    """演示配置管理"""
    print("\n=== 配置管理演示 ===")
    
    config_manager = ValidationConfigManager()
    
    # 創建自定義配置
    custom_config = {
        "scoring_config": {
            "connectivity_weight": 0.4,
            "speed_weight": 0.3,
            "anonymity_weight": 0.2,
            "stability_weight": 0.1
        },
        "speed_config": {
            "timeout": 15,
            "test_url": "https://httpbin.org/delay/1",
            "max_concurrent": 3
        },
        "anonymity_config": {
            "test_urls": [
                "https://httpbin.org/headers",
                "https://api.ipify.org?format=json"
            ],
            "strict_mode": True
        }
    }
    
    # 保存配置
    config_name = "demo_custom_config"
    await config_manager.save_config(config_name, custom_config)
    print(f"已保存自定義配置: {config_name}")
    
    # 獲取所有配置
    all_configs = await config_manager.get_all_configs()
    print(f"\n可用配置: {list(all_configs.keys())}")
    
    # 使用自定義配置創建服務
    service = ProxyValidationService(config_name=config_name)
    await service.start_service()
    
    # 測試代理
    test_proxy = {"ip": "8.8.8.8", "port": 8080, "protocol": "http"}
    result = await service.quick_validate(test_proxy)
    
    if result:
        print(f"\n使用自定義配置驗證結果:")
        print(f"  - 評分: {result.overall_score:.2f}")
        print(f"  - 各項評分: {json.dumps(result.detailed_scores, indent=2, ensure_ascii=False)}")
    
    await service.stop_service()


async def demo_result_analysis():
    """演示結果分析"""
    print("\n=== 結果分析演示 ===")
    
    service = ProxyValidationService()
    await service.start_service()
    
    # 執行一些驗證
    test_proxies = [
        {"ip": "8.8.8.8", "port": 8080, "protocol": "http", "country": "US"},
        {"ip": "1.1.1.1", "port": 3128, "protocol": "https", "country": "US"},
        {"ip": "208.67.222.222", "port": 8080, "protocol": "http", "country": "US"}
    ]
    
    results = await service.validate_batch(test_proxies)
    
    # 分析結果
    print("\n結果分析:")
    
    # 按評分排序
    sorted_results = sorted(results, key=lambda x: x.overall_score if x else 0, reverse=True)
    
    print("\n按評分排序:")
    for i, result in enumerate(sorted_results[:3]):
        if result:
            print(f"  {i+1}. {result.proxy_info.get('ip', 'Unknown')} - 評分: {result.overall_score:.1f}")
    
    # 按國家分組
    country_groups = {}
    for result in results:
        if result:
            country = result.proxy_info.get('country', 'Unknown')
            if country not in country_groups:
                country_groups[country] = []
            country_groups[country].append(result)
    
    print(f"\n按國家分組:")
    for country, group_results in country_groups.items():
        avg_score = sum(r.overall_score for r in group_results) / len(group_results)
        valid_count = sum(1 for r in group_results if r.is_valid)
        print(f"  {country}: {len(group_results)}個代理, 平均評分: {avg_score:.1f}, 有效: {valid_count}")
    
    await service.stop_service()


async def main():
    """主函數 - 運行所有演示"""
    print("代理驗證系統完整演示")
    print("=" * 50)
    
    try:
        # 運行各個演示
        await demo_single_proxy_validation()
        await demo_batch_validation()
        await demo_configuration_management()
        await demo_result_analysis()
        
        # 注意: 自動化調度演示會運行較長時間，可以選擇性執行
        # await demo_automated_scheduling()
        
        print("\n" + "=" * 50)
        print("所有演示完成！")
        
    except Exception as e:
        print(f"演示過程中出現錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 運行演示
    asyncio.run(main())