"""
驗證模型測試資料工廠
生成驗證相關的測試資料
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from app.models.validation_models import (
    ValidationRequest, ValidationResponse, ValidationStatus,
    ValidationResult, ProxyValidationResult
)


class ValidationFactory:
    """驗證模型測試資料工廠"""
    
    # 預設測試URL
    TEST_URLS = [
        "http://httpbin.org/ip",
        "http://httpbin.org/user-agent",
        "http://httpbin.org/headers",
        "https://www.google.com",
        "https://www.baidu.com",
        "https://api.ipify.org?format=json"
    ]
    
    # 預設用戶代理
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    ]
    
    # 預設超時時間
    DEFAULT_TIMEOUTS = [5, 10, 15, 30, 60]
    
    @classmethod
    def create_validation_request(cls, proxy_id=None, url=None, 
                                user_agent=None, timeout=None, **kwargs):
        """創建驗證請求模型實例"""
        import random
        
        if proxy_id is None:
            proxy_id = random.randint(1, 1000)
        
        if url is None:
            url = random.choice(cls.TEST_URLS)
        
        if user_agent is None:
            user_agent = random.choice(cls.USER_AGENTS)
        
        if timeout is None:
            timeout = random.choice(cls.DEFAULT_TIMEOUTS)
        
        request_data = {
            "proxy_id": proxy_id,
            "url": url,
            "user_agent": user_agent,
            "timeout": timeout,
            "follow_redirects": kwargs.get("follow_redirects", True),
            "max_redirects": kwargs.get("max_redirects", 5),
            "verify_ssl": kwargs.get("verify_ssl", True),
            "headers": kwargs.get("headers", {}),
            "test_download": kwargs.get("test_download", False),
            "download_url": kwargs.get("download_url", "http://speedtest.ftp.otenet.gr/files/test100k.txt"),
            "download_size": kwargs.get("download_size", 102400)  # 100KB
        }
        
        return ValidationRequest(**request_data)
    
    @classmethod
    def create_validation_response(cls, request_id=None, proxy_id=None,
                                 status=None, response_time=None, **kwargs):
        """創建驗證響應模型實例"""
        import random
        
        if request_id is None:
            request_id = random.randint(1000, 9999)
        
        if proxy_id is None:
            proxy_id = random.randint(1, 1000)
        
        if status is None:
            status = random.choice(list(ValidationStatus))
        
        if response_time is None:
            response_time = round(random.uniform(0.1, 10.0), 2)
        
        now = datetime.now()
        
        response_data = {
            "request_id": request_id,
            "proxy_id": proxy_id,
            "status": status,
            "response_time": response_time,
            "status_code": kwargs.get("status_code", random.choice([200, 201, 404, 500])),
            "error_message": kwargs.get("error_message"),
            "ip_address": kwargs.get("ip_address", f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"),
            "country": kwargs.get("country", "Unknown"),
            "user_agent": kwargs.get("user_agent"),
            "headers": kwargs.get("headers", {}),
            "content_length": kwargs.get("content_length", random.randint(100, 10000)),
            "download_speed": kwargs.get("download_speed", round(random.uniform(100, 1000), 2)),
            "validated_at": kwargs.get("validated_at", now)
        }
        
        return ValidationResponse(**response_data)
    
    @classmethod
    def create_validation_result(cls, proxy_id=None, total_tests=None,
                              success_count=None, failed_count=None, **kwargs):
        """創建驗證結果模型實例"""
        import random
        
        if proxy_id is None:
            proxy_id = random.randint(1, 1000)
        
        if total_tests is None:
            total_tests = random.randint(1, 10)
        
        if success_count is None:
            success_count = random.randint(0, total_tests)
        
        if failed_count is None:
            failed_count = total_tests - success_count
        
        success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
        
        now = datetime.now()
        
        result_data = {
            "proxy_id": proxy_id,
            "total_tests": total_tests,
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": round(success_rate, 2),
            "average_response_time": kwargs.get("average_response_time", round(random.uniform(0.5, 5.0), 2)),
            "average_download_speed": kwargs.get("average_download_speed", round(random.uniform(200, 800), 2)),
            "last_validated": kwargs.get("last_validated", now),
            "validation_period": kwargs.get("validation_period", 3600)  # 1小時
        }
        
        return ValidationResult(**result_data)
    
    @classmethod
    def create_proxy_validation_result(cls, proxy=None, validation_result=None,
                                     responses=None, **kwargs):
        """創建代理驗證結果模型實例"""
        from .proxy_factory import ProxyFactory
        
        if proxy is None:
            proxy = ProxyFactory.create_proxy_model()
        
        if validation_result is None:
            validation_result = cls.create_validation_result(proxy_id=proxy.id)
        
        if responses is None:
            responses = [
                cls.create_validation_response(proxy_id=proxy.id)
                for _ in range(3)
            ]
        
        result_data = {
            "proxy": proxy,
            "validation_result": validation_result,
            "responses": responses,
            "validated_at": kwargs.get("validated_at", datetime.now()),
            "is_valid": kwargs.get("is_valid", validation_result.success_rate >= 80),
            "recommended_status": kwargs.get("recommended_status", 
                                           "active" if validation_result.success_rate >= 80 else "inactive")
        }
        
        return ProxyValidationResult(**result_data)
    
    @classmethod
    def create_validation_batch(cls, count, **kwargs):
        """批量創建驗證請求"""
        requests = []
        for i in range(count):
            request = cls.create_validation_request(**kwargs)
            requests.append(request)
        
        return requests