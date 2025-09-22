"""
API端點單元測試
測試後端API的各個端點功能
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.models.proxy_models import ProxyModel, ProxyStatus
from app.core.exceptions import ProxyValidationError, ProxyNotFoundError


class TestProxyEndpoints:
    """代理相關API端點測試"""
    
    @pytest.fixture
    def client(self):
        """創建測試客戶端"""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)
    
    @pytest.fixture
    def sample_proxy_data(self):
        """樣本代理數據"""
        return {
            "host": "192.168.1.100",
            "port": 8080,
            "type": "http",
            "username": "test_user",
            "password": "test_pass"
        }
    
    def test_health_check(self, client):
        """測試健康檢查端點"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_system_status(self, client):
        """測試系統狀態端點"""
        response = client.get("/api/v1/system/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "uptime" in data
        assert "version" in data
    
    @patch('app.api.endpoints.proxy.ProxyService')
    def test_get_proxies_list(self, mock_service, client):
        """測試獲取代理列表"""
        # 模擬服務返回數據
        mock_service_instance = Mock()
        mock_service_instance.get_proxies.return_value = {
            "proxies": [
                {
                    "id": 1,
                    "host": "192.168.1.100",
                    "port": 8080,
                    "type": "http",
                    "status": "active",
                    "score": 85.0
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 10
        }
        mock_service.return_value = mock_service_instance
        
        response = client.get("/api/v1/proxies")
        
        assert response.status_code == 200
        data = response.json()
        assert "proxies" in data
        assert data["total"] == 1
    
    @patch('app.api.endpoints.proxy.ProxyService')
    def test_get_proxy_by_id_success(self, mock_service, client):
        """測試根據ID獲取代理 - 成功"""
        mock_service_instance = Mock()
        mock_service_instance.get_proxy_by_id.return_value = {
            "id": 1,
            "host": "192.168.1.100",
            "port": 8080,
            "type": "http",
            "status": "active",
            "score": 85.0
        }
        mock_service.return_value = mock_service_instance
        
        response = client.get("/api/v1/proxies/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["host"] == "192.168.1.100"
    
    @patch('app.api.endpoints.proxy.ProxyService')
    def test_get_proxy_by_id_not_found(self, mock_service, client):
        """測試根據ID獲取代理 - 不存在"""
        mock_service_instance = Mock()
        mock_service_instance.get_proxy_by_id.side_effect = ProxyNotFoundError("Proxy not found")
        mock_service.return_value = mock_service_instance
        
        response = client.get("/api/v1/proxies/999")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]
    
    @patch('app.api.endpoints.proxy.ProxyService')
    def test_create_proxy_success(self, mock_service, client, sample_proxy_data):
        """測試創建代理 - 成功"""
        mock_service_instance = Mock()
        mock_service_instance.create_proxy.return_value = {
            "id": 1,
            **sample_proxy_data,
            "status": "pending",
            "score": 0.0,
            "created_at": datetime.now().isoformat()
        }
        mock_service.return_value = mock_service_instance
        
        response = client.post("/api/v1/proxies", json=sample_proxy_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["host"] == sample_proxy_data["host"]
        assert data["port"] == sample_proxy_data["port"]
    
    def test_create_proxy_invalid_data(self, client):
        """測試創建代理 - 無效數據"""
        invalid_data = {
            "host": "invalid_host",
            "port": 99999,  # 無效端口
            "type": "invalid_type"
        }
        
        response = client.post("/api/v1/proxies", json=invalid_data)
        
        assert response.status_code == 422  # 驗證錯誤
    
    @patch('app.api.endpoints.proxy.ProxyService')
    def test_update_proxy_success(self, mock_service, client, sample_proxy_data):
        """測試更新代理 - 成功"""
        mock_service_instance = Mock()
        mock_service_instance.update_proxy.return_value = {
            "id": 1,
            **sample_proxy_data,
            "status": "active",
            "score": 85.0,
            "updated_at": datetime.now().isoformat()
        }
        mock_service.return_value = mock_service_instance
        
        update_data = {"status": "active", "score": 85.0}
        response = client.put("/api/v1/proxies/1", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["score"] == 85.0
    
    @patch('app.api.endpoints.proxy.ProxyService')
    def test_delete_proxy_success(self, mock_service, client):
        """測試刪除代理 - 成功"""
        mock_service_instance = Mock()
        mock_service_instance.delete_proxy.return_value = True
        mock_service.return_value = mock_service_instance
        
        response = client.delete("/api/v1/proxies/1")
        
        assert response.status_code == 204
    
    @patch('app.api.endpoints.proxy.ProxyService')
    def test_validate_proxy_success(self, mock_service, client):
        """測試代理驗證 - 成功"""
        mock_service_instance = Mock()
        mock_service_instance.validate_proxy.return_value = {
            "proxy": "192.168.1.100:8080",
            "is_valid": True,
            "score": 85.0,
            "validation_details": {
                "connection_test": "passed",
                "speed_test": "passed",
                "anonymity_test": "passed"
            }
        }
        mock_service.return_value = mock_service_instance
        
        response = client.post("/api/v1/proxies/1/validate")
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["score"] == 85.0
    
    @patch('app.api.endpoints.proxy.ProxyService')
    def test_validate_proxy_failure(self, mock_service, client):
        """測試代理驗證 - 失敗"""
        mock_service_instance = Mock()
        mock_service_instance.validate_proxy.side_effect = ProxyValidationError("Validation failed")
        mock_service.return_value = mock_service_instance
        
        response = client.post("/api/v1/proxies/1/validate")
        
        assert response.status_code == 422
        data = response.json()
        assert "Validation failed" in data["detail"]
    
    @patch('app.api.endpoints.proxy.ProxyService')
    def test_validate_batch_proxies(self, mock_service, client):
        """測試批量代理驗證"""
        mock_service_instance = Mock()
        mock_service_instance.validate_proxies_batch.return_value = [
            {
                "proxy": "192.168.1.100:8080",
                "is_valid": True,
                "score": 85.0
            },
            {
                "proxy": "192.168.1.101:8080",
                "is_valid": False,
                "score": 25.0
            }
        ]
        mock_service.return_value = mock_service_instance
        
        batch_data = {
            "proxies": [
                {"host": "192.168.1.100", "port": 8080},
                {"host": "192.168.1.101", "port": 8080}
            ]
        }
        
        response = client.post("/api/v1/proxies/validate-batch", json=batch_data)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2


class TestValidationEndpoints:
    """驗證相關API端點測試"""
    
    @pytest.fixture
    def client(self):
        """創建測試客戶端"""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)
    
    @patch('app.api.endpoints.validation.ValidationService')
    def test_get_validation_status(self, mock_service, client):
        """測試獲取驗證狀態"""
        mock_service_instance = Mock()
        mock_service_instance.get_validation_status.return_value = {
            "status": "running",
            "progress": 75,
            "total_proxies": 100,
            "processed_proxies": 75,
            "estimated_completion": (datetime.now() + timedelta(minutes=5)).isoformat()
        }
        mock_service.return_value = mock_service_instance
        
        response = client.get("/api/v1/validation/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["progress"] == 75
    
    @patch('app.api.endpoints.validation.ValidationService')
    def test_get_validation_history(self, mock_service, client):
        """測試獲取驗證歷史"""
        mock_service_instance = Mock()
        mock_service_instance.get_validation_history.return_value = {
            "history": [
                {
                    "id": 1,
                    "start_time": datetime.now().isoformat(),
                    "end_time": (datetime.now() + timedelta(hours=1)).isoformat(),
                    "total_proxies": 100,
                    "valid_proxies": 75,
                    "success_rate": 0.75
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 10
        }
        mock_service.return_value = mock_service_instance
        
        response = client.get("/api/v1/validation/history")
        
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert data["total"] == 1
    
    @patch('app.api.endpoints.validation.ValidationService')
    def test_start_validation_job(self, mock_service, client):
        """測試啟動驗證任務"""
        mock_service_instance = Mock()
        mock_service_instance.start_validation_job.return_value = {
            "job_id": "test-job-123",
            "status": "started",
            "message": "Validation job started successfully"
        }
        mock_service.return_value = mock_service_instance
        
        job_data = {
            "proxy_ids": [1, 2, 3],
            "validation_level": "standard"
        }
        
        response = client.post("/api/v1/validation/start", json=job_data)
        
        assert response.status_code == 202  # Accepted
        data = response.json()
        assert data["status"] == "started"
        assert data["job_id"] == "test-job-123"
    
    @patch('app.api.endpoints.validation.ValidationService')
    def test_stop_validation_job(self, mock_service, client):
        """測試停止驗證任務"""
        mock_service_instance = Mock()
        mock_service_instance.stop_validation_job.return_value = {
            "job_id": "test-job-123",
            "status": "stopped",
            "message": "Validation job stopped successfully"
        }
        mock_service.return_value = mock_service_instance
        
        response = client.post("/api/v1/validation/stop/test-job-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stopped"


class TestStatisticsEndpoints:
    """統計相關API端點測試"""
    
    @pytest.fixture
    def client(self):
        """創建測試客戶端"""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)
    
    @patch('app.api.endpoints.statistics.StatisticsService')
    def test_get_proxy_statistics(self, mock_service, client):
        """測試獲取代理統計"""
        mock_service_instance = Mock()
        mock_service_instance.get_proxy_statistics.return_value = {
            "total_proxies": 1000,
            "active_proxies": 750,
            "inactive_proxies": 250,
            "average_score": 75.5,
            "success_rate": 0.75,
            "by_type": {
                "http": 600,
                "https": 300,
                "socks5": 100
            }
        }
        mock_service.return_value = mock_service_instance
        
        response = client.get("/api/v1/statistics/proxies")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_proxies"] == 1000
        assert data["active_proxies"] == 750
        assert data["success_rate"] == 0.75
    
    @patch('app.api.endpoints.statistics.StatisticsService')
    def test_get_performance_metrics(self, mock_service, client):
        """測試獲取性能指標"""
        mock_service_instance = Mock()
        mock_service_instance.get_performance_metrics.return_value = {
            "average_response_time": 2.5,
            "average_download_speed": 500.0,
            "validation_throughput": 50.0,
            "error_rate": 0.05,
            "uptime_percentage": 99.9
        }
        mock_service.return_value = mock_service_instance
        
        response = client.get("/api/v1/statistics/performance")
        
        assert response.status_code == 200
        data = response.json()
        assert data["average_response_time"] == 2.5
        assert data["error_rate"] == 0.05
    
    @patch('app.api.endpoints.statistics.StatisticsService')
    def test_get_usage_analytics(self, mock_service, client):
        """測試獲取使用分析"""
        mock_service_instance = Mock()
        mock_service_instance.get_usage_analytics.return_value = {
            "daily_usage": [
                {"date": "2024-01-01", "requests": 1000, "unique_proxies": 500},
                {"date": "2024-01-02", "requests": 1200, "unique_proxies": 600}
            ],
            "peak_usage_hour": 14,
            "most_used_proxies": [
                {"proxy": "192.168.1.100:8080", "usage_count": 100},
                {"proxy": "192.168.1.101:8080", "usage_count": 95}
            ]
        }
        mock_service.return_value = mock_service_instance
        
        response = client.get("/api/v1/statistics/usage")
        
        assert response.status_code == 200
        data = response.json()
        assert "daily_usage" in data
        assert "peak_usage_hour" in data
        assert "most_used_proxies" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])