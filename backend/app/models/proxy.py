"""
代理IP數據模型
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON, Index, Text
from sqlalchemy.ext.declarative import declarative_base
import uuid
import os

Base = declarative_base()

# 根據數據庫類型選擇合適的UUID列類型
database_type = os.getenv('DATABASE_TYPE', 'sqlite').lower()

if database_type == 'postgresql':
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    UUIDType = PG_UUID(as_uuid=True)
else:
    # SQLite使用TEXT存儲UUID字符串
    UUIDType = String(36)


class Proxy(Base):
    """代理IP實體模型"""
    __tablename__ = "proxies"
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    ip = Column(String(45), nullable=False, index=True, comment="IP地址")
    port = Column(Integer, nullable=False, comment="端口號")
    protocol = Column(String(10), nullable=False, index=True, comment="協議類型")
    country = Column(String(2), index=True, comment="國家代碼")
    city = Column(String(100), comment="城市")
    anonymity = Column(String(20), index=True, comment="匿名等級")
    status = Column(String(20), default="inactive", index=True, comment="狀態")
    response_time = Column(Integer, default=0, comment="響應時間(ms)")
    success_rate = Column(Float, default=0.0, comment="成功率")
    last_checked = Column(DateTime, default=datetime.utcnow, comment="最後檢查時間")
    last_success = Column(DateTime, comment="最後成功時間")
    source = Column(String(100), comment="來源")
    quality_score = Column(Float, default=0.0, comment="質量評分")
    extra_metadata = Column(JSON, default=dict, comment="額外元數據")
    is_active = Column(Boolean, default=True, index=True, comment="是否啟用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="創建時間")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新時間")
    
    # 複合索引
    __table_args__ = (
        Index('idx_proxy_ip_port', 'ip', 'port', unique=True),
        Index('idx_proxy_status_protocol', 'status', 'protocol'),
        Index('idx_proxy_quality_score', 'quality_score'),
        Index('idx_proxy_last_checked', 'last_checked'),
    )


class ProxySource(Base):
    """代理來源配置"""
    __tablename__ = "proxy_sources"
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, comment="來源名稱")
    source_type = Column(String(50), nullable=False, comment="來源類型")
    config = Column(JSON, default=dict, comment="來源配置")
    is_active = Column(Boolean, default=True, comment="是否啟用")
    priority = Column(Integer, default=1, comment="優先級")
    last_crawl = Column(DateTime, comment="最後爬取時間")
    crawl_interval = Column(Integer, default=3600, comment="爬取間隔(秒)")
    success_rate = Column(Float, default=0.0, comment="成功率")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProxyCheckResult(Base):
    """代理檢查結果"""
    __tablename__ = "proxy_check_results"
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    proxy_id = Column(UUIDType, nullable=False, index=True)
    is_successful = Column(Boolean, nullable=False, comment="是否成功")
    response_time = Column(Integer, comment="響應時間")
    error_message = Column(Text, comment="錯誤信息")
    check_type = Column(String(50), comment="檢查類型")
    target_url = Column(String(500), comment="目標URL")
    headers_sent = Column(JSON, default=dict, comment="發送的請求頭")
    headers_received = Column(JSON, default=dict, comment="接收的響應頭")
    status_code = Column(Integer, comment="HTTP狀態碼")
    checked_at = Column(DateTime, default=datetime.utcnow, index=True, comment="檢查時間")
    
    __table_args__ = (
        Index('idx_check_result_proxy_time', 'proxy_id', 'checked_at'),
        Index('idx_check_result_success', 'is_successful', 'checked_at'),
    )


class ProxyCrawlLog(Base):
    """代理爬取日誌"""
    __tablename__ = "proxy_crawl_logs"
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String(100), nullable=False, index=True, comment="來源")
    total_found = Column(Integer, default=0, comment="總共找到數量")
    success = Column(Boolean, nullable=False, comment="是否成功")
    error_message = Column(Text, comment="錯誤信息")
    extra_metadata = Column(JSON, default=dict, comment="元數據")
    crawled_at = Column(DateTime, default=datetime.utcnow, index=True, comment="爬取時間")
    
    __table_args__ = (
        Index('idx_crawl_log_source_time', 'source', 'crawled_at'),
        Index('idx_crawl_log_success', 'success', 'crawled_at'),
    )


class ETLTask(Base):
    """ETL任務記錄"""
    __tablename__ = "etl_tasks"
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_type = Column(String(50), nullable=False, index=True, comment="任務類型")
    status = Column(String(20), default="pending", index=True, comment="任務狀態")
    parameters = Column(JSON, default=dict, comment="任務參數")
    result = Column(JSON, default=dict, comment="執行結果")
    error_message = Column(Text, comment="錯誤信息")
    started_at = Column(DateTime, comment="開始時間")
    completed_at = Column(DateTime, comment="完成時間")
    duration = Column(Integer, comment="執行時長(秒)")
    created_by = Column(String(100), comment="創建者")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_etl_task_status_type', 'status', 'task_type'),
        Index('idx_etl_task_created', 'created_at'),
    )