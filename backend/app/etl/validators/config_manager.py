"""
驗證配置管理器
管理不同類型的驗證配置和策略
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import aiofiles


@dataclass
class ValidationConfig:
    """驗證配置數據類"""
    name: str
    description: str
    test_level: str  # basic, standard, comprehensive
    timeout: int
    retry_count: int
    concurrent_limit: int
    scoring_weights: Dict[str, float]
    test_endpoints: List[str]
    anonymity_checks: List[str]
    geolocation_checks: bool
    speed_tests: bool
    stability_threshold: float
    min_score_threshold: float
    auto_retry_failed: bool
    cleanup_interval: int


class ValidationConfigManager:
    """
    驗證配置管理器
    提供不同場景的驗證配置管理
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路徑
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = Path(config_path) if config_path else Path('./validation_configs')
        self.config_path.mkdir(exist_ok=True)
        
        # 預設配置
        self.default_configs = self._create_default_configs()
        self.custom_configs: Dict[str, ValidationConfig] = {}
        
        # 載入現有配置
        self._load_configs()
    
    def _create_default_configs(self) -> Dict[str, ValidationConfig]:
        """創建預設配置"""
        configs = {
            'fast_check': ValidationConfig(
                name='fast_check',
                description='快速驗證 - 基礎連接測試',
                test_level='basic',
                timeout=10,
                retry_count=1,
                concurrent_limit=50,
                scoring_weights={
                    'connection_success': 0.7,
                    'response_time': 0.2,
                    'stability': 0.1
                },
                test_endpoints=['http://httpbin.org/ip'],
                anonymity_checks=[],
                geolocation_checks=False,
                speed_tests=False,
                stability_threshold=0.5,
                min_score_threshold=30.0,
                auto_retry_failed=False,
                cleanup_interval=3600
            ),
            
            'standard_validation': ValidationConfig(
                name='standard_validation',
                description='標準驗證 - 完整功能測試',
                test_level='standard',
                timeout=15,
                retry_count=2,
                concurrent_limit=20,
                scoring_weights={
                    'connection_success': 0.4,
                    'response_time': 0.2,
                    'anonymity_level': 0.2,
                    'geolocation_accuracy': 0.1,
                    'stability': 0.1
                },
                test_endpoints=[
                    'http://httpbin.org/ip',
                    'http://httpbin.org/headers',
                    'http://httpbin.org/user-agent'
                ],
                anonymity_checks=['ip_detection', 'header_analysis', 'proxy_detection'],
                geolocation_checks=True,
                speed_tests=True,
                stability_threshold=0.7,
                min_score_threshold=60.0,
                auto_retry_failed=True,
                cleanup_interval=7200
            ),
            
            'comprehensive_analysis': ValidationConfig(
                name='comprehensive_analysis',
                description='綜合分析 - 深度性能評估',
                test_level='comprehensive',
                timeout=30,
                retry_count=3,
                concurrent_limit=10,
                scoring_weights={
                    'connection_success': 0.25,
                    'response_time': 0.15,
                    'download_speed': 0.15,
                    'anonymity_level': 0.15,
                    'geolocation_accuracy': 0.1,
                    'stability': 0.1,
                    'reliability': 0.1
                },
                test_endpoints=[
                    'http://httpbin.org/ip',
                    'http://httpbin.org/headers',
                    'http://httpbin.org/user-agent',
                    'http://httpbin.org/delay/1',
                    'http://httpbin.org/bytes/1024'
                ],
                anonymity_checks=['ip_detection', 'header_analysis', 'proxy_detection', 'dns_leak', 'webrtc_leak'],
                geolocation_checks=True,
                speed_tests=True,
                stability_threshold=0.8,
                min_score_threshold=75.0,
                auto_retry_failed=True,
                cleanup_interval=10800
            ),
            
            'security_focused': ValidationConfig(
                name='security_focused',
                description='安全導向 - 重點匿名性測試',
                test_level='comprehensive',
                timeout=20,
                retry_count=2,
                concurrent_limit=15,
                scoring_weights={
                    'anonymity_level': 0.5,
                    'connection_success': 0.2,
                    'response_time': 0.1,
                    'stability': 0.1,
                    'geolocation_accuracy': 0.1
                },
                test_endpoints=[
                    'http://httpbin.org/ip',
                    'http://httpbin.org/headers',
                    'http://httpbin.org/user-agent',
                    'http://httpbin.org/cookies'
                ],
                anonymity_checks=['ip_detection', 'header_analysis', 'proxy_detection', 'dns_leak', 'webrtc_leak', 'fingerprinting'],
                geolocation_checks=True,
                speed_tests=False,
                stability_threshold=0.8,
                min_score_threshold=70.0,
                auto_retry_failed=True,
                cleanup_interval=7200
            ),
            
            'performance_optimized': ValidationConfig(
                name='performance_optimized',
                description='性能優化 - 高速連接測試',
                test_level='standard',
                timeout=5,
                retry_count=1,
                concurrent_limit=100,
                scoring_weights={
                    'response_time': 0.4,
                    'connection_success': 0.3,
                    'download_speed': 0.2,
                    'stability': 0.1
                },
                test_endpoints=[
                    'http://httpbin.org/ip',
                    'http://httpbin.org/bytes/1024'
                ],
                anonymity_checks=['ip_detection'],
                geolocation_checks=False,
                speed_tests=True,
                stability_threshold=0.6,
                min_score_threshold=50.0,
                auto_retry_failed=False,
                cleanup_interval=1800
            )
        }
        
        return configs
    
    def get_config(self, config_name: str) -> Optional[ValidationConfig]:
        """
        獲取配置
        
        Args:
            config_name: 配置名稱
            
        Returns:
            ValidationConfig: 配置對象
        """
        if config_name in self.custom_configs:
            return self.custom_configs[config_name]
        elif config_name in self.default_configs:
            return self.default_configs[config_name]
        else:
            self.logger.warning(f"配置不存在: {config_name}")
            return None
    
    def create_custom_config(self, config: ValidationConfig) -> bool:
        """
        創建自定義配置
        
        Args:
            config: 配置對象
            
        Returns:
            bool: 是否成功
        """
        try:
            self.custom_configs[config.name] = config
            self._save_config(config)
            self.logger.info(f"創建自定義配置: {config.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"創建配置失敗: {e}")
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
        try:
            config = self.get_config(config_name)
            if not config:
                return False
            
            # 更新配置屬性
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                else:
                    self.logger.warning(f"未知配置屬性: {key}")
            
            # 保存更新
            self._save_config(config)
            self.logger.info(f"更新配置: {config_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新配置失敗: {e}")
            return False
    
    def delete_config(self, config_name: str) -> bool:
        """
        刪除自定義配置
        
        Args:
            config_name: 配置名稱
            
        Returns:
            bool: 是否成功
        """
        try:
            if config_name in self.default_configs:
                self.logger.warning(f"不能刪除預設配置: {config_name}")
                return False
            
            if config_name in self.custom_configs:
                del self.custom_configs[config_name]
                
                # 刪除配置文件
                config_file = self.config_path / f"{config_name}.json"
                if config_file.exists():
                    config_file.unlink()
                
                self.logger.info(f"刪除配置: {config_name}")
                return True
            else:
                self.logger.warning(f"配置不存在: {config_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"刪除配置失敗: {e}")
            return False
    
    def list_configs(self) -> List[Dict[str, str]]:
        """
        列出所有配置
        
        Returns:
            List[Dict]: 配置列表
        """
        configs = []
        
        # 預設配置
        for name, config in self.default_configs.items():
            configs.append({
                'name': name,
                'description': config.description,
                'type': 'default',
                'test_level': config.test_level
            })
        
        # 自定義配置
        for name, config in self.custom_configs.items():
            configs.append({
                'name': name,
                'description': config.description,
                'type': 'custom',
                'test_level': config.test_level
            })
        
        return configs
    
    def get_config_summary(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        獲取配置摘要
        
        Args:
            config_name: 配置名稱
            
        Returns:
            Dict: 配置摘要
        """
        config = self.get_config(config_name)
        if not config:
            return None
        
        return {
            'name': config.name,
            'description': config.description,
            'test_level': config.test_level,
            'timeout': config.timeout,
            'retry_count': config.retry_count,
            'concurrent_limit': config.concurrent_limit,
            'min_score_threshold': config.min_score_threshold,
            'auto_retry_failed': config.auto_retry_failed,
            'test_endpoints_count': len(config.test_endpoints),
            'anonymity_checks_count': len(config.anonymity_checks),
            'has_geolocation_checks': config.geolocation_checks,
            'has_speed_tests': config.speed_tests
        }
    
    def _save_config(self, config: ValidationConfig):
        """保存配置到文件"""
        try:
            config_file = self.config_path / f"{config.name}.json"
            config_data = asdict(config)
            
            # 異步保存
            import asyncio
            asyncio.create_task(self._async_save_config(config_file, config_data))
            
        except Exception as e:
            self.logger.error(f"保存配置文件失敗: {e}")
    
    async def _async_save_config(self, config_file: Path, config_data: Dict[str, Any]):
        """異步保存配置"""
        try:
            async with aiofiles.open(config_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(config_data, ensure_ascii=False, indent=2))
                
        except Exception as e:
            self.logger.error(f"異步保存配置失敗: {e}")
    
    def _load_configs(self):
        """載入配置文件"""
        try:
            if not self.config_path.exists():
                return
            
            for config_file in self.config_path.glob("*.json"):
                try:
                    import asyncio
                    asyncio.run(self._async_load_config(config_file))
                    
                except Exception as e:
                    self.logger.error(f"載入配置文件失敗 {config_file}: {e}")
                    
        except Exception as e:
            self.logger.error(f"載入配置失敗: {e}")
    
    async def _async_load_config(self, config_file: Path):
        """異步載入配置"""
        try:
            async with aiofiles.open(config_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                config_data = json.loads(content)
            
            config = ValidationConfig(**config_data)
            
            # 不要覆蓋預設配置
            if config.name not in self.default_configs:
                self.custom_configs[config.name] = config
                self.logger.info(f"載入自定義配置: {config.name}")
                
        except Exception as e:
            self.logger.error(f"異步載入配置失敗 {config_file}: {e}")
    
    def create_config_from_template(self, template_name: str, new_config_name: str, 
                                  updates: Optional[Dict[str, Any]] = None) -> Optional[ValidationConfig]:
        """
        從模板創建新配置
        
        Args:
            template_name: 模板配置名稱
            new_config_name: 新配置名稱
            updates: 更新內容
            
        Returns:
            ValidationConfig: 新配置對象
        """
        try:
            template_config = self.get_config(template_name)
            if not template_config:
                return None
            
            # 複製配置
            config_data = asdict(template_config)
            config_data['name'] = new_config_name
            config_data['description'] = f"基於 {template_name} 的自定義配置"
            
            # 應用更新
            if updates:
                config_data.update(updates)
            
            new_config = ValidationConfig(**config_data)
            
            # 保存新配置
            self.create_custom_config(new_config)
            
            return new_config
            
        except Exception as e:
            self.logger.error(f"從模板創建配置失敗: {e}")
            return None
    
    def validate_config(self, config: ValidationConfig) -> List[str]:
        """
        驗證配置有效性
        
        Args:
            config: 配置對象
            
        Returns:
            List[str]: 錯誤列表
        """
        errors = []
        
        # 基本驗證
        if not config.name or not config.name.strip():
            errors.append("配置名稱不能為空")
        
        if config.timeout <= 0:
            errors.append("超時時間必須大於0")
        
        if config.retry_count < 0:
            errors.append("重試次數不能為負數")
        
        if config.concurrent_limit <= 0:
            errors.append("並發限制必須大於0")
        
        # 權重驗證
        total_weight = sum(config.scoring_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            errors.append(f"評分權重總和必須為1.0，當前為{total_weight}")
        
        # 閾值驗證
        if not (0 <= config.stability_threshold <= 1):
            errors.append("穩定性閾值必須在0-1之間")
        
        if not (0 <= config.min_score_threshold <= 100):
            errors.append("最低分數閾值必須在0-100之間")
        
        # 測試端點驗證
        if not config.test_endpoints:
            errors.append("測試端點不能為空")
        
        return errors


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def test_config_manager():
        # 創建配置管理器
        manager = ValidationConfigManager()
        
        # 列出所有配置
        configs = manager.list_configs()
        print("可用配置:")
        for config in configs:
            print(f"  - {config['name']}: {config['description']} ({config['type']})")
        
        # 獲取配置摘要
        summary = manager.get_config_summary('standard_validation')
        if summary:
            print(f"\n標準驗證配置摘要:")
            for key, value in summary.items():
                print(f"  {key}: {value}")
        
        # 創建自定義配置
        custom_config = ValidationConfig(
            name='my_custom_config',
            description='我的自定義驗證配置',
            test_level='standard',
            timeout=20,
            retry_count=2,
            concurrent_limit=30,
            scoring_weights={
                'connection_success': 0.5,
                'response_time': 0.3,
                'stability': 0.2
            },
            test_endpoints=['http://httpbin.org/ip'],
            anonymity_checks=['ip_detection'],
            geolocation_checks=True,
            speed_tests=True,
            stability_threshold=0.7,
            min_score_threshold=65.0,
            auto_retry_failed=True,
            cleanup_interval=3600
        )
        
        # 驗證配置
        errors = manager.validate_config(custom_config)
        if errors:
            print(f"\n配置驗證錯誤: {errors}")
        else:
            print("\n配置驗證通過")
            
            # 創建配置
            if manager.create_custom_config(custom_config):
                print("自定義配置創建成功")
            
            # 從模板創建新配置
            new_config = manager.create_config_from_template(
                'fast_check',
                'my_fast_config',
                {'timeout': 5, 'concurrent_limit': 200}
            )
            
            if new_config:
                print(f"從模板創建配置成功: {new_config.name}")
    
    # 運行測試
    asyncio.run(test_config_manager())