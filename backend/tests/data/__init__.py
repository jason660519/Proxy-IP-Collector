"""
測試數據和工具模塊
提供測試所需的樣本數據和輔助函數
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class MockProxyData:
    """模擬代理數據類"""
    host: str
    port: int
    type: str
    username: Optional[str] = None
    password: Optional[str] = None
    status: str = "pending"
    score: float = 0.0
    country: Optional[str] = None
    city: Optional[str] = None
    response_time: Optional[float] = None
    download_speed: Optional[float] = None
    anonymity_level: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TestDataGenerator:
    """測試數據生成器"""
    
    @staticmethod
    def generate_valid_proxy() -> Dict[str, Any]:
        """生成有效的代理數據"""
        return {
            "host": "192.168.1.100",
            "port": 8080,
            "type": "http",
            "username": "test_user",
            "password": "test_pass",
            "status": "active",
            "score": 85.0,
            "country": "US",
            "city": "New York",
            "response_time": 2.5,
            "download_speed": 500.0,
            "anonymity_level": "high",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    
    @staticmethod
    def generate_invalid_proxy() -> Dict[str, Any]:
        """生成無效的代理數據"""
        return {
            "host": "invalid_host",
            "port": 99999,
            "type": "invalid_type"
        }
    
    @staticmethod
    def generate_proxy_list(count: int = 5) -> List[Dict[str, Any]]:
        """生成代理列表"""
        proxies = []
        for i in range(count):
            proxy = {
                "host": f"192.168.1.{100 + i}",
                "port": 8080 + i,
                "type": ["http", "https", "socks5"][i % 3],
                "status": ["active", "failed", "pending"][i % 3],
                "score": 50.0 + (i * 10),
                "country": ["US", "CN", "EU"][i % 3],
                "response_time": 1.0 + (i * 0.5),
                "download_speed": 300.0 + (i * 50)
            }
            proxies.append(proxy)
        return proxies
    
    @staticmethod
    def generate_validation_result(is_valid: bool = True) -> Dict[str, Any]:
        """生成驗證結果"""
        if is_valid:
            return {
                "proxy": "192.168.1.100:8080",
                "is_valid": True,
                "score": 85.0,
                "validation_details": {
                    "connection_test": "passed",
                    "speed_test": "passed",
                    "anonymity_test": "passed",
                    "geo_test": "passed"
                },
                "response_time": 2.5,
                "download_speed": 500.0,
                "anonymity_level": "high",
                "country": "US",
                "city": "New York",
                "validated_at": datetime.now()
            }
        else:
            return {
                "proxy": "192.168.1.100:8080",
                "is_valid": False,
                "score": 25.0,
                "validation_details": {
                    "connection_test": "failed",
                    "speed_test": "failed",
                    "anonymity_test": "failed",
                    "geo_test": "failed"
                },
                "error": "Connection timeout",
                "validated_at": datetime.now()
            }
    
    @staticmethod
    def generate_statistics() -> Dict[str, Any]:
        """生成統計數據"""
        return {
            "total_proxies": 100,
            "active_proxies": 75,
            "failed_proxies": 15,
            "pending_proxies": 10,
            "average_score": 82.5,
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
    
    @staticmethod
    def generate_performance_metrics() -> Dict[str, Any]:
        """生成性能指標"""
        return {
            "average_response_time": 2.5,
            "average_download_speed": 450.0,
            "validation_success_rate": 0.85,
            "total_validations": 1000,
            "validation_time_stats": {
                "min": 1.0,
                "max": 10.0,
                "avg": 3.5,
                "median": 3.0
            }
        }
    
    @staticmethod
    def generate_usage_analytics() -> Dict[str, Any]:
        """生成使用分析"""
        return {
            "daily_usage": [
                {"date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"), 
                 "usage_count": 150 + (i * 10)}
                for i in range(7)
            ],
            "peak_usage_time": "14:00-16:00",
            "most_used_proxy_type": "http",
            "total_requests": 10000,
            "unique_users": 150
        }
    
    @staticmethod
    def generate_api_response(endpoint: str, status: str = "success") -> Dict[str, Any]:
        """生成API響應"""
        if status == "success":
            if endpoint == "proxies":
                return {
                    "proxies": TestDataGenerator.generate_proxy_list(3),
                    "total": 3,
                    "page": 1,
                    "page_size": 10
                }
            elif endpoint == "proxy_detail":
                return TestDataGenerator.generate_valid_proxy()
            elif endpoint == "validation":
                return TestDataGenerator.generate_validation_result()
            elif endpoint == "statistics":
                return TestDataGenerator.generate_statistics()
        else:
            return {
                "error": "Invalid request",
                "message": "The request contains invalid parameters",
                "details": {
                    "field": "host",
                    "message": "Invalid host format"
                }
            }


class MockResponseGenerator:
    """模擬響應生成器"""
    
    @staticmethod
    def create_http_response(status_code: int = 200, 
                           content: str = "", 
                           headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """創建HTTP響應"""
        return {
            "status_code": status_code,
            "content": content or f"Mock response content for status {status_code}",
            "headers": headers or {"Content-Type": "text/html"},
            "text": content or f"Mock response text for status {status_code}",
            "json": lambda: json.loads(content) if content else {}
        }
    
    @staticmethod
    def create_speed_test_response(download_speed: float = 500.0, 
                                 response_time: float = 2.5) -> Dict[str, Any]:
        """創建速度測試響應"""
        return {
            "download_speed": download_speed,
            "response_time": response_time,
            "status": "completed",
            "test_duration": 5.0,
            "file_size": 1024 * 1024  # 1MB
        }
    
    @staticmethod
    def create_geo_response(country: str = "US", 
                          city: str = "New York") -> Dict[str, Any]:
        """創建地理位置響應"""
        return {
            "country": country,
            "city": city,
            "region": f"{city} Region",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "timezone": "America/New_York",
            "isp": "Test ISP",
            "org": "Test Organization"
        }
    
    @staticmethod
    def create_anonymity_response(level: str = "high") -> Dict[str, Any]:
        """創建匿名性測試響應"""
        return {
            "anonymity_level": level,
            "headers_detected": {
                "X-Forwarded-For": "hidden",
                "X-Real-IP": "hidden",
                "Via": "hidden"
            },
            "ip_revealed": False,
            "proxy_detected": True,
            "score": 95.0 if level == "high" else (75.0 if level == "medium" else 50.0)
        }


# 導出常用的測試數據
SAMPLE_PROXIES = TestDataGenerator.generate_proxy_list(5)
SAMPLE_VALID_PROXY = TestDataGenerator.generate_valid_proxy()
SAMPLE_INVALID_PROXY = TestDataGenerator.generate_invalid_proxy()
SAMPLE_VALIDATION_RESULT = TestDataGenerator.generate_validation_result()
SAMPLE_STATISTICS = TestDataGenerator.generate_statistics()
SAMPLE_PERFORMANCE_METRICS = TestDataGenerator.generate_performance_metrics()
SAMPLE_USAGE_ANALYTICS = TestDataGenerator.generate_usage_analytics()