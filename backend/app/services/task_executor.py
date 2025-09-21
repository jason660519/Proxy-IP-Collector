"""
任務執行器服務
處理各種類型任務的實際執行邏輯
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import aiohttp
import random
from urllib.parse import urlparse

# 配置日誌
logger = logging.getLogger(__name__)

class TaskType(Enum):
    """任務類型"""
    HEALTH_CHECK = "health_check"
    PROXY_TEST = "proxy_test"
    DATA_COLLECTION = "data_collection"
    SYSTEM_MAINTENANCE = "system_maintenance"
    CUSTOM = "custom"

class TaskStatus(Enum):
    """任務狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class TaskExecutor:
    """任務執行器"""
    
    def __init__(self):
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.max_concurrent_tasks = 10
        
    async def __aenter__(self):
        """異步上下文管理器進入"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=10)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出"""
        if self.session:
            await self.session.close()
        # 取消所有正在運行的任務
        for task in self.active_tasks.values():
            task.cancel()
        
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行任務
        
        Args:
            task_data: 任務數據
            
        Returns:
            Dict[str, Any]: 執行結果
        """
        task_id = task_data['id']
        task_type = TaskType(task_data['type'])
        config = task_data.get('config', {})
        
        try:
            logger.info(f"開始執行任務 {task_id}, 類型: {task_type.value}")
            
            # 根據任務類型執行相應的邏輯
            if task_type == TaskType.HEALTH_CHECK:
                result = await self._execute_health_check(task_id, config)
            elif task_type == TaskType.PROXY_TEST:
                result = await self._execute_proxy_test(task_id, config)
            elif task_type == TaskType.DATA_COLLECTION:
                result = await self._execute_data_collection(task_id, config)
            elif task_type == TaskType.SYSTEM_MAINTENANCE:
                result = await self._execute_system_maintenance(task_id, config)
            else:
                result = await self._execute_custom_task(task_id, config)
            
            logger.info(f"任務 {task_id} 執行完成")
            return {
                'success': True,
                'result': result,
                'completed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"任務 {task_id} 執行失敗: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'completed_at': datetime.utcnow().isoformat()
            }
        finally:
            # 清理活動任務
            self.active_tasks.pop(task_id, None)
    
    async def _execute_health_check(self, task_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行健康檢查任務
        
        Args:
            task_id: 任務ID
            config: 任務配置
            
        Returns:
            Dict[str, Any]: 檢查結果
        """
        logger.info(f"開始健康檢查任務 {task_id}")
        
        # 獲取配置參數
        proxy_urls = config.get('proxy_urls', ['http://httpbin.org/ip'])
        timeout = config.get('timeout', 10)
        retry_count = config.get('retry_count', 3)
        
        logger.info(f"健康檢查配置 - proxy_urls: {proxy_urls}, timeout: {timeout}, retry_count: {retry_count}")
        
        results = []
        total_checks = len(proxy_urls)
        successful_checks = 0
        
        for i, url in enumerate(proxy_urls):
            try:
                logger.info(f"檢查URL {i+1}/{total_checks}: {url}")
                
                # 模擬檢查延遲
                await asyncio.sleep(random.uniform(0.5, 2.0))
                
                # 模擬檢查結果（實際應該使用真實的代理檢查邏輯）
                check_result = {
                    'url': url,
                    'status': 'healthy',
                    'response_time': random.uniform(0.1, 2.0),
                    'status_code': 200,
                    'checked_at': datetime.utcnow().isoformat()
                }
                
                logger.info(f"URL檢查成功: {url}, 響應時間: {check_result['response_time']:.2f}s")
                results.append(check_result)
                successful_checks += 1
                
            except Exception as e:
                logger.error(f"檢查URL失敗 {url}: {str(e)}")
                error_result = {
                    'url': url,
                    'status': 'failed',
                    'error': str(e),
                    'checked_at': datetime.utcnow().isoformat()
                }
                results.append(error_result)
        
        summary = {
            'total_checks': total_checks,
            'successful_checks': successful_checks,
            'failed_checks': total_checks - successful_checks,
            'success_rate': successful_checks / total_checks if total_checks > 0 else 0,
            'results': results,
            'execution_time': random.uniform(5, 15)
        }
        
        logger.info(f"健康檢查任務 {task_id} 完成 - 總檢查: {total_checks}, 成功: {successful_checks}, 失敗: {total_checks - successful_checks}, 成功率: {summary['success_rate']:.2%}")
        return summary
    
    async def _execute_proxy_test(self, task_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行代理測試任務
        
        Args:
            task_id: 任務ID
            config: 任務配置
            
        Returns:
            Dict[str, Any]: 測試結果
        """
        logger.info(f"執行代理測試任務 {task_id}")
        
        # 模擬代理測試
        proxy_list = config.get('proxies', [])
        test_urls = config.get('test_urls', ['http://httpbin.org/ip'])
        timeout = config.get('timeout', 15)
        
        results = []
        total_proxies = len(proxy_list) if proxy_list else 10
        
        # 如果沒有提供代理列表，生成模擬數據
        if not proxy_list:
            proxy_list = [
                {'ip': f'192.168.1.{i}', 'port': 8080, 'protocol': 'http'}
                for i in range(1, min(total_proxies + 1, 11))
            ]
        
        successful_tests = 0
        
        for i, proxy in enumerate(proxy_list):
            try:
                logger.info(f"測試代理 {i+1}/{len(proxy_list)}: {proxy['ip']}:{proxy['port']}")
                
                # 模擬測試延遲
                await asyncio.sleep(random.uniform(0.5, 3.0))
                
                # 模擬測試結果
                success_rate = random.uniform(0.6, 0.95)
                is_working = random.random() < success_rate
                
                test_result = {
                    'proxy': f"{proxy['ip']}:{proxy['port']}",
                    'protocol': proxy.get('protocol', 'http'),
                    'is_working': is_working,
                    'response_time': random.uniform(0.5, 5.0) if is_working else None,
                    'anonymity': random.choice(['transparent', 'anonymous', 'elite']) if is_working else None,
                    'location': random.choice(['US', 'EU', 'Asia']) if is_working else None,
                    'tested_at': datetime.utcnow().isoformat()
                }
                
                results.append(test_result)
                if is_working:
                    successful_tests += 1
                
            except Exception as e:
                logger.error(f"測試代理失敗 {proxy}: {str(e)}")
                results.append({
                    'proxy': f"{proxy['ip']}:{proxy['port']}",
                    'protocol': proxy.get('protocol', 'http'),
                    'is_working': False,
                    'error': str(e),
                    'tested_at': datetime.utcnow().isoformat()
                })
        
        return {
            'total_proxies': len(proxy_list),
            'working_proxies': successful_tests,
            'failed_proxies': len(proxy_list) - successful_tests,
            'success_rate': successful_tests / len(proxy_list) if proxy_list else 0,
            'results': results,
            'execution_time': random.uniform(10, 30)
        }
    
    async def _execute_data_collection(self, task_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行數據收集任務
        
        Args:
            task_id: 任務ID
            config: 任務配置
            
        Returns:
            Dict[str, Any]: 收集結果
        """
        logger.info(f"執行數據收集任務 {task_id}")
        
        # 獲取配置參數
        source_urls = config.get('source_urls', ['http://example.com'])
        max_pages = config.get('max_pages', 10)
        collection_type = config.get('collection_type', 'proxies')
        
        results = []
        collected_data = []
        
        for i, url in enumerate(source_urls):
            try:
                logger.info(f"收集數據來源 {i+1}/{len(source_urls)}: {url}")
                
                # 模擬數據收集延遲
                await asyncio.sleep(random.uniform(1.0, 3.0))
                
                # 模擬收集到的數據
                if collection_type == 'proxies':
                    data = self._generate_mock_proxy_data(random.randint(5, 20))
                else:
                    data = self._generate_mock_general_data(random.randint(10, 50))
                
                collection_result = {
                    'source': url,
                    'data_collected': len(data),
                    'data': data[:5],  # 只返回前5條作為示例
                    'collected_at': datetime.utcnow().isoformat()
                }
                
                collected_data.extend(data)
                results.append(collection_result)
                
            except Exception as e:
                logger.error(f"數據收集失敗 {url}: {str(e)}")
                results.append({
                    'source': url,
                    'data_collected': 0,
                    'error': str(e),
                    'collected_at': datetime.utcnow().isoformat()
                })
        
        return {
            'total_sources': len(source_urls),
            'successful_sources': len([r for r in results if 'error' not in r]),
            'total_data_collected': len(collected_data),
            'results': results,
            'execution_time': random.uniform(15, 45)
        }
    
    async def _execute_system_maintenance(self, task_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行系統維護任務
        
        Args:
            task_id: 任務ID
            config: 任務配置
            
        Returns:
            Dict[str, Any]: 維護結果
        """
        logger.info(f"執行系統維護任務 {task_id}")
        
        # 獲取維護類型
        maintenance_type = config.get('maintenance_type', 'cleanup')
        
        results = []
        
        try:
            if maintenance_type == 'cleanup':
                # 清理過期數據
                results.append(await self._cleanup_expired_data())
            elif maintenance_type == 'optimize':
                # 優化數據庫
                results.append(await self._optimize_database())
            elif maintenance_type == 'backup':
                # 備份數據
                results.append(await self._backup_data())
            else:
                results.append({
                    'type': maintenance_type,
                    'status': 'unsupported',
                    'message': f'不支持的維護類型: {maintenance_type}'
                })
            
            return {
                'maintenance_type': maintenance_type,
                'results': results,
                'execution_time': random.uniform(5, 20)
            }
            
        except Exception as e:
            logger.error(f"系統維護失敗: {str(e)}")
            return {
                'maintenance_type': maintenance_type,
                'status': 'failed',
                'error': str(e),
                'execution_time': random.uniform(5, 15)
            }
    
    async def _execute_custom_task(self, task_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行自定義任務
        
        Args:
            task_id: 任務ID
            config: 任務配置
            
        Returns:
            Dict[str, Any]: 執行結果
        """
        logger.info(f"執行自定義任務 {task_id}")
        
        # 模擬自定義任務執行
        await asyncio.sleep(random.uniform(2, 8))
        
        return {
            'task_type': 'custom',
            'status': 'completed',
            'message': '自定義任務執行完成',
            'config_used': config,
            'execution_time': random.uniform(2, 8)
        }
    
    def _generate_mock_proxy_data(self, count: int) -> List[Dict[str, Any]]:
        """生成模擬代理數據"""
        data = []
        for i in range(count):
            data.append({
                'ip': f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
                'port': random.randint(1000, 9999),
                'protocol': random.choice(['http', 'https', 'socks4', 'socks5']),
                'anonymity': random.choice(['transparent', 'anonymous', 'elite']),
                'country': random.choice(['US', 'CN', 'EU', 'JP', 'KR']),
                'response_time': random.uniform(0.1, 5.0),
                'uptime': random.uniform(80, 100),
                'last_checked': datetime.utcnow().isoformat()
            })
        return data
    
    def _generate_mock_general_data(self, count: int) -> List[Dict[str, Any]]:
        """生成模擬通用數據"""
        data = []
        for i in range(count):
            data.append({
                'id': i + 1,
                'title': f"數據項 {i + 1}",
                'value': random.uniform(1, 100),
                'category': random.choice(['A', 'B', 'C']),
                'timestamp': datetime.utcnow().isoformat()
            })
        return data
    
    async def _cleanup_expired_data(self) -> Dict[str, Any]:
        """清理過期數據"""
        logger.info("清理過期數據")
        await asyncio.sleep(random.uniform(2, 5))
        return {
            'type': 'cleanup',
            'status': 'completed',
            'cleaned_items': random.randint(100, 1000),
            'freed_space': f"{random.randint(10, 100)}MB"
        }
    
    async def _optimize_database(self) -> Dict[str, Any]:
        """優化數據庫"""
        logger.info("優化數據庫")
        await asyncio.sleep(random.uniform(3, 8))
        return {
            'type': 'optimize',
            'status': 'completed',
            'optimized_tables': random.randint(5, 20),
            'performance_improvement': f"{random.randint(10, 50)}%"
        }
    
    async def _backup_data(self) -> Dict[str, Any]:
        """備份數據"""
        logger.info("備份數據")
        await asyncio.sleep(random.uniform(5, 15))
        return {
            'type': 'backup',
            'status': 'completed',
            'backup_size': f"{random.randint(100, 500)}MB",
            'backup_location': f"/backups/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }


# 全局任務執行器實例
task_executor: Optional[TaskExecutor] = None


async def get_task_executor() -> TaskExecutor:
    """獲取任務執行器實例"""
    global task_executor
    if task_executor is None:
        task_executor = TaskExecutor()
        await task_executor.__aenter__()
    return task_executor


async def cleanup_task_executor():
    """清理任務執行器"""
    global task_executor
    if task_executor:
        await task_executor.__aexit__(None, None, None)
        task_executor = None