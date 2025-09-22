"""
結構化日誌模塊
提供JSON格式的結構化日誌記錄功能
"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path

from .monitoring_config import MonitoringConfig


class JSONFormatter(logging.Formatter):
    """JSON格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日誌記錄為JSON"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process
        }
        
        # 添加額外字段
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)
        
        # 添加異常信息
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class StructuredLogger:
    """結構化日誌記錄器"""
    
    def __init__(self, name: str, config: MonitoringConfig):
        """初始化日誌記錄器"""
        self.logger = logging.getLogger(name)
        self.config = config
        self._setup_logger()
    
    def _setup_logger(self):
        """設置日誌記錄器"""
        self.logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # 清除現有的處理器
        self.logger.handlers.clear()
        
        # 創建控制台處理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        # 設置格式化器
        if self.config.log_format == "json":
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 創建文件處理器（如果配置了日誌文件）
        if self.config.log_file:
            log_path = Path(self.config.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=self.config.log_max_size,
                backupCount=self.config.log_backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def log(self, level: str, message: str, **kwargs):
        """記錄日誌"""
        if hasattr(self.logger, level.lower()):
            log_method = getattr(self.logger, level.lower())
            
            # 創建額外字段
            extra_fields = {}
            for key, value in kwargs.items():
                if key not in ["exc_info", "stack_info"]:
                    extra_fields[key] = value
            
            # 創建自定義記錄
            record = self.logger.makeRecord(
                name=self.logger.name,
                level=getattr(logging, level.upper()),
                fn="",
                lno=0,
                msg=message,
                args=(),
                exc_info=kwargs.get("exc_info"),
                extra={"extra_fields": extra_fields}
            )
            
            self.logger.handle(record)
    
    def debug(self, message: str, **kwargs):
        """記錄調試日誌"""
        self.log("DEBUG", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """記錄信息日誌"""
        self.log("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """記錄警告日誌"""
        self.log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """記錄錯誤日誌"""
        self.log("ERROR", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """記錄嚴重錯誤日誌"""
        self.log("CRITICAL", message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """記錄異常日誌"""
        self.log("ERROR", message, exc_info=True, **kwargs)


# 全局日誌記錄器實例
_logger: Optional[StructuredLogger] = None


def get_logger(name: str = "app", config: Optional[MonitoringConfig] = None) -> StructuredLogger:
    """獲取日誌記錄器實例"""
    global _logger
    
    if _logger is None:
        if config is None:
            config = MonitoringConfig.from_env()
        _logger = StructuredLogger(name, config)
    
    return _logger


def log_proxy_operation(operation: str, proxy_data: Dict[str, Any], **kwargs):
    """記錄代理操作日誌"""
    logger = get_logger()
    logger.info(
        f"代理操作: {operation}",
        operation=operation,
        proxy_data=proxy_data,
        **kwargs
    )


def log_validation_result(proxy_id: str, is_valid: bool, validation_time: float, **kwargs):
    """記錄代理驗證結果"""
    logger = get_logger()
    logger.info(
        f"代理驗證結果: {'有效' if is_valid else '無效'}",
        proxy_id=proxy_id,
        is_valid=is_valid,
        validation_time=validation_time,
        **kwargs
    )


def log_performance_metric(metric_name: str, value: float, unit: str = "ms", **kwargs):
    """記錄性能指標"""
    logger = get_logger()
    logger.info(
        f"性能指標: {metric_name} = {value} {unit}",
        metric_name=metric_name,
        value=value,
        unit=unit,
        **kwargs
    )


def log_error(error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
    """記錄錯誤"""
    logger = get_logger()
    logger.error(
        f"錯誤: {error_type} - {error_message}",
        error_type=error_type,
        error_message=error_message,
        context=context or {},
        **kwargs
    )


def log_request(method: str, url: str, status_code: int, response_time: float, **kwargs):
    """記錄HTTP請求"""
    logger = get_logger()
    logger.info(
        f"HTTP請求: {method} {url} - {status_code}",
        method=method,
        url=url,
        status_code=status_code,
        response_time=response_time,
        **kwargs
    )