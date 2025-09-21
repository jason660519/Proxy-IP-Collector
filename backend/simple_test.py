"""
簡化任務執行器測試
"""
import asyncio
import json
from datetime import datetime
from app.services.task_executor import TaskExecutor

async def test_task_executor():
    """測試任務執行器"""
    print("開始測試任務執行器...")
    
    async with TaskExecutor() as executor:
        # 測試健康檢查任務
        print("\n1. 測試健康檢查任務")
        health_task = {
            'id': 'health-test-1',
            'type': 'health_check',
            'config': {
                'proxy_urls': ['http://httpbin.org/ip'],
                'timeout': 5,
                'retry_count': 1
            }
        }
        
        result = await executor.execute_task(health_task)
        print(f"健康檢查結果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # 測試數據收集任務
        print("\n2. 測試數據收集任務")
        collection_task = {
            'id': 'collection-test-1',
            'type': 'data_collection',
            'config': {
                'proxy_sources': ['free-proxy-list.net'],
                'max_proxies': 5,
                'timeout': 10
            }
        }
        
        result = await executor.execute_task(collection_task)
        print(f"數據收集結果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        print("\n測試完成！")

if __name__ == "__main__":
    asyncio.run(test_task_executor())