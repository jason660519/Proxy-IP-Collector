"""
IP評分引擎 - 智能代理評分系統
根據多個維度對代理IP進行綜合評分
"""

import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import statistics


class IPScoringEngine:
    """
    IP評分引擎
    根據代理的各項指標計算綜合評分
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化評分引擎
        
        Args:
            config: 評分配置
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 評分權重配置
        self.weights = self.config.get('weights', {
            'connection_success': 0.25,      # 連接成功率
            'response_time': 0.20,             # 響應時間
            'anonymity_level': 0.20,           # 匿名等級
            'stability': 0.15,                 # 穩定性
            'geolocation': 0.10,               # 地理位置
            'speed': 0.10                      # 速度
        })
        
        # 評分標準
        self.standards = self.config.get('standards', {
            'response_time_thresholds': {
                'excellent': 1.0,    # 1秒內
                'good': 3.0,         # 3秒內
                'acceptable': 5.0,   # 5秒內
                'poor': 10.0         # 10秒內
            },
            'anonymity_scores': {
                'elite': 100,        # 高匿名
                'anonymous': 80,     # 匿名
                'transparent': 40    # 透明
            },
            'min_score': 60,         # 最低有效分數
            'max_score': 100         # 最高評分
        })
        
        # 歷史數據緩存
        self.history_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.cache_timeout = self.config.get('cache_timeout', 3600)  # 1小時
    
    async def calculate_score(self, validation_data: Dict[str, Any]) -> float:
        """
        計算代理綜合評分
        
        Args:
            validation_data: 驗證數據
            
        Returns:
            float: 綜合評分 (0-100)
        """
        try:
            self.logger.info("開始計算代理評分")
            
            scores = {}
            
            # 1. 連接成功率評分
            scores['connection_success'] = self._score_connection_success(
                validation_data.get('connection', {})
            )
            
            # 2. 響應時間評分
            scores['response_time'] = self._score_response_time(
                validation_data.get('connection', {}).get('response_time', 0)
            )
            
            # 3. 匿名等級評分
            scores['anonymity_level'] = self._score_anonymity_level(
                validation_data.get('anonymity', {})
            )
            
            # 4. 穩定性評分
            scores['stability'] = await self._score_stability(validation_data)
            
            # 5. 地理位置評分
            scores['geolocation'] = self._score_geolocation(
                validation_data.get('geolocation', {})
            )
            
            # 6. 速度評分
            scores['speed'] = self._score_speed(
                validation_data.get('speed', {})
            )
            
            # 計算加權總分
            total_score = sum(
                scores[key] * self.weights.get(key, 0) 
                for key in scores
            )
            
            # 應用評分修正
            final_score = self._apply_score_adjustments(total_score, validation_data)
            
            self.logger.info(f"代理評分計算完成: {final_score:.1f}/100")
            self.logger.info(f"各項評分: {scores}")
            
            return final_score
            
        except Exception as e:
            self.logger.error(f"評分計算失敗: {e}")
            return 0.0
    
    def _score_connection_success(self, connection_data: Dict[str, Any]) -> float:
        """
        連接成功率評分
        
        Args:
            connection_data: 連接測試數據
            
        Returns:
            float: 連接評分 (0-100)
        """
        if connection_data.get('success', False):
            status_code = connection_data.get('status_code', 0)
            
            if 200 <= status_code < 300:
                return 100.0
            elif 300 <= status_code < 400:
                return 80.0
            elif 400 <= status_code < 500:
                return 60.0
            else:
                return 40.0
        else:
            error = connection_data.get('error', '')
            if 'timeout' in error.lower():
                return 20.0
            elif 'connection' in error.lower():
                return 10.0
            else:
                return 0.0
    
    def _score_response_time(self, response_time: float) -> float:
        """
        響應時間評分
        
        Args:
            response_time: 響應時間（秒）
            
        Returns:
            float: 響應時間評分 (0-100)
        """
        thresholds = self.standards['response_time_thresholds']
        
        if response_time <= thresholds['excellent']:
            return 100.0
        elif response_time <= thresholds['good']:
            # 線性插值：1秒=100分，3秒=80分
            return 100.0 - (response_time - thresholds['excellent']) * 10.0
        elif response_time <= thresholds['acceptable']:
            # 3秒=80分，5秒=60分
            return 80.0 - (response_time - thresholds['good']) * 10.0
        elif response_time <= thresholds['poor']:
            # 5秒=60分，10秒=20分
            return 60.0 - (response_time - thresholds['acceptable']) * 8.0
        else:
            return max(0.0, 20.0 - (response_time - thresholds['poor']) * 2.0)
    
    def _score_anonymity_level(self, anonymity_data: Dict[str, Any]) -> float:
        """
        匿名等級評分
        
        Args:
            anonymity_data: 匿名性測試數據
            
        Returns:
            float: 匿名等級評分 (0-100)
        """
        level = anonymity_data.get('level', 'unknown')
        anonymity_scores = self.standards['anonymity_scores']
        
        return anonymity_scores.get(level, 50.0)
    
    async def _score_stability(self, validation_data: Dict[str, Any]) -> float:
        """
        穩定性評分
        
        Args:
            validation_data: 驗證數據
            
        Returns:
            float: 穩定性評分 (0-100)
        """
        # 獲取代理IP作為緩存鍵
        proxy_key = self._get_proxy_key(validation_data)
        
        # 獲取歷史數據
        history = self._get_proxy_history(proxy_key)
        
        if not history:
            # 沒有歷史數據，給予中等評分
            return 70.0
        
        # 計算穩定性指標
        success_rate = self._calculate_success_rate(history)
        response_time_stability = self._calculate_response_time_stability(history)
        score_consistency = self._calculate_score_consistency(history)
        
        # 綜合穩定性評分
        stability_score = (
            success_rate * 0.4 +
            response_time_stability * 0.3 +
            score_consistency * 0.3
        )
        
        # 更新歷史緩存
        self._update_proxy_history(proxy_key, validation_data)
        
        return stability_score
    
    def _score_geolocation(self, geolocation_data: Dict[str, Any]) -> float:
        """
        地理位置評分
        
        Args:
            geolocation_data: 地理位置數據
            
        Returns:
            float: 地理位置評分 (0-100)
        """
        if not geolocation_data.get('success', False):
            return 50.0  # 無法獲取地理位置，給予中等評分
        
        country = geolocation_data.get('country', '')
        
        # 根據國家/地區給予不同評分
        # 這裡可以根據實際需求調整
        preferred_countries = ['US', 'CA', 'GB', 'DE', 'FR', 'JP', 'SG']
        restricted_countries = ['CN', 'IR', 'KP', 'SY']
        
        if country in preferred_countries:
            return 90.0
        elif country in restricted_countries:
            return 30.0
        else:
            return 70.0
    
    def _score_speed(self, speed_data: Dict[str, Any]) -> float:
        """
        速度評分
        
        Args:
            speed_data: 速度測試數據
            
        Returns:
            float: 速度評分 (0-100)
        """
        if not speed_data.get('success', False):
            return 0.0
        
        download_speed = speed_data.get('download_speed', 0)  # MB/s
        upload_speed = speed_data.get('upload_speed', 0)       # MB/s
        
        # 下載速度評分（假設10MB/s為滿分）
        download_score = min(100.0, (download_speed / 10.0) * 100)
        
        # 上傳速度評分（假設5MB/s為滿分）
        upload_score = min(100.0, (upload_speed / 5.0) * 100)
        
        # 綜合速度評分（下載權重70%，上傳權重30%）
        return download_score * 0.7 + upload_score * 0.3
    
    def _apply_score_adjustments(self, base_score: float, validation_data: Dict[str, Any]) -> float:
        """
        應用評分修正
        
        Args:
            base_score: 基礎評分
            validation_data: 驗證數據
            
        Returns:
            float: 修正後的評分
        """
        adjusted_score = base_score
        
        # 根據代理類型調整
        proxy_type = validation_data.get('proxy', {}).get('type', 'unknown')
        
        if proxy_type == 'elite':
            adjusted_score += 5.0
        elif proxy_type == 'socks5':
            adjusted_score += 3.0
        elif proxy_type == 'https':
            adjusted_score += 2.0
        
        # 根據端口調整（常見端口可能更穩定）
        port = validation_data.get('proxy', {}).get('port', 0)
        common_ports = [80, 8080, 3128, 8081, 9090]
        if port in common_ports:
            adjusted_score += 2.0
        
        # 確保評分在有效範圍內
        return max(0.0, min(100.0, adjusted_score))
    
    def _get_proxy_key(self, validation_data: Dict[str, Any]) -> str:
        """
        獲取代理緩存鍵
        
        Args:
            validation_data: 驗證數據
            
        Returns:
            str: 緩存鍵
        """
        proxy_data = validation_data.get('proxy', {})
        ip = proxy_data.get('ip', '')
        port = proxy_data.get('port', 0)
        return f"{ip}:{port}"
    
    def _get_proxy_history(self, proxy_key: str) -> List[Dict[str, Any]]:
        """
        獲取代理歷史數據
        
        Args:
            proxy_key: 代理緩存鍵
            
        Returns:
            List: 歷史數據列表
        """
        current_time = time.time()
        
        if proxy_key in self.history_cache:
            # 清理過期的歷史數據
            history = self.history_cache[proxy_key]
            valid_history = [
                record for record in history
                if current_time - record['timestamp'] < self.cache_timeout
            ]
            self.history_cache[proxy_key] = valid_history
            return valid_history
        
        return []
    
    def _update_proxy_history(self, proxy_key: str, validation_data: Dict[str, Any]) -> None:
        """
        更新代理歷史數據
        
        Args:
            proxy_key: 代理緩存鍵
            validation_data: 驗證數據
        """
        if proxy_key not in self.history_cache:
            self.history_cache[proxy_key] = []
        
        # 添加新的歷史記錄
        history_record = {
            'timestamp': time.time(),
            'connection_success': validation_data.get('connection', {}).get('success', False),
            'response_time': validation_data.get('connection', {}).get('response_time', 0),
            'anonymity_level': validation_data.get('anonymity', {}).get('level', 'unknown'),
            'score': self._calculate_base_score(validation_data)
        }
        
        self.history_cache[proxy_key].append(history_record)
        
        # 限制歷史數據數量
        max_history = 100
        if len(self.history_cache[proxy_key]) > max_history:
            self.history_cache[proxy_key] = self.history_cache[proxy_key][-max_history:]
    
    def _calculate_base_score(self, validation_data: Dict[str, Any]) -> float:
        """
        計算基礎評分（用於歷史記錄）
        
        Args:
            validation_data: 驗證數據
            
        Returns:
            float: 基礎評分
        """
        # 簡化的基礎評分計算
        connection_score = self._score_connection_success(
            validation_data.get('connection', {})
        )
        response_time_score = self._score_response_time(
            validation_data.get('connection', {}).get('response_time', 0)
        )
        anonymity_score = self._score_anonymity_level(
            validation_data.get('anonymity', {})
        )
        
        return (connection_score + response_time_score + anonymity_score) / 3.0
    
    def _calculate_success_rate(self, history: List[Dict[str, Any]]) -> float:
        """
        計算成功率
        
        Args:
            history: 歷史數據
            
        Returns:
            float: 成功率 (0-100)
        """
        if not history:
            return 50.0  # 默認成功率
        
        success_count = sum(1 for record in history if record.get('connection_success', False))
        return (success_count / len(history)) * 100.0
    
    def _calculate_response_time_stability(self, history: List[Dict[str, Any]]) -> float:
        """
        計算響應時間穩定性
        
        Args:
            history: 歷史數據
            
        Returns:
            float: 穩定性評分 (0-100)
        """
        if not history:
            return 70.0  # 默認穩定性
        
        response_times = [
            record.get('response_time', 0) 
            for record in history 
            if record.get('connection_success', False)
        ]
        
        if not response_times:
            return 30.0  # 沒有成功的響應時間數據
        
        # 計算標準差
        if len(response_times) > 1:
            std_dev = statistics.stdev(response_times)
            mean_time = statistics.mean(response_times)
            
            # 變異係數（標準差/均值）
            cv = std_dev / mean_time if mean_time > 0 else 0
            
            # 變異係數越小，穩定性越高
            stability_score = max(0.0, min(100.0, 100.0 - (cv * 50)))
            return stability_score
        else:
            return 85.0  # 只有一個數據點，給予較高穩定性
    
    def _calculate_score_consistency(self, history: List[Dict[str, Any]]) -> float:
        """
        計算評分一致性
        
        Args:
            history: 歷史數據
            
        Returns:
            float: 一致性評分 (0-100)
        """
        if not history:
            return 70.0  # 默認一致性
        
        scores = [record.get('score', 0) for record in history]
        
        if len(scores) <= 1:
            return 85.0  # 數據點太少
        
        # 計算評分的標準差
        std_dev = statistics.stdev(scores)
        
        # 標準差越小，一致性越高
        consistency_score = max(0.0, min(100.0, 100.0 - (std_dev * 2)))
        return consistency_score