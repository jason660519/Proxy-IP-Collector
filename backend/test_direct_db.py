"""
直接數據庫測試，繞過API層
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.proxy import Proxy
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from datetime import datetime

async def test_database_queries():
    """測試數據庫查詢"""
    print("開始測試數據庫查詢...")
    
    try:
        async for db in get_db():
            # 測試簡單計數
            print("1. 測試總數量查詢...")
            total_query = select(func.count()).select_from(Proxy)
            total_result = await db.execute(total_query)
            total_count = total_result.scalar() or 0
            print(f"   總數量: {total_count}")
            
            # 測試活動代理計數
            print("2. 測試活動代理計數...")
            active_query = select(func.count()).select_from(Proxy).where(Proxy.is_active == True)
            active_result = await db.execute(active_query)
            active_count = active_result.scalar() or 0
            print(f"   活動代理: {active_count}")
            
            # 測試分組查詢（可能是最慢的）
            print("3. 測試協議分組統計...")
            try:
                protocol_query = select(Proxy.protocol, func.count()).group_by(Proxy.protocol)
                protocol_result = await db.execute(protocol_query)
                protocol_stats = {}
                for protocol, count in protocol_result:
                    if protocol and protocol != "None" and str(protocol).strip():
                        protocol_stats[str(protocol).strip()] = int(count or 0)
                print(f"   協議統計: {protocol_stats}")
            except Exception as e:
                print(f"   協議統計失敗: {e}")
                
            # 測試最後更新時間
            print("4. 測試最後更新時間...")
            try:
                last_updated_query = select(func.max(Proxy.updated_at))
                last_updated_result = await db.execute(last_updated_query)
                last_updated = last_updated_result.scalar() or datetime.utcnow()
                print(f"   最後更新: {last_updated}")
            except Exception as e:
                print(f"   最後更新時間失敗: {e}")
                
            print("✅ 數據庫查詢測試完成！")
            
    except Exception as e:
        print(f"❌ 數據庫測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database_queries())