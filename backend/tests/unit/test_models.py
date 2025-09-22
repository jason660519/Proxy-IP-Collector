"""
數據模型單元測試
測試數據模型的驗證和序列化功能
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
import sys
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.models.proxy_models import (
    ProxyModel, ProxyStatus, ProxyCreate, ProxyUpdate,
    ProxyValidationResult, ProxyStatistics, ValidationJob
)
from app.models.validation_models import (
    ValidationRequest, ValidationResponse, ValidationStatus,
    ValidationLevel, ValidationConfig
)


class TestProxyModels:
    """代理模型測試類"""
    
    def test_proxy_model_creation_valid(self):
        """測試創建有效的代理模型"""
        proxy_data = {
            "id": 1,
            "host": "192.168.1.100",
            "port": 8080,
            "type": "http",
            "username": "test_user",
            "password": "test_pass",
            "status": ProxyStatus.ACTIVE,
            "score": 85.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        proxy = ProxyModel(**proxy_data)
        
        assert proxy.id == 1
        assert proxy.host == "192.168.1.100"
        assert proxy.port == 8080
        assert proxy.type == "http"
        assert proxy.status == ProxyStatus.ACTIVE
        assert proxy.score == 85.0
    
    def test_proxy_model_creation_invalid_port(self):
        """測試創建代理模型 - 無效端口"""
        proxy_data = {
            "id": 1,
            "host": "192.168.1.100",
            "port": 99999,  # 無效端口
            "type": "http",
            "status": ProxyStatus.ACTIVE,
            "score": 85.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        with pytest.raises(ValidationError):
            ProxyModel(**proxy_data)
    
    def test_proxy_model_creation_invalid_type(self):
        """測試創建代理模型 - 無效類型"""
        proxy_data = {
            "id": 1,
            "host": "192.168.1.100",
            "port": 8080,
            "type": "invalid_type",  # 無效類型
            "status": ProxyStatus.ACTIVE,
            "score": 85.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        with pytest.raises(ValidationError):
            ProxyModel(**proxy_data)
    
    def test_proxy_model_creation_invalid_score(self):
        """測試創建代理模型 - 無效評分"""
        proxy_data = {
            "id": 1,
            "host": "192.168.1.100",
            "port": 8080,
            "type": "http",
            "status": ProxyStatus.ACTIVE,
            "score": 150.0,  # 無效評分（超過100）
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        with pytest.raises(ValidationError):
            ProxyModel(**proxy_data)
    
    def test_proxy_create_model(self):
        """測試代理創建模型"""
        create_data = {
            "host": "192.168.1.100",
            "port": 8080,
            "type": "http",
            "username": "test_user",
            "password": "test_pass"
        }
        
        proxy_create = ProxyCreate(**create_data)
        
        assert proxy_create.host == "192.168.1.100"
        assert proxy_create.port == 8080
        assert proxy_create.type == "http"
        assert proxy_create.username == "test_user"
        assert proxy_create.password == "test_pass"
    
    def test_proxy_update_model(self):
        """測試代理更新模型"""
        update_data = {
            "status": ProxyStatus.INACTIVE,
            "score": 90.0
        }
        
        proxy_update = ProxyUpdate(**update_data)
        
        assert proxy_update.status == ProxyStatus.INACTIVE
        assert proxy_update.score == 90.0
    
    def test_proxy_validation_result_model(self):
        """測試代理驗證結果模型"""
        result_data = {
            "proxy": "192.168.1.100:8080",
            "is_valid": True,
            "score": 85.0,
            "validation_details": {
                "connection_test": "passed",
                "speed_test": "passed",
                "anonymity_test": "passed"
            },
            "validation_time": datetime.now()
        }
        
        validation_result = ProxyValidationResult(**result_data)
        
        assert validation_result.proxy == "192.168.1.100:8080"
        assert validation_result.is_valid is True
        assert validation_result.score == 85.0
        assert "connection_test" in validation_result.validation_details
    
    def test_proxy_statistics_model(self):
        """測試代理統計模型"""
        stats_data = {
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
        
        stats = ProxyStatistics(**stats_data)
        
        assert stats.total_proxies == 1000
        assert stats.active_proxies == 750
        assert stats.success_rate == 0.75
        assert stats.by_type["http"] == 600
        assert stats.by_type["https"] == 300
        assert stats.by_type["socks5"] == 100
    
    def test_proxy_status_enum(self):
        """測試代理狀態枚舉"""
        # 測試所有有效的狀態值
        valid_statuses = [
            ProxyStatus.ACTIVE,
            ProxyStatus.INACTIVE,
            ProxyStatus.PENDING,
            ProxyStatus.VALIDATING,
            ProxyStatus.FAILED
        ]
        
        for status in valid_statuses:
            proxy_data = {
                "id": 1,
                "host": "192.168.1.100",
                "port": 8080,
                "type": "http",
                "status": status,
                "score": 85.0,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            proxy = ProxyModel(**proxy_data)
            assert proxy.status == status


class TestValidationModels:
    """驗證模型測試類"""
    
    def test_validation_request_model(self):
        """測試驗證請求模型"""
        request_data = {
            "proxy_ids": [1, 2, 3],
            "validation_level": ValidationLevel.STANDARD
        }
        
        request = ValidationRequest(**request_data)
        
        assert request.proxy_ids == [1, 2, 3]
        assert request.validation_level == ValidationLevel.STANDARD
    
    def test_validation_response_model(self):
        """測試驗證響應模型"""
        response_data = {
            "job_id": "test-job-123",
            "status": ValidationStatus.RUNNING,
            "message": "Validation started successfully"
        }
        
        response = ValidationResponse(**response_data)
        
        assert response.job_id == "test-job-123"
        assert response.status == ValidationStatus.RUNNING
        assert response.message == "Validation started successfully"
    
    def test_validation_status_model(self):
        """測試驗證狀態模型"""
        status_data = {
            "job_id": "test-job-123",
            "status": ValidationStatus.COMPLETED,
            "progress": 100,
            "total_proxies": 10,
            "processed_proxies": 10,
            "valid_proxies": 8,
            "invalid_proxies": 2,
            "estimated_completion": datetime.now()
        }
        
        status = ValidationStatus(**status_data)
        
        assert status.job_id == "test-job-123"
        assert status.status == ValidationStatus.COMPLETED
        assert status.progress == 100
        assert status.total_proxies == 10
        assert status.valid_proxies == 8
        assert status.invalid_proxies == 2
    
    def test_validation_level_enum(self):
        """測試驗證級別枚舉"""
        # 測試所有有效的驗證級別
        valid_levels = [
            ValidationLevel.BASIC,
            ValidationLevel.STANDARD,
            ValidationLevel.COMPREHENSIVE
        ]
        
        for level in valid_levels:
            config_data = {"validation_level": level}
            config = ValidationConfig(**config_data)
            assert config.validation_level == level
    
    def test_validation_config_model(self):
        """測試驗證配置模型"""
        config_data = {
            "validation_level": ValidationLevel.COMPREHENSIVE,
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "concurrent_limit": 10
        }
        
        config = ValidationConfig(**config_data)
        
        assert config.validation_level == ValidationLevel.COMPREHENSIVE
        assert config.timeout_seconds == 30
        assert config.retry_attempts == 3
        assert config.concurrent_limit == 10
    
    def test_validation_config_model_defaults(self):
        """測試驗證配置模型默認值"""
        config_data = {
            "validation_level": ValidationLevel.STANDARD
        }
        
        config = ValidationConfig(**config_data)
        
        assert config.validation_level == ValidationLevel.STANDARD
        assert config.timeout_seconds == 10  # 默認值
        assert config.retry_attempts == 2    # 默認值
        assert config.concurrent_limit == 5  # 默認值
    
    def test_validation_job_model(self):
        """測試驗證任務模型"""
        job_data = {
            "id": 1,
            "job_id": "test-job-123",
            "validation_level": ValidationLevel.STANDARD,
            "status": ValidationStatus.RUNNING,
            "total_proxies": 100,
            "processed_proxies": 50,
            "created_at": datetime.now(),
            "started_at": datetime.now(),
            "completed_at": None
        }
        
        job = ValidationJob(**job_data)
        
        assert job.id == 1
        assert job.job_id == "test-job-123"
        assert job.validation_level == ValidationLevel.STANDARD
        assert job.status == ValidationStatus.RUNNING
        assert job.total_proxies == 100
        assert job.processed_proxies == 50
        assert job.completed_at is None


class TestModelSerialization:
    """模型序列化測試類"""
    
    def test_proxy_model_to_dict(self):
        """測試代理模型轉換為字典"""
        proxy_data = {
            "id": 1,
            "host": "192.168.1.100",
            "port": 8080,
            "type": "http",
            "status": ProxyStatus.ACTIVE,
            "score": 85.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        proxy = ProxyModel(**proxy_data)
        proxy_dict = proxy.model_dump()
        
        assert proxy_dict["id"] == 1
        assert proxy_dict["host"] == "192.168.1.100"
        assert proxy_dict["port"] == 8080
        assert proxy_dict["type"] == "http"
        assert proxy_dict["status"] == ProxyStatus.ACTIVE
        assert proxy_dict["score"] == 85.0
    
    def test_proxy_model_json_serialization(self):
        """測試代理模型JSON序列化"""
        proxy_data = {
            "id": 1,
            "host": "192.168.1.100",
            "port": 8080,
            "type": "http",
            "status": ProxyStatus.ACTIVE,
            "score": 85.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        proxy = ProxyModel(**proxy_data)
        json_str = proxy.model_dump_json()
        
        assert isinstance(json_str, str)
        assert "192.168.1.100" in json_str
        assert "8080" in json_str
        assert "http" in json_str
    
    def test_validation_result_model_serialization(self):
        """測試驗證結果模型序列化"""
        result_data = {
            "proxy": "192.168.1.100:8080",
            "is_valid": True,
            "score": 85.0,
            "validation_details": {
                "connection_test": "passed",
                "speed_test": "passed"
            },
            "validation_time": datetime.now()
        }
        
        result = ProxyValidationResult(**result_data)
        result_dict = result.model_dump()
        
        assert result_dict["proxy"] == "192.168.1.100:8080"
        assert result_dict["is_valid"] is True
        assert result_dict["score"] == 85.0
        assert "connection_test" in result_dict["validation_details"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])