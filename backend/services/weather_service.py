"""
Weather Service - Lấy thông tin thời tiết thực tế
"""

import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

class WeatherService:
    """Service để lấy thông tin thời tiết từ các API"""
    
    def __init__(self):
        from config.settings import settings
        self.api_key = settings.openweather_api_key or ''
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.cache = {}
        self.cache_duration = timedelta(minutes=30)  # Cache 30 phút
        
    def get_weather(self, city: str, country_code: str = "VN") -> Dict[str, Any]:
        """Lấy thông tin thời tiết cho thành phố"""
        try:
            # Kiểm tra cache trước
            cache_key = f"{city}_{country_code}"
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if datetime.now() - cached_data['timestamp'] < self.cache_duration:
                    logger.info(f"Using cached weather data for {city}")
                    return cached_data['data']
            
            # Nếu không có API key, trả về thông báo
            if not self.api_key:
                return {
                    'success': False,
                    'error': 'Weather API key not configured',
                    'message': 'Em chưa được cấu hình để lấy thông tin thời tiết thực tế.'
                }
            
            # Gọi API
            url = f"{self.base_url}/weather"
            params = {
                'q': f"{city},{country_code}",
                'appid': self.api_key,
                'units': 'metric',  # Độ C
                'lang': 'vi'  # Tiếng Việt
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Format dữ liệu
                weather_info = {
                    'success': True,
                    'city': data['name'],
                    'country': data['sys']['country'],
                    'temperature': round(data['main']['temp']),
                    'feels_like': round(data['main']['feels_like']),
                    'humidity': data['main']['humidity'],
                    'pressure': data['main']['pressure'],
                    'description': data['weather'][0]['description'],
                    'wind_speed': round(data['wind']['speed'] * 3.6, 1),  # m/s to km/h
                    'wind_direction': data['wind'].get('deg', 0),
                    'visibility': data.get('visibility', 0) / 1000,  # m to km
                    'timestamp': datetime.now().isoformat()
                }
                
                # Cache kết quả
                self.cache[cache_key] = {
                    'data': weather_info,
                    'timestamp': datetime.now()
                }
                
                return weather_info
            else:
                logger.error(f"Weather API error: {response.status_code}")
                return {
                    'success': False,
                    'error': f'API error: {response.status_code}',
                    'message': 'Em không thể lấy thông tin thời tiết lúc này.'
                }
                
        except requests.exceptions.Timeout:
            logger.error("Weather API timeout")
            return {
                'success': False,
                'error': 'API timeout',
                'message': 'Em không thể kết nối với dịch vụ thời tiết.'
            }
        except Exception as e:
            logger.error(f"Weather service error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Em gặp lỗi khi lấy thông tin thời tiết.'
            }
    
    def get_weather_forecast(self, city: str, country_code: str = "VN", days: int = 5) -> Dict[str, Any]:
        """Lấy dự báo thời tiết"""
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'error': 'Weather API key not configured',
                    'message': 'Em chưa được cấu hình để lấy dự báo thời tiết.'
                }
            
            url = f"{self.base_url}/forecast"
            params = {
                'q': f"{city},{country_code}",
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'vi',
                'cnt': days * 8  # 8 forecasts per day
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Process forecast data
                forecasts = []
                for item in data['list'][:days * 8:8]:  # Take one forecast per day
                    forecast = {
                        'date': datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d'),
                        'temperature': round(item['main']['temp']),
                        'description': item['weather'][0]['description'],
                        'humidity': item['main']['humidity'],
                        'wind_speed': round(item['wind']['speed'] * 3.6, 1)
                    }
                    forecasts.append(forecast)
                
                return {
                    'success': True,
                    'city': data['city']['name'],
                    'country': data['city']['country'],
                    'forecasts': forecasts,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': f'API error: {response.status_code}',
                    'message': 'Em không thể lấy dự báo thời tiết.'
                }
                
        except Exception as e:
            logger.error(f"Weather forecast error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Em gặp lỗi khi lấy dự báo thời tiết.'
            }
    
    def format_weather_response(self, weather_data: Dict[str, Any]) -> str:
        """Format thông tin thời tiết thành text"""
        if not weather_data.get('success'):
            return weather_data.get('message', 'Em không thể lấy thông tin thời tiết.')
        
        city = weather_data['city']
        temp = weather_data['temperature']
        description = weather_data['description']
        humidity = weather_data['humidity']
        wind_speed = weather_data['wind_speed']
        
        response = f"Em đã kiểm tra thời tiết cho anh. Hiện tại ở {city} đang {description} với nhiệt độ {temp}°C. "
        response += f"Độ ẩm {humidity}% và gió {wind_speed} km/h. "
        
        # Thêm gợi ý
        if temp < 20:
            response += "Anh nên mang áo ấm nhé!"
        elif temp > 30:
            response += "Trời nóng, anh nhớ uống nhiều nước!"
        elif humidity > 80:
            response += "Độ ẩm cao, anh có thể mang ô phòng khi trời mưa."
        
        return response

# Singleton instance
weather_service = WeatherService()
