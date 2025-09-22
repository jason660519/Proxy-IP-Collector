"""
測試配置和工具模塊
提供測試所需的通用配置、fixture和工具函數
"""

import pytest
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import json
import tempfile
from pathlib import Path
import sys
import os

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestConfig:
    """測試配置類"""
    
    # 測試數據庫配置
    TEST_DATABASE_URL = "sqlite:///./test.db"
    
    # 測試超時配置
    DEFAULT_TIMEOUT = 30
    
    # 測試代理數據
    SAMPLE_PROXIES = [
        {"host": "192.168.1.100", "port": 8080, "type": "http"},
        {"host": "10.0.0.1", "port": 3128, "type": "https"},
        {"host": "203.0.113.1", "port": 1080, "type": "socks5"}
    ]
    
    # 測試API端點
    TEST_ENDPOINTS = [
        "http://httpbin.org/ip",
        "http://httpbin.org/headers",
        "http://httpbin.org/user-agent"
    ]

@pytest.fixture
def event_loop():
    """創建事件循環fixture"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_config():
    """測試配置fixture"""
    return TestConfig()

@pytest.fixture
def sample_proxy_data():
    """樣本代理數據fixture"""
    return {
        "proxy": {
            "host": "192.168.1.100",
            "port": 8080,
            "type": "http",
            "username": None,
            "password": None
        },
        "expected_response_time": 5.0,
        "expected_success_rate": 0.8
    }

@pytest.fixture
def mock_validation_result():
    """模擬驗證結果fixture"""
    return {
        "proxy": "192.168.1.100:8080",
        "is_valid": True,
        "score": 85.5,
        "response_time": 2.3,
        "anonymity_level": "high",
        "geolocation": {
            "country": "US",
            "city": "New York",
            "latitude": 40.7128,
            "longitude": -74.0060
        },
        "tests_passed": 8,
        "tests_failed": 1,
        "validation_time": 15.2,
        "timestamp": datetime.now().isoformat(),
        "recommendations": ["代理性能良好", "建議定期檢查穩定性"]
    }

@pytest.fixture
def temp_db():
    """臨時數據庫fixture"""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    yield db_path
    os.close(db_fd)
    os.unlink(db_path)

class MockResponse:
    """模擬HTTP響應類"""
    
    def __init__(self, json_data: Dict[str, Any] = None, status_code: int = 200, text: str = ""):
        self.json_data = json_data or {}
        self.status_code = status_code
        self.text = text
        self.headers = {"content-type": "application/json"}
    
    def json(self):
        return self.json_data
    
    async def text(self):
        return self.text
    
    async def json_async(self):
        return self.json_data

def create_mock_response(data: Dict[str, Any], status: int = 200) -> MockResponse:
    """創建模擬響應輔助函數"""
    return MockResponse(json_data=data, status_code=status)

def assert_valid_proxy_data(proxy_data: Dict[str, Any]):
    """驗證代理數據格式"""
    required_fields = ["host", "port", "type"]
    for field in required_fields:
        assert field in proxy_data, f"缺少必要字段: {field}"
    
    assert isinstance(proxy_data["port"], int), "端口必須是整數"
    assert 1 <= proxy_data["port"] <= 65535, "端口範圍無效"
    assert proxy_data["type"] in ["http", "https", "socks4", "socks5"], "代理類型無效"

def assert_valid_validation_result(result: Dict[str, Any]):
    """驗證驗證結果格式"""
    required_fields = ["proxy", "is_valid", "score", "response_time", "timestamp"]
    for field in required_fields:
        assert field in result, f"缺少必要字段: {field}"
    
    assert isinstance(result["is_valid"], bool), "is_valid必須是布爾值"
    assert 0 <= result["score"] <= 100, "評分必須在0-100之間"
    assert result["response_time"] >= 0, "響應時間不能為負數"

class AsyncMock:
    """異步模擬類"""
    
    def __init__(self, return_value: Any = None, side_effect: Exception = None):
        self.return_value = return_value
        self.side_effect = side_effect
        self.call_count = 0
        self.call_args = []
    
    async def __call__(self, *args, **kwargs):
        self.call_count += 1
        self.call_args.append((args, kwargs))
        
        if self.side_effect:
            raise self.side_effect
        
        return self.return_value

def async_mock(return_value: Any = None, side_effect: Exception = None) -> AsyncMock:
    """創建異步模擬對象"""
    return AsyncMock(return_value=return_value, side_effect=side_effect)