"""
系統診斷腳本
分析系統性能和識別瓶頸
"""
import asyncio
import time
import json
from datetime import datetime
from typing import Dict, Any
import aiohttp
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemDiagnostics:
    """系統診斷類"""
    
    def __init__(self):
        self.results = {}
    
    async def check_server_status(self) -> Dict[str, Any]:
        """檢查服務器狀態"""
        logger.info("檢查服務器狀態...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # 檢查基本API端點
                async with session.get('http://localhost:8000/api/v1/health') as response:
                    health_data = await response.json()
                    
                # 檢查任務列表
                async with session.get('http://localhost:8000/api/v1/tasks') as response:
                    tasks_data = await response.json()
                    
                return {
                    'status': 'running',
                    'health': health_data,
                    'total_tasks': len(tasks_data),
                    'running_tasks': len([t for t in tasks_data if t.get('status') == 'running']),
                    'pending_tasks': len([t for t in tasks_data if t.get('status') == 'pending'])
                }
        except Exception as e:
            logger.error(f"服務器檢查失敗: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def run_diagnostics(self) -> Dict[str, Any]:
        """運行完整診斷"""
        logger.info("開始系統診斷...")
        
        start_time = time.time()
        
        # 檢查服務器狀態
        server_status = await self.check_server_status()
        
        end_time = time.time()
        
        self.results = {
            'diagnostic_time': datetime.now().isoformat(),
            'execution_time': end_time - start_time,
            'server_status': server_status
        }
        
        logger.info("系統診斷完成")
        return self.results
    
    def generate_report(self) -> str:
        """生成診斷報告"""
        if not self.results:
            return "尚未運行診斷"
        
        report = []
        report.append("=" * 60)
        report.append("系統診斷報告")
        report.append("=" * 60)
        report.append(f"診斷時間: {self.results['diagnostic_time']}")
        report.append(f"執行時間: {self.results['execution_time']:.2f}秒")
        report.append("")
        
        # 服務器狀態
        server = self.results['server_status']
        report.append("服務器狀態:")
        if server['status'] == 'running':
            report.append(f"  狀態: 運行中")
            report.append(f"  總任務數: {server['total_tasks']}")
            report.append(f"  運行中任務: {server['running_tasks']}")
            report.append(f"  待處理任務: {server['pending_tasks']}")
        else:
            report.append(f"  狀態: 錯誤 - {server.get('error', '未知錯誤')}")
        report.append("")
        
        return "\n".join(report)

async def main():
    """主函數"""
    diagnostics = SystemDiagnostics()
    
    try:
        # 運行診斷
        results = await diagnostics.run_diagnostics()
        
        # 生成報告
        report = diagnostics.generate_report()
        print(report)
        
        # 保存詳細結果到文件
        with open('diagnostic_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n詳細結果已保存到 diagnostic_results.json")
        
    except Exception as e:
        logger.error(f"診斷過程中出現錯誤: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())