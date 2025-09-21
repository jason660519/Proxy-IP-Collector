#!/usr/bin/env python3
"""
任務執行器測試腳本
用於驗證任務執行器的功能
"""

import asyncio
import logging
from datetime import datetime
from app.services.task_executor import TaskExecutor

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_task_executor():
    """測試任務執行器"""
    logger.info("開始測試任務執行器")
    
    # 創建執行器實例
    executor = TaskExecutor()
    
    # 測試數據收集任務
    logger.info("測試數據收集任務...")
    data_collection_task = {
        'id': 'test-data-collection',
        'type': 'data_collection',
        'config': {
            'proxy_url': 'http://example.com',
            'timeout': 30,
            'max_retries': 3
        },
        'parameters': {
            'target_url': 'https://example.com/data',
            'data_type': 'json'
        }
    }
    
    try:
        result = await executor.execute_task(data_collection_task)
        logger.info(f"數據收集任務結果: {result}")
    except Exception as e:
        logger.error(f"數據收集任務失敗: {str(e)}")
    
    # 測試健康檢查任務
    logger.info("測試健康檢查任務...")
    health_check_task = {
        'id': 'test-health-check',
        'type': 'health_check',
        'config': {
            'proxy_url': 'http://example.com',
            'timeout': 10,
            'max_retries': 2
        },
        'parameters': {}
    }
    
    try:
        result = await executor.execute_task(health_check_task)
        logger.info(f"健康檢查任務結果: {result}")
    except Exception as e:
        logger.error(f"健康檢查任務失敗: {str(e)}")
    
    logger.info("任務執行器測試完成")

if __name__ == "__main__":
    asyncio.run(test_task_executor())