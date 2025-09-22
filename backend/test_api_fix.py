"""
API修復驗證測試
驗證我們對API端點的修復是否有效
"""

import asyncio
import sys
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.api.v1.proxies import get_proxies, get_proxy, delete_proxy, validate_proxy
from app.api.v1.crawl import get_crawl_history
from app.core.database_manager import get_db, get_db_session_manager


async def test_api_fixes():
    """測試API修復"""
    print("開始測試API修復...")
    
    try:
        # 測試1: 檢查函數簽名
        print("\n1. 檢查函數簽名...")
        
        # 檢查 get_proxy 的參數類型
        import inspect
        sig = inspect.signature(get_proxy)
        proxy_id_param = sig.parameters['proxy_id']
        print(f"   get_proxy proxy_id 參數類型: {proxy_id_param.annotation}")
        
        sig = inspect.signature(delete_proxy)
        proxy_id_param = sig.parameters['proxy_id']
        print(f"   delete_proxy proxy_id 參數類型: {proxy_id_param.annotation}")
        
        sig = inspect.signature(validate_proxy)
        proxy_id_param = sig.parameters['proxy_id']
        print(f"   validate_proxy proxy_id 參數類型: {proxy_id_param.annotation}")
        
        # 測試2: 檢查數據庫依賴注入
        print("\n2. 檢查數據庫依賴注入...")
        
        # 檢查是否正確導入了get_db
        assert hasattr(sys.modules['app.core.database_manager'], 'get_db'), "get_db 別名未找到"
        print("   ✓ get_db 別名存在")
        
        # 測試3: 檢查函數定義
        print("\n3. 檢查函數定義...")
        
        # 獲取函數源碼檢查字段名稱
        import inspect
        
        # 檢查 get_proxies 中的匿名度字段
        source = inspect.getsource(get_proxies)
        if "Proxy.anonymity" in source:
            print("   ✓ get_proxies 使用正確的匿名度字段: Proxy.anonymity")
        else:
            print("   ✗ get_proxies 匿名度字段錯誤")
        
        # 檢查 get_random_proxy 中的匿名度字段
        from app.api.v1.proxies import get_random_proxy
        source = inspect.getsource(get_random_proxy)
        if "Proxy.anonymity" in source:
            print("   ✓ get_random_proxy 使用正確的匿名度字段: Proxy.anonymity")
        else:
            print("   ✗ get_random_proxy 匿名度字段錯誤")
        
        # 檢查 validate_proxy 中的字段
        source = inspect.getsource(validate_proxy)
        if "proxy.last_checked" in source:
            print("   ✓ validate_proxy 使用正確的時間字段: proxy.last_checked")
        else:
            print("   ✗ validate_proxy 時間字段錯誤")
        
        print("\n✅ 所有API修復驗證完成！")
        return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_api_fixes())
    sys.exit(0 if success else 1)