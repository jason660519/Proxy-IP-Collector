"""
監控系統初始化模塊
提供監控系統的統一初始化接口
"""

import asyncio
import logging
from typing import Optional

from .monitoring import (
    initialize_monitoring,
    get_metrics_exporter,
    get_prometheus_exporter,
    get_grafana_dashboard
)
from .health_check import initialize_health_check
from .config_manager import get_config


logger = logging.getLogger(__name__)


class MonitoringManager:
    """監控管理器"""
    
    def __init__(self):
        self.config = get_config()
        self.is_initialized = False
        self.metrics_exporter = None
        self.prometheus_exporter = None
        self.grafana_dashboard = None
        
    async def initialize(self) -> bool:
        """初始化監控系統"""
        try:
            logger.info("開始初始化監控系統...")
            
            # 獲取配置
            monitoring_config = self.config.monitoring
            
            if not monitoring_config.enabled:
                logger.info("監控系統已禁用，跳過初始化")
                return True
            
            # 初始化健康檢查
            await initialize_health_check()
            logger.info("健康檢查初始化完成")
            
            # 初始化指標收集
            await initialize_monitoring()
            logger.info("指標收集初始化完成")
            
            # 獲取導出器實例
            self.metrics_exporter = get_metrics_exporter()
            self.prometheus_exporter = get_prometheus_exporter()
            self.grafana_dashboard = get_grafana_dashboard()
            
            # 啟動Prometheus服務器（如果配置啟用）
            if monitoring_config.prometheus_enabled:
                await self.prometheus_exporter.start_prometheus_server(
                    host=monitoring_config.prometheus_host,
                    port=monitoring_config.prometheus_port
                )
                logger.info(f"Prometheus服務器啟動完成 - {monitoring_config.prometheus_host}:{monitoring_config.prometheus_port}")
            
            # 保存Grafana儀表板配置
            if monitoring_config.grafana_dashboard_path:
                self.grafana_dashboard.save_dashboard_config(
                    monitoring_config.grafana_dashboard_path
                )
                logger.info(f"Grafana儀表板配置已保存到: {monitoring_config.grafana_dashboard_path}")
            
            self.is_initialized = True
            logger.info("監控系統初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"監控系統初始化失敗: {e}")
            return False
    
    async def shutdown(self) -> None:
        """關閉監控系統"""
        try:
            logger.info("開始關閉監控系統...")
            
            if self.metrics_exporter:
                self.metrics_exporter.stop_metrics_collection()
                logger.info("指標收集已停止")
            
            if self.prometheus_exporter:
                self.prometheus_exporter.stop_prometheus_server()
                logger.info("Prometheus服務器已停止")
            
            self.is_initialized = False
            logger.info("監控系統關閉完成")
            
        except Exception as e:
            logger.error(f"監控系統關閉失敗: {e}")
    
    def get_status(self) -> dict:
        """獲取監控系統狀態"""
        return {
            "initialized": self.is_initialized,
            "metrics_exporter": self.metrics_exporter is not None,
            "prometheus_exporter": self.prometheus_exporter is not None,
            "grafana_dashboard": self.grafana_dashboard is not None,
            "config": {
                "enabled": self.config.monitoring.enabled,
                "prometheus_enabled": self.config.monitoring.prometheus_enabled,
                "prometheus_host": self.config.monitoring.prometheus_host,
                "prometheus_port": self.config.monitoring.prometheus_port,
                "grafana_dashboard_path": self.config.monitoring.grafana_dashboard_path
            }
        }


# 全局監控管理器實例
_monitoring_manager: Optional[MonitoringManager] = None


def get_monitoring_manager() -> MonitoringManager:
    """獲取監控管理器實例"""
    global _monitoring_manager
    if _monitoring_manager is None:
        _monitoring_manager = MonitoringManager()
    return _monitoring_manager


async def initialize_monitoring_system() -> bool:
    """初始化監控系統（便捷函數）"""
    manager = get_monitoring_manager()
    return await manager.initialize()


async def shutdown_monitoring_system() -> None:
    """關閉監控系統（便捷函數）"""
    manager = get_monitoring_manager()
    await manager.shutdown()


def get_monitoring_status() -> dict:
    """獲取監控系統狀態（便捷函數）"""
    manager = get_monitoring_manager()
    return manager.get_status()


if __name__ == "__main__":
    # 測試監控系統初始化
    import asyncio
    
    async def test_monitoring_system():
        print("測試監控系統...")
        
        # 初始化監控系統
        success = await initialize_monitoring_system()
        print(f"監控系統初始化: {'成功' if success else '失敗'}")
        
        if success:
            # 獲取狀態
            status = get_monitoring_status()
            print(f"監控系統狀態: {status}")
            
            # 等待一段時間讓指標收集運行
            print("等待指標收集...")
            await asyncio.sleep(10)
            
            # 關閉監控系統
            await shutdown_monitoring_system()
            print("監控系統已關閉")
        
        print("測試完成！")
    
    asyncio.run(test_monitoring_system())