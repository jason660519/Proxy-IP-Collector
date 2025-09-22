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

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.etl.validators.validation_system import StandaloneValidationSystem
from app.etl.validators.ip_scoring_engine import IPScoringEngine
from app.etl.validators.geolocation_validator import GeolocationValidator
from app.etl.validators.speed_tester import SpeedTester
from app.etl.validators.anonymity_tester import AnonymityTester


class TestIPScoringEngine:
    """IP評分引擎測試類"""
    
    @pytest.fixture
    def scoring_engine(self):
        """創建評分引擎實例"""
        weights = {
            'connection_success': 0.25,
            'response_time': 0.20,
            'anonymity_level': 0.20,
            'stability': 0.15,
            'geolocation': 0.10,
            'speed': 0.10
        }
        return IPScoringEngine(weights=weights)
    
    def test_calculate_score_with_valid_data(self, scoring_engine):
        """測試使用有效數據計算評分"""
        test_data = {
            'connection_success': True,
            'response_time': 2.5,
            'anonymity_level': 'high',
            'stability': 0.9,
            'geolocation_accuracy': 0.95,
            'download_speed': 500
        }
        
        score = scoring_engine.calculate_score(test_data)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score > 70  # 有效數據應該有較高評分
    
    def test_calculate_score_with_poor_performance(self, scoring_engine):
        """測試性能較差的代理評分"""
        test_data = {
            'connection_success': False,
            'response_time': 15.0,
            'anonymity_level': 'low',
            'stability': 0.3,
            'geolocation_accuracy': 0.4,
            'download_speed': 50
        }
        
        score = scoring_engine.calculate_score(test_data)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score < 50  # 性能差應該有較低評分
    
    def test_calculate_score_with_partial_data(self, scoring_engine):
        """測試部分數據缺失的情況"""
        test_data = {
            'connection_success': True,
            'response_time': 3.0,
            # 缺少部分字段
        }
        
        score = scoring_engine.calculate_score(test_data)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
    
    def test_invalid_weights_handling(self):
        """測試無效權重處理"""
        invalid_weights = {
            'connection_success': 0.5,
            'response_time': 0.5,
            # 總和不為1.0
        }
        
        with pytest.raises(ValueError):
            IPScoringEngine(weights=invalid_weights)


