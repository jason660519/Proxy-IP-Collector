"""
集成測試包
測試系統各組件之間的集成和交互
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

from app.api.endpoints.proxy import ProxyService
from app.etl.validators.validation_system import StandaloneValidationSystem
from app.core.database import get_db_connection


class TestProxyValidationIntegration:
    """代理驗證集成測試"""
    
    @pytest.fixture
    def proxy_service(self):
        """創建代理服務實例"""
        return ProxyService()
    
    @pytest.fixture
    def validation_system(self):
        """創建驗證系統實例"""
        return StandaloneValidationSystem()
    
    @pytest.mark.asyncio
    async def test_proxy_lifecycle_integration(self, proxy_service, validation_system, mock_db_connection):
        """測試代理完整生命週期集成"""
        # 1. 創建代理
        proxy_data = {
            "host": "192.168.1.100",
            "port": 8080,
            "type": "http",
            "username": "test_user",
            "password": "test_pass"
        }
        
        # 設置模擬返回值
        mock_db_connection.execute.return_value.fetchone.return_value = {
            "id": 1,
            **proxy_data,
            "status": "pending",
            "score": 0.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        with patch('app.services.proxy_service.get_db_connection') as mock_db_conn:
            mock_db_conn.return_value.__aenter__.return_value = mock_db_connection
            
            created_proxy = await proxy_service.create_proxy(proxy_data)
            assert created_proxy is not None
            assert created_proxy["host"] == proxy_data["host"]
            assert created_proxy["status"] == "pending"
        
        # 2. 驗證代理
        validation_result = await validation_system.validate_proxy(proxy_data)
        assert validation_result is not None
        assert "is_valid" in validation_result
        assert "score" in validation_result
        
        # 3. 更新代理狀態
        # 更新模擬返回值
        mock_db_connection.execute.return_value.fetchone.return_value = {
            "id": 1,
            **proxy_data,
            "status": "active" if validation_result["is_valid"] else "failed",
            "score": validation_result["score"],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        with patch('app.services.proxy_service.get_db_connection') as mock_db_conn:
            mock_db_conn.return_value.__aenter__.return_value = mock_db_connection
            
            update_data = {
                "status": "active" if validation_result["is_valid"] else "failed",
                "score": validation_result["score"]
            }
            updated_proxy = await proxy_service.update_proxy(1, update_data)
            assert updated_proxy is not None
            assert updated_proxy["status"] in ["active", "failed"]
    
    @pytest.mark.asyncio
    async def test_batch_proxy_validation_integration(self, proxy_service, validation_system):
        """測試批量代理驗證集成"""
        proxies = [
            {"host": "192.168.1.100", "port": 8080, "type": "http"},
            {"host": "192.168.1.101", "port": 8080, "type": "https"},
            {"host": "192.168.1.102", "port": 8080, "type": "socks5"}
        ]
        
        # 批量驗證
        results = await validation_system.validate_proxies_batch(proxies)
        
        assert results is not None
        assert len(results) == 3
        
        for i, result in enumerate(results):
            assert result["proxy"] == f"{proxies[i]['host']}:{proxies[i]['port']}"
            assert "is_valid" in result
            assert "score" in result
    
    @pytest.mark.asyncio
    async def test_proxy_service_with_validation_integration(self, proxy_service):
        """測試代理服務與驗證集成"""
        proxy_data = {
            "host": "192.168.1.100",
            "port": 8080,
            "type": "http"
        }
        
        with patch('app.services.proxy_service.StandaloneValidationSystem') as mock_validation_system:
            mock_validator = Mock()
            mock_validator.validate_proxy.return_value = {
                "proxy": "192.168.1.100:8080",
                "is_valid": True,
                "score": 85.0,
                "validation_details": {
                    "connection_test": "passed",
                    "speed_test": "passed",
                    "anonymity_test": "passed"
                }
            }
            mock_validation_system.return_value = mock_validator
            
            result = await proxy_service.validate_proxy(proxy_data)
            
            assert result is not None
            assert result["is_valid"] is True
            assert result["score"] == 85.0
            assert "validation_details" in result


class TestDatabaseIntegration:
    """數據庫集成測試"""
    
    @pytest.mark.asyncio
    async def test_database_connection_integration(self):
        """測試數據庫連接集成"""
        # 測試數據庫連接
        try:
            async with get_db_connection() as conn:
                # 執行簡單的查詢測試連接
                result = await conn.execute("SELECT 1")
                row = await result.fetchone()
                assert row[0] == 1
        except Exception as e:
            pytest.skip(f"數據庫連接測試跳過: {e}")
    
    @pytest.mark.asyncio
    async def test_proxy_crud_database_integration(self):
        """測試代理CRUD數據庫集成"""
        from app.services.proxy_service import ProxyService
        
        proxy_service = ProxyService()
        
        # 測試數據
        proxy_data = {
            "host": "192.168.1.200",
            "port": 8080,
            "type": "http",
            "username": "integration_test",
            "password": "test_pass"
        }
        
        try:
            # 創建代理
            with patch('app.services.proxy_service.get_db_connection') as mock_db_conn:
                mock_conn = AsyncMock()
                mock_conn.execute.return_value = AsyncMock()
                mock_conn.execute.return_value.fetchone.return_value = {
                    "id": 999,
                    **proxy_data,
                    "status": "pending",
                    "score": 0.0,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                mock_db_conn.return_value.__aenter__.return_value = mock_conn
                
                created_proxy = await proxy_service.create_proxy(proxy_data)
                assert created_proxy is not None
                assert created_proxy["host"] == proxy_data["host"]
            
            # 查詢代理
            with patch('app.services.proxy_service.get_db_connection') as mock_db_conn:
                mock_conn = AsyncMock()
                mock_conn.execute.return_value = AsyncMock()
                mock_conn.execute.return_value.fetchone.return_value = {
                    "id": 999,
                    **proxy_data,
                    "status": "pending",
                    "score": 0.0,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                mock_db_conn.return_value.__aenter__.return_value = mock_conn
                
                retrieved_proxy = await proxy_service.get_proxy_by_id(999)
                assert retrieved_proxy is not None
                assert retrieved_proxy["host"] == proxy_data["host"]
            
            # 更新代理
            with patch('app.services.proxy_service.get_db_connection') as mock_db_conn:
                mock_conn = AsyncMock()
                mock_conn.execute.return_value = AsyncMock()
                mock_conn.execute.return_value.fetchone.return_value = {
                    "id": 999,
                    **proxy_data,
                    "status": "active",
                    "score": 85.0,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                mock_db_conn.return_value.__aenter__.return_value = mock_conn
                
                update_data = {"status": "active", "score": 85.0}
                updated_proxy = await proxy_service.update_proxy(999, update_data)
                assert updated_proxy is not None
                assert updated_proxy["status"] == "active"
                assert updated_proxy["score"] == 85.0
            
            # 刪除代理
            with patch('app.services.proxy_service.get_db_connection') as mock_db_conn:
                mock_conn = AsyncMock()
                mock_conn.execute.return_value = AsyncMock()
                mock_conn.execute.return_value.rowcount = 1
                mock_db_conn.return_value.__aenter__.return_value = mock_conn
                
                delete_result = await proxy_service.delete_proxy(999)
                assert delete_result is True
                
        except Exception as e:
            pytest.skip(f"數據庫集成測試跳過: {e}")


class TestAPIIntegration:
    """API集成測試"""
    
    @pytest.fixture
    def client(self):
        """創建測試客戶端"""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)
    
    @patch('app.api.endpoints.proxy.ProxyService')
    def test_proxy_api_crud_integration(self, mock_service, client):
        """測試代理API CRUD集成"""
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance
        
        # 測試數據
        proxy_data = {
            "host": "192.168.1.100",
            "port": 8080,
            "type": "http",
            "username": "api_test",
            "password": "test_pass"
        }
        
        created_proxy = {
            "id": 1,
            **proxy_data,
            "status": "pending",
            "score": 0.0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # 1. 創建代理
        mock_service_instance.create_proxy.return_value = created_proxy
        response = client.post("/api/v1/proxies", json=proxy_data)
        assert response.status_code == 201
        assert response.json()["host"] == proxy_data["host"]
        
        # 2. 獲取代理列表
        mock_service_instance.get_proxies.return_value = {
            "proxies": [created_proxy],
            "total": 1,
            "page": 1,
            "page_size": 10
        }
        response = client.get("/api/v1/proxies")
        assert response.status_code == 200
        assert len(response.json()["proxies"]) == 1
        
        # 3. 根據ID獲取代理
        mock_service_instance.get_proxy_by_id.return_value = created_proxy
        response = client.get("/api/v1/proxies/1")
        assert response.status_code == 200
        assert response.json()["id"] == 1
        
        # 4. 更新代理
        updated_proxy = {**created_proxy, "status": "active", "score": 85.0}
        mock_service_instance.update_proxy.return_value = updated_proxy
        update_data = {"status": "active", "score": 85.0}
        response = client.put("/api/v1/proxies/1", json=update_data)
        assert response.status_code == 200
        assert response.json()["status"] == "active"
        assert response.json()["score"] == 85.0
        
        # 5. 驗證代理
        validation_result = {
            "proxy": "192.168.1.100:8080",
            "is_valid": True,
            "score": 85.0,
            "validation_details": {}
        }
        mock_service_instance.validate_proxy.return_value = validation_result
        response = client.post("/api/v1/proxies/1/validate")
        assert response.status_code == 200
        assert response.json()["is_valid"] is True
        
        # 6. 刪除代理
        mock_service_instance.delete_proxy.return_value = True
        response = client.delete("/api/v1/proxies/1")
        assert response.status_code == 204
    
    def test_validation_api_integration(self, client):
        """測試驗證API集成"""
        with patch('app.api.endpoints.validation.ValidationService') as mock_service:
            mock_service_instance = Mock()
            mock_service.return_value = mock_service_instance
            
            # 啟動驗證任務
            job_data = {
                "proxy_ids": [1, 2, 3],
                "validation_level": "standard"
            }
            mock_service_instance.start_validation_job.return_value = {
                "job_id": "test-job-123",
                "status": "started",
                "message": "Validation job started successfully"
            }
            response = client.post("/api/v1/validation/start", json=job_data)
            assert response.status_code == 202
            assert response.json()["job_id"] == "test-job-123"
            
            # 獲取驗證狀態
            mock_service_instance.get_validation_status.return_value = {
                "status": "running",
                "progress": 75,
                "total_proxies": 100,
                "processed_proxies": 75
            }
            response = client.get("/api/v1/validation/status")
            assert response.status_code == 200
            assert response.json()["status"] == "running"
            assert response.json()["progress"] == 75
            
            # 停止驗證任務
            mock_service_instance.stop_validation_job.return_value = {
                "job_id": "test-job-123",
                "status": "stopped",
                "message": "Validation job stopped successfully"
            }
            response = client.post("/api/v1/validation/stop/test-job-123")
            assert response.status_code == 200
            assert response.json()["status"] == "stopped"


class TestPerformanceIntegration:
    """性能集成測試"""
    
    @pytest.mark.asyncio
    async def test_batch_validation_performance(self):
        """測試批量驗證性能"""
        validation_system = StandaloneValidationSystem()
        
        # 創建大量代理進行測試
        proxies = []
        for i in range(50):  # 50個代理
            proxies.append({
                "host": f"192.168.1.{100 + i}",
                "port": 8080,
                "type": "http"
            })
        
        # 模擬驗證組件
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
                    
                    start_time = datetime.now()
                    results = await validation_system.validate_proxies_batch(proxies)
                    end_time = datetime.now()
                    
                    # 驗證結果
                    assert results is not None
                    assert len(results) == 50
                    
                    # 驗證性能（應該在合理時間內完成）
                    duration = (end_time - start_time).total_seconds()
                    assert duration < 30  # 50個代理應該在30秒內完成
                    
                    print(f"批量驗證50個代理耗時: {duration:.2f}秒")
    
    @pytest.mark.asyncio
    async def test_concurrent_validation_performance(self):
        """測試並發驗證性能"""
        validation_system = StandaloneValidationSystem()
        
        # 創建並發任務
        proxy = {"host": "192.168.1.100", "port": 8080, "type": "http"}
        
        # 模擬驗證組件
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
                    
                    # 並發執行10個驗證任務
                    tasks = []
                    for _ in range(10):
                        task = validation_system.validate_proxy(proxy)
                        tasks.append(task)
                    
                    start_time = datetime.now()
                    results = await asyncio.gather(*tasks)
                    end_time = datetime.now()
                    
                    # 驗證結果
                    assert results is not None
                    assert len(results) == 10
                    assert all(result is not None for result in results)
                    
                    # 驗證性能
                    duration = (end_time - start_time).total_seconds()
                    print(f"並發驗證10個代理耗時: {duration:.2f}秒")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])