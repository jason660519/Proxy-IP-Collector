#!/usr/bin/env python3
"""
代理收集器部署驗證腳本

該腳本用於驗證代理收集器系統的完整部署，包括：
- 數據庫連接測試
- Redis連接測試
- 應用程序API測試
- 監控系統測試
- 代理功能測試
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import aiohttp
import asyncpg
try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
import requests
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeploymentValidator:
    """部署驗證器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'errors': []
            }
        }
    
    def log_test_result(self, test_name: str, passed: bool, message: str = "", error: Optional[str] = None):
        """記錄測試結果"""
        self.results['tests'][test_name] = {
            'passed': passed,
            'message': message,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results['summary']['total'] += 1
        if passed:
            self.results['summary']['passed'] += 1
            logger.info(f"✓ {test_name}: {message}")
        else:
            self.results['summary']['failed'] += 1
            if error:
                self.results['summary']['errors'].append(f"{test_name}: {error}")
            logger.error(f"✗ {test_name}: {message} {error or ''}")
    
    async def test_database_connection(self) -> bool:
        """測試數據庫連接"""
        test_name = "Database Connection"
        
        try:
            db_type = self.config.get('DATABASE_TYPE', 'sqlite')
            db_url = self.config.get('DATABASE_URL', '')
            
            if db_type == 'sqlite':
                # SQLite測試
                db_path = db_url.replace('sqlite:///', '')
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                conn.close()
                
                if result and result[0] == 1:
                    self.log_test_result(test_name, True, f"SQLite connection successful: {db_path}")
                    return True
                else:
                    self.log_test_result(test_name, False, "SQLite query failed")
                    return False
                    
            elif db_type == 'postgresql':
                # PostgreSQL測試
                if not POSTGRES_AVAILABLE:
                    self.log_test_result(test_name, False, "PostgreSQL module not available (psycopg2 not installed)")
                    return False
                    
                try:
                    # 同步測試
                    conn = psycopg2.connect(db_url)
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    conn.close()
                    
                    if result and result[0] == 1:
                        self.log_test_result(test_name, True, f"PostgreSQL connection successful")
                        return True
                    else:
                        self.log_test_result(test_name, False, "PostgreSQL query failed")
                        return False
                        
                except Exception as e:
                    self.log_test_result(test_name, False, "PostgreSQL connection failed", str(e))
                    return False
            else:
                self.log_test_result(test_name, False, f"Unsupported database type: {db_type}")
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, "Database connection test failed", str(e))
            return False
    
    async def test_redis_connection(self) -> bool:
        """測試Redis連接"""
        test_name = "Redis Connection"
        
        if not REDIS_AVAILABLE:
            self.log_test_result(test_name, False, "Redis module not available (not installed)")
            return False
        
        try:
            redis_url = self.config.get('REDIS_URL', 'redis://localhost:6379/0')
            
            # 解析Redis URL
            redis_host = 'localhost'
            redis_port = 6379
            redis_db = 0
            redis_password = None
            
            if '@' in redis_url:
                # 包含認證信息
                parts = redis_url.split('@')
                auth_part = parts[0].replace('redis://', '')
                host_part = parts[1]
                
                if ':' in auth_part:
                    redis_password = auth_part.split(':')[1]
                
                host_parts = host_part.split(':')
                redis_host = host_parts[0]
                if len(host_parts) > 1:
                    port_db = host_parts[1].split('/')
                    redis_port = int(port_db[0])
                    if len(port_db) > 1:
                        redis_db = int(port_db[1])
            else:
                # 不包含認證信息
                host_part = redis_url.replace('redis://', '')
                host_parts = host_part.split(':')
                redis_host = host_parts[0]
                if len(host_parts) > 1:
                    port_db = host_parts[1].split('/')
                    redis_port = int(port_db[0])
                    if len(port_db) > 1:
                        redis_db = int(port_db[1])
            
            # 測試連接
            r = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # 測試Ping
            result = r.ping()
            if result:
                # 測試基本操作
                test_key = "deployment_test"
                r.set(test_key, "test_value", ex=60)
                value = r.get(test_key)
                
                if value == b"test_value":
                    self.log_test_result(test_name, True, f"Redis connection successful: {redis_host}:{redis_port}")
                    return True
                else:
                    self.log_test_result(test_name, False, "Redis basic operations failed")
                    return False
            else:
                self.log_test_result(test_name, False, "Redis ping failed")
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, "Redis connection failed", str(e))
            return False
    
    async def test_application_api(self) -> bool:
        """測試應用程序API"""
        test_name = "Application API"
        
        try:
            base_url = self.config.get('APP_URL', 'http://localhost:8000')
            
            # 測試健康端點
            health_url = urljoin(base_url, '/health')
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(health_url) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        
                        if health_data.get('status') == 'healthy':
                            self.log_test_result(test_name, True, f"Health check passed: {health_data}")
                            
                            # 測試其他端點
                            await self.test_api_endpoints(base_url)
                            return True
                        else:
                            self.log_test_result(test_name, False, f"Health check failed: {health_data}")
                            return False
                    else:
                        self.log_test_result(test_name, False, f"Health endpoint returned {response.status}")
                        return False
                        
        except Exception as e:
            self.log_test_result(test_name, False, "Application API test failed", str(e))
            return False
    
    async def test_api_endpoints(self, base_url: str):
        """測試API端點"""
        endpoints = [
            ('/api/v1/proxies', 'GET'),
            ('/api/v1/proxies/stats', 'GET'),
            ('/metrics', 'GET')
        ]
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for endpoint, method in endpoints:
                try:
                    url = urljoin(base_url, endpoint)
                    
                    if method == 'GET':
                        async with session.get(url) as response:
                            if response.status in [200, 401, 403]:  # 接受需要認證的響應
                                self.log_test_result(
                                    f"API Endpoint {endpoint}", 
                                    True, 
                                    f"Endpoint accessible (status: {response.status})"
                                )
                            else:
                                self.log_test_result(
                                    f"API Endpoint {endpoint}", 
                                    False, 
                                    f"Endpoint returned {response.status}"
                                )
                    
                except Exception as e:
                    self.log_test_result(
                        f"API Endpoint {endpoint}", 
                        False, 
                        "Endpoint test failed", 
                        str(e)
                    )
    
    async def test_monitoring_system(self) -> bool:
        """測試監控系統"""
        test_name = "Monitoring System"
        
        try:
            prometheus_url = self.config.get('PROMETHEUS_URL', 'http://localhost:9090')
            grafana_url = self.config.get('GRAFANA_URL', 'http://localhost:3000')
            
            monitoring_passed = True
            
            # 測試Prometheus
            try:
                prometheus_health = urljoin(prometheus_url, '/-/healthy')
                response = requests.get(prometheus_health, timeout=5)
                
                if response.status_code == 200:
                    self.log_test_result("Prometheus", True, "Prometheus is healthy")
                else:
                    self.log_test_result("Prometheus", False, f"Prometheus returned {response.status_code}")
                    monitoring_passed = False
                    
            except Exception as e:
                self.log_test_result("Prometheus", False, "Prometheus connection failed", str(e))
                monitoring_passed = False
            
            # 測試Grafana
            try:
                grafana_health = urljoin(grafana_url, '/api/health')
                response = requests.get(grafana_health, timeout=5)
                
                if response.status_code == 200:
                    self.log_test_result("Grafana", True, "Grafana is healthy")
                else:
                    self.log_test_result("Grafana", False, f"Grafana returned {response.status_code}")
                    monitoring_passed = False
                    
            except Exception as e:
                self.log_test_result("Grafana", False, "Grafana connection failed", str(e))
                monitoring_passed = False
            
            return monitoring_passed
            
        except Exception as e:
            self.log_test_result(test_name, False, "Monitoring system test failed", str(e))
            return False
    
    async def test_proxy_functionality(self) -> bool:
        """測試代理功能"""
        test_name = "Proxy Functionality"
        
        try:
            base_url = self.config.get('APP_URL', 'http://localhost:8000')
            
            # 測試代理統計端點
            stats_url = urljoin(base_url, '/api/v1/proxies/stats')
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(stats_url) as response:
                    if response.status == 200:
                        stats_data = await response.json()
                        
                        # 檢查基本統計信息
                        if 'total' in stats_data and 'active' in stats_data:
                            self.log_test_result(
                                test_name, 
                                True, 
                                f"Proxy stats available: {stats_data}"
                            )
                            
                            # 如果有活躍代理，測試代理獲取
                            if stats_data.get('active', 0) > 0:
                                await self.test_proxy_retrieval(base_url)
                            
                            return True
                        else:
                            self.log_test_result(test_name, False, f"Invalid stats format: {stats_data}")
                            return False
                    else:
                        self.log_test_result(test_name, False, f"Stats endpoint returned {response.status}")
                        return False
                        
        except Exception as e:
            self.log_test_result(test_name, False, "Proxy functionality test failed", str(e))
            return False
    
    async def test_proxy_retrieval(self, base_url: str):
        """測試代理獲取"""
        try:
            proxy_url = urljoin(base_url, '/api/v1/proxies?limit=1')
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(proxy_url) as response:
                    if response.status == 200:
                        proxy_data = await response.json()
                        
                        if isinstance(proxy_data, list) and len(proxy_data) > 0:
                            proxy = proxy_data[0]
                            if 'ip' in proxy and 'port' in proxy:
                                self.log_test_result(
                                    "Proxy Retrieval", 
                                    True, 
                                    f"Successfully retrieved proxy: {proxy['ip']}:{proxy['port']}"
                                )
                            else:
                                self.log_test_result(
                                    "Proxy Retrieval", 
                                    False, 
                                    f"Invalid proxy format: {proxy}"
                                )
                        else:
                            self.log_test_result(
                                "Proxy Retrieval", 
                                False, 
                                "No proxies returned"
                            )
                    else:
                        self.log_test_result(
                            "Proxy Retrieval", 
                            False, 
                            f"Proxy endpoint returned {response.status}"
                        )
                        
        except Exception as e:
            self.log_test_result("Proxy Retrieval", False, "Proxy retrieval failed", str(e))
    
    async def test_metrics_collection(self) -> bool:
        """測試指標收集"""
        test_name = "Metrics Collection"
        
        try:
            base_url = self.config.get('APP_URL', 'http://localhost:8000')
            metrics_url = urljoin(base_url, '/metrics')
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(metrics_url) as response:
                    if response.status == 200:
                        metrics_text = await response.text()
                        
                        # 檢查基本指標
                        required_metrics = [
                            'proxy_collector_',
                            'http_requests_',
                            'system_'
                        ]
                        
                        found_metrics = []
                        for metric_prefix in required_metrics:
                            if any(line.startswith(metric_prefix) for line in metrics_text.split('\n') if not line.startswith('#')):
                                found_metrics.append(metric_prefix)
                        
                        if len(found_metrics) >= 2:  # 至少找到2類指標
                            self.log_test_result(
                                test_name, 
                                True, 
                                f"Metrics collection working: found {len(found_metrics)} metric categories"
                            )
                            return True
                        else:
                            self.log_test_result(
                                test_name, 
                                False, 
                                f"Insufficient metrics found: {found_metrics}"
                            )
                            return False
                    else:
                        self.log_test_result(test_name, False, f"Metrics endpoint returned {response.status}")
                        return False
                        
        except Exception as e:
            self.log_test_result(test_name, False, "Metrics collection test failed", str(e))
            return False
    
    async def test_performance_baseline(self) -> bool:
        """測試性能基準"""
        test_name = "Performance Baseline"
        
        try:
            base_url = self.config.get('APP_URL', 'http://localhost:8000')
            health_url = urljoin(base_url, '/health')
            
            # 測試響應時間
            start_time = time.time()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(health_url) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200 and response_time < 5.0:  # 5秒閾值
                        self.log_test_result(
                            test_name, 
                            True, 
                            f"Response time: {response_time:.2f}s (threshold: 5.0s)"
                        )
                        return True
                    elif response.status != 200:
                        self.log_test_result(test_name, False, f"Bad response status: {response.status}")
                        return False
                    else:
                        self.log_test_result(
                            test_name, 
                            False, 
                            f"Slow response: {response_time:.2f}s (threshold: 5.0s)"
                        )
                        return False
                        
        except Exception as e:
            self.log_test_result(test_name, False, "Performance baseline test failed", str(e))
            return False
    
    async def run_all_tests(self) -> Dict:
        """運行所有測試"""
        logger.info("開始部署驗證測試...")
        
        # 運行測試
        await self.test_database_connection()
        await self.test_redis_connection()
        await self.test_application_api()
        await self.test_monitoring_system()
        await self.test_proxy_functionality()
        await self.test_metrics_collection()
        await self.test_performance_baseline()
        
        # 生成報告
        self.generate_report()
        
        return self.results
    
    def generate_report(self):
        """生成測試報告"""
        logger.info("\n" + "="*60)
        logger.info("部署驗證測試報告")
        logger.info("="*60)
        
        summary = self.results['summary']
        
        logger.info(f"總測試數: {summary['total']}")
        logger.info(f"通過: {summary['passed']} ✅")
        logger.info(f"失敗: {summary['failed']} ❌")
        
        if summary['failed'] > 0:
            logger.info("\n失敗的測試:")
            for test_name, test_result in self.results['tests'].items():
                if not test_result['passed']:
                    logger.info(f"  - {test_name}: {test_result['message']}")
                    if test_result['error']:
                        logger.info(f"    錯誤: {test_result['error']}")
        
        # 保存報告
        report_file = f"deployment-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n詳細報告已保存到: {report_file}")
        
        # 返回整體狀態
        success = summary['failed'] == 0
        logger.info(f"\n整體狀態: {'✅ 部署成功' if success else '❌ 部署失敗'}")
        
        return success

