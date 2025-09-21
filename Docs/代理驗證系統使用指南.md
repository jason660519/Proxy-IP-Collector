# 代理驗證系統

這是一個功能完整的代理IP驗證與評分系統，提供智能的代理質量評估和自動化管理功能。

## 功能特性

### 🎯 核心功能
- **智能評分算法**: 綜合考慮連接成功率、響應時間、匿名性、穩定性等多個維度
- **多維度驗證**: 連接性、速度、匿名性、地理位置、穩定性全面檢測
- **自動化調度**: 支持定時任務和批量處理
- **靈活配置**: 多種預設配置和自定義配置選項
- **統計分析**: 詳細的驗證統計和結果分析

### 🔧 驗證組件

#### 1. 代理驗證器 (ProxyValidator)
- 基礎連接測試
- 協議支持 (HTTP, HTTPS, SOCKS4, SOCKS5)
- 錯誤處理和重試機制

#### 2. IP評分引擎 (IPScoringEngine)
- 智能綜合評分算法
- 多維度權重配置
- 評分修正和校準

#### 3. 地理位置驗證器 (GeolocationValidator)
- 真實地理位置檢測
- 代理位置一致性驗證
- 地理位置風險評估

#### 4. 速度測試器 (SpeedTester)
- 連接速度測試
- 下載速度測試
- 響應時間測量
- 穩定性評估

#### 5. 匿名性測試器 (AnonymityTester)
- 匿名等級評估
- 標頭洩露檢測
- 代理特徵識別
- 隱私保護評估

## 快速開始

### 基本使用

```python
import asyncio
from validators import ProxyValidationService

async def main():
    # 創建驗證服務
    service = ProxyValidationService()
    
    # 啟動服務
    await service.start_service()
    
    # 測試代理
    proxy = {
        "ip": "8.8.8.8",
        "port": 8080,
        "protocol": "http"
    }
    
    # 快速驗證
    result = await service.quick_validate(proxy)
    
    if result:
        print(f"代理評分: {result.overall_score:.1f}/100")
        print(f"可用性: {'可用' if result.is_valid else '不可用'}")
        print(f"匿名等級: {result.anonymity_level}")
    
    # 停止服務
    await service.stop_service()

# 運行
asyncio.run(main())
```

### 批量驗證

```python
# 批量驗證代理
proxies = [
    {"ip": "8.8.8.8", "port": 8080, "protocol": "http"},
    {"ip": "1.1.1.1", "port": 3128, "protocol": "https"},
    # 更多代理...
]

results = await service.validate_batch(proxies, max_concurrent=5)

# 分析結果
valid_proxies = [r for r in results if r and r.is_valid]
print(f"有效代理: {len(valid_proxies)}/{len(proxies)}")
```

### 自動化調度

```python
# 創建定期驗證任務
job_id = await service.schedule_validation(
    proxies=proxies,
    interval_seconds=300,  # 5分鐘
    job_name="regular_validation"
)

# 獲取任務狀態
status = service.get_job_status(job_id)
print(f"任務狀態: {status}")

# 停止任務
await service.stop_scheduled_job(job_id)
```

## 配置管理

### 使用預設配置

```python
from validators import ValidationConfigManager

config_manager = ValidationConfigManager()

# 獲取預設配置
configs = {
    "default": "預設平衡配置",
    "strict": "�格格驗證配置", 
    "fast": "快速驗證配置",
    "comprehensive": "全面驗證配置"
}

for name, description in configs.items():
    config = await config_manager.get_preset_config(name)
    print(f"{description}: 已加載")
```

### 自定義配置

```python
# 創建自定義配置
custom_config = {
    "scoring_config": {
        "connectivity_weight": 0.4,  # 連接性權重
        "speed_weight": 0.3,        # 速度權重
        "anonymity_weight": 0.2,    # 匿名性權重
        "stability_weight": 0.1       # 穩定性權重
    },
    "speed_config": {
        "timeout": 15,
        "test_url": "https://example.com",
        "max_concurrent": 5
    },
    "anonymity_config": {
        "strict_mode": True,
        "test_urls": ["https://api.ipify.org"]
    }
}

# 保存配置
await config_manager.save_config("my_config", custom_config)

# 使用自定義配置
service = ProxyValidationService(config_name="my_config")
```

## 結果分析

### 驗證結果結構

```python
# ProxyValidationResult 包含以下信息
result = await service.quick_validate(proxy)

print(f"代理信息: {result.proxy_info}")
print(f"綜合評分: {result.overall_score}")
print(f"可用性: {result.is_valid}")
print(f"連接成功率: {result.connectivity_score}")
print(f"響應時間: {result.response_time}ms")
print(f"匿名等級: {result.anonymity_level}")
print(f"地理位置: {result.geolocation}")
print(f"詳細評分: {result.detailed_scores}")
print(f"建議: {result.recommendations}")
print(f"驗證時間: {result.validation_time}")
```

### 統計數據

```python
# 獲取驗證統計
stats = service.get_validation_stats()

print(f"總驗證數: {stats['total_validations']}")
print(f"有效代理: {stats['valid_proxies']}")
print(f"成功率: {stats['success_rate']:.1%}")
print(f"平均評分: {stats['average_score']:.1f}")
```

## 高級功能

### 使用特定驗證組件

```python
from validators import (
    ProxyValidator,
    IPScoringEngine, 
    GeolocationValidator,
    SpeedTester,
    AnonymityTester
)

# 單獨使用驗證組件
validator = ProxyValidator()
scoring_engine = IPScoringEngine()
speed_tester = SpeedTester()

# 執行特定測試
is_valid = await validator.validate_proxy(proxy)
speed_result = await speed_tester.test_speed(proxy)
score = scoring_engine.calculate_score(test_results)
```

### 自動化管理

```python
from validators import AutomatedValidationManager

# 創建自動化管理器
manager = AutomatedValidationManager()

# 添加驗證任務
job = await manager.add_validation_job(
    proxies=proxies,
    priority=1,
    config_name="strict"
)

# 獲取任務狀態
status = await manager.get_job_status(job.id)
results = await manager.get_job_results(job.id)
```

## 測試和演示

### 快速測試

```bash
# 運行快速測試
python test_validation.py
```

### 完整演示

```bash
# 運行完整演示
python demo_validation_system.py
```

## 性能優化建議

### 1. 並發控制
- 根據網絡環境調整 `max_concurrent` 參數
- 建議值：5-20 個並發連接

### 2. 超時設置
- 根據代理質量調整超時時間
- 建議值：10-30 秒

### 3. 緩存策略
- 啟用結果緩存避免重複驗證
- 設置合理的緩存過期時間

### 4. 配置優化
- 根據使用場景選擇合適的配置
- 平衡驗證精度和速度需求

## 錯誤處理

### 常見問題

1. **連接超時**: 增加超時時間或檢查網絡
2. **驗證失敗**: 檢查代理格式和協議支持
3. **評分異常**: 檢查配置權重設置

### 調試模式

```python
import logging

# 啟用調試日誌
logging.basicConfig(level=logging.DEBUG)

# 運行驗證
result = await service.quick_validate(proxy)
```

## 更新日誌

### v1.0.0
- 基礎驗證功能
- 多維度評分系統
- 自動化調度
- 配置管理

## 貢獻指南

歡迎提交 Issue 和 Pull Request 來改進這個代理驗證系統。

## 許可證

MIT License - 詳見 LICENSE 文件