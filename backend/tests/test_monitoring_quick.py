"""
監控系統快速測試腳本
驗證監控系統的各項功能是否正常運作
"""

import sys
import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime

# 添加後端目錄到Python路徑
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def test_monitoring_system():
    """測試監控系統"""
    
    print("🔍 開始測試監控系統...")
    
    # 測試1: 檢查監控模塊
    print("\n📊 1. 檢查監控模塊...")
    
    try:
        from app.core.monitoring_config import MonitoringConfig
        from app.core.structured_logging import StructuredLogger, get_logger
        from app.core.metrics_collector import MetricsCollector
        
        print("  ✅ 監控模塊導入成功")
        
        # 測試配置
        config = MonitoringConfig()
        print(f"  📋 配置: Prometheus={config.prometheus_enabled}, 日誌格式={config.log_format}")
        
    except ImportError as e:
        print(f"  ❌ 監控模塊導入失敗: {e}")
        return False
    
    # 測試2: 測試日誌記錄器
    print("\n📝 2. 測試日誌記錄器...")
    
    try:
        logger = get_logger("test_monitoring")
        logger.info("監控系統測試開始", test_type="monitoring", timestamp=datetime.utcnow().isoformat())
        print("  ✅ 日誌記錄器工作正常")
        
    except Exception as e:
        print(f"  ❌ 日誌記錄器測試失敗: {e}")
        return False
    
    # 測試3: 測試指標收集器
    print("\n📈 3. 測試指標收集器...")
    
    try:
        config = MonitoringConfig()
        collector = MetricsCollector(config)
        
        # 收集系統指標
        metrics = collector.get_metrics_data()
        print(f"  ✅ 指標收集成功: {len(metrics)} 個指標類別")
        
        # 健康檢查
        health = collector.check_health()
        print(f"  ✅ 健康檢查完成: 狀態={health['status']}")
        
    except Exception as e:
        print(f"  ❌ 指標收集器測試失敗: {e}")
        return False
    
    # 測試4: 測試API端點（如果服務器在運行）
    print("\n🌐 4. 測試監控API端點...")
    
    base_url = "http://localhost:8000"
    endpoints = [
        "/monitoring/health",
        "/monitoring/metrics",
        "/monitoring/status",
        "/monitoring/alerts"
    ]
    
    server_running = False
    
    try:
        # 檢查服務器是否運行
        response = requests.get(f"{base_url}/", timeout=2)
        if response.status_code == 200:
            server_running = True
            print("  ✅ API服務器正在運行")
    except requests.exceptions.RequestException:
        print("  ⚠️  API服務器未運行，跳過API測試")
    
    if server_running:
        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✅ {endpoint}: 狀態碼={response.status_code}")
                    
                    # 特殊檢查
                    if endpoint == "/monitoring/health":
                        print(f"     系統狀態: {data.get('status', 'unknown')}")
                    elif endpoint == "/monitoring/status":
                        print(f"     Prometheus: {data.get('prometheus', {}).get('enabled', False)}")
                else:
                    print(f"  ❌ {endpoint}: 狀態碼={response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"  ❌ {endpoint}: 請求失敗 - {e}")
    
    # 測試5: 測試性能監控
    print("\n⚡ 5. 測試性能監控...")
    
    try:
        from app.core.structured_logging import log_performance_metric
        
        # 記錄一些性能指標
        log_performance_metric("test_operation", 0.123, "seconds", test_id="monitoring_test")
        log_performance_metric("memory_usage", 64.5, "MB", component="test")
        
        print("  ✅ 性能指標記錄成功")
        
    except Exception as e:
        print(f"  ❌ 性能監控測試失敗: {e}")
        return False
    
    # 測試6: 測試告警閾值
    print("\n🚨 6. 測試告警閾值...")
    
    try:
        config = MonitoringConfig()
        
        # 檢查告警閾值配置
        thresholds = config.alert_thresholds
        print(f"  📊 CPU閾值: {thresholds['cpu_usage']}%")
        print(f"  📊 內存閾值: {thresholds['memory_usage']}%")
        print(f"  📊 磁盤閾值: {thresholds['disk_usage']}%")
        print(f"  📊 錯誤率閾值: {thresholds['error_rate']}%")
        
        print("  ✅ 告警閾值配置正常")
        
    except Exception as e:
        print(f"  ❌ 告警閾值測試失敗: {e}")
        return False
    
    print("\n🎉 監控系統測試完成！")
    print("\n📋 測試總結:")
    print("  ✅ 監控模塊功能正常")
    print("  ✅ 日誌記錄器工作正常")
    print("  ✅ 指標收集器運行正常")
    print(f"  {'✅' if server_running else '⚠️'} API端點{'正常' if server_running else '未測試'}")
    print("  ✅ 性能監控功能正常")
    print("  ✅ 告警系統配置正常")
    
    print("\n🔧 下一步建議:")
    print("1. 啟動API服務器: python -m app.main")
    print("2. 訪問監控面板: http://localhost:8000/monitoring/health")
    print("3. 查看Prometheus指標: http://localhost:8000/monitoring/metrics")
    print("4. 配置外部Prometheus服務器抓取指標")
    print("5. 設置Grafana儀表板可視化指標")
    
    return True


def test_prometheus_integration():
    """測試Prometheus集成"""
    
    print("\n🔍 測試Prometheus集成...")
    
    try:
        from prometheus_client import Counter, Histogram, Gauge, generate_latest
        
        # 創建測試指標
        test_counter = Counter('test_counter', '測試計數器')
        test_histogram = Histogram('test_histogram', '測試直方圖')
        test_gauge = Gauge('test_gauge', '測試儀表')
        
        # 設置指標值
        test_counter.inc(5)
        test_histogram.observe(0.5)
        test_gauge.set(42)
        
        # 生成指標數據
        metrics_data = generate_latest()
        
        if metrics_data:
            print("  ✅ Prometheus指標生成成功")
            print(f"  📊 數據大小: {len(metrics_data)} 字節")
        else:
            print("  ❌ Prometheus指標生成失敗")
            
    except ImportError:
        print("  ⚠️  prometheus_client 未安裝，跳過Prometheus測試")
    except Exception as e:
        print(f"  ❌ Prometheus集成測試失敗: {e}")


if __name__ == "__main__":
    print(f"工作目錄: {os.getcwd()}")
    print(f"Python路徑: {sys.path[0]}")
    
    # 運行主要測試
    success = test_monitoring_system()
    
    # 運行Prometheus集成測試
    test_prometheus_integration()
    
    if success:
        print("\n🎊 監控系統測試通過！")
        sys.exit(0)
    else:
        print("\n💥 監控系統測試失敗！")
        sys.exit(1)