class TestGeolocationValidator:
    """地理位置驗證器測試類"""
    
    @pytest.fixture
    def geo_validator(self):
        """創建地理位置驗證器實例"""
        return GeolocationValidator()
    
    @pytest.mark.asyncio
    async def test_validate_geolocation_success(self, geo_validator):
        """測試成功的地理位置驗證"""
        mock_response = {
            "ip": "8.8.8.8",
            "country": "US",
            "city": "Mountain View",
            "latitude": 37.386,
            "longitude": -122.0838
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aenter__.return_value.status = 200
            
            result = await geo_validator.validate_geolocation("8.8.8.8", 8080)
            
            assert result is not None
            assert 'country' in result
            assert 'city' in result
            assert 'latitude' in result
            assert 'longitude' in result
    
    @pytest.mark.asyncio
    async def test_validate_geolocation_failure(self, geo_validator):
        """測試地理位置驗證失敗"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 404
            
            result = await geo_validator.validate_geolocation("invalid.ip", 8080)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_validate_geolocation_with_timeout(self, geo_validator):
        """測試地理位置驗證超時"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = asyncio.TimeoutError()
            
            result = await geo_validator.validate_geolocation("8.8.8.8", 8080)
            
            assert result is None


class TestSpeedTester:
    """速度測試器測試類"""
    
    @pytest.fixture
    def speed_tester(self):
        """創建速度測試器實例"""
        return SpeedTester()
    
    @pytest.mark.asyncio
    async def test_test_connection_speed_success(self, speed_tester):
        """測試成功的連接速度測試"""
        mock_response = Mock()
        mock_response.status = 200
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await speed_tester.test_connection_speed(
                "8.8.8.8", 8080, "http://httpbin.org/ip"
            )
            
            assert result is not None
            assert 'response_time' in result
            assert 'download_speed' in result
            assert result['response_time'] > 0
    
    @pytest.mark.asyncio
    async def test_test_connection_speed_timeout(self, speed_tester):
        """測試連接速度測試超時"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = asyncio.TimeoutError()
            
            result = await speed_tester.test_connection_speed(
                "8.8.8.8", 8080, "http://httpbin.org/ip"
            )
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_test_connection_speed_connection_error(self, speed_tester):
        """測試連接錯誤處理"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = ConnectionError("Connection failed")
            
            result = await speed_tester.test_connection_speed(
                "8.8.8.8", 8080, "http://httpbin.org/ip"
            )
            
            assert result is None


class TestAnonymityTester:
    """匿名性測試器測試類"""
    
    @pytest.fixture
    def anonymity_tester(self):
        """創建匿名性測試器實例"""
        return AnonymityTester()
    
    @pytest.mark.asyncio
    async def test_test_anonymity_high_anonymity(self, anonymity_tester):
        """測試高匿名性代理"""
        mock_response = {
            "origin": "8.8.8.8",  # 代理服務器IP
            "headers": {
                "User-Agent": "test-agent",
                "X-Forwarded-For": None
            }
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aenter__.return_value.status = 200
            
            result = await anonymity_tester.test_anonymity("8.8.8.8", 8080)
            
            assert result is not None
            assert 'anonymity_level' in result
            assert result['anonymity_level'] in ['high', 'medium', 'low']
    
    @pytest.mark.asyncio
    async def test_test_anonymity_low_anonymity(self, anonymity_tester):
        """測試低匿名性代理"""
        mock_response = {
            "origin": "1.2.3.4",  # 真實IP
            "headers": {
                "User-Agent": "test-agent",
                "X-Forwarded-For": "1.2.3.4"
            }
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aenter__.return_value.status = 200
            
            result = await anonymity_tester.test_anonymity("8.8.8.8", 8080)
            
            assert result is not None
            assert result['anonymity_level'] == 'low'
    
    @pytest.mark.asyncio
    async def test_test_anonymity_with_error(self, anonymity_tester):
        """測試匿名性測試錯誤處理"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            result = await anonymity_tester.test_anonymity("8.8.8.8", 8080)
            
            assert result is None


class TestStandaloneValidationSystem:
    """獨立驗證系統測試類"""
    
    @pytest.fixture
    def validation_system(self):
        """創建驗證系統實例"""
        return StandaloneValidationSystem()
    
    @pytest.mark.asyncio
    async def test_validate_single_proxy_success(self, validation_system, sample_proxy_data):
        """測試單個代理驗證成功"""
        proxy = sample_proxy_data["proxy"]
        
        # 模擬各個組件的成功響應
        with patch.object(validation_system.speed_tester, 'test_connection_speed', return_value={
            'response_time': 2.0,
            'download_speed': 500
        }):
            with patch.object(validation_system.anonymity_tester, 'test_anonymity', return_value={
                'anonymity_level': 'high'
            }):
                with patch.object(validation_system.geo_validator, 'validate_geolocation', return_value={
                    'country': 'US',
                    'city': 'New York'
                }):
                    
                    result = await validation_system.validate_proxy(proxy)
                    
                    assert result is not None
                    assert result['proxy'] == f"{proxy['host']}:{proxy['port']}"
                    assert 'score' in result
                    assert 'is_valid' in result
                    assert result['is_valid'] is True
    
    @pytest.mark.asyncio
    async def test_validate_single_proxy_failure(self, validation_system, sample_proxy_data):
        """測試單個代理驗證失敗"""
        proxy = sample_proxy_data["proxy"]
        
        # 模擬連接失敗
        with patch.object(validation_system.speed_tester, 'test_connection_speed', return_value=None):
            
            result = await validation_system.validate_proxy(proxy)
            
            assert result is not None
            assert result['is_valid'] is False
            assert result['score'] == 0
    
    @pytest.mark.asyncio
    async def test_validate_batch_proxies(self, validation_system):
        """測試批量代理驗證"""
        proxies = [
            {"host": "192.168.1.100", "port": 8080, "type": "http"},
            {"host": "192.168.1.101", "port": 8080, "type": "http"}
        ]
        
        # 模擬批量驗證
        with patch.object(validation_system, 'validate_proxy') as mock_validate:
            mock_validate.return_value = {
                'proxy': '192.168.1.100:8080',
                'is_valid': True,
                'score': 85.0
            }
            
            results = await validation_system.validate_proxies_batch(proxies)
            
            assert isinstance(results, list)
            assert len(results) == 2
            assert all(result['is_valid'] is True for result in results)
    
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