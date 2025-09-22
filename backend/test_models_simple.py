#!/usr/bin/env python3
"""
簡單模型測試腳本
測試代理模型的導入和基本功能
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    # 測試導入模型
    print("正在測試模型導入...")
    from app.models.proxy import Proxy, ProxySource, ProxyCheckResult, ProxyCrawlLog, ETLTask
    print("✅ 模型導入成功")
    
    # 測試UUID類型
    print("\n正在檢查UUID類型...")
    print(f"Proxy.id類型: {type(Proxy.__table__.columns.id.type)}")
    print(f"ProxySource.id類型: {type(ProxySource.__table__.columns.id.type)}")
    print(f"ProxyCheckResult.id類型: {type(ProxyCheckResult.__table__.columns.id.type)}")
    print(f"ProxyCrawlLog.id類型: {type(ProxyCrawlLog.__table__.columns.id.type)}")
    print(f"ETLTask.id類型: {type(ETLTask.__table__.columns.id.type)}")
    
    # 測試創建模型實例
    print("\n正在測試模型實例化...")
    from datetime import datetime
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # 創建SQLite內存數據庫
    engine = create_engine('sqlite:///:memory:')
    
    # 創建所有表
    from app.models.proxy import Base
    Base.metadata.create_all(engine)
    print("✅ 數據庫表創建成功")
    
    # 創建會話
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 測試插入數據
    print("\n正在測試數據插入...")
    proxy = Proxy(
        ip="192.168.1.100",
        port=8080,
        protocol="http",
        status="active",
        source="test"
    )
    session.add(proxy)
    session.commit()
    print(f"✅ 代理插入成功，ID: {proxy.id}")
    
    # 測試查詢
    print("\n正在測試數據查詢...")
    result = session.query(Proxy).first()
    print(f"✅ 查詢成功，找到代理: {result.ip}:{result.port}")
    
    session.close()
    print("\n🎉 所有測試通過！模型兼容性問題已解決")
    
except Exception as e:
    print(f"❌ 測試失敗: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)