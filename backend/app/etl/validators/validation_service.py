"""
整合驗證服務
提供統一的代理驗證服務接口
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json

from .validation_system import ProxyValidationSystem, ProxyValidationResult
from .automated_manager import AutomatedValidationManager, ValidationJob
from .config_manager import ValidationConfigManager, ValidationConfig
from .proxy_validator import ProxyValidator
from .ip_scoring_engine import IPScoringEngine


class ProxyValidationService:
    """
    代理驗證服務
    提供統一的代理驗證服務接口，整合所有驗證組件
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化代理驗證服務
        
        Args:
            config: 服務配置
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化各個組件
        self.config_manager = ValidationConfigManager(
            self.config.get('config_path')
        )
        
        self.validation_system = ProxyValidationSystem(
            self.config.get('validation_system', {})
        )
        
        self.automated_manager = AutomatedValidationManager(
            self.config.get('automated_manager', {})
        )
        
        # 服務狀態
        self.is_running = False
        self.service_start_time = None
        self.service_stats = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'avg_validation_time': 0.0,
            'total_proxies_tested': 0
        }
    
    async def start_service(self):
        """啟動驗證服務"""
        self.logger.info("啟動代理驗證服務")
        
        try:
            # 啟動自動化管理器
            manager_task = asyncio.create_task(self.automated_manager.start())
            
            self.is_running = True
            self.service_start_time = datetime.now()
            
            self.logger.info("代理驗證服務啟動成功")
            return manager_task
            
        except Exception as e:
            self.logger.error(f"啟動驗證服務失敗: {e}")
            raise
    
    async def stop_service(self):
        """停止驗證服務"""
        self.logger.info("停止代理驗證服務")
        
        try:
            # 停止自動化管理器
            await self.automated_manager.stop()
            
            self.is_running = False
            self.logger.info("代理驗證服務已停止")
            
        except Exception as e:
            self.logger.error(f"停止驗證服務失敗: {e}")
            raise
    
    async def validate_proxy(self, proxy: Any, config_name: str = 'standard_validation') -> ProxyValidationResult:
        """
        驗證單個代理
        
        Args:
            proxy: 代理對象
            config_name: 配置名稱
            
        Returns:
            ProxyValidationResult: 驗證結果
        """
        start_time = datetime.now()
        
        try:
            # 獲取配置
            config = self.config_manager.get_config(config_name)
            if not config:
                raise ValueError(f"配置不存在: {config_name}")
            
            # 執行驗證
            result = await self.validation_system.validate_single_proxy(proxy, config.test_level)
            
            # 更新統計
            self._update_validation_stats(start_time, result.success)
            
            return result
            
        except Exception as e:
            self.logger.error(f"代理驗證失敗: {e}")
            # 創建失敗結果
            result = ProxyValidationResult(
                proxy=proxy,
                success=False,
                overall_score=0.0,
                connection_test={'success': False, 'error': str(e)},
                anonymity_test={'anonymity_level': 'unknown', 'score': 0},
                geolocation_test={'success': False, 'score': 0},
                speed_test={'download_speed': 0, 'response_time': 0, 'score': 0},
                timestamp=datetime.now(),
                test_duration=(datetime.now() - start_time).total_seconds(),
                recommendations=[f"驗證失敗: {e}"],
                raw_results={}
            )
            
            self._update_validation_stats(start_time, False)
            return result
    
    async def validate_proxies_batch(self, proxies: List[Any], config_name: str = 'standard_validation') -> List[ProxyValidationResult]:
        """
        批量驗證代理
        
        Args:
            proxies: 代理列表
            config_name: 配置名稱
            
        Returns:
            List[ProxyValidationResult]: 驗證結果列表
        """
        start_time = datetime.now()
        
        try:
            # 獲取配置
            config = self.config_manager.get_config(config_name)
            if not config:
                raise ValueError(f"配置不存在: {config_name}")
            
            # 執行批量驗證
            results = await self.validation_system.validate_proxies_batch(proxies, config.test_level)
            
            # 更新統計
            successful_count = sum(1 for r in results if r.success)
            self._update_batch_stats(len(proxies), successful_count, start_time)
            
            return results
            
        except Exception as e:
            self.logger.error(f"批量驗證失敗: {e}")
            self._update_batch_stats(len(proxies), 0, start_time)
            return []
    
    async def schedule_validation_job(self, proxies: List[Any], config_name: str = 'standard_validation',
                                    priority: int = 5, schedule_delay: Optional[int] = None) -> str:
        """
        調度驗證任務
        
        Args:
            proxies: 代理列表
            config_name: 配置名稱
            priority: 優先級
            schedule_delay: 延遲執行秒數
            
        Returns:
            str: 任務ID
        """
        try:
            # 獲取配置
            config = self.config_manager.get_config(config_name)
            if not config:
                raise ValueError(f"配置不存在: {config_name}")
            
            # 添加驗證任務
            job_id = await self.automated_manager.add_validation_job(
                proxies=proxies,
                test_level=config.test_level,
                priority=priority,
                schedule_delay=schedule_delay
            )
            
            self.logger.info(f"調度驗證任務成功: {job_id}, 代理數: {len(proxies)}")
            return job_id
            
        except Exception as e:
            self.logger.error(f"調度驗證任務失敗: {e}")
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取任務狀態
        
        Args:
            job_id: 任務ID
            
        Returns:
            Dict: 任務狀態
        """
        return await self.automated_manager.get_job_status(job_id)
    
    async def get_service_status(self) -> Dict[str, Any]:
        """
        獲取服務狀態
        
        Returns:
            Dict: 服務狀態
        """
        manager_status = await self.automated_manager.get_system_status()
        validation_stats = self.validation_system.get_system_stats()
        
        return {
            'service_running': self.is_running,
            'service_start_time': self.service_start_time.isoformat() if self.service_start_time else None,
            'uptime_seconds': (datetime.now() - self.service_start_time).total_seconds() if self.service_start_time else 0,
            'service_stats': self.service_stats.copy(),
            'manager_status': manager_status,
            'validation_stats': validation_stats,
            'available_configs': self.config_manager.list_configs(),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_available_configs(self) -> List[Dict[str, str]]:
        """
        獲取可用配置列表
        
        Returns:
            List[Dict]: 配置列表
        """
        return self.config_manager.list_configs()
    
    def get_config_details(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        獲取配置詳情
        
        Args:
            config_name: 配置名稱
            
        Returns:
            Dict: 配置詳情
        """
        return self.config_manager.get_config_summary(config_name)
    
    def create_custom_config(self, config_data: Dict[str, Any]) -> bool:
        """
        創建自定義配置
        
        Args:
            config_data: 配置數據
            
        Returns:
            bool: 是否成功
        """
        try:
            config = ValidationConfig(**config_data)
            return self.config_manager.create_custom_config(config)
            
        except Exception as e:
            self.logger.error(f"創建自定義配置失敗: {e}")
            return False
    
    def update_config(self, config_name: str, updates: Dict[str, Any]) -> bool:
        """
        更新配置
        
        Args:
            config_name: 配置名稱
            updates: 更新內容
            
        Returns:
            bool: 是否成功
        """
        return self.config_manager.update_config(config_name, updates)
    
    def delete_config(self, config_name: str) -> bool:
        """
        刪除配置
        
        Args:
            config_name: 配置名稱
            
        Returns:
            bool: 是否成功
        """
        return self.config_manager.delete_config(config_name)
    
    def _update_validation_stats(self, start_time: datetime, success: bool):
        """更新驗證統計"""
        duration = (datetime.now() - start_time).total_seconds()
        
        self.service_stats['total_validations'] += 1
        self.service_stats['total_proxies_tested'] += 1
        
        if success:
            self.service_stats['successful_validations'] += 1
        else:
            self.service_stats['failed_validations'] += 1
        
        # 更新平均驗證時間
        total_time = self.service_stats['avg_validation_time'] * (self.service_stats['total_validations'] - 1)
        self.service_stats['avg_validation_time'] = (total_time + duration) / self.service_stats['total_validations']
    
    def _update_batch_stats(self, total_proxies: int, successful_count: int, start_time: datetime):
        """更新批量驗證統計"""
        duration = (datetime.now() - start_time).total_seconds()
        
        self.service_stats['total_validations'] += 1
        self.service_stats['total_proxies_tested'] += total_proxies
        self.service_stats['successful_validations'] += successful_count
        self.service_stats['failed_validations'] += (total_proxies - successful_count)
        
        # 更新平均驗證時間
        total_time = self.service_stats['avg_validation_time'] * (self.service_stats['total_validations'] - 1)
        self.service_stats['avg_validation_time'] = (total_time + duration) / self.service_stats['total_validations']
    
    async def quick_validate(self, proxy: Any) -> Dict[str, Any]:
        """
        快速驗證代理（簡化接口）
        
        Args:
            proxy: 代理對象
            
        Returns:
            Dict: 簡化驗證結果
        """
        result = await self.validate_proxy(proxy, 'fast_check')
        
        return {
            'proxy': f"{proxy.ip}:{proxy.port}",
            'success': result.success,
            'score': result.overall_score,
            'anonymity_level': result.anonymity_test.get('anonymity_level', 'unknown'),
            'response_time': result.speed_test.get('response_time', 0),
            'country': result.geolocation_test.get('proxy_country', 'unknown'),
            'recommendations': result.recommendations[:2]  # 只返回前兩個建議
        }
    
    async def comprehensive_validate(self, proxy: Any) -> Dict[str, Any]:
        """
        綜合驗證代理（詳細接口）
        
        Args:
            proxy: 代理對象
            
        Returns:
            Dict: 詳細驗證結果
        """
        result = await self.validate_proxy(proxy, 'comprehensive_analysis')
        
        return {
            'proxy': f"{proxy.ip}:{proxy.port}",
            'success': result.success,
            'overall_score': result.overall_score,
            'connection_test': result.connection_test,
            'anonymity_test': result.anonymity_test,
            'geolocation_test': result.geolocation_test,
            'speed_test': result.speed_test,
            'test_duration': result.test_duration,
            'all_recommendations': result.recommendations,
            'raw_results': result.raw_results
        }


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    # 模擬代理對象
    class MockProxy:
        def __init__(self, ip, port, protocol='http'):
            self.ip = ip
            self.port = port
            self.protocol = protocol
            self.country = 'US'
            self.anonymity = 'elite'
    
    async def test_validation_service():
        # 創建驗證服務
        config = {
            'automated_manager': {
                'max_concurrent_jobs': 2,
                'persistence_enabled': False
            }
        }
        
        service = ProxyValidationService(config)
        
        # 啟動服務
        service_task = await service.start_service()
        
        # 測試代理
        test_proxy = MockProxy('8.8.8.8', 8080)
        
        # 快速驗證
        quick_result = await service.quick_validate(test_proxy)
        print("快速驗證結果:")
        print(json.dumps(quick_result, indent=2, ensure_ascii=False))
        
        # 綜合驗證
        comprehensive_result = await service.comprehensive_validate(test_proxy)
        print("\n綜合驗證結果:")
        print(json.dumps(comprehensive_result, indent=2, ensure_ascii=False))
        
        # 獲取服務狀態
        service_status = await service.get_service_status()
        print("\n服務狀態:")
        print(json.dumps(service_status, indent=2, ensure_ascii=False))
        
        # 停止服務
        await service.stop_service()
    
    # 運行測試
    asyncio.run(test_validation_service())