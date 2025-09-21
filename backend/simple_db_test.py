"""
簡化數據庫連接測試腳本

這個腳本專注於測試PostgreSQL連接，避免Redis兼容性問題
"""

import asyncio
import asyncpg
import sqlite3
from pathlib import Path
import sys
import os
from typing import Dict, Any, List

# 添加項目根目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.config import settings
except ImportError:
    # 如果無法導入，創建模擬配置
    class MockSettings:
        DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/proxy_collector"
    
    settings = MockSettings()


class SimpleDatabaseTester:
    """簡化數據庫連接測試器"""
    
    def __init__(self):
        self.test_results = {}
        self.recommendations = []
    
    async def test_postgresql_connection(self) -> Dict[str, any]:
        """測試PostgreSQL連接"""
        print("🔍 正在測試PostgreSQL連接...")
        print(f"   連接URL: {settings.DATABASE_URL}")
        
        try:
            # 解析數據庫URL
            db_url = settings.DATABASE_URL
            
            # 嘗試連接
            print("   正在嘗試連接...")
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
            
        except asyncpg.exceptions.CannotConnectNowError as e:
            print(f"❌ PostgreSQL服務未運行或拒絕連接: {e}")
            return {
                "status": "failed",
                "message": "PostgreSQL服務未運行或拒絕連接",
                "error": str(e),
                "recommendation": "請確保PostgreSQL服務已啟動並接受連接"
            }
            
        except asyncpg.exceptions.InvalidPasswordError as e:
            print(f"❌ PostgreSQL認證失敗: {e}")
            return {
                "status": "failed",
                "message": "用戶名或密碼錯誤",
                "error": str(e),
                "recommendation": "請檢查數據庫認證配置"
            }
            
        except Exception as e:
            print(f"❌ PostgreSQL連接錯誤: {type(e).__name__}: {str(e)}")
            return {
                "status": "failed",
                "message": f"連接錯誤: {str(e)}",
                "error_type": type(e).__name__,
                "recommendation": "請檢查數據庫配置和網絡連接"
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
            print(f"   數據庫文件: {db_path}")
            
            conn = sqlite3.connect(db_path)
            
            # 測試查詢
            result = conn.execute("SELECT sqlite_version()").fetchone()
            
            # 創建測試表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 插入測試數據
            conn.execute("INSERT INTO test_table (name) VALUES (?)", ("test_record",))
            conn.commit()
            
            # 查詢測試數據
            test_data = conn.execute("SELECT * FROM test_table LIMIT 1").fetchone()
            
            conn.close()
            
            print(f"✅ SQLite後備方案可用")
            print(f"   版本: {result[0]}")
            print(f"   測試數據: {test_data}")
            
            return {
                "status": "success",
                "message": "SQLite後備方案可用",
                "version": result[0],
                "database_path": str(db_path),
                "test_data": test_data
            }
            
        except Exception as e:
            print(f"❌ SQLite測試失敗: {str(e)}")
            return {
                "status": "failed",
                "message": f"SQLite測試失敗: {str(e)}"
            }
    
    def check_database_services(self) -> Dict[str, any]:
        """檢查數據庫服務狀態"""
        print("🔍 正在檢查數據庫服務狀態...")
        
        import subprocess
        import platform
        
        services_status = {}
        
        # 檢查PostgreSQL
        try:
            if platform.system() == "Windows":
                # Windows下檢查PostgreSQL服務
                result = subprocess.run(
                    ["sc", "query", "postgresql"], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                services_status["postgresql"] = {
                    "running": "RUNNING" in result.stdout,
                    "status": "running" if "RUNNING" in result.stdout else "stopped"
                }
            else:
                # Linux/macOS下檢查PostgreSQL進程
                result = subprocess.run(
                    ["pgrep", "postgres"], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                services_status["postgresql"] = {
                    "running": result.returncode == 0,
                    "status": "running" if result.returncode == 0 else "stopped"
                }
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            services_status["postgresql"] = {
                "running": False,
                "status": "unknown",
                "error": "無法檢測PostgreSQL服務狀態"
            }
        
        # 顯示服務狀態
        for service, status in services_status.items():
            if status["running"]:
                print(f"✅ {service.upper()} 服務正在運行")
            else:
                print(f"❌ {service.upper()} 服務未運行")
        
        return services_status
    
    def generate_recommendations(self, results: Dict[str, any]) -> List[str]:
        """生成改進建議"""
        recommendations = []
        
        # PostgreSQL建議
        if results.get("postgresql", {}).get("status") == "failed":
            recommendations.append("📝 PostgreSQL改進建議：")
            recommendations.append("  1. 安裝PostgreSQL：")
            recommendations.append("     - Windows: 下載並安裝PostgreSQL安裝包")
            recommendations.append("     - macOS: brew install postgresql")
            recommendations.append("     - Linux: sudo apt-get install postgresql")
            recommendations.append("  2. 創建數據庫和用戶：")
            recommendations.append("     - 創建數據庫: CREATE DATABASE proxy_collector;")
            recommendations.append("     - 創建用戶: CREATE USER postgres WITH PASSWORD 'password';")
            recommendations.append("     - 授權: GRANT ALL PRIVILEGES ON DATABASE proxy_collector TO postgres;")
            recommendations.append("  3. 啟動服務：")
            recommendations.append("     - Windows: net start postgresql")
            recommendations.append("     - macOS/Linux: brew services start postgresql")
            recommendations.append("  4. 檢查端口：確保5432端口開放")
        
        # SQLite建議
        if results.get("sqlite", {}).get("status") == "success":
            recommendations.append("\n✅ SQLite方案：")
            recommendations.append("  - SQLite已準備就緒，可作為開發環境使用")
            recommendations.append("  - 適合單機開發和測試")
            recommendations.append("  - 生產環境建議使用PostgreSQL")
        
        # 通用建議
        recommendations.append("\n🔧 通用建議：")
        recommendations.append("  1. 環境變量：創建 .env 文件並配置正確的連接參數")
        recommendations.append("  2. 網絡連接：確保數據庫服務器可訪問")
        recommendations.append("  3. 防火牆：檢查防火牆設置是否阻止連接")
        recommendations.append("  4. 配置文件：檢查 app/core/config.py 中的配置")
        
        return recommendations
    
    async def run_full_diagnostic(self) -> Dict[str, any]:
        """運行完整診斷"""
        print("🚀 開始數據庫連接診斷...")
        print("=" * 60)
        
        # 檢查服務狀態
        services_status = self.check_database_services()
        self.test_results["services"] = services_status
        
        # 測試PostgreSQL
        pg_result = await self.test_postgresql_connection()
        self.test_results["postgresql"] = pg_result
        
        # 測試SQLite後備方案
        sqlite_result = self.test_sqlite_fallback()
        self.test_results["sqlite"] = sqlite_result
        
        # 生成建議
        self.recommendations = self.generate_recommendations(self.test_results)
        
        # 生成總結報告
        report = {
            "timestamp": "2024-01-20T10:30:00Z",
            "summary": {
                "total_tests": 2,
                "passed": sum(1 for r in self.test_results.values() if isinstance(r, dict) and r.get("status") == "success"),
                "failed": sum(1 for r in self.test_results.values() if isinstance(r, dict) and r.get("status") == "failed")
            },
            "results": self.test_results,
            "recommendations": self.recommendations,
            "next_steps": [
                "根據測試結果配置數據庫連接",
                "更新 .env 文件中的連接參數",
                "重新運行測試以驗證配置",
                "考慮使用SQLite進行開發環境部署"
            ]
        }
        
        print("\n" + "=" * 60)
        print("📊 診斷完成！")
        print(f"通過測試：{report['summary']['passed']}/{report['summary']['total_tests']}")
        
        if self.recommendations:
            print("\n" + "\n".join(self.recommendations))
        
        return report


# 添加缺失的導入
from typing import Dict, Any, List

async def main():
    """主函數"""
    tester = SimpleDatabaseTester()
    
    try:
        report = await tester.run_full_diagnostic()
        
        # 保存報告
        with open("database_diagnostic_report.json", "w", encoding="utf-8") as f:
            import json
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 詳細報告已保存到：database_diagnostic_report.json")
        
        # 提供即時建議
        if report['summary']['passed'] == 0:
            print("\n⚠️ 建議：")
            print("1. 使用SQLite進行開發環境部署")
            print("2. 在生產環境配置PostgreSQL")
            print("3. 創建 .env 文件配置連接參數")
        
    except KeyboardInterrupt:
        print("\n⚠️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中出現錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 確保在Windows上正確運行異步代碼
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())