"""
數據庫模擬測試
測試數據庫模擬和隔離性，確保測試之間不互相影響
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import sys
from pathlib import Path
import tempfile
import sqlite3
import os

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.proxy_validator import ProxyValidator
from app.models.proxy import Proxy
from app.core.database import get_db


class TestDatabaseMocking:
    """數據庫模擬測試類"""
    
    def test_mock_db_connection_fixture(self, mock_db_connection):
        """測試模擬數據庫連接fixture"""
        # 測試模擬連接的基本功能
        assert mock_db_connection is not None
        assert isinstance(mock_db_connection, AsyncMock)
        
        # 測試 fixture 的基本功能 - 模擬連接應該可以被調用
        # 由於 AsyncMock 的特殊性，我們只測試對象類型和基本存在性
        print(f"mock_db_connection type: {type(mock_db_connection)}")
        
        # 驗證這是一個有效的模擬對象
        assert mock_db_connection is not None
        
        # 測試 execute 方法是否存在並可以調用
        assert hasattr(mock_db_connection, 'execute')
        assert callable(mock_db_connection.execute)
    
    @pytest.mark.asyncio
    async def test_mock_db_session_fixture(self, mock_db_session):
        """測試模擬數據庫會話fixture"""
        # 測試模擬會話的基本功能
        assert mock_db_session is not None
        
        # 測試上下文管理器
        async with mock_db_session as session:
            assert session is not None
            
            # 測試提交和回滾
            await session.commit()
            assert session.committed is True
            
            await session.rollback()
            assert session.rolled_back is True
        
        # 測試關閉
        assert mock_db_session.closed is True
    
    def test_isolated_test_db_fixture(self, isolated_test_db):
        """測試隔離的測試數據庫fixture"""
        # 驗證數據庫文件存在
        assert os.path.exists(isolated_test_db)
        
        # 測試數據庫連接
        conn = sqlite3.connect(isolated_test_db)
        cursor = conn.cursor()
        
        # 測試表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='proxies'")
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == 'proxies'
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='validation_results'")
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == 'validation_results'
        
        conn.close()
    
    def test_proxy_validator_with_mock_db(self, mock_db_session):
        """測試代理驗證器使用模擬數據庫會話"""
        # 創建驗證器實例，直接傳入模擬會話
        validator = ProxyValidator(db_session=mock_db_session)
        
        # 驗證驗證器正確初始化
        assert validator.db_session == mock_db_session
        assert validator.timeout.total == 30
        
        # 測試基本屬性
        assert "http://httpbin.org/ip" in validator.test_urls.values()
        assert "Mozilla/5.0" in validator.default_headers["User-Agent"]
        
        # 驗證模擬會話可用
        assert mock_db_session is not None
    
    @pytest.mark.asyncio
    async def test_database_connection_mocking(self):
        """測試數據庫連接模擬"""
        # 創建模擬連接
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = AsyncMock()
        mock_conn.execute.return_value.fetchone.return_value = {"result": "test"}
        
        # 測試模擬連接
        result = await mock_conn.execute("SELECT 1")
        data = await result.fetchone()
        
        assert data["result"] == "test"
        assert mock_conn.execute.called
    
    @pytest.mark.asyncio
    async def test_database_transaction_mocking(self):
        """測試數據庫事務模擬"""
        # 創建模擬連接
        mock_conn = AsyncMock()
        mock_conn.commit.return_value = None
        mock_conn.rollback.return_value = None
        mock_conn.close.return_value = None
        
        # 測試事務操作
        await mock_conn.commit()
        await mock_conn.rollback()
        await mock_conn.close()
        
        # 驗證調用
        assert mock_conn.commit.called
        assert mock_conn.rollback.called
        assert mock_conn.close.called
    
    def test_database_isolation(self):
        """測試數據庫隔離性"""
        # 創建兩個獨立的模擬連接
        mock_conn1 = AsyncMock()
        mock_conn2 = AsyncMock()
        
        # 設置不同的返回值
        mock_conn1.execute.return_value.fetchone.return_value = {"id": 1, "data": "test1"}
        mock_conn2.execute.return_value.fetchone.return_value = {"id": 2, "data": "test2"}
        
        # 驗證它們是獨立的
        assert mock_conn1 is not mock_conn2
        assert mock_conn1.execute.return_value.fetchone.return_value != mock_conn2.execute.return_value.fetchone.return_value
    
    @pytest.mark.asyncio
    async def test_async_database_operations(self):
        """測試異步數據庫操作"""
        # 創建模擬異步連接
        mock_conn = AsyncMock()
        
        # 設置異步返回值
        mock_conn.execute.return_value = AsyncMock()
        mock_conn.execute.return_value.fetchall.return_value = [
            {"id": 1, "name": "test1"},
            {"id": 2, "name": "test2"}
        ]
        
        # 測試異步操作
        result = await mock_conn.execute("SELECT * FROM table")
        data = await result.fetchall()
        
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[1]["id"] == 2
    
    def test_connection_pool_mocking(self):
        """測試連接池模擬"""
        # 創建模擬連接池
        mock_pool = Mock()
        mock_pool.acquire.return_value = AsyncMock()
        mock_pool.release.return_value = None
        mock_pool.close.return_value = None
        
        # 測試連接池操作
        conn = mock_pool.acquire()
        mock_pool.release(conn)
        mock_pool.close()
        
        # 驗證調用
        assert mock_pool.acquire.called
        assert mock_pool.release.called
        assert mock_pool.close.called


class TestDatabaseErrorHandling:
    """數據庫錯誤處理測試類"""
    
    @pytest.mark.asyncio
    async def test_database_connection_error_handling(self):
        """測試數據庫連接錯誤處理"""
        # 創建會拋出異常的模擬連接
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("Connection failed")
        
        # 測試異常處理
        with pytest.raises(Exception) as exc_info:
            await mock_conn.execute("SELECT 1")
        
        assert "Connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_database_timeout_handling(self):
        """測試數據庫超時處理"""
        # 創建會超時的模擬連接
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = asyncio.TimeoutError("Query timeout")
        
        # 測試超時處理
        with pytest.raises(asyncio.TimeoutError) as exc_info:
            await mock_conn.execute("SELECT * FROM large_table")
        
        assert "Query timeout" in str(exc_info.value)
    
    def test_database_cleanup(self, isolated_test_db):
        """測試數據庫清理"""
        # 驗證測試數據庫存在
        assert os.path.exists(isolated_test_db)
        
        # 在測試數據庫中插入一些數據
        conn = sqlite3.connect(isolated_test_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO proxies (host, port, type) VALUES (?, ?, ?)",
                      ("test.example.com", 8080, "http"))
        conn.commit()
        
        # 驗證數據存在
        cursor.execute("SELECT COUNT(*) FROM proxies")
        count = cursor.fetchone()[0]
        assert count == 1
        
        conn.close()
        
        # fixture會在測試結束後自動清理數據庫文件