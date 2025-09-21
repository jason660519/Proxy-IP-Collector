#!/usr/bin/env python3
"""
代理IP連通性和穩定性驗證器
"""
import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os

# 添加後端目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.logging import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class ProxyValidator:
    """代理驗證器"""
    
    def __init__(self):
        self.session = None
        self.test_urls = [
            "http://httpbin.org/ip",
            "https://httpbin.org/ip", 
            "http://icanhazip.com",
            "https://icanhazip.com"
        ]
        
    async def __aenter__(self):
        """異步上下文管理器進入"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=10, connect=5)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    async def validate_proxy(self, ip: str, port: int, protocol: str = "http") -> Dict[str, Any]:
        """
        驗證單個代理
        
        Args:
            ip: 代理IP地址
            port: 代理端口
            protocol: 代理協議 (http/socks4/socks5)
            
        Returns:
            Dict[str, Any]: 驗證結果
        """
        proxy_url = f"{protocol}://{ip}:{port}"
        
        result = {
            "ip": ip,
            "port": port,
            "protocol": protocol,
            "proxy_url": proxy_url,
            "is_valid": False,
            "response_time": None,
            "error": None,
            "test_url": None,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 構建代理連接器
            if protocol == "http":
                connector = aiohttp.ProxyConnector.from_url(proxy_url)
            else:
                # 對於SOCKS代理，需要額外的庫支持
                result["error"] = f"不支持的協議: {protocol}"
                return result
            
            # 測試代理連接
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=10, connect=5)
            ) as test_session:
                
                for test_url in self.test_urls:
                    try:
                        start_time = time.time()
                        async with test_session.get(test_url) as response:
                            end_time = time.time()
                            response_time = (end_time - start_time) * 1000
                            
                            if response.status == 200:
                                result.update({
                                    "is_valid": True,
                                    "response_time": round(response_time, 2),
                                    "test_url": test_url,
                                    "status_code": response.status
                                })
                                break
                                
                    except Exception as e:
                        continue
                
                if not result["is_valid"]:
                    result["error"] = "所有測試URL都失敗"
                    
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    async def validate_proxy_list(self, proxies: List[Dict[str, Any]], max_concurrent: int = 10) -> List[Dict[str, Any]]:
        """
        批量驗證代理列表
        
        Args:
            proxies: 代理列表
            max_concurrent: 最大併發數
            
        Returns:
            List[Dict[str, Any]]: 驗證結果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []
        
        async def validate_with_semaphore(proxy_data):
            async with semaphore:
                return await self.validate_proxy(
                    proxy_data["ip"],
                    proxy_data["port"],
                    proxy_data.get("protocol", "http")
                )
        
        # 創建驗證任務
        tasks = [validate_with_semaphore(proxy) for proxy in proxies]
        
        # 執行驗證
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理異常結果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "ip": proxies[i]["ip"],
                    "port": proxies[i]["port"],
                    "protocol": proxies[i].get("protocol", "http"),
                    "is_valid": False,
                    "error": str(result),
                    "timestamp": datetime.now().isoformat()
                })
            else:
                processed_results.append(result)
        
        return processed_results


