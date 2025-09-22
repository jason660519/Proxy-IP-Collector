import socket
import urllib.request
import json

def check_service():
    """檢查服務是否正常運行"""
    try:
        # 檢查端口是否監聽
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        
        if result != 0:
            print("❌ 端口8000未監聽")
            return False
            
        print("✅ 端口8000正在監聽")
        
        # 嘗試訪問系統配置端點（通常最簡單）
        try:
            with urllib.request.urlopen('http://localhost:8000/api/v1/system/config', timeout=5) as response:
                data = json.loads(response.read().decode())
                print(f"✅ 系統配置端點正常: {data}")
        except Exception as e:
            print(f"❌ 系統配置端點失敗: {e}")
            
        # 嘗試訪問代理統計端點
        try:
            with urllib.request.urlopen('http://localhost:8000/api/v1/proxies/stats', timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    print(f"✅ 代理統計端點正常: 總數 {data.get('total_count', 0)}")
                else:
                    print(f"❌ 代理統計端點返回狀態碼: {response.status}")
        except Exception as e:
            print(f"❌ 代理統計端點失敗: {e}")
            
        return True
        
    except Exception as e:
        print(f"💥 檢查過程中出錯: {e}")
        return False

if __name__ == "__main__":
    check_service()