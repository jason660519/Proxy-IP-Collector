"""
詳細API端點測試腳本
獲取具體的錯誤信息
"""

import requests
import json
import traceback
from datetime import datetime

def test_endpoints_detailed():
    """詳細測試所有API端點"""
    base_url = "http://localhost:8000/api/v1"
    
    print(f"開始詳細測試API端點... {datetime.now()}")
    print("=" * 50)
    
    endpoints = [
        ("代理列表", f"{base_url}/proxies/list"),
        ("代理統計", f"{base_url}/proxies/stats"),
        ("爬取歷史", f"{base_url}/crawl/history"),
        ("系統配置", f"{base_url}/system/config")
    ]
    
    for name, url in endpoints:
        print(f"\n🔍 測試 {name} 端點:")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, timeout=15)
            print(f"狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ 成功: {json.dumps(data, ensure_ascii=False, indent=2)[:200]}...")
                except json.JSONDecodeError:
                    print(f"✅ 成功 (非JSON響應): {response.text[:100]}...")
            else:
                print(f"❌ 失敗: {response.text}")
                
                # 嘗試解析錯誤詳情
                try:
                    error_data = response.json()
                    if 'detail' in error_data:
                        print(f"錯誤詳情: {error_data['detail']}")
                except:
                    pass
                    
        except requests.exceptions.Timeout:
            print(f"⏰ 超時錯誤: 請求超時 (15秒)")
        except requests.exceptions.ConnectionError as e:
            print(f"🔗 連接錯誤: 無法連接到服務")
            print(f"錯誤信息: {str(e)}")
        except Exception as e:
            print(f"💥 意外錯誤: {str(e)}")
            print(f"堆棧跟踪: {traceback.format_exc()}")
        
        print("-" * 30)
    
    print("\n📊 測試完成！")

if __name__ == "__main__":
    test_endpoints_detailed()