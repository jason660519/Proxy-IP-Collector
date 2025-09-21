#!/usr/bin/env python3
"""
代理驗證系統簡化測試腳本

這個腳本提供不依賴數據庫模型的基本功能測試
"""

import asyncio
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

# 添加路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class SimpleProxy:
    """簡化的代理數據類"""
    ip: str
    port: int
    protocol: str = "http"
    country: str = "Unknown"
    username: Optional[str] = None
    password: Optional[str] = None
    score: float = 0.0
    is_active: bool = False
    anonymity_level: str = "unknown"
    response_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'ip': self.ip,
            'port': self.port,
            'protocol': self.protocol,
            'country': self.country,
            'score': self.score,
            'is_active': self.is_active,
            'anonymity_level': self.anonymity_level,
            'response_time': self.response_time
        }


# 導入驗證組件（使用簡化版本）
from ip_scoring_engine import IPScoringEngine
from geolocation_validator import GeolocationValidator
from speed_tester import SpeedTester
from anonymity_tester import AnonymityTester


async def test_ip_scoring_engine():
    """測試IP評分引擎"""
    print("=== 測試IP評分引擎 ===")
    
    try:
        engine = IPScoringEngine()
        
        # 測試數據
        test_data = {
            'connection': {'success': True, 'response_time': 1.5},
            'anonymity': {'level': 'elite', 'score': 90},
            'geolocation': {'risk_score': 10},
            'speed': {'download_speed': 500, 'stability_score': 85},
            'response_time': 1.5
        }
        
        score = await engine.calculate_score(test_data)
        print(f"✓ 評分計算成功: {score:.1f}/100")
        
        # 測試配置
        config = engine.get_default_config()
        print(f"✓ 默認配置: {len(config)} 個配置項")
        
        return True
        
    except Exception as e:
        print(f"✗ IP評分引擎測試失敗: {e}")
        return False


async def test_geolocation_validator():
    """測試地理位置驗證器"""
    print("\n=== 測試地理位置驗證器 ===")
    
    try:
        validator = GeolocationValidator()
        
        # 測試代理
        proxy = SimpleProxy(ip="8.8.8.8", port=8080, country="US")
        
        # 測試地理位置驗證（模擬）
        result = await validator.validate_location(proxy)
        print(f"✓ 地理位置驗證完成")
        print(f"  - 真實位置: {result.get('real_location', 'Unknown')}")
        print(f"  - 代理位置: {result.get('proxy_location', 'Unknown')}")
        print(f"  - 風險評分: {result.get('risk_score', 0)}")
        
        return True
        
    except Exception as e:
        print(f"✗ 地理位置驗證器測試失敗: {e}")
        return False


async def test_speed_tester():
    """測試速度測試器"""
    print("\n=== 測試速度測試器 ===")
    
    try:
        tester = SpeedTester()
        
        # 測試代理
        proxy = SimpleProxy(ip="8.8.8.8", port=8080)
        
        # 測試速度（模擬）
        result = await tester.test_speed(proxy)
        print(f"✓ 速度測試完成")
        print(f"  - 連接速度: {result.get('connect_speed', 0):.1f}ms")
        print(f"  - 下載速度: {result.get('download_speed', 0):.1f}KB/s")
        print(f"  - 穩定性評分: {result.get('stability_score', 0):.1f}")
        
        return True
        
    except Exception as e:
        print(f"✗ 速度測試器測試失敗: {e}")
        return False


async def test_anonymity_tester():
    """測試匿名性測試器"""
    print("\n=== 測試匿名性測試器 ===")
    
    try:
        tester = AnonymityTester()
        
        # 測試代理
        proxy = SimpleProxy(ip="8.8.8.8", port=8080)
        
        # 測試匿名性（模擬）
        result = await tester.test_anonymity(proxy)
        print(f"✓ 匿名性測試完成")
        print(f"  - 匿名等級: {result.get('level', 'Unknown')}")
        print(f"  - 匿名評分: {result.get('anonymity_score', 0):.1f}")
        print(f"  - 標頭洩露: {result.get('header_leaks', [])}")
        
        return True
        
    except Exception as e:
        print(f"✗ 匿名性測試器測試失敗: {e}")
        return False


async def test_validation_workflow():
    """測試完整驗證流程"""
    print("\n=== 測試完整驗證流程 ===")
    
    try:
        # 初始化所有組件
        scoring_engine = IPScoringEngine()
        geo_validator = GeolocationValidator()
        speed_tester = SpeedTester()
        anonymity_tester = AnonymityTester()
        
        # 測試代理
        proxy = SimpleProxy(ip="8.8.8.8", port=8080, country="US")
        
        print(f"開始驗證代理: {proxy.ip}:{proxy.port}")
        
        # 1. 地理位置驗證
        print("1. 地理位置驗證...")
        geo_result = await geo_validator.validate_location(proxy)
        
        # 2. 速度測試
        print("2. 速度測試...")
        speed_result = await speed_tester.test_speed(proxy)
        
        # 3. 匿名性測試
        print("3. 匿名性測試...")
        anonymity_result = await anonymity_tester.test_anonymity(proxy)
        
        # 4. 綜合評分
        print("4. 綜合評分...")
        validation_data = {
            'connection': {'success': True, 'response_time': 1.5},
            'anonymity': anonymity_result,
            'geolocation': geo_result,
            'speed': speed_result,
            'response_time': 1.5
        }
        
        final_score = await scoring_engine.calculate_score(validation_data)
        
        # 更新代理信息
        proxy.score = final_score
        proxy.is_active = final_score >= 60
        proxy.anonymity_level = anonymity_result.get('level', 'unknown')
        proxy.response_time = speed_result.get('connect_speed', 0)
        
        print(f"✓ 驗證完成!")
        print(f"  - 最終評分: {final_score:.1f}/100")
        print(f"  - 代理狀態: {'有效' if proxy.is_active else '無效'}")
        print(f"  - 匿名等級: {proxy.anonymity_level}")
        print(f"  - 響應時間: {proxy.response_time:.1f}ms")
        
        return True
        
    except Exception as e:
        print(f"✗ 完整流程測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """運行所有測試"""
    print("代理驗證系統簡化測試")
    print("=" * 50)
    
    test_results = []
    
    # 運行各個測試
    test_results.append(await test_ip_scoring_engine())
    test_results.append(await test_geolocation_validator())
    test_results.append(await test_speed_tester())
    test_results.append(await test_anonymity_tester())
    test_results.append(await test_validation_workflow())
    
    # 總結結果
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 50)
    print(f"測試完成: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！核心組件運行正常")
        return True
    else:
        print("⚠️  部分測試失敗，請檢查錯誤信息")
        return False


if __name__ == "__main__":
    # 運行測試
    success = asyncio.run(run_all_tests())
    
    # 退出碼
    sys.exit(0 if success else 1)