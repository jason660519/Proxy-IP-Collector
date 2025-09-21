"""
測試運行中的服務器功能
"""
import requests
import json
from datetime import datetime

def test_api_endpoints():
    """測試API端點"""
    base_url = "http://localhost:8001"
    
    print("🧪 開始測試運行中的服務器...")
    print(f"⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 測試健康檢查
    print("\n1️⃣ 測試健康檢查端點...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康檢查通過: {data['status']}")
        else:
            print(f"❌ 健康檢查失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 健康檢查異常: {e}")
    
    # 測試爬取器列表
    print("\n2️⃣ 測試爬取器列表端點...")
    try:
        response = requests.get(f"{base_url}/api/v1/extract/extractors", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 爬取器列表獲取成功: {data['count']} 個爬取器")
            print(f"📋 可用爬取器: {', '.join(data['extractors'][:5])}...")
        else:
            print(f"❌ 爬取器列表獲取失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 爬取器列表異常: {e}")
    
    # 測試單個爬取器
    print("\n3️⃣ 測試單個爬取器端點...")
    try:
        payload = {"limit": 5, "test_mode": True}
        response = requests.post(
            f"{base_url}/api/v1/extract/89ip.cn", 
            json=payload, 
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 單個爬取器測試成功: {data['count']} 個代理")
            print(f"🔍 爬取器: {data['extractor']}")
            print(f"⏱️ 耗時: {data['duration']}秒")
        else:
            print(f"❌ 單個爬取器測試失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 單個爬取器異常: {e}")
    
    # 測試所有爬取器
    print("\n4️⃣ 測試所有爬取器端點...")
    try:
        payload = {"limit": 3}
        response = requests.post(
            f"{base_url}/api/v1/extract/all", 
            json=payload, 
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 所有爬取器測試成功: 總共 {data['total_proxies']} 個代理")
            print(f"📊 爬取器結果:")
            for name, result in data['results'].items():
                print(f"   • {name}: {result['count']} 個代理")
        else:
            print(f"❌ 所有爬取器測試失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 所有爬取器異常: {e}")
    
    # 測試前端頁面
    print("\n5️⃣ 測試前端頁面...")
    try:
        response = requests.get(f"{base_url}/frontend/extractors_showcase.html", timeout=5)
        if response.status_code == 200:
            print("✅ 前端頁面可訪問")
            print(f"📄 頁面大小: {len(response.text)} 字符")
        else:
            print(f"❌ 前端頁面訪問失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 前端頁面異常: {e}")
    
    print("\n" + "="*60)
    print("🎉 測試完成！")
    print("\n📖 可用鏈接:")
    print(f"   • API 文檔: {base_url}/docs")
    print(f"   • 前端頁面: {base_url}/frontend/extractors_showcase.html")
    print(f"   • 健康檢查: {base_url}/health")

if __name__ == "__main__":
    test_api_endpoints()
