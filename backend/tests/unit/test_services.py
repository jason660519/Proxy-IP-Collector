"""
服務層單元測試
測試業務邏輯層的核心功能
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.proxy_service import ProxyService
from app.services.validation_service import ValidationService
from app.services.statistics_service import StatisticsService
from app.models.proxy_models import ProxyModel, ProxyStatus
from app.core.exceptions import ProxyNotFoundError, ProxyValidationError


class TestProxyService:
    """代理服務測試類"""
    
    @pytest.fixture
    def proxy_service(self):
        """創建代理服務實例"""
        return ProxyService()
    
    @pytest.fixture
    def sample_proxy_data(self):
        """樣本代理數據"""
        return {
            "id": 1,
            "host": "192.168.1.100",
            "port": 8080,
            "type": "http",
            "username": "test_user",
            "password": "test_pass",
            "status": "active",
            "score": 85.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    
    @patch('app.services.proxy_service.get_db_connection')
    async def test_create_proxy_success(self, mock_db_conn, proxy_service, sample_proxy_data):
        """測試創建代理 - 成功"""
        # 模擬數據庫連接和執行
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = AsyncMock()
        mock_conn.execute.return_value.fetchone.return_value = {
            "id": 1,
            **sample_proxy_data
        }
        mock_db_conn.return_value.__aenter__.return_value = mock_conn
        
        result = await proxy_service.create_proxy(sample_proxy_data)
        
        assert result is not None
        assert result["host"] == sample_proxy_data["host"]
        assert result["port"] == sample_proxy_data["port"]
    
    @patch('app.services.proxy_service.get_db_connection')
    async def test_get_proxy_by_id_success(self, mock_db_conn, proxy_service, sample_proxy_data):
        """測試根據ID獲取代理 - 成功"""
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = AsyncMock()
        mock_conn.execute.return_value.fetchone.return_value = sample_proxy_data
        mock_db_conn.return_value.__aenter__.return_value = mock_conn
        
        result = await proxy_service.get_proxy_by_id(1)
        
        assert result is not None
        assert result["id"] == 1
        assert result["host"] == sample_proxy_data["host"]
    
    @patch('app.services.proxy_service.get_db_connection')
    async def test_get_proxy_by_id_not_found(self, mock_db_conn, proxy_service):
        """測試根據ID獲取代理 - 不存在"""
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = AsyncMock()
        mock_conn.execute.return_value.fetchone.return_value = None
        mock_db_conn.return_value.__aenter__.return_value = mock_conn
        
        with pytest.raises(ProxyNotFoundError):
            await proxy_service.get_proxy_by_id(999)
    
    @patch('app.services.proxy_service.get_db_connection')
    async def test_update_proxy_success(self, mock_db_conn, proxy_service, sample_proxy_data):
        """測試更新代理 - 成功"""
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = AsyncMock()
        mock_conn.execute.return_value.fetchone.return_value = sample_proxy_data
        mock_db_conn.return_value.__aenter__.return_value = mock_conn
        
        update_data = {"status": "inactive", "score": 90.0}
        result = await proxy_service.update_proxy(1, update_data)
        
        assert result is not None
        assert result["status"] == "inactive"
        assert result["score"] == 90.0
    
    @patch('app.services.proxy_service.get_db_connection')
    async def test_delete_proxy_success(self, mock_db_conn, proxy_service):
        """測試刪除代理 - 成功"""
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = AsyncMock()
        mock_conn.execute.return_value.rowcount = 1
        mock_db_conn.return_value.__aenter__.return_value = mock_conn
        
        result = await proxy_service.delete_proxy(1)
        
        assert result is True
    
    @patch('app.services.proxy_service.get_db_connection')
    async def test_get_proxies_with_filters(self, mock_db_conn, proxy_service):
        """測試獲取代理列表 - 帶過濾條件"""
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = AsyncMock()
        mock_conn.execute.return_value.fetchall.return_value = [
            {"id": 1, "host": "192.168.1.100", "port": 8080, "type": "http", "status": "active", "score": 85.0},
            {"id": 2, "host": "192.168.1.101", "port": 8080, "type": "http", "status": "active", "score": 90.0}
        ]
        mock_conn.execute.return_value.fetchone.return_value = {"total": 2}
        mock_db_conn.return_value.__aenter__.return_value = mock_conn
        
        filters = {"status": "active", "type": "http"}
        result = await proxy_service.get_proxies(filters=filters, page=1, page_size=10)
        
        assert result is not None
        assert result["total"] == 2
        assert len(result["proxies"]) == 2
    
    @patch('app.services.proxy_service.StandaloneValidationSystem')
    async def test_validate_proxy_success(self, mock_validation_system, proxy_service):
        """測試代理驗證 - 成功"""
        mock_validator = Mock()
        mock_validator.validate_proxy.return_value = {
            "proxy": "192.168.1.100:8080",
            "is_valid": True,
            "score": 85.0,
            "validation_details": {}
        }
        mock_validation_system.return_value = mock_validator
        
        proxy_data = {"host": "192.168.1.100", "port": 8080, "type": "http"}
        result = await proxy_service.validate_proxy(proxy_data)
        
        assert result is not None
        assert result["is_valid"] is True
        assert result["score"] == 85.0
    
    @patch('app.services.proxy_service.StandaloneValidationSystem')
    async def test_validate_proxy_failure(self, mock_validation_system, proxy_service):
        """測試代理驗證 - 失敗"""
        mock_validator = Mock()
        mock_validator.validate_proxy.return_value = {
            "proxy": "192.168.1.100:8080",
            "is_valid": False,
            "score": 0,
            "validation_details": {}
        }
        mock_validation_system.return_value = mock_validator
        
        proxy_data = {"host": "192.168.1.100", "port": 8080, "type": "http"}
        result = await proxy_service.validate_proxy(proxy_data)
        
        assert result is not None
        assert result["is_valid"] is False
        assert result["score"] == 0


class TestValidationService:
    """驗證服務測試類"""
    
    @pytest.fixture
    def validation_service(self):
        """創建驗證服務實例"""
        return ValidationService()
    
    @patch('app.services.validation_service.StandaloneValidationSystem')
    async def test_start_validation_job(self, mock_validation_system, validation_service):
        """測試啟動驗證任務"""
        mock_validator = Mock()
        mock_validator.validate_proxies_batch.return_value = [
            {"proxy": "192.168.1.100:8080", "is_valid": True, "score": 85.0},
            {"proxy": "192.168.1.101:8080", "is_valid": False, "score": 25.0}
        ]
        mock_validation_system.return_value = mock_validator
        
        job_data = {
            "proxy_ids": [1, 2],
            "validation_level": "standard"
        }
        
        result = await validation_service.start_validation_job(job_data)
        
        assert result is not None
        assert result["status"] == "started"
        assert "job_id" in result
    
    async def test_get_validation_status(self, validation_service):
        """測試獲取驗證狀態"""
        # 模擬正在運行的驗證任務
        validation_service.active_jobs = {
            "test-job-123": {
                "status": "running",
                "progress": 75,
                "total_proxies": 100,
                "processed_proxies": 75,
                "start_time": datetime.now()
            }
        }
        
        result = await validation_service.get_validation_status("test-job-123")
        
        assert result is not None
        assert result["status"] == "running"
        assert result["progress"] == 75
        assert result["total_proxies"] == 100
    
    async def test_get_validation_status_not_found(self, validation_service):
        """測試獲取不存在的驗證任務狀態"""
        with pytest.raises(ProxyValidationError):
            await validation_service.get_validation_status("non-existent-job")
    
    async def test_stop_validation_job(self, validation_service):
        """測試停止驗證任務"""
        validation_service.active_jobs = {
            "test-job-123": {
                "status": "running",
                "task": AsyncMock()
            }
        }
        
        result = await validation_service.stop_validation_job("test-job-123")
        
        assert result is not None
        assert result["status"] == "stopped"
    
    @patch('app.services.validation_service.get_db_connection')
    async def test_get_validation_history(self, mock_db_conn, validation_service):
        """測試獲取驗證歷史"""
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = AsyncMock()
        mock_conn.execute.return_value.fetchall.return_value = [
            {
                "id": 1,
                "start_time": datetime.now(),
                "end_time": datetime.now() + timedelta(hours=1),
                "total_proxies": 100,
                "valid_proxies": 75,
                "success_rate": 0.75
            }
        ]
        mock_conn.execute.return_value.fetchone.return_value = {"total": 1}
        mock_db_conn.return_value.__aenter__.return_value = mock_conn
        
        result = await validation_service.get_validation_history(page=1, page_size=10)
        
        assert result is not None
        assert result["total"] == 1
        assert len(result["history"]) == 1
        assert result["history"][0]["success_rate"] == 0.75


class TestStatisticsService:
    """統計服務測試類"""
    
    @pytest.fixture
    def statistics_service(self):
        """創建統計服務實例"""
        return StatisticsService()
    
    @patch('app.services.statistics_service.get_db_connection')
    async def test_get_proxy_statistics(self, mock_db_conn, statistics_service):
        """測試獲取代理統計"""
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = AsyncMock()
        mock_conn.execute.return_value.fetchone.return_value = {
            "total_proxies": 1000,
            "active_proxies": 750,
            "inactive_proxies": 250,
            "average_score": 75.5,
            "success_rate": 0.75
        }
        mock_db_conn.return_value.__aenter__.return_value = mock_conn
        
        result = await statistics_service.get_proxy_statistics()
        
        assert result is not None
        assert result["total_proxies"] == 1000
        assert result["active_proxies"] == 750
        assert result["success_rate"] == 0.75
    
    @patch('app.services.statistics_service.get_db_connection')
    async def test_get_performance_metrics(self, mock_db_conn, statistics_service):
        """測試獲取性能指標"""
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = AsyncMock()
        mock_conn.execute.return_value.fetchone.return_value = {
            "average_response_time": 2.5,
            "average_download_speed": 500.0,
            "validation_throughput": 50.0,
            "error_rate": 0.05,
            "uptime_percentage": 99.9
        }
        mock_db_conn.return_value.__aenter__.return_value = mock_conn
        
        result = await statistics_service.get_performance_metrics()
        
        assert result is not None
        assert result["average_response_time"] == 2.5
        assert result["error_rate"] == 0.05
        assert result["uptime_percentage"] == 99.9
    
    @patch('app.services.statistics_service.get_db_connection')
    async def test_get_usage_analytics(self, mock_db_conn, statistics_service):
        """測試獲取使用分析"""
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = AsyncMock()
        mock_conn.execute.return_value.fetchall.return_value = [
            {"date": "2024-01-01", "requests": 1000, "unique_proxies": 500},
            {"date": "2024-01-02", "requests": 1200, "unique_proxies": 600}
        ]
        mock_conn.execute.return_value.fetchone.return_value = {"peak_hour": 14}
        mock_db_conn.return_value.__aenter__.return_value = mock_conn
        
        result = await statistics_service.get_usage_analytics(days=7)
        
        assert result is not None
        assert "daily_usage" in result
        assert "peak_usage_hour" in result
        assert len(result["daily_usage"]) == 2
        assert result["peak_usage_hour"] == 14
    
    @patch('app.services.statistics_service.get_db_connection')
    async def test_get_proxy_distribution(self, mock_db_conn, statistics_service):
        """測試獲取代理分佈"""
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = AsyncMock()
        mock_conn.execute.return_value.fetchall.return_value = [
            {"type": "http", "count": 600},
            {"type": "https", "count": 300},
            {"type": "socks5", "count": 100}
        ]
        mock_db_conn.return_value.__aenter__.return_value = mock_conn
        
        result = await statistics_service.get_proxy_distribution()
        
        assert result is not None
        assert len(result) == 3
        assert result[0]["type"] == "http"
        assert result[0]["count"] == 600


if __name__ == "__main__":
    pytest.main([__file__, "-v"])