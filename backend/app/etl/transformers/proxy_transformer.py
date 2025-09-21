"""
數據轉換器模組
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.schemas.proxy import ProtocolType, AnonymityLevel
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProxyDataTransformer:
    """代理數據轉換器"""
    
    @staticmethod
    def normalize_proxy_data(proxy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        標準化代理數據
        
        Args:
            proxy_data: 原始代理數據
            
        Returns:
            Dict[str, Any]: 標準化後的代理數據
        """
        normalized = {}
        
        # IP地址標準化
        normalized["ip"] = ProxyDataTransformer._normalize_ip(proxy_data.get("ip", ""))
        
        # 端口標準化
        normalized["port"] = ProxyDataTransformer._normalize_port(proxy_data.get("port"))
        
        # 協議標準化
        normalized["protocol"] = ProxyDataTransformer._normalize_protocol(
            proxy_data.get("protocol", "")
        )
        
        # 匿名級別標準化
        normalized["anonymity_level"] = ProxyDataTransformer._normalize_anonymity_level(
            proxy_data.get("anonymity_level", "")
        )
        
        # 國家標準化
        normalized["country"] = ProxyDataTransformer._normalize_country(
            proxy_data.get("country", "")
        )
        
        # 城市標準化
        normalized["city"] = ProxyDataTransformer._normalize_city(
            proxy_data.get("city", "")
        )
        
        # 速度標準化
        normalized["speed"] = ProxyDataTransformer._normalize_speed(
            proxy_data.get("speed")
        )
        
        # 可靠性標準化
        normalized["reliability"] = ProxyDataTransformer._normalize_reliability(
            proxy_data.get("reliability")
        )
        
        # 來源
        normalized["source"] = proxy_data.get("source", "unknown")
        
        # 驗證時間
        normalized["last_verified"] = proxy_data.get("last_verified", datetime.utcnow())
        
        return normalized
    
    @staticmethod
    def _normalize_ip(ip: str) -> Optional[str]:
        """
        標準化IP地址
        
        Args:
            ip: IP地址字符串
            
        Returns:
            Optional[str]: 標準化的IP地址或None
        """
        if not ip:
            return None
        
        import ipaddress
        
        try:
            # 驗證IP地址格式
            ip_obj = ipaddress.ip_address(ip.strip())
            return str(ip_obj)
        except ValueError:
            logger.warning(f"無效的IP地址: {ip}")
            return None
    
    @staticmethod
    def _normalize_port(port: Any) -> Optional[int]:
        """
        標準化端口
        
        Args:
            port: 端口值
            
        Returns:
            Optional[int]: 標準化的端口或None
        """
        if not port:
            return None
        
        try:
            port_int = int(port)
            if 1 <= port_int <= 65535:
                return port_int
            else:
                logger.warning(f"端口超出有效範圍: {port}")
                return None
        except (ValueError, TypeError):
            logger.warning(f"無效的端口: {port}")
            return None
    
    @staticmethod
    def _normalize_protocol(protocol: str) -> str:
        """
        標準化協議類型
        
        Args:
            protocol: 協議字符串
            
        Returns:
            str: 標準化的協議類型
        """
        if not protocol:
            return ProtocolType.HTTP.value
        
        protocol_lower = protocol.lower().strip()
        
        # 映射常見的協議名稱
        protocol_map = {
            "http": ProtocolType.HTTP.value,
            "https": ProtocolType.HTTPS.value,
            "ssl": ProtocolType.HTTPS.value,
            "socks4": ProtocolType.SOCKS4.value,
            "socks5": ProtocolType.SOCKS5.value,
            "socks": ProtocolType.SOCKS5.value,
        }
        
        return protocol_map.get(protocol_lower, ProtocolType.HTTP.value)
    
    @staticmethod
    def _normalize_anonymity_level(anonymity: str) -> str:
        """
        標準化匿名級別
        
        Args:
            anonymity: 匿名級別字符串
            
        Returns:
            str: 標準化的匿名級別
        """
        if not anonymity:
            return None
        
        anonymity_lower = anonymity.lower().strip()
        
        # 映射常見的匿名級別
        anonymity_map = {
            "elite": AnonymityLevel.ELITE.value,
            "high": AnonymityLevel.ELITE.value,
            "anonymous": AnonymityLevel.ANONYMOUS.value,
            "medium": AnonymityLevel.ANONYMOUS.value,
            "transparent": AnonymityLevel.TRANSPARENT.value,
            "low": AnonymityLevel.TRANSPARENT.value,
        }
        
        # 檢查是否包含關鍵詞
        for key, value in anonymity_map.items():
            if key in anonymity_lower:
                return value
        
        return None
    
    @staticmethod
    def _normalize_country(country: str) -> Optional[str]:
        """
        標準化國家名稱
        
        Args:
            country: 國家名稱
            
        Returns:
            Optional[str]: 標準化的國家代碼或名稱
        """
        if not country:
            return None
        
        country_upper = country.upper().strip()
        
        # 國家代碼映射（部分示例）
        country_map = {
            "CN": "China",
            "US": "United States",
            "GB": "United Kingdom",
            "JP": "Japan",
            "KR": "South Korea",
            "DE": "Germany",
            "FR": "France",
            "CA": "Canada",
            "AU": "Australia",
            "RU": "Russia",
        }
        
        # 如果已經是國家代碼，返回對應的國家名稱
        if len(country_upper) == 2 and country_upper in country_map:
            return country_map[country_upper]
        
        # 否則返回原始名稱（清理格式）
        return country.strip()
    
    @staticmethod
    def _normalize_city(city: str) -> Optional[str]:
        """
        標準化城市名稱
        
        Args:
            city: 城市名稱
            
        Returns:
            Optional[str]: 標準化的城市名稱
        """
        if not city:
            return None
        
        return city.strip()
    
    @staticmethod
    def _normalize_speed(speed: Any) -> Optional[float]:
        """
        標準化速度值
        
        Args:
            speed: 速度值
            
        Returns:
            Optional[float]: 標準化的速度值（毫秒）
        """
        if speed is None:
            return None
        
        try:
            speed_value = float(speed)
            
            # 如果速度值看起來像是秒，轉換為毫秒
            if speed_value < 100:
                speed_value = speed_value * 1000
            
            return speed_value
            
        except (ValueError, TypeError):
            logger.warning(f"無效的速度值: {speed}")
            return None
    
    @staticmethod
    def _normalize_reliability(reliability: Any) -> Optional[float]:
        """
        標準化可靠性值
        
        Args:
            reliability: 可靠性值
            
        Returns:
            Optional[float]: 標準化的可靠性值（0-1之間）
        """
        if reliability is None:
            return None
        
        try:
            reliability_value = float(reliability)
            
            # 如果可靠性是百分比，轉換為小數
            if reliability_value > 1:
                reliability_value = reliability_value / 100.0
            
            # 確保在有效範圍內
            if 0 <= reliability_value <= 1:
                return reliability_value
            else:
                logger.warning(f"可靠性值超出有效範圍: {reliability}")
                return None
                
        except (ValueError, TypeError):
            logger.warning(f"無效的可靠性值: {reliability}")
            return None
    
    @staticmethod
    def validate_proxy_data(proxy_data: Dict[str, Any]) -> bool:
        """
        驗證代理數據的有效性
        
        Args:
            proxy_data: 代理數據
            
        Returns:
            bool: 是否有效
        """
        # 必需字段驗證
        required_fields = ["ip", "port"]
        for field in required_fields:
            if not proxy_data.get(field):
                logger.warning(f"代理數據缺少必需字段: {field}")
                return False
        
        # IP地址驗證
        ip = proxy_data.get("ip")
        if not ProxyDataTransformer._normalize_ip(ip):
            return False
        
        # 端口驗證
        port = proxy_data.get("port")
        if not ProxyDataTransformer._normalize_port(port):
            return False
        
        # 協議驗證
        protocol = proxy_data.get("protocol", "")
        valid_protocols = [p.value for p in ProtocolType]
        if protocol not in valid_protocols:
            logger.warning(f"無效的協議類型: {protocol}")
            return False
        
        return True
    
    @staticmethod
    def transform_batch(proxy_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量轉換代理數據
        
        Args:
            proxy_data_list: 代理數據列表
            
        Returns:
            List[Dict[str, Any]]: 轉換後的代理數據列表
        """
        transformed_list = []
        
        for proxy_data in proxy_data_list:
            try:
                # 標準化數據
                normalized = ProxyDataTransformer.normalize_proxy_data(proxy_data)
                
                # 驗證數據
                if ProxyDataTransformer.validate_proxy_data(normalized):
                    transformed_list.append(normalized)
                else:
                    logger.warning(f"代理數據驗證失敗: {proxy_data}")
                    
            except Exception as e:
                logger.error(f"轉換代理數據失敗: {proxy_data}, 錯誤: {e}")
                continue
        
        logger.info(f"批量轉換完成: {len(proxy_data_list)} -> {len(transformed_list)}")
        return transformed_list


class ProxyDataFilter:
    """代理數據過濾器"""
    
    @staticmethod
    def filter_by_criteria(
        proxy_data_list: List[Dict[str, Any]],
        min_speed: Optional[float] = None,
        min_reliability: Optional[float] = None,
        allowed_countries: Optional[List[str]] = None,
        allowed_protocols: Optional[List[str]] = None,
        min_anonymity: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        根據條件過濾代理數據
        
        Args:
            proxy_data_list: 代理數據列表
            min_speed: 最小速度要求（毫秒）
            min_reliability: 最小可靠性要求（0-1）
            allowed_countries: 允許的國家列表
            allowed_protocols: 允許的協議列表
            min_anonymity: 最小匿名級別
            
        Returns:
            List[Dict[str, Any]]: 過濾後的代理數據列表
        """
        filtered_list = []
        
        for proxy_data in proxy_data_list:
            try:
                # 速度過濾
                if min_speed is not None:
                    speed = proxy_data.get("speed")
                    if speed is not None and speed > min_speed:
                        continue
                
                # 可靠性過濾
                if min_reliability is not None:
                    reliability = proxy_data.get("reliability")
                    if reliability is not None and reliability < min_reliability:
                        continue
                
                # 國家過濾
                if allowed_countries:
                    country = proxy_data.get("country")
                    if country and country not in allowed_countries:
                        continue
                
                # 協議過濾
                if allowed_protocols:
                    protocol = proxy_data.get("protocol")
                    if protocol and protocol not in allowed_protocols:
                        continue
                
                # 匿名級別過濾
                if min_anonymity:
                    anonymity = proxy_data.get("anonymity_level", "unknown")
                    if not ProxyDataFilter._compare_anonymity_level(anonymity, min_anonymity):
                        continue
                
                filtered_list.append(proxy_data)
                
            except Exception as e:
                logger.error(f"過濾代理數據失敗: {proxy_data}, 錯誤: {e}")
                continue
        
        logger.info(f"過濾完成: {len(proxy_data_list)} -> {len(filtered_list)}")
        return filtered_list
    
    @staticmethod
    def _compare_anonymity_level(current: str, required: str) -> bool:
        """
        比較匿名級別
        
        Args:
            current: 當前匿名級別
            required: 要求的匿名級別
            
        Returns:
            bool: 是否滿足要求
        """
        # 匿名級別的優先級
        anonymity_priority = {
            "elite": 3,
            "anonymous": 2,
            "transparent": 1,
            "unknown": 0,
        }
        
        current_priority = anonymity_priority.get(current.lower(), 0)
        required_priority = anonymity_priority.get(required.lower(), 0)
        
        return current_priority >= required_priority