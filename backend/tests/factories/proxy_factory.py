"""
代理模型測試資料工廠
生成代理相關的測試資料
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from app.models.proxy_models import (
    ProxyModel, ProxyStatus, ProxyCreate, ProxyUpdate,
    ProxyValidationResult, ProxyStatistics
)


class ProxyFactory:
    """代理模型測試資料工廠"""
    
    # 預設代理主機列表
    DEFAULT_HOSTS = [
        "192.168.1.100", "192.168.1.101", "192.168.1.102",
        "10.0.0.1", "10.0.0.2", "10.0.0.3",
        "172.16.0.1", "172.16.0.2", "172.16.0.3"
    ]
    
    # 預設代理類型
    PROXY_TYPES = ["http", "https", "socks5", "socks4"]
    
    # 預設端口範圍
    PORT_RANGE = (8000, 9000)
    
    @classmethod
    def create_proxy_model(cls, proxy_id=None, host=None, port=None, 
                          proxy_type=None, status=None, score=None, **kwargs):
        """創建代理模型實例"""
        import random
        
        if proxy_id is None:
            proxy_id = random.randint(1, 10000)
        
        if host is None:
            host = random.choice(cls.DEFAULT_HOSTS)
        
        if port is None:
            port = random.randint(*cls.PORT_RANGE)
        
        if proxy_type is None:
            proxy_type = random.choice(cls.PROXY_TYPES)
        
        if status is None:
            status = random.choice(list(ProxyStatus))
        
        if score is None:
            score = round(random.uniform(0, 100), 1)
        
        now = datetime.now()
        
        proxy_data = {
            "id": proxy_id,
            "host": host,
            "port": port,
            "type": proxy_type,
            "status": status,
            "score": score,
            "created_at": kwargs.get("created_at", now),
            "updated_at": kwargs.get("updated_at", now),
            "username": kwargs.get("username"),
            "password": kwargs.get("password"),
            "country": kwargs.get("country", "US"),
            "city": kwargs.get("city", "New York"),
            "isp": kwargs.get("isp", "Test ISP"),
            "last_validated": kwargs.get("last_validated", now - timedelta(hours=1)),
            "validation_count": kwargs.get("validation_count", random.randint(0, 100)),
            "success_count": kwargs.get("success_count", random.randint(0, 80)),
            "response_time": kwargs.get("response_time", round(random.uniform(0.1, 5.0), 2)),
            "download_speed": kwargs.get("download_speed", round(random.uniform(100, 1000), 2))
        }
        
        return ProxyModel(**proxy_data)
    
    @classmethod
    def create_proxy_create(cls, host=None, port=None, proxy_type=None, **kwargs):
        """創建代理創建模型實例"""
        import random
        
        if host is None:
            host = random.choice(cls.DEFAULT_HOSTS)
        
        if port is None:
            port = random.randint(*cls.PORT_RANGE)
        
        if proxy_type is None:
            proxy_type = random.choice(cls.PROXY_TYPES)
        
        create_data = {
            "host": host,
            "port": port,
            "type": proxy_type,
            "username": kwargs.get("username"),
            "password": kwargs.get("password"),
            "country": kwargs.get("country", "US"),
            "city": kwargs.get("city", "New York"),
            "isp": kwargs.get("isp", "Test ISP")
        }
        
        return ProxyCreate(**create_data)
    
    @classmethod
    def create_proxy_batch(cls, count, **kwargs):
        """批量創建代理模型實例"""
        proxies = []
        for i in range(count):
            proxy = cls.create_proxy_model(proxy_id=i + 1, **kwargs)
            proxies.append(proxy)
        
        return proxies