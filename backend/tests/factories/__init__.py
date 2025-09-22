"""
測試資料工廠模組
提供各種測試資料的工廠類
"""

from .proxy_factory import ProxyFactory
from .validation_factory import ValidationFactory
from .user_factory import UserFactory

__all__ = ["ProxyFactory", "ValidationFactory", "UserFactory"]