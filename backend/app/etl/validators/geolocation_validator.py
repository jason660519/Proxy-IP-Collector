"""
地理位置驗證器 - 代理地理位置檢測與驗證
檢測代理的真實地理位置並驗證其準確性
"""

import asyncio
import aiohttp
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json


class GeolocationValidator:
    """
    地理位置驗證器
    檢測代理的地理位置信息並驗證其準確性
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化地理位置驗證器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 地理位置API配置
        self.geo_apis = self.config.get('geo_apis', [
            'http://ip-api.com/json/{}',
            'https://ipapi.co/{}/json/',
            'https://freegeoip.app/json/{}'
        ])
        
        self.timeout = self.config.get('timeout', 10)
        self.max_retries = self.config.get('max_retries', 2)
        self.cache_timeout = self.config.get('cache_timeout', 3600)  # 1小時
        
        # 地理位置緩存
        self.geo_cache: Dict[str, Dict[str, Any]] = {}
        
        # 國家代碼映射
        self.country_mapping = {
            'United States': 'US',
            'China': 'CN',
            'United Kingdom': 'GB',
            'Japan': 'JP',
            'Germany': 'DE',
            'France': 'FR',
            'Canada': 'CA',
            'Australia': 'AU',
            'Russia': 'RU',
            'Netherlands': 'NL'
        }
    
    async def validate_location(self, proxy: Any) -> Dict[str, Any]:
        """
        驗證代理地理位置
        
        Args:
            proxy: 代理對象
            
        Returns:
            Dict: 驗證結果
        """
        try:
            self.logger.info(f"開始驗證代理 {proxy.ip}:{proxy.port} 的地理位置")
            
            # 檢查緩存
            cache_key = f"{proxy.ip}:{proxy.port}"
            cached_result = self._get_cached_geo(cache_key)
            if cached_result:
                self.logger.info(f"使用緩存的地理位置數據")
                return cached_result
            
            # 獲取真實地理位置
            real_location = await self._get_real_location()
            if not real_location:
                return {
                    'success': False,
                    'error': '無法獲取真實地理位置',
                    'proxy_location': None,
                    'real_location': None
                }
            
            # 通過代理獲取地理位置
            proxy_location = await self._get_proxy_location(proxy)
            if not proxy_location:
                return {
                    'success': False,
                    'error': '無法通過代理獲取地理位置',
                    'proxy_location': None,
                    'real_location': real_location
                }
            
            # 分析地理位置差異
            location_analysis = self._analyze_location_difference(
                real_location, proxy_location
            )
            
            result = {
                'success': True,
                'proxy_location': proxy_location,
                'real_location': real_location,
                'analysis': location_analysis,
                'timestamp': datetime.now().isoformat()
            }
            
            # 緩存結果
            self._cache_geo(cache_key, result)
            
            self.logger.info(
                f"地理位置驗證完成 - 代理: {proxy_location.get('country', 'Unknown')}, "
                f"真實: {real_location.get('country', 'Unknown')}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"地理位置驗證失敗: {e}")
            return {
                'success': False,
                'error': str(e),
                'proxy_location': None,
                'real_location': None
            }
    
    async def _get_real_location(self) -> Optional[Dict[str, Any]]:
        """
        獲取真實地理位置
        
        Returns:
            Dict: 地理位置信息
        """
        try:
            # 獲取真實IP
            real_ip = await self._get_real_ip()
            if not real_ip:
                return None
            
            # 查詢IP地理位置
            location = await self._query_ip_location(real_ip)
            return location
            
        except Exception as e:
            self.logger.error(f"獲取真實地理位置失敗: {e}")
            return None
    
    async def _get_proxy_location(self, proxy: Any) -> Optional[Dict[str, Any]]:
        """
        通過代理獲取地理位置
        
        Args:
            proxy: 代理對象
            
        Returns:
            Dict: 地理位置信息
        """
        try:
            # 通過代理獲取IP
            proxy_ip = await self._get_proxy_ip(proxy)
            if not proxy_ip:
                return None
            
            # 查詢代理IP地理位置
            location = await self._query_ip_location(proxy_ip)
            return location
            
        except Exception as e:
            self.logger.error(f"獲取代理地理位置失敗: {e}")
            return None
    
    async def _get_real_ip(self) -> Optional[str]:
        """
        獲取真實IP地址
        
        Returns:
            str: IP地址
        """
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # 使用多個IP查詢服務
                ip_services = [
                    'https://api.ipify.org?format=json',
                    'https://ipapi.co/json/',
                    'http://httpbin.org/ip'
                ]
                
                for service in ip_services:
                    try:
                        async with session.get(service, timeout=5) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                # 提取IP地址
                                if 'ip' in data:
                                    return data['ip']
                                elif 'origin' in data:
                                    return data['origin'].split(',')[0].strip()
                                
                    except Exception as e:
                        self.logger.warning(f"IP查詢服務 {service} 失敗: {e}")
                        continue
                
                return None
                
        except Exception as e:
            self.logger.error(f"獲取真實IP失敗: {e}")
            return None
    
    async def _get_proxy_ip(self, proxy: Any) -> Optional[str]:
        """
        通過代理獲取IP地址
        
        Args:
            proxy: 代理對象
            
        Returns:
            str: IP地址
        """
        try:
            # 構建代理URL
            proxy_url = f"{proxy.protocol}://{proxy.ip}:{proxy.port}"
            if hasattr(proxy, 'username') and hasattr(proxy, 'password'):
                if proxy.username and proxy.password:
                    proxy_url = f"{proxy.protocol}://{proxy.username}:{proxy.password}@{proxy.ip}:{proxy.port}"
            
            timeout = aiohttp.ClientTimeout(total=15)
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                # 使用多個IP查詢服務
                ip_services = [
                    'https://api.ipify.org?format=json',
                    'http://httpbin.org/ip',
                    'https://ipapi.co/json/'
                ]
                
                for service in ip_services:
                    try:
                        async with session.get(
                            service,
                            proxy=proxy_url,
                            timeout=10
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                # 提取IP地址
                                if 'ip' in data:
                                    return data['ip']
                                elif 'origin' in data:
                                    return data['origin'].split(',')[0].strip()
                                
                    except Exception as e:
                        self.logger.warning(f"代理IP查詢服務 {service} 失敗: {e}")
                        continue
                
                return None
                
        except Exception as e:
            self.logger.error(f"通過代理獲取IP失敗: {e}")
            return None
        finally:
            await connector.close()
    
    async def _query_ip_location(self, ip: str) -> Optional[Dict[str, Any]]:
        """
        查詢IP地理位置
        
        Args:
            ip: IP地址
            
        Returns:
            Dict: 地理位置信息
        """
        # 檢查緩存
        if ip in self.geo_cache:
            cached_data = self.geo_cache[ip]
            if time.time() - cached_data.get('cache_time', 0) < self.cache_timeout:
                return cached_data.get('location')
        
        # 嘗試多個地理位置API
        for api_template in self.geo_apis:
            try:
                api_url = api_template.format(ip)
                location = await self._call_geo_api(api_url)
                
                if location:
                    # 緩存結果
                    self.geo_cache[ip] = {
                        'location': location,
                        'cache_time': time.time()
                    }
                    return location
                    
            except Exception as e:
                self.logger.warning(f"地理位置API {api_template} 失敗: {e}")
                continue
        
        return None
    
    async def _call_geo_api(self, api_url: str) -> Optional[Dict[str, Any]]:
        """
        調用地理位置API
        
        Args:
            api_url: API URL
            
        Returns:
            Dict: 標準化的地理位置信息
        """
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._normalize_geo_data(data, api_url)
                    else:
                        self.logger.warning(f"地理位置API返回錯誤: {response.status}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"調用地理位置API失敗: {e}")
            return None
    
    def _normalize_geo_data(self, raw_data: Dict[str, Any], api_url: str) -> Dict[str, Any]:
        """
        標準化地理位置數據
        
        Args:
            raw_data: 原始API數據
            api_url: API URL
            
        Returns:
            Dict: 標準化的地理位置信息
        """
        normalized = {
            'ip': raw_data.get('ip', raw_data.get('query', '')),
            'country': 'Unknown',
            'country_code': 'Unknown',
            'region': 'Unknown',
            'city': 'Unknown',
            'latitude': 0.0,
            'longitude': 0.0,
            'timezone': 'Unknown',
            'isp': 'Unknown',
            'organization': 'Unknown'
        }
        
        # 根據不同的API進行數據標準化
        if 'ip-api.com' in api_url:
            normalized.update({
                'country': raw_data.get('country', 'Unknown'),
                'country_code': raw_data.get('countryCode', 'Unknown'),
                'region': raw_data.get('regionName', 'Unknown'),
                'city': raw_data.get('city', 'Unknown'),
                'latitude': float(raw_data.get('lat', 0.0)),
                'longitude': float(raw_data.get('lon', 0.0)),
                'timezone': raw_data.get('timezone', 'Unknown'),
                'isp': raw_data.get('isp', 'Unknown'),
                'organization': raw_data.get('org', 'Unknown')
            })
        
        elif 'ipapi.co' in api_url:
            normalized.update({
                'country': raw_data.get('country_name', 'Unknown'),
                'country_code': raw_data.get('country', 'Unknown'),
                'region': raw_data.get('region', 'Unknown'),
                'city': raw_data.get('city', 'Unknown'),
                'latitude': float(raw_data.get('latitude', 0.0)),
                'longitude': float(raw_data.get('longitude', 0.0)),
                'timezone': raw_data.get('timezone', 'Unknown'),
                'isp': raw_data.get('org', 'Unknown'),
                'organization': raw_data.get('org', 'Unknown')
            })
        
        elif 'freegeoip.app' in api_url:
            normalized.update({
                'country': raw_data.get('country_name', 'Unknown'),
                'country_code': raw_data.get('country_code', 'Unknown'),
                'region': raw_data.get('region_name', 'Unknown'),
                'city': raw_data.get('city', 'Unknown'),
                'latitude': float(raw_data.get('latitude', 0.0)),
                'longitude': float(raw_data.get('longitude', 0.0)),
                'timezone': raw_data.get('time_zone', 'Unknown'),
                'isp': raw_data.get('ip', 'Unknown'),
                'organization': raw_data.get('organization', 'Unknown')
            })
        
        return normalized
    
    def _analyze_location_difference(self, real_location: Dict[str, Any], proxy_location: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析地理位置差異
        
        Args:
            real_location: 真實地理位置
            proxy_location: 代理地理位置
            
        Returns:
            Dict: 差異分析結果
        """
        analysis = {
            'same_country': False,
            'same_region': False,
            'same_city': False,
            'distance_km': 0.0,
            'risk_level': 'low',
            'details': ''
        }
        
        try:
            # 檢查國家
            real_country = real_location.get('country_code', '')
            proxy_country = proxy_location.get('country_code', '')
            
            if real_country and proxy_country:
                analysis['same_country'] = (real_country == proxy_country)
            
            # 檢查地區
            real_region = real_location.get('region', '').lower()
            proxy_region = proxy_location.get('region', '').lower()
            
            if real_region and proxy_region:
                analysis['same_region'] = (real_region == proxy_region)
            
            # 檢查城市
            real_city = real_location.get('city', '').lower()
            proxy_city = proxy_location.get('city', '').lower()
            
            if real_city and proxy_city:
                analysis['same_city'] = (real_city == proxy_city)
            
            # 計算距離
            real_lat = real_location.get('latitude', 0.0)
            real_lon = real_location.get('longitude', 0.0)
            proxy_lat = proxy_location.get('latitude', 0.0)
            proxy_lon = proxy_location.get('longitude', 0.0)
            
            if all([real_lat, real_lon, proxy_lat, proxy_lon]):
                distance = self._calculate_distance(
                    real_lat, real_lon, proxy_lat, proxy_lon
                )
                analysis['distance_km'] = distance
            
            # 風險評估
            analysis['risk_level'] = self._assess_location_risk(analysis)
            
            # 生成詳細描述
            analysis['details'] = self._generate_location_details(
                real_location, proxy_location, analysis
            )
            
        except Exception as e:
            self.logger.error(f"地理位置差異分析失敗: {e}")
            analysis['details'] = f"分析失敗: {e}"
        
        return analysis
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        計算兩點間的距離（公里）
        
        Args:
            lat1: 第一點緯度
            lon1: 第一點經度
            lat2: 第二點緯度
            lon2: 第二點經度
            
        Returns:
            float: 距離（公里）
        """
        import math
        
        # 將角度轉換為弧度
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine公式
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # 地球半徑（公里）
        r = 6371
        
        return c * r
    
    def _assess_location_risk(self, analysis: Dict[str, Any]) -> str:
        """
        評估地理位置風險
        
        Args:
            analysis: 差異分析結果
            
        Returns:
            str: 風險等級
        """
        risk_score = 0
        
        # 不同國家風險較高
        if not analysis.get('same_country', False):
            risk_score += 3
        
        # 距離風險
        distance = analysis.get('distance_km', 0)
        if distance > 1000:  # 超過1000公里
            risk_score += 2
        elif distance > 500:  # 超過500公里
            risk_score += 1
        
        if risk_score >= 4:
            return 'high'
        elif risk_score >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _generate_location_details(self, real_location: Dict[str, Any], 
                                 proxy_location: Dict[str, Any], 
                                 analysis: Dict[str, Any]) -> str:
        """
        生成地理位置詳細描述
        
        Args:
            real_location: 真實地理位置
            proxy_location: 代理地理位置
            analysis: 差異分析結果
            
        Returns:
            str: 詳細描述
        """
        details = []
        
        # 代理位置信息
        proxy_country = proxy_location.get('country', 'Unknown')
        proxy_city = proxy_location.get('city', 'Unknown')
        details.append(f"代理位置: {proxy_country}, {proxy_city}")
        
        # 差異分析
        if analysis.get('same_country', False):
            details.append("✓ 代理與真實位置在同一國家")
        else:
            real_country = real_location.get('country', 'Unknown')
            details.append(f"⚠ 代理與真實位置在不同國家 ({proxy_country} vs {real_country})")
        
        # 距離信息
        distance = analysis.get('distance_km', 0)
        if distance > 0:
            details.append(f"兩地距離: {distance:.1f} 公里")
        
        # 風險等級
        risk_level = analysis.get('risk_level', 'low')
        risk_icons = {'low': '✓', 'medium': '⚠', 'high': '✗'}
        risk_text = {'low': '低風險', 'medium': '中等風險', 'high': '高風險'}
        
        details.append(f"{risk_icons[risk_level]} 地理位置風險: {risk_text[risk_level]}")
        
        return ' | '.join(details)
    
    def _get_cached_geo(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        獲取緩存的地理位置
        
        Args:
            cache_key: 緩存鍵
            
        Returns:
            Dict: 緩存的地理位置信息
        """
        if cache_key in self.geo_cache:
            cached_data = self.geo_cache[cache_key]
            cache_time = cached_data.get('cache_time', 0)
            
            if time.time() - cache_time < self.cache_timeout:
                return cached_data.get('result')
        
        return None
    
    def _cache_geo(self, cache_key: str, result: Dict[str, Any]) -> None:
        """
        緩存地理位置結果
        
        Args:
            cache_key: 緩存鍵
            result: 地理位置結果
        """
        self.geo_cache[cache_key] = {
            'result': result,
            'cache_time': time.time()
        }