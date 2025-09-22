import pytest
import asyncio
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 測試配置
TEST_TIMEOUT = 30  # 測試超時時間（秒）
MAX_ASYNCIO_WORKERS = 4  # 最大異步工作線程數

# 測試數據庫配置
TEST_DB_PATH = ":memory:"  # 使用內存數據庫進行測試
TEST_DB_ECHO = False  # 是否輸出 SQL 語句

# 測試覆蓋率配置
COVERAGE_MIN_PERCENTAGE = 80  # 最小覆蓋率百分比
COVERAGE_EXCLUDE_LINES = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]

# 測試分類配置
TEST_CATEGORIES = {
    "unit": "單元測試",
    "integration": "集成測試", 
    "database": "數據庫測試",
    "network": "網絡測試",
    "performance": "性能測試"
}

# 測試重試配置
TEST_RETRY_ATTEMPTS = 3  # 測試失敗重試次數
TEST_RETRY_DELAY = 1  # 重試延遲（秒）

# 日誌配置
TEST_LOG_LEVEL = "INFO"  # 測試日誌級別
TEST_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def pytest_configure(config):
    """pytest 配置鉤子"""
    # 註冊自定義標記
    for marker_name, marker_desc in TEST_CATEGORIES.items():
        config.addinivalue_line(
            "markers", f"{marker_name}: {marker_desc}"
        )
    
    # 設置異步測試模式
    config.option.asyncio_mode = "auto"

def pytest_collection_modifyitems(config, items):
    """修改測試項目集合"""
    for item in items:
        # 根據測試文件路徑自動添加標記
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "database" in str(item.fspath):
            item.add_marker(pytest.mark.database)
        elif "network" in str(item.fspath):
            item.add_marker(pytest.mark.network)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        
        # 為異步測試添加標記
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)

@pytest.fixture(scope="session")
def event_loop():
    """創建會話級別的事件循環"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def setup_test_environment():
    """設置測試環境"""
    # 設置測試超時
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError(f"測試超時（超過 {TEST_TIMEOUT} 秒）")
    
    # 設置信號處理器（僅在 Unix 系統上）
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(TEST_TIMEOUT)
    
    yield
    
    # 清理
    if hasattr(signal, 'SIGALRM'):
        signal.alarm(0)  # 取消超時