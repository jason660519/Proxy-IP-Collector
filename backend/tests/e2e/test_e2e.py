"""
端到端測試包
測試完整的用戶流程和系統功能
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path
import json
import httpx

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from app.main import app


class TestEndToEndProxyManagement:
    """代理管理端到端測試"""
    
    @pytest.fixture
    def client(self):
        """創建測試客戶端"""
        return TestClient(app)
    
    @pytest.fixture
    def test_proxy_data(self):
        """測試代理數據"""
        return {
            "host": "192.168.1.100",
            "port": 8080,
            "type": "http",
            "username": "e2e_test",
            "password": "test_pass"
        }
    
    def test_complete_proxy_lifecycle_e2e(self, client, test_proxy_data):
        """測試完整的代理生命週期端到端流程"""
        
        # 1. 創建代理
        with patch('app.services.proxy_service.get_db_connection') as mock_db_conn:
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = AsyncMock()
            mock_conn.execute.return_value.fetchone.return_value = {
                "id": 1,
                **test_proxy_data,
                "status": "pending",
                "score": 0.0,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            mock_db_conn.return_value.__aenter__.return_value = mock_conn
            
            response = client.post("/api/v1/proxies", json=test_proxy_data)
            assert response.status_code == 201
            created_proxy = response.json()
            proxy_id = created_proxy["id"]
            
            # 驗證創建的代理數據
            assert created_proxy["host"] == test_proxy_data["host"]
            assert created_proxy["port"] == test_proxy_data["port"]
            assert created_proxy["status"] == "pending"
        
        # 2. 獲取代理詳情
        with patch('app.services.proxy_service.get_db_connection') as mock_db_conn:
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = AsyncMock()
            mock_conn.execute.return_value.fetchone.return_value = created_proxy
            mock_db_conn.return_value.__aenter__.return_value = mock_conn
            
            response = client.get(f"/api/v1/proxies/{proxy_id}")
            assert response.status_code == 200
            retrieved_proxy = response.json()
            assert retrieved_proxy["id"] == proxy_id
        
        # 3. 驗證代理
        with patch('app.services.proxy_service.StandaloneValidationSystem') as mock_validation:
            mock_validator = Mock()
            mock_validator.validate_proxy.return_value = {
                "proxy": f"{test_proxy_data['host']}:{test_proxy_data['port']}",
                "is_valid": True,
                "score": 85.0,
                "validation_details": {
                    "connection_test": "passed",
                    "speed_test": "passed",
                    "anonymity_test": "passed"
                }
            }
            mock_validation.return_value = mock_validator
            
            response = client.post(f"/api/v1/proxies/{proxy_id}/validate")
            assert response.status_code == 200
            validation_result = response.json()
            assert validation_result["is_valid"] is True
            assert validation_result["score"] == 85.0
        
        # 4. 更新代理狀態
        update_data = {"status": "active", "score": 85.0}
        with patch('app.services.proxy_service.get_db_connection') as mock_db_conn:
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = AsyncMock()
            mock_conn.execute.return_value.fetchone.return_value = {
                **created_proxy,
                "status": "active",
                "score": 85.0,
                "updated_at": datetime.now()
            }
            mock_db_conn.return_value.__aenter__.return_value = mock_conn
            
            response = client.put(f"/api/v1/proxies/{proxy_id}", json=update_data)
            assert response.status_code == 200
            updated_proxy = response.json()
            assert updated_proxy["status"] == "active"
            assert updated_proxy["score"] == 85.0
        
        # 5. 獲取代理列表
        with patch('app.services.proxy_service.get_db_connection') as mock_db_conn:
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = AsyncMock()
            mock_conn.execute.return_value.fetchall.return_value = [updated_proxy]
            mock_conn.execute.return_value.fetchone.return_value = {"count": 1}
            mock_db_conn.return_value.__aenter__.return_value = mock_conn
            
            response = client.get("/api/v1/proxies")
            assert response.status_code == 200
            proxy_list = response.json()
            assert proxy_list["total"] == 1
            assert len(proxy_list["proxies"]) == 1
        
        # 6. 刪除代理
        with patch('app.services.proxy_service.get_db_connection') as mock_db_conn:
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = AsyncMock()
            mock_conn.execute.return_value.rowcount = 1
            mock_db_conn.return_value.__aenter__.return_value = mock_conn
            
            response = client.delete(f"/api/v1/proxies/{proxy_id}")
            assert response.status_code == 204
        
        # 7. 驗證代理已被刪除
        with patch('app.services.proxy_service.get_db_connection') as mock_db_conn:
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = AsyncMock()
            mock_conn.execute.return_value.fetchone.return_value = None
            mock_db_conn.return_value.__aenter__.return_value = mock_conn
            
            response = client.get(f"/api/v1/proxies/{proxy_id}")
            assert response.status_code == 404
    
    def test_batch_proxy_validation_e2e(self, client):
        """測試批量代理驗證端到端流程"""
        
        # 創建多個代理
        proxies = [
            {"host": "192.168.1.100", "port": 8080, "type": "http"},
            {"host": "192.168.1.101", "port": 8080, "type": "https"},
            {"host": "192.168.1.102", "port": 8080, "type": "socks5"}
        ]
        
        created_proxies = []
        for i, proxy_data in enumerate(proxies):
            with patch('app.services.proxy_service.get_db_connection') as mock_db_conn:
                mock_conn = AsyncMock()
                mock_conn.execute.return_value = AsyncMock()
                mock_conn.execute.return_value.fetchone.return_value = {
                    "id": i + 1,
                    **proxy_data,
                    "status": "pending",
                    "score": 0.0,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                mock_db_conn.return_value.__aenter__.return_value = mock_conn
                
                response = client.post("/api/v1/proxies", json=proxy_data)
                assert response.status_code == 201
                created_proxies.append(response.json())
        
        # 批量驗證
        validation_request = {
            "proxy_ids": [p["id"] for p in created_proxies],
            "validation_level": "standard"
        }
        
        with patch('app.api.endpoints.validation.ValidationService') as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.start_validation_job.return_value = {
                "job_id": "batch-job-123",
                "status": "started",
                "message": "Batch validation started"
            }
            mock_service.return_value = mock_service_instance
            
            response = client.post("/api/v1/validation/start", json=validation_request)
            assert response.status_code == 202
            job_result = response.json()
            assert job_result["job_id"] == "batch-job-123"
            assert job_result["status"] == "started"
        
        # 檢查驗證狀態
        with patch('app.api.endpoints.validation.ValidationService') as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.get_validation_status.return_value = {
                "status": "completed",
                "progress": 100,
                "total_proxies": 3,
                "processed_proxies": 3,
                "results": [
                    {"proxy_id": 1, "is_valid": True, "score": 85.0},
                    {"proxy_id": 2, "is_valid": True, "score": 78.0},
                    {"proxy_id": 3, "is_valid": False, "score": 25.0}
                ]
            }
            mock_service.return_value = mock_service_instance
            
            response = client.get("/api/v1/validation/status")
            assert response.status_code == 200
            status_result = response.json()
            assert status_result["status"] == "completed"
            assert status_result["progress"] == 100
            assert len(status_result["results"]) == 3


class TestEndToEndStatistics:
    """統計功能端到端測試"""
    
    @pytest.fixture
    def client(self):
        """創建測試客戶端"""
        return TestClient(app)
    
    def test_statistics_dashboard_e2e(self, client):
        """測試統計儀表板端到端流程"""
        
        # 獲取代理統計
        with patch('app.api.endpoints.statistics.StatisticsService') as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.get_proxy_statistics.return_value = {
                "total_proxies": 100,
                "active_proxies": 75,
                "failed_proxies": 15,
                "pending_proxies": 10,
                "average_score": 82.5
            }
            mock_service.return_value = mock_service_instance
            
            response = client.get("/api/v1/statistics/proxies")
            assert response.status_code == 200
            proxy_stats = response.json()
            assert proxy_stats["total_proxies"] == 100
            assert proxy_stats["active_proxies"] == 75
            assert proxy_stats["average_score"] == 82.5
        
        # 獲取性能指標
        with patch('app.api.endpoints.statistics.StatisticsService') as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.get_performance_metrics.return_value = {
                "average_response_time": 2.5,
                "average_download_speed": 450.0,
                "validation_success_rate": 0.85,
                "total_validations": 1000
            }
            mock_service.return_value = mock_service_instance
            
            response = client.get("/api/v1/statistics/performance")
            assert response.status_code == 200
            performance_metrics = response.json()
            assert performance_metrics["average_response_time"] == 2.5
            assert performance_metrics["validation_success_rate"] == 0.85
        
        # 獲取使用分析
        with patch('app.api.endpoints.statistics.StatisticsService') as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.get_usage_analytics.return_value = {
                "daily_usage": [
                    {"date": "2024-01-01", "usage_count": 150},
                    {"date": "2024-01-02", "usage_count": 180},
                    {"date": "2024-01-03", "usage_count": 165}
                ],
                "peak_usage_time": "14:00-16:00",
                "most_used_proxy_type": "http"
            }
            mock_service.return_value = mock_service_instance
            
            response = client.get("/api/v1/statistics/usage")
            assert response.status_code == 200
            usage_analytics = response.json()
            assert len(usage_analytics["daily_usage"]) == 3
            assert usage_analytics["peak_usage_time"] == "14:00-16:00"
            assert usage_analytics["most_used_proxy_type"] == "http"
        
        # 獲取代理分佈
        with patch('app.api.endpoints.statistics.StatisticsService') as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.get_proxy_distribution.return_value = {
                "by_type": {
                    "http": 60,
                    "https": 25,
                    "socks5": 15
                },
                "by_country": {
                    "US": 40,
                    "CN": 30,
                    "EU": 30
                },
                "by_score_range": {
                    "90-100": 25,
                    "80-89": 35,
                    "70-79": 25,
                    "<70": 15
                }
            }
            mock_service.return_value = mock_service_instance
            
            response = client.get("/api/v1/statistics/distribution")
            assert response.status_code == 200
            distribution = response.json()
            assert distribution["by_type"]["http"] == 60
            assert distribution["by_country"]["US"] == 40
            assert sum(distribution["by_score_range"].values()) == 100


class TestEndToEndErrorHandling:
    """錯誤處理端到端測試"""
    
    @pytest.fixture
    def client(self):
        """創建測試客戶端"""
        return TestClient(app)
    
    def test_invalid_proxy_creation_e2e(self, client):
        """測試無效代理創建的錯誤處理"""
        
        # 測試無效的代理數據
        invalid_proxies = [
            {"host": "invalid_host", "port": 8080, "type": "http"},  # 無效的主機
            {"host": "192.168.1.100", "port": 99999, "type": "http"},  # 無效的端口
            {"host": "192.168.1.100", "port": 8080, "type": "invalid_type"},  # 無效的類型
            {"port": 8080, "type": "http"},  # 缺少主機
            {"host": "192.168.1.100", "type": "http"},  # 缺少端口
        ]
        
        for invalid_proxy in invalid_proxies:
            response = client.post("/api/v1/proxies", json=invalid_proxy)
            assert response.status_code == 422  # 驗證錯誤
    
    def test_nonexistent_proxy_operations_e2e(self, client):
        """測試不存在代理的操作錯誤處理"""
        
        nonexistent_id = 99999
        
        # 獲取不存在的代理
        with patch('app.services.proxy_service.get_db_connection') as mock_db_conn:
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = AsyncMock()
            mock_conn.execute.return_value.fetchone.return_value = None
            mock_db_conn.return_value.__aenter__.return_value = mock_conn
            
            response = client.get(f"/api/v1/proxies/{nonexistent_id}")
            assert response.status_code == 404
    
    def test_validation_errors_e2e(self, client):
        """測試驗證相關的錯誤處理"""
        
        # 驗證不存在的代理
        with patch('app.services.proxy_service.get_db_connection') as mock_db_conn:
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = AsyncMock()
            mock_conn.execute.return_value.fetchone.return_value = None
            mock_db_conn.return_value.__aenter__.return_value = mock_conn
            
            response = client.post("/api/v1/proxies/99999/validate")
            assert response.status_code == 404
    
    def test_batch_validation_errors_e2e(self, client):
        """測試批量驗證的錯誤處理"""
        
        # 空的代理ID列表
        response = client.post("/api/v1/validation/start", json={"proxy_ids": []})
        assert response.status_code == 422
        
        # 無效的代理ID格式
        response = client.post("/api/v1/validation/start", json={"proxy_ids": ["invalid"]})
        assert response.status_code == 422


class TestEndToEndPerformance:
    """端到端性能測試"""
    
    @pytest.fixture
    def client(self):
        """創建測試客戶端"""
        return TestClient(app)
    
    def test_api_response_times_e2e(self, client):
        """測試API響應時間"""
        
        # 健康檢查端點
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = (end_time - start_time) * 1000  # 轉換為毫秒
        assert response_time < 1000  # 應該在1秒內響應
        print(f"健康檢查響應時間: {response_time:.2f}ms")
        
        # 代理列表端點
        with patch('app.services.proxy_service.get_db_connection') as mock_db_conn:
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = AsyncMock()
            mock_conn.execute.return_value.fetchall.return_value = []
            mock_conn.execute.return_value.fetchone.return_value = {"count": 0}
            mock_db_conn.return_value.__aenter__.return_value = mock_conn
            
            start_time = time.time()
            response = client.get("/api/v1/proxies")
            end_time = time.time()
            
            assert response.status_code == 200
            response_time = (end_time - start_time) * 1000
            assert response_time < 2000  # 應該在2秒內響應
            print(f"代理列表響應時間: {response_time:.2f}ms")
    
    def test_concurrent_requests_e2e(self, client):
        """測試並發請求處理"""
        
        import concurrent.futures
        
        def make_request():
            return client.get("/health")
        
        # 並發執行10個請求
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # 驗證所有請求都成功
        assert all(response.status_code == 200 for response in responses)
        assert len(responses) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])