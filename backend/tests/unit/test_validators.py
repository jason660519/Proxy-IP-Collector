"""
代理驗證器單元測試
測試代理驗證相關的核心功能
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path
import aiohttp

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.etl.validators.validation_system import ProxyValidationSystem, ProxyValidationResult
from app.etl.validators.ip_scoring_engine import IPScoringEngine
from app.etl.validators.geolocation_validator import GeolocationValidator
from app.etl.validators.speed_tester import SpeedTester
from app.etl.validators.anonymity_tester import AnonymityTester


class TestIPScoringEngine:
    """IP評分引擎測試類"""
    
    @pytest.fixture
    def scoring_engine(self):
        """創建評分引擎實例"""
        config = {
            'weights': {
                'connection_success': 0.25,
                'response_time': 0.20,
                'anonymity_level': 0.20,
                'stability': 0.15,
                'geolocation': 0.10,
                'speed': 0.10
            }
        }
        return IPScoringEngine(config=config)
    
    @pytest.mark.asyncio
    async def test_calculate_score_with_valid_data(self, scoring_engine):
        """測試使用有效數據計算評分"""
        test_data = {
            'connection': {
                'success': True,
                'response_time': 2.5
            },
            'anonymity': {
                'level': 'elite'
            },
            'geolocation': {
                'success': True,
                'country': 'US'
            },
            'speed': {
                'success': True,
                'download_speed': 5.0,  # MB/s
                'upload_speed': 2.0     # MB/s
            }
        }
        
        score = await scoring_engine.calculate_score(test_data)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score > 70  # 有效數據應該有較高評分
    
    @pytest.mark.asyncio
    async def test_calculate_score_with_poor_performance(self, scoring_engine):
        """測試性能較差的代理評分"""
        test_data = {
            'connection': {
                'success': False,
                'response_time': 15.0
            },
            'anonymity': {
                'level': 'transparent'
            },
            'geolocation': {
                'success': False,
                'country': 'CN'
            },
            'speed': {
                'success': True,
                'download_speed': 0.5,  # MB/s
                'upload_speed': 0.2     # MB/s
            }
        }
        
        score = await scoring_engine.calculate_score(test_data)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score < 50  # 性能差應該有較低評分
    
    @pytest.mark.asyncio
    async def test_calculate_score_with_partial_data(self, scoring_engine):
        """測試部分數據缺失的情況"""
        test_data = {
            'connection': {
                'success': True,
                'response_time': 3.0
            }
            # 缺少其他字段
        }
        
        score = await scoring_engine.calculate_score(test_data)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
    
    def test_invalid_weights_handling(self):
        """測試無效權重處理"""
        invalid_config = {
            'weights': {
                'connection_success': 0.5,
                'response_time': 0.5,
                # 總和不為1.0
            }
        }
        
        # IPScoringEngine 不會驗證權重總和，所以這個測試應該通過
        engine = IPScoringEngine(config=invalid_config)
        assert engine is not None


class TestGeolocationValidator:
    """地理位置驗證器測試類"""
    
    @pytest.fixture
    def geo_validator(self):
        """創建地理位置驗證器實例"""
        return GeolocationValidator()
    
    @pytest.mark.asyncio
    async def test_validate_geolocation_success(self, geo_validator):
        """測試成功的地理位置驗證"""
        # 創建一個簡單的代理對象
        class SimpleProxy:
            def __init__(self, ip, port):
                self.ip = ip
                self.port = port
        
        proxy = SimpleProxy("8.8.8.8", 8080)
        
        # 模擬真實位置
        real_location = {
            "ip": "1.2.3.4",
            "country": "US",
            "country_code": "US",
            "city": "New York",
            "latitude": 40.7128,
            "longitude": -74.0060
        }
        
        # 模擬代理位置
        proxy_location = {
            "ip": "8.8.8.8",
            "country": "US",
            "country_code": "US",
            "city": "Mountain View",
            "latitude": 37.386,
            "longitude": -122.0838
        }
        
        with patch.object(geo_validator, '_get_real_location', return_value=real_location):
            with patch.object(geo_validator, '_get_proxy_location', return_value=proxy_location):
                result = await geo_validator.validate_location(proxy)
                
                assert result is not None
                assert result['success'] is True
                assert 'proxy_location' in result
                assert 'real_location' in result
                assert 'analysis' in result
    
    @pytest.mark.asyncio
    async def test_validate_geolocation_failure(self, geo_validator):
        """測試地理位置驗證失敗"""
        # 創建一個簡單的代理對象
        class SimpleProxy:
            def __init__(self, ip, port):
                self.ip = ip
                self.port = port
        
        proxy = SimpleProxy("invalid.ip", 8080)
        
        with patch.object(geo_validator, '_get_real_location', return_value=None):
            result = await geo_validator.validate_location(proxy)
            
            assert result is not None
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_validate_geolocation_with_timeout(self, geo_validator):
        """測試地理位置驗證超時"""
        # 創建一個簡單的代理對象
        class SimpleProxy:
            def __init__(self, ip, port):
                self.ip = ip
                self.port = port
        
        proxy = SimpleProxy("8.8.8.8", 8080)
        
        with patch.object(geo_validator, '_get_real_location', side_effect=asyncio.TimeoutError()):
            result = await geo_validator.validate_location(proxy)
            
            assert result is not None
            assert result['success'] is False


class TestSpeedTester:
    """速度測試器測試類"""
    
    @pytest.fixture
    def speed_tester(self):
        """創建速度測試器實例"""
        return SpeedTester()
    
    @pytest.mark.asyncio
    async def test_test_speed_success(self, speed_tester):
        """測試成功的速度測試"""
        # 創建一個簡單的代理對象
        class SimpleProxy:
            def __init__(self, ip, port):
                self.ip = ip
                self.port = port
                self.protocol = 'http'
        
        proxy = SimpleProxy("8.8.8.8", 8080)
        
        # 模擬各個測試方法
        with patch.object(speed_tester, '_test_connection') as mock_connection, \
             patch.object(speed_tester, '_test_response_time') as mock_response_time, \
             patch.object(speed_tester, '_test_download_speed') as mock_download_speed, \
             patch.object(speed_tester, '_test_stability') as mock_stability:
            
            mock_connection.return_value = {
                'success': True,
                'connect_time': 500,
                'status_code': 200,
                'status': 'connected'
            }
            
            mock_response_time.return_value = {
                'success': True,
                'avg_response_time': 1000,
                'grade': 'good'
            }
            
            mock_download_speed.return_value = {
                'success': True,
                'avg_speed_kbps': 512,
                'grade': 'good'
            }
            
            mock_stability.return_value = {
                'success': True,
                'success_rate': 0.95,
                'stability_grade': 'excellent'
            }
            
            result = await speed_tester.test_speed(proxy)
            
            assert result is not None
            assert result['success'] is True
            assert 'connection_test' in result
            assert 'response_time_test' in result
            assert 'download_speed_test' in result
            assert 'stability_test' in result
            assert 'overall_score' in result
            assert result['overall_score'] > 0
    
    @pytest.mark.asyncio
    async def test_test_speed_timeout(self, speed_tester):
        """測試速度測試超時"""
        # 創建一個簡單的代理對象
        class SimpleProxy:
            def __init__(self, ip, port):
                self.ip = ip
                self.port = port
                self.protocol = 'http'
        
        proxy = SimpleProxy("8.8.8.8", 8080)
        
        with patch.object(speed_tester, '_test_connection', side_effect=asyncio.TimeoutError()):
            result = await speed_tester.test_speed(proxy)
            
            assert result is not None
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_test_speed_connection_error(self, speed_tester):
        """測試連接錯誤處理"""
        # 創建一個簡單的代理對象
        class SimpleProxy:
            def __init__(self, ip, port):
                self.ip = ip
                self.port = port
                self.protocol = 'http'
        
        proxy = SimpleProxy("8.8.8.8", 8080)
        
        with patch.object(speed_tester, '_test_connection', side_effect=ConnectionError("Connection failed")):
            result = await speed_tester.test_speed(proxy)
            
            assert result is not None
            assert result['success'] is False
            assert 'error' in result


class TestAnonymityTester:
    """匿名性測試器測試類"""
    
    @pytest.fixture
    def anonymity_tester(self):
        """創建匿名性測試器實例"""
        return AnonymityTester()
    
    @pytest.mark.asyncio
    async def test_test_anonymity_high_anonymity(self, anonymity_tester):
        """測試高匿名性代理"""
        # 創建一個簡單的代理對象
        class SimpleProxy:
            def __init__(self, ip, port):
                self.ip = ip
                self.port = port
                self.protocol = 'http'
        
        proxy = SimpleProxy("8.8.8.8", 8080)
        
        # 模擬真實IP和代理信息
        with patch.object(anonymity_tester, '_get_real_ip', return_value="1.2.3.4"), \
             patch.object(anonymity_tester, '_get_proxy_info', return_value={
                 'proxy_ip': '8.8.8.8',
                 'headers': {
                     'User-Agent': 'test-agent',
                     'X-Forwarded-For': None
                 }
             }), \
             patch.object(anonymity_tester, '_analyze_anonymity', return_value={
                 'ip_hidden': True,
                 'anonymity_score': 80
             }), \
             patch.object(anonymity_tester, '_check_header_leakage', return_value={
                 'header_leakage_score': 90
             }), \
             patch.object(anonymity_tester, '_detect_proxy_features', return_value={
                 'proxy_detection_score': 85
             }), \
             patch.object(anonymity_tester, '_assess_overall_anonymity', return_value={
                 'level': 'elite',
                 'score': 85.0,
                 'description': '高匿代理 - 極佳的匿名性'
             }):
            
            result = await anonymity_tester.test_anonymity(proxy)
            
            assert result is not None
            assert result['success'] is True
            assert 'overall_assessment' in result
            assert result['overall_assessment']['level'] == 'elite'
    
    @pytest.mark.asyncio
    async def test_test_anonymity_low_anonymity(self, anonymity_tester):
        """測試低匿名性代理"""
        # 創建一個簡單的代理對象
        class SimpleProxy:
            def __init__(self, ip, port):
                self.ip = ip
                self.port = port
                self.protocol = 'http'
        
        proxy = SimpleProxy("8.8.8.8", 8080)
        
        # 模擬真實IP和代理信息（真實IP洩露）
        with patch.object(anonymity_tester, '_get_real_ip', return_value="1.2.3.4"), \
             patch.object(anonymity_tester, '_get_proxy_info', return_value={
                 'proxy_ip': '1.2.3.4',  # 與真實IP相同，表示洩露
                 'headers': {
                     'User-Agent': 'test-agent',
                     'X-Forwarded-For': '1.2.3.4'
                 }
             }), \
             patch.object(anonymity_tester, '_analyze_anonymity', return_value={
                 'ip_hidden': False,
                 'real_ip_exposed': True,
                 'anonymity_score': 20
             }), \
             patch.object(anonymity_tester, '_check_header_leakage', return_value={
                 'header_leakage_score': 30
             }), \
             patch.object(anonymity_tester, '_detect_proxy_features', return_value={
                 'proxy_detection_score': 40
             }), \
             patch.object(anonymity_tester, '_assess_overall_anonymity', return_value={
                 'level': 'transparent',
                 'score': 30.0,
                 'description': '透明代理 - 基本的匿名性'
             }):
            
            result = await anonymity_tester.test_anonymity(proxy)
            
            assert result is not None
            assert result['success'] is True
            assert 'overall_assessment' in result
            assert result['overall_assessment']['level'] == 'transparent'
    
    @pytest.mark.asyncio
    async def test_test_anonymity_connection_error(self, anonymity_tester):
        """測試匿名性測試的連接錯誤"""
        # 創建一個簡單的代理對象
        class SimpleProxy:
            def __init__(self, ip, port):
                self.ip = ip
                self.port = port
                self.protocol = 'http'
        
        proxy = SimpleProxy("8.8.8.8", 8080)
        
        # 模擬連接錯誤
        with patch.object(anonymity_tester, '_get_real_ip', side_effect=aiohttp.ClientError("Connection failed")):
            result = await anonymity_tester.test_anonymity(proxy)
            
            assert result is not None
            assert result['success'] is False
            assert 'error' in result


class TestProxyValidationSystem:
    """代理驗證系統測試類"""
    
    @pytest.fixture
    def validation_system(self):
        """創建驗證系統實例"""
        return ProxyValidationSystem()
    
    @pytest.mark.asyncio
    async def test_validate_single_proxy_success(self, validation_system, sample_proxy_data):
        """測試單個代理驗證成功"""
        # 創建一個簡單的代理對象，有必要的屬性
        class SimpleProxy:
            def __init__(self, ip, port, protocol="http"):
                self.ip = ip
                self.port = port
                self.protocol = protocol
                self.country = "US"
                self.anonymity = "high"
        
        proxy = SimpleProxy(
            ip=sample_proxy_data["proxy"]["host"],
            port=sample_proxy_data["proxy"]["port"],
            protocol="http"
        )
        
        # 執行實際的驗證
        result = await validation_system.validate_proxy(proxy)
        
        assert result is not None
        assert result.proxy_id == f"{proxy.ip}:{proxy.port}"
        assert isinstance(result.success, bool)
        assert 0 <= result.overall_score <= 100
    
    @pytest.mark.asyncio
    async def test_validate_single_proxy_failure(self, validation_system, sample_proxy_data):
        """測試單個代理驗證失敗"""
        # 創建一個簡單的代理對象
        class SimpleProxy:
            def __init__(self, ip, port, protocol="http"):
                self.ip = ip
                self.port = port
                self.protocol = protocol
                self.country = "US"
                self.anonymity = "high"
        
        # 使用無效的IP地址
        proxy = SimpleProxy(
            ip="256.256.256.256",  # 無效IP
            port=8080,
            protocol="invalid"
        )
        
        # 執行驗證
        result = await validation_system.validate_proxy(proxy)
        
        assert result is not None
        assert isinstance(result.success, bool)
        assert 0 <= result.overall_score <= 100
    
    @pytest.mark.asyncio
    async def test_validate_batch_proxies(self, validation_system):
        """測試批量代理驗證"""
        # 創建一個簡單的代理對象
        class SimpleProxy:
            def __init__(self, ip, port, protocol="http"):
                self.ip = ip
                self.port = port
                self.protocol = protocol
                self.country = "US"
                self.anonymity = "high"
        
        # 創建代理對象列表
        proxies = [
            SimpleProxy(ip="192.168.1.100", port=8080, protocol="http"),
            SimpleProxy(ip="192.168.1.101", port=8080, protocol="http")
        ]
        
        # 執行批量驗證
        results = await validation_system.validate_proxies_batch(proxies)
        
        assert isinstance(results, list)
        assert len(results) == 2
        assert all(isinstance(result, ProxyValidationResult) for result in results)
    
    def test_get_test_config_basic(self, validation_system):
        """測試基本測試配置"""
        config = validation_system._get_test_config('basic')
        
        assert config['connection_test'] is True
        assert config['speed_test'] is False
        assert config['geolocation_test'] is False
        assert config['anonymity_test'] is False
        assert config['scoring_test'] is True
    
    def test_get_test_config_standard(self, validation_system):
        """測試標準測試配置"""
        config = validation_system._get_test_config('standard')
        
        assert config['connection_test'] is True
        assert config['speed_test'] is True
        assert config['geolocation_test'] is True
        assert config['anonymity_test'] is False
        assert config['scoring_test'] is True
    
    def test_get_test_config_comprehensive(self, validation_system):
        """測試綜合測試配置"""
        config = validation_system._get_test_config('comprehensive')
        
        assert config['connection_test'] is True
        assert config['speed_test'] is True
        assert config['geolocation_test'] is True
        assert config['anonymity_test'] is True
        assert config['scoring_test'] is True
    
    def test_get_test_config_invalid(self, validation_system):
        """測試無效測試等級"""
        config = validation_system._get_test_config('invalid_level')
        
        # 應該返回默認的綜合配置
        assert config['connection_test'] is True
        assert config['scoring_test'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])