def load_config() -> Dict:
    """加載配置"""
    config = {}
    
    # 從環境變量加載
    for key, default_value in [
        ('DATABASE_TYPE', 'sqlite'),
        ('DATABASE_URL', 'sqlite:///data/proxy_collector.db'),
        ('REDIS_URL', 'redis://localhost:6379/0'),
        ('APP_URL', 'http://localhost:8000'),
        ('PROMETHEUS_URL', 'http://localhost:9090'),
        ('GRAFANA_URL', 'http://localhost:3000'),
    ]:
        config[key] = os.getenv(key, default_value)
    
    # 從配置文件加載（如果存在）
    config_files = [
        '.env',
        'config.json',
        '../.env',
        '../config.json'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                if config_file.endswith('.env'):
                    # 加載.env文件
                    with open(config_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and '=' in line and not line.startswith('#'):
                                key, value = line.split('=', 1)
                                config[key] = value.strip('"\'')
                
                elif config_file.endswith('.json'):
                    # 加載JSON文件
                    with open(config_file, 'r') as f:
                        file_config = json.load(f)
                        config.update(file_config)
                        
            except Exception as e:
                logger.warning(f"無法加載配置文件 {config_file}: {e}")
    
    return config

async def main():
    """主函數"""
    try:
        # 加載配置
        config = load_config()
        logger.info("配置加載完成")
        
        # 創建驗證器
        validator = DeploymentValidator(config)
        
        # 運行測試
        results = await validator.run_all_tests()
        
        # 返回退出碼
        success = results['summary']['failed'] == 0
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("\n測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        logger.error(f"測試運行失敗: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())