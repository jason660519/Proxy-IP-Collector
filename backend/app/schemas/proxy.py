"""
代理IP數據結構定義
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class ProtocolType(str, Enum):
    """協議類型枚舉"""
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


class AnonymityLevel(str, Enum):
    """匿名等級枚舉"""
    TRANSPARENT = "transparent"
    ANONYMOUS = "anonymous"
    ELITE = "elite"


class ProxyStatus(str, Enum):
    """代理狀態枚舉"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"


class ProxyBase(BaseModel):
    """代理IP基礎模型"""
    ip: str = Field(..., description="IP地址")
    port: int = Field(..., ge=1, le=65535, description="端口號")
    protocol: ProtocolType = Field(..., description="協議類型")
    country: Optional[str] = Field(None, max_length=2, description="國家代碼")
    city: Optional[str] = Field(None, max_length=100, description="城市")
    anonymity: Optional[AnonymityLevel] = Field(None, description="匿名等級")
    status: ProxyStatus = Field(default=ProxyStatus.INACTIVE, description="狀態")
    response_time: int = Field(default=0, ge=0, description="響應時間(ms)")
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="成功率")
    source: Optional[str] = Field(None, max_length=100, description="來源")
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0, description="質量評分")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="額外元數據")
    is_active: bool = Field(default=True, description="是否啟用")

    @validator('ip')
    def validate_ip(cls, v):
        """驗證IP地址格式"""
        import re
        ip_pattern = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
        if not ip_pattern.match(v):
            raise ValueError('Invalid IP address format')
        return v

    @validator('port')
    def validate_port(cls, v):
        """驗證端口範圍"""
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v


class ProxyCreate(ProxyBase):
    """創建代理IP模型"""
    pass


class ProxyUpdate(BaseModel):
    """更新代理IP模型"""
    status: Optional[ProxyStatus] = None
    response_time: Optional[int] = Field(None, ge=0)
    success_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    last_checked: Optional[datetime] = None
    last_success: Optional[datetime] = None


class ProxyResponse(ProxyBase):
    """代理IP響應模型"""
    id: str
    last_checked: Optional[datetime] = None
    last_success: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProxyListResponse(BaseModel):
    """代理IP列表響應"""
    proxies: List[ProxyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProxySourceConfig(BaseModel):
    """代理來源配置"""
    name: str = Field(..., max_length=100, description="來源名稱")
    source_type: str = Field(..., description="來源類型")
    config: Dict[str, Any] = Field(default_factory=dict, description="來源配置")
    is_active: bool = Field(default=True, description="是否啟用")
    priority: int = Field(default=1, ge=1, le=10, description="優先級")
    crawl_interval: int = Field(default=3600, ge=60, description="爬取間隔(秒)")


class ProxyCheckResultBase(BaseModel):
    """代理檢查結果基礎模型"""
    proxy_id: str = Field(..., description="代理ID")
    is_successful: bool = Field(..., description="是否成功")
    response_time: Optional[int] = Field(None, ge=0, description="響應時間")
    error_message: Optional[str] = None
    check_type: str = Field(..., description="檢查類型")
    target_url: Optional[str] = None
    headers_sent: Dict[str, str] = Field(default_factory=dict, description="發送的請求頭")
    headers_received: Dict[str, str] = Field(default_factory=dict, description="接收的響應頭")
    status_code: Optional[int] = None


class ProxyCheckResultCreate(ProxyCheckResultBase):
    """創建代理檢查結果模型"""
    pass


class ProxyCheckResultResponse(ProxyCheckResultBase):
    """代理檢查結果響應模型"""
    id: str
    checked_at: datetime

    class Config:
        from_attributes = True


class ProxyCrawlLogBase(BaseModel):
    """代理爬取日誌基礎模型"""
    source: str = Field(..., max_length=100, description="來源")
    total_found: int = Field(default=0, ge=0, description="總共找到數量")
    success: bool = Field(..., description="是否成功")
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元數據")


class ProxyCrawlLogCreate(ProxyCrawlLogBase):
    """創建代理爬取日誌模型"""
    pass


class ProxyCrawlLogResponse(ProxyCrawlLogBase):
    """代理爬取日誌響應模型"""
    id: str
    crawled_at: datetime

    class Config:
        from_attributes = True


class ETLTaskBase(BaseModel):
    """ETL任務基礎模型"""
    task_type: str = Field(..., description="任務類型")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="任務參數")
    created_by: Optional[str] = Field(None, max_length=100, description="創建者")


class ETLTaskCreate(ETLTaskBase):
    """創建ETL任務模型"""
    pass


class ETLTaskUpdate(BaseModel):
    """更新ETL任務模型"""
    status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[int] = None


class ETLTaskResponse(ETLTaskBase):
    """ETL任務響應模型"""
    id: str
    status: str
    result: Dict[str, Any]
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProxyFilter(BaseModel):
    """代理IP過濾器"""
    protocol: Optional[ProtocolType] = None
    country: Optional[str] = None
    anonymity: Optional[AnonymityLevel] = None
    status: Optional[ProxyStatus] = None
    min_response_time: Optional[int] = Field(None, ge=0)
    max_response_time: Optional[int] = Field(None, ge=0)
    min_success_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    min_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_active: Optional[bool] = None
    source: Optional[str] = None


class ProxyStats(BaseModel):
    """代理統計信息"""
    total_proxies: int
    active_proxies: int
    inactive_proxies: int
    protocols: Dict[str, int]
    countries: Dict[str, int]
    anonymity_levels: Dict[str, int]
    avg_response_time: float
    avg_success_rate: float
    avg_quality_score: float
    last_updated: datetime


class ProxyValidationRequest(BaseModel):
    """代理驗證請求"""
    proxy_ids: Optional[List[str]] = None
    protocols: Optional[List[ProtocolType]] = None
    countries: Optional[List[str]] = None
    max_concurrent: int = Field(default=10, ge=1, le=100)
    timeout: int = Field(default=10, ge=1, le=60)
    test_urls: Optional[List[str]] = None


class ProxyValidationResponse(BaseModel):
    """代理驗證響應"""
    total_tested: int
    successful: int
    failed: int
    results: List[ProxyCheckResultResponse]
    duration: int
    started_at: datetime
    completed_at: datetime