class MockProxyValidator:
    """模擬代理驗證器（用於測試）"""
    
    def __init__(self):
        self.test_results = []
        
    async def validate_proxy(self, ip: str, port: int, protocol: str = "http") -> Dict[str, Any]:
        """模擬代理驗證"""
        import random
        
        # 模擬網絡延遲
        await asyncio.sleep(random.uniform(0.1, 2.0))
        
        # 模擬驗證結果（80%成功率）
        is_valid = random.random() > 0.2
        response_time = random.uniform(50, 2000) if is_valid else None
        
        result = {
            "ip": ip,
            "port": port,
            "protocol": protocol,
            "is_valid": is_valid,
            "response_time": round(response_time, 2) if response_time else None,
            "error": None if is_valid else "連接超時",
            "test_url": "http://httpbin.org/ip",
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        return result
    
    async def validate_proxy_list(self, proxies: List[Dict[str, Any]], max_concurrent: int = 10) -> List[Dict[str, Any]]:
        """批量模擬代理驗證"""
        results = []
        
        for proxy in proxies:
            result = await self.validate_proxy(
                proxy["ip"],
                proxy["port"],
                proxy.get("protocol", "http")
            )
            results.append(result)
        
        return results


async def test_proxy_validation():
    """測試代理驗證功能"""
    print("🔍 開始代理IP連通性和穩定性測試...")
    
    # 模擬代理數據
    mock_proxies = [
        {"ip": "127.0.0.1", "port": 8080, "protocol": "http"},
        {"ip": "192.168.1.1", "port": 3128, "protocol": "http"},
        {"ip": "10.0.0.1", "port": 1080, "protocol": "socks5"},
        {"ip": "172.16.0.1", "port": 8080, "protocol": "http"},
        {"ip": "203.0.113.1", "port": 3128, "protocol": "http"},
    ]
    
    print(f"📊 測試 {len(mock_proxies)} 個模擬代理...")
    
    # 使用模擬驗證器進行測試
    validator = MockProxyValidator()
    results = await validator.validate_proxy_list(mock_proxies, max_concurrent=5)
    
    # 分析結果
    valid_proxies = [r for r in results if r["is_valid"]]
    invalid_proxies = [r for r in results if not r["is_valid"]]
    
    print(f"\n📈 驗證結果:")
    print(f"總數: {len(results)}")
    print(f"有效: {len(valid_proxies)} ({len(valid_proxies)/len(results)*100:.1f}%)")
    print(f"無效: {len(invalid_proxies)} ({len(invalid_proxies)/len(results)*100:.1f}%)")
    
    if valid_proxies:
        avg_response_time = sum(r["response_time"] for r in valid_proxies if r["response_time"]) / len(valid_proxies)
        print(f"平均響應時間: {avg_response_time:.2f}ms")
        
        print(f"\n✅ 有效代理:")
        for proxy in valid_proxies:
            print(f"   {proxy['ip']}:{proxy['port']} ({proxy['protocol']}) - {proxy['response_time']}ms")
    
    if invalid_proxies:
        print(f"\n❌ 無效代理:")
        for proxy in invalid_proxies:
            print(f"   {proxy['ip']}:{proxy['port']} ({proxy['protocol']}) - {proxy.get('error', 'Unknown error')}")
    
    # 生成報告
    report_data = {
        "test_timestamp": datetime.now().isoformat(),
        "total_proxies": len(results),
        "valid_proxies": len(valid_proxies),
        "invalid_proxies": len(invalid_proxies),
        "success_rate": len(valid_proxies)/len(results)*100,
        "average_response_time": avg_response_time if valid_proxies else None,
        "results": results
    }
    
    with open("proxy_validation_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 詳細報告已保存到: proxy_validation_report.json")


def create_proxy_test_data():
    """創建代理測試數據"""
    print("📝 創建代理測試數據...")
    
    # 從URL測試報告中讀取可用的來源
    try:
        with open("url_test_report.json", "r", encoding="utf-8") as f:
            url_report = json.load(f)
        
        working_sources = url_report["summary"]["working_sources"]
        print(f"✅ 找到 {len(working_sources)} 個可用的代理來源")
        
        # 為每個來源創建模擬代理數據
        test_proxies = []
        for i, source in enumerate(working_sources):
            # 為每個來源創建幾個模擬代理
            for j in range(3):
                proxy = {
                    "ip": f"203.{i}.{j}.100",
                    "port": 8080 + j,
                    "protocol": "http",
                    "source": source,
                    "country": "US",
                    "anonymity_level": "anonymous"
                }
                test_proxies.append(proxy)
        
        # 保存測試數據
        with open("test_proxy_data.json", "w", encoding="utf-8") as f:
            json.dump(test_proxies, f, ensure_ascii=False, indent=2)
        
        print(f"📄 創建了 {len(test_proxies)} 個測試代理數據，保存到: test_proxy_data.json")
        return test_proxies
        
    except FileNotFoundError:
        print("❌ 未找到URL測試報告，創建默認測試數據")
        
        # 創建默認測試數據
        test_proxies = [
            {"ip": "127.0.0.1", "port": 8080, "protocol": "http", "source": "test", "country": "US"},
            {"ip": "192.168.1.1", "port": 3128, "protocol": "http", "source": "test", "country": "CN"},
            {"ip": "10.0.0.1", "port": 1080, "protocol": "socks5", "source": "test", "country": "JP"},
        ]
        
        with open("test_proxy_data.json", "w", encoding="utf-8") as f:
            json.dump(test_proxies, f, ensure_ascii=False, indent=2)
        
        print(f"📄 創建了 {len(test_proxies)} 個默認測試代理數據")
        return test_proxies


async def main():
    """主函數"""
    print("🚀 開始代理IP驗證測試...")
    
    # 創建測試數據
    test_proxies = create_proxy_test_data()
    
    # 執行驗證測試
    await test_proxy_validation()
    
    print("\n✅ 代理驗證測試完成！")


if __name__ == "__main__":
    asyncio.run(main())
