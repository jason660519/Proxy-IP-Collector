"""
freeproxylist.net 專用ETL處理流程
專為freeproxylist.net設計的Extract-Transform-Load管道，包含數據清洗、格式轉換與儲存邏輯
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime

from ..extractors import BaseExtractor, WebScrapingExtractor
from ..transformers import ProxyDataTransformer
from ..validators import ProxyValidator
from ...models.proxy import Proxy
from ...database import get_db


@dataclass
class ETLStats:
    """ETL統計信息"""
    extracted: int = 0
    transformed: int = 0
    validated: int = 0
    saved: int = 0
    errors: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class FreeProxyListNetETLPipeline:
    """
    freeproxylist.net專用ETL管道
    實現完整的Extract-Transform-Load處理流程
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化ETL管道
        
        Args:
            config: 配置字典，包含提取器、轉換器等設置
        """
        self.config = config
        self.extractor = WebScrapingExtractor(config.get('extractor', {}))
        self.transformer = ProxyDataTransformer()
        self.validator = ProxyValidator()
        self.stats = ETLStats()
        self.logger = logging.getLogger(__name__)
        
    async def run(self) -> ETLStats:
        """
        執行ETL流程
        
        Returns:
            ETLStats: 統計信息
        """
        self.stats.start_time = datetime.now()
        self.logger.info("開始freeproxylist.net ETL處理流程")
        
        try:
            # 1. 提取階段
            extracted_data = await self._extract()
            
            # 2. 轉換階段
            transformed_data = await self._transform(extracted_data)
            
            # 3. 驗證階段
            validated_data = await self._validate(transformed_data)
            
            # 4. 載入階段
            await self._load(validated_data)
            
        except Exception as e:
            self.logger.error(f"ETL流程執行失敗: {e}")
            self.stats.errors += 1
            raise
        finally:
            self.stats.end_time = datetime.now()
            self._log_summary()
            
        return self.stats
    
    async def _extract(self) -> List[Dict[str, Any]]:
        """提取數據"""
        self.logger.info("開始提取數據...")
        
        # 使用專屬提取器提取數據
        from ..extractors import FreeProxyListNetEnhancedExtractor
        extractor = FreeProxyListNetEnhancedExtractor(self.config)
        
        results = await extractor.extract()
        self.stats.extracted = len(results)
        
        self.logger.info(f"成功提取 {self.stats.extracted} 條數據")
        return results
    
    async def _transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """轉換數據"""
        self.logger.info("開始轉換數據...")
        
        transformed_data = []
        for item in data:
            try:
                # 標準化代理數據格式
                transformed = await self.transformer.transform_proxy_data(item)
                if transformed:
                    transformed_data.append(transformed)
            except Exception as e:
                self.logger.warning(f"數據轉換失敗: {e}")
                self.stats.errors += 1
        
        self.stats.transformed = len(transformed_data)
        self.logger.info(f"成功轉換 {self.stats.transformed} 條數據")
        return transformed_data
    
    async def _validate(self, data: List[Dict[str, Any]]) -> List[Proxy]:
        """驗證數據"""
        self.logger.info("開始驗證數據...")
        
        validated_proxies = []
        for item in data:
            try:
                # 創建代理對象
                proxy = Proxy(**item)
                
                # 驗證代理可用性
                is_valid = await self.validator.validate_proxy(proxy)
                if is_valid:
                    validated_proxies.append(proxy)
                    self.stats.validated += 1
            except Exception as e:
                self.logger.warning(f"代理驗證失敗: {e}")
                self.stats.errors += 1
        
        self.logger.info(f"成功驗證 {self.stats.validated} 個代理")
        return validated_proxies
    
    async def _load(self, proxies: List[Proxy]) -> None:
        """載入數據到數據庫"""
        self.logger.info("開始載入數據到數據庫...")
        
        db = get_db()
        saved_count = 0
        
        for proxy in proxies:
            try:
                # 檢查是否已存在
                existing = db.query(Proxy).filter_by(
                    ip=proxy.ip, port=proxy.port
                ).first()
                
                if not existing:
                    db.add(proxy)
                    saved_count += 1
                else:
                    # 更新現有記錄
                    existing.score = proxy.score
                    existing.last_verified = proxy.last_verified
                    
            except Exception as e:
                self.logger.error(f"數據庫操作失敗: {e}")
                self.stats.errors += 1
        
        try:
            db.commit()
            self.stats.saved = saved_count
            self.logger.info(f"成功保存 {self.stats.saved} 個新代理")
        except Exception as e:
            db.rollback()
            self.logger.error(f"數據庫提交失敗: {e}")
            raise
    
    def _log_summary(self) -> None:
        """記錄處理摘要"""
        duration = (self.stats.end_time - self.stats.start_time).total_seconds()
        
        summary = f"""
        freeproxylist.net ETL處理完成
        處理時長: {duration:.2f}秒
        提取數據: {self.stats.extracted} 條
        轉換成功: {self.stats.transformed} 條
        驗證通過: {self.stats.validated} 個
        保存代理: {self.stats.saved} 個
        錯誤數量: {self.stats.errors} 個
        """
        
        self.logger.info(summary)


# 使用示例
async def main():
    """測試ETL管道"""
    config = {
        'base_url': 'https://freeproxylist.net/',
        'request_delay': 1.0,
        'max_concurrent': 5
    }
    
    pipeline = FreeProxyListNetETLPipeline(config)
    stats = await pipeline.run()
    
    print(f"ETL處理完成，保存了 {stats.saved} 個代理")


if __name__ == "__main__":
    asyncio.run(main())