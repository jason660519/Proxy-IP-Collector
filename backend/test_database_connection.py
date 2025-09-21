"""
數據庫連接測試腳本

這個腳本用於測試和診斷數據庫連接問題
"""

import asyncio
import asyncpg
import sqlite3
import aioredis
from pathlib import Path
import sys
import os

# 添加項目根目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.config import settings
except ImportError:
    # 如果無法導入，創建模擬配置
    class MockSettings:
        DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/proxy_collector"
        REDIS_URL = "redis://localhost:6379/0"
    
    settings = MockSettings()


class DatabaseConnectionTester:
    """數據庫連接測試器"""
    
    def __init__(self):
        self.test_results = {}
        self.recommendations = []
    
    async def test_postgresql_connection(self) -> Dict[str, any]:
        """測試PostgreSQL連接"""
        print("🔍 正在測試PostgreSQL連接...")
        
        try:
            # 解析數據庫URL
            db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
            
            # 嘗試連接
            conn = await asyncpg.connect(db_url)
            
            # 測試查詢
            result = await conn.fetchval("SELECT version()")
            await conn.close()
            
            print(f"✅ PostgreSQL連接成功")
            print(f"   版本: {result}")
            
            return {
                "status": "success",
                "message": "PostgreSQL連接正常",
                "version": result,
                "url": db_url.split('@')[1] if '@' in db_url else db_url
            }
            
        except asyncpg.exceptions.CannotConnectNowError:
            print("❌ PostgreSQL服務未運行或拒絕連接")
            return {
                "status": "failed",
                "message": "PostgreSQL服務未運行或拒絕連接",
                "recommendation": "請確保PostgreSQL服務已啟動並接受連接"
            }
            
        except asyncpg.exceptions.InvalidPasswordError:
            print("❌ PostgreSQL認證失敗")
            return {
                "status": "failed",
                "message": "用戶名或密碼錯誤",
                "recommendation": "請檢查數據庫認證配置"
            }
            
        except Exception as e:
            print(f"❌ PostgreSQL連接錯誤: {str(e)}")
            return {
                "status": "failed",
                "message": f"連接錯誤: {str(e)}",
                "recommendation": "請檢查數據庫配置和網絡連接"
            }
    
    async def test_redis_connection(self) -> Dict[str, any]:
        """測試Redis連接"""
        print("🔍 正在測試Redis連接...")
        
        try:
            redis = aioredis.from_url(settings.REDIS_URL)
            
            # 測試連接
            await redis.ping()
            
            # 測試基本操作
            await redis.set("test_key", "test_value", ex=60)
            value = await redis.get("test_key")
            await redis.delete("test_key")
            
            await redis.close()
            
            print(f"✅ Redis連接成功")
            print(f"   測試值: {value.decode()}")
            
            return {
                "status": "success",
                "message": "Redis連接正常",
                "test_value": value.decode(),
                "url": settings.REDIS_URL
            }
            
        except Exception as e:
            print(f"❌ Redis連接錯誤: {str(e)}")
            return {
                "status": "failed",
                "message": f"連接錯誤: {str(e)}",
                "recommendation": "請確保Redis服務已啟動"
            }
    
    def test_sqlite_fallback(self) -> Dict[str, any]:
        """測試SQLite後備方案"""
        print("🔍 正在測試SQLite後備方案...")
        
        try:
            # 創建數據目錄
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            # 測試SQLite連接
            db_path = data_dir / "proxy_collector.db"
            conn = sqlite3.connect(db_path)
            
            # 測試查詢
            result = conn.execute("SELECT sqlite_version()").fetchone()
            conn.close()
            
            print(f"✅ SQLite後備方案可用")
            print(f"   版本: {result[0]}")
            print(f"   數據庫文件: {db_path}")
            
            return {
                "status": "success",
                "message": "SQLite後備方案可用",
                "version": result[0],
                "database_path": str(db_path)
            }
            
        except Exception as e:
            print(f"❌ SQLite測試失敗: {str(e)}")
            return {
                "status": "failed",
                "message": f"SQLite測試失敗: {str(e)}"
            }
    
    def generate_recommendations(self, results: Dict[str, any]) -> List[str]:
        """生成改進建議"""
        recommendations = []
        
        # PostgreSQL建議
        if results.get("postgresql", {}).get("status") == "failed":
            recommendations.append("📝 PostgreSQL改進建議：")
            recommendations.append("  1. 安裝PostgreSQL：下載並安裝PostgreSQL服務器")
            recommendations.append("  2. 創建數據庫：執行 `CREATE DATABASE proxy_collector;`")
            recommendations.append("  3. 創建用戶：執行 `CREATE USER postgres WITH PASSWORD 'password';`")
            recommendations.append("  4. 授權：執行 `GRANT ALL PRIVILEGES ON DATABASE proxy_collector TO postgres;`")
            recommendations.append("  5. 修改配置：更新pg_hba.conf允許本地連接")
        
        # Redis建議
        if results.get("redis", {}).get("status") == "failed":
            recommendations.append("\n📝 Redis改進建議：")
            recommendations.append("  1. 安裝Redis：下載並安裝Redis服務器")
            recommendations.append("  2. 啟動服務：運行 `redis-server`")
            recommendations.append("  3. 測試連接：使用 `redis-cli ping` 測試")
        
        # 通用建議
        recommendations.append("\n🔧 通用建議：")
        recommendations.append("  1. 環境變量：創建 .env 文件並配置正確的連接參數")
        recommendations.append("  2. 網絡連接：確保數據庫服務器可訪問")
        recommendations.append("  3. 防火牆：檢查防火牆設置是否阻止連接")
        
        return recommendations
    
    async def run_full_diagnostic(self) -> Dict[str, any]:
        """運行完整診斷"""
        print("🚀 開始數據庫連接診斷...")
        print("=" * 50)
        
        # 測試PostgreSQL
        pg_result = await self.test_postgresql_connection()
        self.test_results["postgresql"] = pg_result
        
        # 測試Redis
        redis_result = await self.test_redis_connection()
        self.test_results["redis"] = redis_result
        
        # 測試SQLite後備方案
        sqlite_result = self.test_sqlite_fallback()
        self.test_results["sqlite"] = sqlite_result
        
        # 生成建議
        self.recommendations = self.generate_recommendations(self.test_results)
        
        # 生成總結報告
        report = {
            "timestamp": "2024-01-20T10:30:00Z",
            "summary": {
                "total_tests": 3,
                "passed": sum(1 for r in self.test_results.values() if r.get("status") == "success"),
                "failed": sum(1 for r in self.test_results.values() if r.get("status") == "failed")
            },
            "results": self.test_results,
            "recommendations": self.recommendations,
            "next_steps": [
                "根據測試結果配置數據庫連接",
                "更新 .env 文件中的連接參數",
                "重新運行測試以驗證配置"
            ]
        }
        
        print("\n" + "=" * 50)
        print("📊 診斷完成！")
        print(f"通過測試：{report['summary']['passed']}/{report['summary']['total_tests']}")
        
        if self.recommendations:
            print("\n" + "\n".join(self.recommendations))
        
        return report


async def main():
    """主函數"""
    tester = DatabaseConnectionTester()
    
    try:
        report = await tester.run_full_diagnostic()
        
        # 保存報告
        with open("database_diagnostic_report.json", "w", encoding="utf-8") as f:
            import json
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 詳細報告已保存到：database_diagnostic_report.json")
        
    except KeyboardInterrupt:
        print("\n⚠️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中出現錯誤: {str(e)}")


if __name__ == "__main__":
    # 確保在Windows上正確運行異步代碼
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())