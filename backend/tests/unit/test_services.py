"""
服務層單元測試
測試業務邏輯層的核心功能
"""

import pytest
import asyncio
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.proxy_validator import ProxyValidator
from app.models.proxy import Proxy
from app.schemas.proxy import ProxyStatus
from app.core.exceptions import ValidationException


class TestProxyValidator:
    """代理驗證器測試類"""
    
    @pytest.fixture
    def proxy_validator(self):
        """創建代理驗證器實例"""
        mock_db_session = Mock()
        return ProxyValidator(mock_db_session)
    
    @pytest.fixture
    def sample_proxy(self):
        """樣本代理對象"""
        proxy = Mock(spec=Proxy)
        proxy.id = "test-proxy-id"
        proxy.ip = "192.168.1.100"
        proxy.port = 8080
        proxy.protocol = "http"
        proxy.status = "active"
        proxy.response_time = 1000
        proxy.success_rate = 0.85
        proxy.quality_score = 0.85
        proxy.created_at = datetime.now()
        proxy.updated_at = datetime.now()
        return proxy
    
    @pytest.mark.asyncio
    async def test_validate_single_proxy_success(self, proxy_validator, sample_proxy):
        """測試單個代理驗證 - 成功"""
        # 模擬成功的HTTP響應
        with patch.object(proxy_validator, '_test_proxy_connection') as mock_test:
            mock_test.return_value = (True, 1000, 200, None, {"Content-Type": "application/json"})
            
            # 模擬數據庫操作
            with patch.object(proxy_validator, '_update_proxy_status') as mock_update:
                result = await proxy_validator._validate_single_proxy(
                    sample_proxy, 
                    asyncio.Semaphore(1), 
                    10,
                    None
                )
                
                assert result is not None
                assert result.proxy_id == str(sample_proxy.id)
                assert result.is_successful is True
                assert result.error_message is None
                assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_validate_single_proxy_timeout(self, proxy_validator, sample_proxy):
        """測試單個代理驗證 - 超時"""
        # 模擬超時錯誤
        with patch.object(proxy_validator, '_test_proxy_connection') as mock_test:
            mock_test.return_value = (False, 0, 0, "Request timeout", {})
            
            # 模擬數據庫操作
            with patch.object(proxy_validator, '_update_proxy_status') as mock_update:
                result = await proxy_validator._validate_single_proxy(
                    sample_proxy, 
                    asyncio.Semaphore(1), 
                    10,
                    None
                )
                
                assert result is not None
                assert result.proxy_id == str(sample_proxy.id)
                assert result.is_successful is False
                assert "timeout" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_validate_single_proxy_failure(self, proxy_validator, sample_proxy):
        """測試單個代理驗證 - 失敗"""
        # 模擬失敗的HTTP響應
        with patch.object(proxy_validator, '_test_proxy_connection') as mock_test:
            mock_test.return_value = (False, 0, 403, "Forbidden", {"Content-Type": "text/html"})
            
            # 模擬數據庫操作
            with patch.object(proxy_validator, '_update_proxy_status') as mock_update:
                result = await proxy_validator._validate_single_proxy(
                    sample_proxy, 
                    asyncio.Semaphore(1), 
                    10,
                    None
                )
                
                assert result is not None
                assert result.proxy_id == str(sample_proxy.id)
                assert result.is_successful is False
                assert result.error_message is not None
                assert result.status_code == 403
    
    @pytest.mark.asyncio
    async def test_validate_batch_proxies(self, proxy_validator):
        """測試批量代理驗證"""
        # 創建多個代理對象
        proxies = []
        for i in range(3):
            proxy = Mock(spec=Proxy)
            proxy.id = f"test-proxy-{i+1}"
            proxy.ip = f"192.168.1.{100 + i}"
            proxy.port = 8080 + i
            proxy.protocol = "http"
            proxy.status = "active"
            proxy.response_time = 1000
            proxy.success_rate = 0.85
            proxy.quality_score = 0.85
            proxy.created_at = datetime.now()
            proxy.updated_at = datetime.now()
            proxies.append(proxy)
        
        # 模擬驗證結果
        with patch.object(proxy_validator, '_validate_single_proxy') as mock_validate:
            # 第一個代理成功，第二個失敗，第三個成功
            mock_validate.side_effect = [
                Mock(
                    proxy_id="test-proxy-1", 
                    is_successful=True, 
                    error_message=None, 
                    status_code=200,
                    response_time=1000
                ),
                Mock(
                    proxy_id="test-proxy-2", 
                    is_successful=False, 
                    error_message="Connection failed", 
                    status_code=0,
                    response_time=0
                ),
                Mock(
                    proxy_id="test-proxy-3", 
                    is_successful=True, 
                    error_message=None, 
                    status_code=200,
                    response_time=1200
                )
            ]
            
            results = await proxy_validator.validate_proxies(proxies, max_concurrent=2)
            
            assert len(results) == 3
            assert results[0].is_successful is True
            assert results[1].is_successful is False
            assert results[2].is_successful is True
            assert mock_validate.call_count == 3
    
    def test_build_proxy_url(self, proxy_validator, sample_proxy):
        """測試代理URL構建"""
        url = proxy_validator._build_proxy_url(sample_proxy)
        
        expected_url = f"{sample_proxy.protocol}://{sample_proxy.ip}:{sample_proxy.port}"
        assert url == expected_url
    
    def test_select_test_url(self, proxy_validator, sample_proxy):
        """測試測試URL選擇"""
        test_url = proxy_validator._select_test_url(sample_proxy)
        
        # 應該返回預設的測試URL
        assert test_url in ["http://httpbin.org/ip", "https://httpbin.org/ip"]
        
        # 測試HTTPS代理
        sample_proxy.protocol = "https"
        https_test_url = proxy_validator._select_test_url(sample_proxy)
        assert https_test_url == "https://httpbin.org/ip"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])