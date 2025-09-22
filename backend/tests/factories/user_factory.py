"""
用戶模型測試資料工廠
生成用戶相關的測試資料
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from app.models.user_models import (
    UserModel, UserCreate, UserUpdate, UserRole,
    UserStatus, UserLogin, UserToken
)


class UserFactory:
    """用戶模型測試資料工廠"""
    
    # 預設用戶名
    DEFAULT_USERNAMES = [
        "admin", "test_user", "developer", "analyst", "manager",
        "user123", "proxy_master", "data_collector", "validator", "monitor"
    ]
    
    # 預設郵箱域名
    EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "company.com", "test.com"]
    
    # 預設角色
    USER_ROLES = [UserRole.ADMIN, UserRole.USER, UserRole.GUEST]
    
    # 預設狀態
    USER_STATUSES = [UserStatus.ACTIVE, UserStatus.INACTIVE, UserStatus.SUSPENDED]
    
    @classmethod
    def create_user_model(cls, user_id=None, username=None, email=None,
                         role=None, status=None, **kwargs):
        """創建用戶模型實例"""
        import random
        
        if user_id is None:
            user_id = random.randint(1, 10000)
        
        if username is None:
            username = random.choice(cls.DEFAULT_USERNAMES) + str(random.randint(100, 999))
        
        if email is None:
            domain = random.choice(cls.EMAIL_DOMAINS)
            email = f"{username}@{domain}"
        
        if role is None:
            role = random.choice(cls.USER_ROLES)
        
        if status is None:
            status = random.choice(cls.USER_STATUSES)
        
        now = datetime.now()
        
        user_data = {
            "id": user_id,
            "username": username,
            "email": email,
            "hashed_password": kwargs.get("hashed_password", "hashed_password_123"),
            "role": role,
            "status": status,
            "is_active": kwargs.get("is_active", status == UserStatus.ACTIVE),
            "created_at": kwargs.get("created_at", now),
            "updated_at": kwargs.get("updated_at", now),
            "last_login": kwargs.get("last_login", now - timedelta(days=random.randint(0, 30))),
            "login_count": kwargs.get("login_count", random.randint(0, 100)),
            "api_key": kwargs.get("api_key", f"api_key_{user_id}"),
            "api_secret": kwargs.get("api_secret", f"api_secret_{user_id}"),
            "settings": kwargs.get("settings", {
                "theme": "dark",
                "language": "zh-TW",
                "timezone": "Asia/Taipei"
            }),
            "metadata": kwargs.get("metadata", {})
        }
        
        return UserModel(**user_data)
    
    @classmethod
    def create_user_create(cls, username=None, email=None, password=None, **kwargs):
        """創建用戶創建模型實例"""
        import random
        
        if username is None:
            username = random.choice(cls.DEFAULT_USERNAMES) + str(random.randint(100, 999))
        
        if email is None:
            domain = random.choice(cls.EMAIL_DOMAINS)
            email = f"{username}@{domain}"
        
        if password is None:
            password = "test_password_123"
        
        create_data = {
            "username": username,
            "email": email,
            "password": password,
            "role": kwargs.get("role", UserRole.USER),
            "settings": kwargs.get("settings", {
                "theme": "dark",
                "language": "zh-TW",
                "timezone": "Asia/Taipei"
            })
        }
        
        return UserCreate(**create_data)
    
    @classmethod
    def create_user_update(cls, username=None, email=None, **kwargs):
        """創建用戶更新模型實例"""
        update_data = {
            "username": username,
            "email": email,
            "password": kwargs.get("password"),
            "role": kwargs.get("role"),
            "status": kwargs.get("status"),
            "settings": kwargs.get("settings"),
            "metadata": kwargs.get("metadata"),
            "is_active": kwargs.get("is_active")
        }
        
        # 移除None值
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        return UserUpdate(**update_data)
    
    @classmethod
    def create_user_login(cls, username=None, password=None, **kwargs):
        """創建用戶登錄模型實例"""
        import random
        
        if username is None:
            username = random.choice(cls.DEFAULT_USERNAMES) + str(random.randint(100, 999))
        
        if password is None:
            password = "test_password_123"
        
        login_data = {
            "username": username,
            "password": password,
            "remember_me": kwargs.get("remember_me", False),
            "user_agent": kwargs.get("user_agent", "Test User Agent"),
            "ip_address": kwargs.get("ip_address", f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"),
            "device_info": kwargs.get("device_info", "Test Device")
        }
        
        return UserLogin(**login_data)
    
    @classmethod
    def create_user_token(cls, user_id=None, token=None, **kwargs):
        """創建用戶令牌模型實例"""
        import random
        import uuid
        
        if user_id is None:
            user_id = random.randint(1, 10000)
        
        if token is None:
            token = str(uuid.uuid4())
        
        now = datetime.now()
        expires_at = kwargs.get("expires_at", now + timedelta(hours=24))
        
        token_data = {
            "user_id": user_id,
            "token": token,
            "token_type": kwargs.get("token_type", "bearer"),
            "expires_at": expires_at,
            "created_at": kwargs.get("created_at", now),
            "is_active": kwargs.get("is_active", True),
            "scopes": kwargs.get("scopes", ["read", "write"]),
            "refresh_token": kwargs.get("refresh_token", str(uuid.uuid4())),
            "device_id": kwargs.get("device_id", str(uuid.uuid4()))
        }
        
        return UserToken(**token_data)
    
    @classmethod
    def create_user_batch(cls, count, **kwargs):
        """批量創建用戶模型實例"""
        users = []
        for i in range(count):
            user = cls.create_user_model(user_id=i + 1, **kwargs)
            users.append(user)
        
        return users