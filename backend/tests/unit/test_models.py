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

from app.schemas.proxy import ProxyStatus, ProxyCreate, ProxyUpdate, ProxyCheckResultResponse, ProxyStats, ProxyBase, ProxyValidationResponse
class TestProxys:
    """代理模型測試類"""
    
    def test_proxy_model_creation_valid(self):
        """測試創建有效的代理模型"""
        proxy_data = {
            "ip": "192.168.1.100",
            "port": 8080,
            "protocol": "http",
            "status": ProxyStatus.ACTIVE,
            "response_time": 1000,
            "success_rate": 0.85,
            "quality_score": 0.85
        }
        
        proxy = ProxyBase(**proxy_data)
        
        assert proxy.ip == "192.168.1.100"
        assert proxy.port == 8080
        assert proxy.protocol == "http"
        assert proxy.status == ProxyStatus.ACTIVE
        assert proxy.quality_score == 0.85
    
    def test_proxy_model_creation_invalid_port(self):
        """測試創建代理模型 - 無效端口"""
        proxy_data = {
            "ip": "192.168.1.100",
            "port": 99999,  # 無效端口
            "protocol": "http",
            "status": ProxyStatus.ACTIVE,
            "response_time": 1000,
            "success_rate": 0.85,
            "quality_score": 0.85
        }
        
        with pytest.raises(ValueError):
            ProxyBase(**proxy_data)
    
    def test_proxy_model_creation_invalid_type(self):
        """測試創建代理模型 - 無效類型"""
        proxy_data = {
            "ip": "192.168.1.100",
            "port": 8080,
            "protocol": "invalid_type",  # 無效類型
            "status": ProxyStatus.ACTIVE,
            "response_time": 1000,
            "success_rate": 0.85,
            "quality_score": 0.85
        }
        
        with pytest.raises(ValidationError):
            ProxyBase(**proxy_data)
    
    def test_proxy_model_creation_invalid_score(self):
        """測試創建代理模型 - 無效評分"""
        proxy_data = {
            "ip": "192.168.1.100",
            "port": 8080,
            "protocol": "http",
            "status": ProxyStatus.ACTIVE,
            "response_time": 1000,
            "success_rate": 0.85,
            "quality_score": 1.5  # 無效評分（超過1.0）
        }
        
        with pytest.raises(ValidationError):
            ProxyBase(**proxy_data)
    
    def test_proxy_create_model(self):
        """測試代理創建模型"""
        create_data = {
            "ip": "192.168.1.100",
            "port": 8080,
            "protocol": "http",
            "country": "US",
            "city": "New York"
        }
        
        proxy_create = ProxyCreate(**create_data)
        
        assert proxy_create.ip == "192.168.1.100"
        assert proxy_create.port == 8080
        assert proxy_create.protocol == "http"
        assert proxy_create.country == "US"
        assert proxy_create.city == "New York"
    
    def test_proxy_update_model(self):
        """測試代理更新模型"""
        update_data = {
            "status": ProxyStatus.INACTIVE,
            "quality_score": 0.9
        }
        
        proxy_update = ProxyUpdate(**update_data)
        
        assert proxy_update.status == ProxyStatus.INACTIVE
        assert proxy_update.quality_score == 0.9
    
    def test_proxy_check_result_response_model(self):
        """測試代理檢查結果響應模型"""
        from datetime import datetime
        result_data = {
            "id": "result_123",
            "proxy_id": "proxy_123",
            "is_successful": True,
            "response_time": 1500,
            "error_message": None,
            "check_type": "connection",
            "target_url": "http://example.com",
            "headers_sent": {"User-Agent": "test"},
            "headers_received": {"Content-Type": "text/html"},
            "status_code": 200,
            "checked_at": datetime.now()
        }
        
        check_result = ProxyCheckResultResponse(**result_data)
        
        assert check_result.id == "result_123"
        assert check_result.proxy_id == "proxy_123"
        assert check_result.is_successful is True
        assert check_result.response_time == 1500
        assert check_result.status_code == 200
    
    def test_proxy_stats_model(self):
        """測試代理統計模型"""
        stats_data = {
            "total_proxies": 1000,
            "active_proxies": 750,
            "inactive_proxies": 250,
            "protocols": {"http": 600, "https": 300, "socks5": 100},
            "countries": {"US": 300, "CN": 200, "EU": 500},
            "anonymity_levels": {"transparent": 100, "anonymous": 400, "elite": 500},
            "avg_response_time": 1500.0,
            "avg_success_rate": 0.75,
            "avg_quality_score": 0.8,
            "last_updated": datetime.now()
        }
        
        stats = ProxyStats(**stats_data)
        
        assert stats.total_proxies == 1000
        assert stats.active_proxies == 750
        assert stats.avg_success_rate == 0.75
        assert stats.protocols["http"] == 600
        assert stats.protocols["https"] == 300
        assert stats.protocols["socks5"] == 100
    
    def test_proxy_status_enum(self):
        """測試代理狀態枚舉"""
        # 測試所有有效的狀態值
        valid_statuses = [
            ProxyStatus.ACTIVE,
            ProxyStatus.INACTIVE,
            ProxyStatus.UNKNOWN
        ]
        
        for status in valid_statuses:
            proxy_data = {
                "ip": "192.168.1.100",
                "port": 8080,
                "protocol": "http",
                "status": status,
                "response_time": 1000,
                "success_rate": 0.85,
                "quality_score": 0.85
            }
            
            proxy = ProxyBase(**proxy_data)
            assert proxy.status == status



class TestModelSerialization:
    """模型序列化測試類"""
    
    def test_proxy_model_to_dict(self):
        """測試代理模型轉換為字典"""
        proxy_data = {
            "ip": "192.168.1.100",
            "port": 8080,
            "protocol": "http",
            "status": ProxyStatus.ACTIVE,
            "response_time": 1000,
            "success_rate": 0.85,
            "quality_score": 0.85
        }
        
        proxy = ProxyBase(**proxy_data)
        proxy_dict = proxy.model_dump()
        
        assert proxy_dict["ip"] == "192.168.1.100"
        assert proxy_dict["port"] == 8080
        assert proxy_dict["protocol"] == "http"
        assert proxy_dict["status"] == ProxyStatus.ACTIVE
        assert proxy_dict["success_rate"] == 0.85
    
    def test_proxy_model_json_serialization(self):
        """測試代理模型JSON序列化"""
        proxy_data = {
            "ip": "192.168.1.100",
            "port": 8080,
            "protocol": "http",
            "status": ProxyStatus.ACTIVE,
            "response_time": 1000,
            "success_rate": 0.85,
            "quality_score": 0.85
        }
        
        proxy = ProxyBase(**proxy_data)
        json_str = proxy.model_dump_json()
        
        assert isinstance(json_str, str)
        assert "192.168.1.100" in json_str
        assert "8080" in json_str
        assert "http" in json_str
    
    def test_validation_result_model_serialization(self):
        """測試驗證結果模型序列化"""
        result_data = {
            "total_tested": 10,
            "successful": 8,
            "failed": 2,
            "results": [],
            "duration": 300,
            "started_at": datetime.now(),
            "completed_at": datetime.now()
        }
        
        result = ProxyValidationResponse(**result_data)
        result_dict = result.model_dump()
        
        assert result_dict["total_tested"] == 10
        assert result_dict["successful"] == 8
        assert result_dict["failed"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])