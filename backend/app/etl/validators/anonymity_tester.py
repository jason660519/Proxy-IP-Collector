"""
匿名性測試器 - 代理匿名性與隱私保護測試
測試代理的匿名等級、標頭洩露和隱私保護能力
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class AnonymityTester:
    """
    匿名性測試器
    測試代理的匿名等級、標頭洩露和隱私保護能力
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化匿名性測試器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 測試配置
        self.anonymity_test_urls = self.config.get('anonymity_test_urls', [
            'https://httpbin.org/headers',
            'https://www.cloudflare.com/cdn-cgi/trace',
            'https://api.ipify.org?format=json',
            'https://ipapi.co/json/',
            'http://httpbin.org/user-agent'
        ])
        
        self.timeout = self.config.get('timeout', 15)
        self.max_retries = self.config.get('max_retries', 2)
        
        # 匿名等級定義
        self.anonymity_levels = {
            'elite': {
                'name': '高匿代理 (Elite)',
                'description': '完全隱藏原始IP，不洩露代理信息',
                'score': 100
            },
            'anonymous': {
                'name': '匿名代理 (Anonymous)',
                'description': '隱藏原始IP，但會標識使用代理',
                'score': 80
            },
            'transparent': {
                'name': '透明代理 (Transparent)',
                'description': '會洩露原始IP和代理信息',
                'score': 40
            }
        }
        
        # 敏感標頭列表
        self.sensitive_headers = [
            'X-Forwarded-For',
            'X-Real-IP',
            'X-Originating-IP',
            'X-Remote-IP',
            'X-Remote-Addr',
            'X-Client-IP',
            'CF-Connecting-IP',
            'True-Client-IP',
            'X-Forwarded-Proto',
            'X-Proxy-ID',
            'Via',
            'Forwarded'
        ]
        
        # 代理檢測標頭
        self.proxy_headers = [
            'Proxy-Connection',
            'Proxy-Authenticate',
            'Proxy-Authorization'
        ]
    
    async def test_anonymity(self, proxy: Any) -> Dict[str, Any]:
        """
        測試代理匿名性
        
        Args:
            proxy: 代理對象
            
        Returns:
            Dict: 匿名性測試結果
        """
        try:
            self.logger.info(f"開始測試代理 {proxy.ip}:{proxy.port} 的匿名性")
            
            # 1. 獲取真實IP（無代理）
            real_ip = await self._get_real_ip()
            
            # 2. 通過代理獲取信息
            proxy_info = await self._get_proxy_info(proxy)
            
            # 3. 分析匿名性
            anonymity_analysis = self._analyze_anonymity(real_ip, proxy_info)
            
            # 4. 檢測標頭洩露
            header_leakage = self._check_header_leakage(proxy_info)
            
            # 5. 檢測代理特徵
            proxy_detection = self._detect_proxy_features(proxy_info)
            
            # 6. 綜合評估
            overall_assessment = self._assess_overall_anonymity(
                anonymity_analysis, header_leakage, proxy_detection
            )
            
            result = {
                'success': True,
                'proxy': f"{proxy.ip}:{proxy.port}",
                'real_ip': real_ip,
                'proxy_info': proxy_info,
                'anonymity_analysis': anonymity_analysis,
                'header_leakage': header_leakage,
                'proxy_detection': proxy_detection,
                'overall_assessment': overall_assessment,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(
                f"匿名性測試完成 - 代理: {proxy.ip}:{proxy.port}, "
                f"等級: {overall_assessment['level']}, "
                f"評分: {overall_assessment['score']}/100"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"匿名性測試失敗: {e}")
            return {
                'success': False,
                'error': str(e),
                'proxy': f"{proxy.ip}:{proxy.port}",
                'overall_assessment': {
                    'level': 'unknown',
                    'score': 0,
                    'description': '測試失敗'
                },
                'timestamp': datetime.now().isoformat()
            }
    
    async def _get_real_ip(self) -> Optional[str]:
        """
        獲取真實IP地址
        
        Returns:
            str: 真實IP地址
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
                        self.logger.warning(f"真實IP查詢服務 {service} 失敗: {e}")
                        continue
                
                return None
                
        except Exception as e:
            self.logger.error(f"獲取真實IP失敗: {e}")
            return None
    
    async def _get_proxy_info(self, proxy: Any) -> Dict[str, Any]:
        """
        通過代理獲取信息
        
        Args:
            proxy: 代理對象
            
        Returns:
            Dict: 代理信息
        """
        try:
            proxy_url = self._build_proxy_url(proxy)
            
            proxy_info = {
                'proxy_ip': None,
                'headers': {},
                'geo_info': {},
                'proxy_detection': {},
                'test_results': []
            }
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                # 測試多個URL
                for test_url in self.anonymity_test_urls:
                    try:
                        test_result = await self._test_proxy_endpoint(
                            session, test_url, proxy_url
                        )
                        
                        if test_result['success']:
                            proxy_info['test_results'].append(test_result)
                            
                            # 提取IP信息
                            if not proxy_info['proxy_ip'] and 'ip' in test_result:
                                proxy_info['proxy_ip'] = test_result['ip']
                            
                            # 合併標頭信息
                            if 'headers' in test_result:
                                proxy_info['headers'].update(test_result['headers'])
                            
                            # 合併地理位置信息
                            if 'geo_info' in test_result:
                                proxy_info['geo_info'].update(test_result['geo_info'])
                            
                            # 合併代理檢測信息
                            if 'proxy_detection' in test_result:
                                proxy_info['proxy_detection'].update(test_result['proxy_detection'])
                        
                    except Exception as e:
                        self.logger.warning(f"代理信息獲取失敗 {test_url}: {e}")
                        continue
            
            return proxy_info
            
        except Exception as e:
            self.logger.error(f"獲取代理信息失敗: {e}")
            return proxy_info
        finally:
            await connector.close()
    
    async def _test_proxy_endpoint(self, session: aiohttp.ClientSession, 
                                  url: str, proxy_url: str) -> Dict[str, Any]:
        """
        測試代理端點
        
        Args:
            session: HTTP會話
            url: 測試URL
            proxy_url: 代理URL
            
        Returns:
            Dict: 測試結果
        """
        try:
            start_time = datetime.now()
            
            async with session.get(url, proxy=proxy_url, timeout=10) as response:
                response_text = await response.text()
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                
                result = {
                    'success': response.status == 200,
                    'url': url,
                    'status_code': response.status,
                    'response_time': round(response_time, 2),
                    'response_size': len(response_text)
                }
                
                # 解析響應數據
                if 'httpbin.org/headers' in url:
                    result.update(self._parse_httpbin_headers(response_text))
                
                elif 'cloudflare.com/cdn-cgi/trace' in url:
                    result.update(self._parse_cloudflare_trace(response_text))
                
                elif 'api.ipify.org' in url:
                    result.update(self._parse_ipify_response(response_text))
                
                elif 'ipapi.co' in url:
                    result.update(self._parse_ipapi_response(response_text))
                
                elif 'httpbin.org/user-agent' in url:
                    result.update(self._parse_user_agent_response(response_text))
                
                return result
                
        except Exception as e:
            return {
                'success': False,
                'url': url,
                'error': str(e)
            }
    
    def _parse_httpbin_headers(self, response_text: str) -> Dict[str, Any]:
        """
        解析httpbin標頭響應
        
        Args:
            response_text: 響應文本
            
        Returns:
            Dict: 解析結果
        """
        try:
            data = json.loads(response_text)
            headers = data.get('headers', {})
            
            return {
                'headers': headers,
                'ip': headers.get('X-Forwarded-For', '').split(',')[0].strip(),
                'user_agent': headers.get('User-Agent', ''),
                'proxy_detection': {
                    'has_proxy_headers': any(header in headers for header in self.proxy_headers),
                    'has_sensitive_headers': any(header in headers for header in self.sensitive_headers)
                }
            }
        except Exception as e:
            self.logger.warning(f"解析httpbin標頭失敗: {e}")
            return {}
    
    def _parse_cloudflare_trace(self, response_text: str) -> Dict[str, Any]:
        """
        解析Cloudflare trace響應
        
        Args:
            response_text: 響應文本
            
        Returns:
            Dict: 解析結果
        """
        try:
            lines = response_text.strip().split('\n')
            trace_data = {}
            
            for line in lines:
                if '=' in line:
                    key, value = line.split('=', 1)
                    trace_data[key.strip()] = value.strip()
            
            return {
                'ip': trace_data.get('ip', ''),
                'user_agent': trace_data.get('uag', ''),
                'geo_info': {
                    'country': trace_data.get('loc', '').split(',')[0] if trace_data.get('loc') else '',
                    'timezone': trace_data.get('timezone', ''),
                    'colo': trace_data.get('colo', '')
                }
            }
        except Exception as e:
            self.logger.warning(f"解析Cloudflare trace失敗: {e}")
            return {}
    
    def _parse_ipify_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析IPify響應
        
        Args:
            response_text: 響應文本
            
        Returns:
            Dict: 解析結果
        """
        try:
            data = json.loads(response_text)
            return {
                'ip': data.get('ip', '')
            }
        except Exception as e:
            self.logger.warning(f"解析IPify響應失敗: {e}")
            return {}
    
    def _parse_ipapi_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析IPAPI響應
        
        Args:
            response_text: 響應文本
            
        Returns:
            Dict: 解析結果
        """
        try:
            data = json.loads(response_text)
            return {
                'ip': data.get('ip', ''),
                'geo_info': {
                    'country': data.get('country_name', ''),
                    'country_code': data.get('country', ''),
                    'region': data.get('region', ''),
                    'city': data.get('city', ''),
                    'latitude': data.get('latitude', 0),
                    'longitude': data.get('longitude', 0),
                    'timezone': data.get('timezone', ''),
                    'isp': data.get('org', ''),
                    'organization': data.get('org', '')
                }
            }
        except Exception as e:
            self.logger.warning(f"解析IPAPI響應失敗: {e}")
            return {}
    
    def _parse_user_agent_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析User-Agent響應
        
        Args:
            response_text: 響應文本
            
        Returns:
            Dict: 解析結果
        """
        try:
            data = json.loads(response_text)
            return {
                'user_agent': data.get('user-agent', '')
            }
        except Exception as e:
            self.logger.warning(f"解析User-Agent響應失敗: {e}")
            return {}
    
    def _analyze_anonymity(self, real_ip: Optional[str], proxy_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析匿名性
        
        Args:
            real_ip: 真實IP
            proxy_info: 代理信息
            
        Returns:
            Dict: 匿名性分析
        """
        analysis = {
            'ip_hidden': False,
            'ip_leakage': False,
            'proxy_ip_detected': False,
            'real_ip_exposed': False,
            'anonymity_score': 0
        }
        
        try:
            proxy_ip = proxy_info.get('proxy_ip', '')
            
            # 檢查IP是否被隱藏
            if real_ip and proxy_ip:
                analysis['ip_hidden'] = (real_ip != proxy_ip)
                analysis['ip_leakage'] = (real_ip == proxy_ip)
                analysis['real_ip_exposed'] = (real_ip == proxy_ip)
            
            # 檢查代理IP是否被檢測到
            analysis['proxy_ip_detected'] = bool(proxy_ip)
            
            # 計算匿名性評分
            score = 0
            
            if analysis['ip_hidden']:
                score += 60  # IP隱藏是關鍵
            
            if not analysis['real_ip_exposed']:
                score += 20  # 沒有真實IP洩露
            
            if analysis['proxy_ip_detected']:
                score += 20  # 能檢測到代理IP
            
            analysis['anonymity_score'] = min(score, 100)
            
        except Exception as e:
            self.logger.error(f"匿名性分析失敗: {e}")
        
        return analysis
    
    def _check_header_leakage(self, proxy_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        檢查標頭洩露
        
        Args:
            proxy_info: 代理信息
            
        Returns:
            Dict: 標頭洩露檢查結果
        """
        leakage_check = {
            'sensitive_headers_found': [],
            'proxy_headers_found': [],
            'header_leakage_score': 100,
            'risk_level': 'low'
        }
        
        try:
            headers = proxy_info.get('headers', {})
            
            # 檢查敏感標頭
            for header in self.sensitive_headers:
                if header in headers or header.lower() in headers:
                    leakage_check['sensitive_headers_found'].append({
                        'header': header,
                        'value': headers.get(header, headers.get(header.lower(), ''))
                    })
            
            # 檢查代理標頭
            for header in self.proxy_headers:
                if header in headers or header.lower() in headers:
                    leakage_check['proxy_headers_found'].append({
                        'header': header,
                        'value': headers.get(header, headers.get(header.lower(), ''))
                    })
            
            # 計算洩露評分
            total_leaks = len(leakage_check['sensitive_headers_found']) + len(leakage_check['proxy_headers_found'])
            
            if total_leaks == 0:
                leakage_check['header_leakage_score'] = 100
                leakage_check['risk_level'] = 'low'
            elif total_leaks <= 2:
                leakage_check['header_leakage_score'] = 80
                leakage_check['risk_level'] = 'medium'
            elif total_leaks <= 4:
                leakage_check['header_leakage_score'] = 60
                leakage_check['risk_level'] = 'high'
            else:
                leakage_check['header_leakage_score'] = 40
                leakage_check['risk_level'] = 'critical'
            
        except Exception as e:
            self.logger.error(f"標頭洩露檢查失敗: {e}")
            leakage_check['error'] = str(e)
        
        return leakage_check
    
    def _detect_proxy_features(self, proxy_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        檢測代理特徵
        
        Args:
            proxy_info: 代理信息
            
        Returns:
            Dict: 代理特徵檢測結果
        """
        proxy_features = {
            'is_proxy_detected': False,
            'proxy_type_indicators': [],
            'proxy_software_signatures': [],
            'anonymity_features': [],
            'proxy_detection_score': 0
        }
        
        try:
            headers = proxy_info.get('headers', {})
            proxy_detection = proxy_info.get('proxy_detection', {})
            
            # 檢測代理標識
            if proxy_detection.get('has_proxy_headers', False):
                proxy_features['is_proxy_detected'] = True
                proxy_features['proxy_type_indicators'].append('Proxy headers detected')
            
            if proxy_detection.get('has_sensitive_headers', False):
                proxy_features['is_proxy_detected'] = True
                proxy_features['proxy_type_indicators'].append('Sensitive headers detected')
            
            # 檢測軟件簽名
            server_header = headers.get('Server', '')
            via_header = headers.get('Via', '')
            
            if 'squid' in server_header.lower():
                proxy_features['proxy_software_signatures'].append('Squid proxy detected')
            
            if 'nginx' in server_header.lower():
                proxy_features['proxy_software_signatures'].append('Nginx proxy detected')
            
            if 'via' in headers:
                proxy_features['proxy_software_signatures'].append(f'Via header: {via_header}')
            
            # 評估匿名性特徵
            if not proxy_features['is_proxy_detected']:
                proxy_features['anonymity_features'].append('No proxy indicators found')
                proxy_features['proxy_detection_score'] = 100
            else:
                proxy_features['anonymity_features'].append('Proxy indicators detected')
                
                # 根據檢測到的特徵評分
                score_penalty = 0
                
                if proxy_features['proxy_type_indicators']:
                    score_penalty += 30
                
                if proxy_features['proxy_software_signatures']:
                    score_penalty += 20
                
                proxy_features['proxy_detection_score'] = max(0, 100 - score_penalty)
            
        except Exception as e:
            self.logger.error(f"代理特徵檢測失敗: {e}")
            proxy_features['error'] = str(e)
        
        return proxy_features
    
    def _assess_overall_anonymity(self, anonymity_analysis: Dict[str, Any],
                                 header_leakage: Dict[str, Any],
                                 proxy_detection: Dict[str, Any]) -> Dict[str, Any]:
        """
        綜合評估匿名性
        
        Args:
            anonymity_analysis: 匿名性分析
            header_leakage: 標頭洩露檢查
            proxy_detection: 代理特徵檢測
            
        Returns:
            Dict: 綜合評估結果
        """
        assessment = {
            'level': 'unknown',
            'score': 0,
            'description': '評估失敗',
            'recommendations': []
        }
        
        try:
            # 計算綜合評分
            scores = [
                anonymity_analysis.get('anonymity_score', 0),
                header_leakage.get('header_leakage_score', 0),
                proxy_detection.get('proxy_detection_score', 0)
            ]
            
            # 使用加權平均
            weights = [0.5, 0.3, 0.2]  # 匿名性分析權重最高
            weighted_score = sum(score * weight for score, weight in zip(scores, weights))
            
            assessment['score'] = round(weighted_score, 1)
            
            # 確定匿名等級
            if assessment['score'] >= 90:
                assessment['level'] = 'elite'
                assessment['description'] = '高匿代理 - 極佳的匿名性'
            elif assessment['score'] >= 75:
                assessment['level'] = 'anonymous'
                assessment['description'] = '匿名代理 - 良好的匿名性'
            elif assessment['score'] >= 50:
                assessment['level'] = 'transparent'
                assessment['description'] = '透明代理 - 基本的匿名性'
            else:
                assessment['level'] = 'poor'
                assessment['description'] = '低匿名性 - 存在嚴重洩露風險'
            
            # 生成建議
            assessment['recommendations'] = self._generate_anonymity_recommendations(
                anonymity_analysis, header_leakage, proxy_detection, assessment
            )
            
        except Exception as e:
            self.logger.error(f"匿名性綜合評估失敗: {e}")
            assessment['error'] = str(e)
        
        return assessment
    
    def _generate_anonymity_recommendations(self, anonymity_analysis: Dict[str, Any],
                                           header_leakage: Dict[str, Any],
                                           proxy_detection: Dict[str, Any],
                                           overall_assessment: Dict[str, Any]) -> List[str]:
        """
        生成匿名性改進建議
        
        Args:
            anonymity_analysis: 匿名性分析
            header_leakage: 標頭洩露檢查
            proxy_detection: 代理特徵檢測
            overall_assessment: 綜合評估
            
        Returns:
            List: 改進建議列表
        """
        recommendations = []
        
        # 基於匿名性分析的建議
        if not anonymity_analysis.get('ip_hidden', False):
            recommendations.append("⚠️ 代理未能隱藏真實IP地址，建議更換代理服務器")
        
        if anonymity_analysis.get('real_ip_exposed', False):
            recommendations.append("⚠️ 真實IP地址存在洩露風險，請檢查代理配置")
        
        # 基於標頭洩露的建議
        if header_leakage.get('sensitive_headers_found'):
            recommendations.append(f"⚠️ 發現 {len(header_leakage['sensitive_headers_found'])} 個敏感標頭洩露")
        
        if header_leakage.get('proxy_headers_found'):
            recommendations.append(f"⚠️ 發現 {len(header_leakage['proxy_headers_found'])} 個代理標頭")
        
        # 基於代理特徵檢測的建議
        if proxy_detection.get('is_proxy_detected', False):
            recommendations.append("⚠️ 代理服務器特徵被檢測到，匿名性較低")
        
        # 基於綜合評分的建議
        if overall_assessment['score'] < 50:
            recommendations.append("🔴 匿名性評分過低，強烈建議更換代理服務")
        elif overall_assessment['score'] < 75:
            recommendations.append("🟡 匿名性有待改善，可考慮優化代理配置")
        else:
            recommendations.append("✅ 匿名性良好，當前代理配置合理")
        
        # 通用建議
        if not recommendations:
            recommendations.append("✅ 當前代理匿名性配置良好，無需特別改進")
        
        return recommendations
    
    def _build_proxy_url(self, proxy: Any) -> str:
        """
        構建代理URL
        
        Args:
            proxy: 代理對象
            
        Returns:
            str: 代理URL
        """
        protocol = getattr(proxy, 'protocol', 'http')
        username = getattr(proxy, 'username', None)
        password = getattr(proxy, 'password', None)
        
        if username and password:
            return f"{protocol}://{username}:{password}@{proxy.ip}:{proxy.port}"
        else:
            return f"{protocol}://{proxy.ip}:{proxy.port}"