"""
Enhanced AI Service - Xử lý Ollama AI provider với fallback
Đảm bảo service vẫn hoạt động khi AI không khả dụng
"""

import asyncio
import logging
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import requests
import re

from config.settings import settings
from services.weather_service import weather_service
from services.news_service import news_service

logger = logging.getLogger(__name__)

class AIProvider(Enum):
    OLLAMA_GEMMA3N = "ollama_gemma3n" 
    OLLAMA_GEMMA2 = "ollama_gemma2"
    FALLBACK = "fallback"

class AIServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"  # Một số provider không khả dụng
    OFFLINE = "offline"    # Tất cả provider offline

class EnhancedAIService:
    """Enhanced AI Service với fallback và resilience patterns"""
    
    def __init__(self):
        self.ollama_gemma3n_client = None
        self.ollama_gemma2_client = None
        self.current_provider = AIProvider.FALLBACK
        self.provider_status = {}
        self.last_health_check = {}
        self.health_check_interval = 300  # 5 minutes
        
        # Fallback configuration
        self.fallback_enabled = settings.auto_fallback
        self.fallback_messages = self._load_fallback_messages()
        
        # Initialize providers
        self._initialize_providers()
        self._determine_active_provider()
    
    def _initialize_providers(self):
        """Khởi tạo tất cả AI providers"""
        logger.info("Initializing AI providers...")
        
        # Initialize Ollama clients
        self._initialize_ollama_clients()
        
        # Update provider status
        self._update_provider_status()
    
    def _initialize_ollama_clients(self):
        """Khởi tạo Ollama clients cho cả 2 models"""
        try:
            # Import here để tránh lỗi nếu thư viện không có
            try:
                from langchain_ollama import Ollama
            except ImportError:
                # Try alternative import for newer versions
                from langchain_community.llms import Ollama
            
            # Kiểm tra Ollama server trước
            if not self._check_ollama_server():
                logger.warning("Ollama server not available during initialization")
                self.ollama_gemma3n_client = None
                self.ollama_gemma2_client = None
                return
            
            # Initialize Gemma3n client
            try:
                self.ollama_gemma3n_client = Ollama(
                    model=settings.ollama_model,
                    base_url=settings.ollama_base_url,
                    temperature=settings.temperature,
                    num_predict=settings.ollama_max_tokens or settings.max_tokens
                )
                logger.info(f"Ollama Gemma3n client initialized with model: {settings.ollama_model}")
            except Exception as e:
                logger.warning(f"Could not initialize Gemma3n client: {e}")
                self.ollama_gemma3n_client = None
            
            # Initialize Gemma2 client
            try:
                self.ollama_gemma2_client = Ollama(
                    model=settings.ollama_fallback_model,
                    base_url=settings.ollama_base_url,
                    temperature=settings.temperature,
                    num_predict=settings.ollama_max_tokens or settings.max_tokens
                )
                logger.info(f"Ollama Gemma2 client initialized with model: {settings.ollama_fallback_model}")
            except Exception as e:
                logger.warning(f"Could not initialize Gemma2 client: {e}")
                self.ollama_gemma2_client = None
            
        except ImportError as e:
            logger.error(f"Missing langchain_ollama dependency: {e}")
            self.ollama_gemma3n_client = None
            self.ollama_gemma2_client = None
        except Exception as e:
            logger.error(f"Error initializing Ollama clients: {e}")
            self.ollama_gemma3n_client = None
            self.ollama_gemma2_client = None
    
    def _check_ollama_server(self) -> bool:
        """Kiểm tra Ollama server có khả dụng không"""
        try:
            response = requests.get(
                f"{settings.ollama_base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama server check failed: {e}")
            return False
    
    def _update_provider_status(self):
        """Cập nhật trạng thái của các providers"""
        current_time = datetime.now()
        
        # Check Ollama Gemma3n
        if self.ollama_gemma3n_client and self._check_ollama_server():
            try:
                # Simple test call
                test_response = self.ollama_gemma3n_client.invoke("test")
                self.provider_status[AIProvider.OLLAMA_GEMMA3N] = AIServiceStatus.HEALTHY
            except Exception as e:
                logger.warning(f"Ollama Gemma3n health check failed: {e}")
                self.provider_status[AIProvider.OLLAMA_GEMMA3N] = AIServiceStatus.OFFLINE
        else:
            self.provider_status[AIProvider.OLLAMA_GEMMA3N] = AIServiceStatus.OFFLINE
        
        # Check Ollama Gemma2
        if self.ollama_gemma2_client and self._check_ollama_server():
            try:
                # Simple test call
                test_response = self.ollama_gemma2_client.invoke("test")
                self.provider_status[AIProvider.OLLAMA_GEMMA2] = AIServiceStatus.HEALTHY
            except Exception as e:
                logger.warning(f"Ollama Gemma2 health check failed: {e}")
                self.provider_status[AIProvider.OLLAMA_GEMMA2] = AIServiceStatus.OFFLINE
        else:
            self.provider_status[AIProvider.OLLAMA_GEMMA2] = AIServiceStatus.OFFLINE
        
        # Update last check time
        self.last_health_check = {
            provider: current_time for provider in AIProvider if provider != AIProvider.FALLBACK
        }
        
        logger.info(f"Provider status: {self.provider_status}")
    
    def _determine_active_provider(self):
        """Xác định provider đang active"""
        # Ưu tiên Gemma3n, fallback về Gemma2
        if self.is_provider_healthy(AIProvider.OLLAMA_GEMMA3N):
            self.current_provider = AIProvider.OLLAMA_GEMMA3N
            logger.info("Using Ollama Gemma3n as primary provider")
        elif self.is_provider_healthy(AIProvider.OLLAMA_GEMMA2):
            self.current_provider = AIProvider.OLLAMA_GEMMA2
            logger.info("Using Ollama Gemma2 as fallback provider")
        else:
            self.current_provider = AIProvider.FALLBACK
            logger.warning("No Ollama models available, using fallback mode")
        
        logger.info(f"Active AI provider: {self.current_provider.value}")
    
    def is_provider_healthy(self, provider: AIProvider) -> bool:
        """Kiểm tra provider có healthy không"""
        return self.provider_status.get(provider) == AIServiceStatus.HEALTHY
    
    def _should_refresh_health_check(self) -> bool:
        """Kiểm tra có cần refresh health check không"""
        if not self.last_health_check:
            return True
        
        current_time = datetime.now()
        for provider, last_check in self.last_health_check.items():
            if current_time - last_check > timedelta(seconds=self.health_check_interval):
                return True
        return False
    
    async def _refresh_health_check(self):
        """Refresh health check cho tất cả providers"""
        if self._should_refresh_health_check():
            logger.info("Refreshing provider health checks...")
            self._update_provider_status()
            self._determine_active_provider()
    
    def _load_fallback_messages(self) -> Dict[str, str]:
        """Load fallback messages từ config"""
        return {
            'default': getattr(settings, 'fallback_message', 
                "Em là Bixby! Em đã nhận được tin nhắn: '{user_input}'. "
                "Hiện tại em chưa kết nối được với AI, nhưng em sẽ sớm có thể trò chuyện thông minh hơn!"),
            'error': getattr(settings, 'error_message',
                "Em là Bixby! Xin lỗi, em gặp chút vấn đề kỹ thuật khi xử lý câu hỏi của anh. "
                "Em đã ghi nhận: '{user_input}' và sẽ cố gắng trả lời tốt hơn!")
        }
    
    def _detect_intent(self, message: str) -> Dict[str, Any]:
        """Phát hiện ý định của user message"""
        message_lower = message.lower()
        
        # Weather intent
        weather_keywords = ['thời tiết', 'nhiệt độ', 'mưa', 'nắng', 'gió', 'độ ẩm', 'nóng', 'lạnh']
        if any(keyword in message_lower for keyword in weather_keywords):
            # Extract city name
            city_patterns = [
                r'thời tiết (?:ở|tại) (.+?)(?:\s|$)',
                r'nhiệt độ (?:ở|tại) (.+?)(?:\s|$)',
                r'(.+?) (?:có|đang) (?:mưa|nắng|nóng|lạnh)'
            ]
            
            city = None
            for pattern in city_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    city = match.group(1).strip()
                    break
            
            if not city:
                city = "Hà Nội"  # Default city
            
            return {
                'intent': 'weather',
                'city': city,
                'confidence': 0.8
            }
        
        # News intent
        news_keywords = ['tin tức', 'tin mới', 'báo chí', 'thời sự', 'tin nóng', 'tin hot']
        if any(keyword in message_lower for keyword in news_keywords):
            return {
                'intent': 'news',
                'query': message,
                'confidence': 0.7
            }
        
        # General chat
        return {
            'intent': 'general',
            'confidence': 0.5
        }
    
    async def _get_real_time_data(self, intent: Dict[str, Any]) -> Optional[str]:
        """Lấy dữ liệu thời gian thực dựa trên intent"""
        try:
            if intent['intent'] == 'weather':
                city = intent.get('city', 'Hà Nội')
                weather_data = weather_service.get_weather(city)
                return weather_service.format_weather_response(weather_data)
            
            elif intent['intent'] == 'news':
                query = intent.get('query', '')
                if 'tin tức' in query.lower() or 'tin mới' in query.lower():
                    news_data = news_service.get_top_headlines()
                else:
                    news_data = news_service.search_news(query)
                return news_service.format_news_response(news_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting real-time data: {e}")
            return None
    
    def get_service_status(self) -> Dict[str, Any]:
        """Lấy trạng thái tổng quan của service"""
        healthy_providers = [
            provider.value for provider, status in self.provider_status.items() 
            if status == AIServiceStatus.HEALTHY
        ]
        
        if len(healthy_providers) >= 1:
            overall_status = AIServiceStatus.HEALTHY
        else:
            overall_status = AIServiceStatus.OFFLINE
        
        return {
            'status': overall_status.value,
            'current_provider': self.current_provider.value,
            'available_providers': healthy_providers,
            'provider_details': {p.value: s.value for p, s in self.provider_status.items()},
            'fallback_enabled': self.fallback_enabled,
            'last_health_check': {
                p.value: check_time.isoformat() 
                for p, check_time in self.last_health_check.items()
            }
        }
    
    async def generate_response(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        Generate AI response với fallback support và real-time data
        Service sẽ luôn trả về response, không bao giờ fail hoàn toàn
        """
        # Refresh health check nếu cần
        await self._refresh_health_check()
        
        # Detect intent
        intent = self._detect_intent(message)
        
        # Try to get real-time data first
        real_time_data = None
        if intent['confidence'] > 0.6:
            real_time_data = await self._get_real_time_data(intent)
        
        # Thử generate với current provider
        try:
            if self.current_provider == AIProvider.OLLAMA_GEMMA3N and self.ollama_gemma3n_client:
                response = await self._generate_ollama_response(message, real_time_data, self.ollama_gemma3n_client, **kwargs)
                return self._format_success_response(response, AIProvider.OLLAMA_GEMMA3N)
            elif self.current_provider == AIProvider.OLLAMA_GEMMA2 and self.ollama_gemma2_client:
                response = await self._generate_ollama_response(message, real_time_data, self.ollama_gemma2_client, **kwargs)
                return self._format_success_response(response, AIProvider.OLLAMA_GEMMA2)
                
        except Exception as e:
            logger.error(f"Error with {self.current_provider.value}: {e}")
            
            # Nếu auto_fallback enabled, thử provider khác
            if self.fallback_enabled:
                fallback_response = await self._try_fallback_providers(message, real_time_data, **kwargs)
                if fallback_response:
                    return fallback_response
        
        # Cuối cùng, sử dụng fallback message
        return self._generate_fallback_response(message, real_time_data, **kwargs)
    
    async def _generate_ollama_response(self, message: str, real_time_data: Optional[str] = None, client=None, **kwargs) -> str:
        """Generate response từ Ollama"""
        try:
            full_prompt = self._build_full_prompt(message, real_time_data, **kwargs)
            response = await asyncio.to_thread(client.invoke, full_prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    async def _try_fallback_providers(self, message: str, real_time_data: Optional[str] = None, **kwargs) -> Optional[Dict[str, Any]]:
        """Thử các providers khác khi current provider fail"""
        providers_to_try = []
        
        # Nếu đang dùng Gemma3n, thử Gemma2
        if self.current_provider == AIProvider.OLLAMA_GEMMA3N and self.is_provider_healthy(AIProvider.OLLAMA_GEMMA2):
            providers_to_try.append(AIProvider.OLLAMA_GEMMA2)
        
        # Nếu đang dùng Gemma2, thử Gemma3n
        elif self.current_provider == AIProvider.OLLAMA_GEMMA2 and self.is_provider_healthy(AIProvider.OLLAMA_GEMMA3N):
            providers_to_try.append(AIProvider.OLLAMA_GEMMA3N)
        
        for provider in providers_to_try:
            try:
                logger.info(f"Trying fallback provider: {provider.value}")
                
                if provider == AIProvider.OLLAMA_GEMMA3N and self.ollama_gemma3n_client:
                    response = await self._generate_ollama_response(message, real_time_data, self.ollama_gemma3n_client, **kwargs)
                    self.current_provider = provider
                    return self._format_success_response(response, provider)
                
                elif provider == AIProvider.OLLAMA_GEMMA2 and self.ollama_gemma2_client:
                    response = await self._generate_ollama_response(message, real_time_data, self.ollama_gemma2_client, **kwargs)
                    self.current_provider = provider
                    return self._format_success_response(response, provider)
                    
            except Exception as e:
                logger.warning(f"Fallback provider {provider.value} also failed: {e}")
                continue
        
        return None
    
    def _build_full_prompt(self, message: str, real_time_data: Optional[str] = None, **kwargs) -> str:
        """Xây dựng full prompt với system message và context"""
        system_prompt = getattr(settings, 'system_prompt', '')
        time_format = getattr(settings, 'time_format', '')
        
        # Add current time if configured
        if time_format:
            from datetime import datetime
            import pytz
            tz = pytz.timezone(getattr(settings, 'timezone', 'Asia/Ho_Chi_Minh'))
            current_time = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z')
            time_info = time_format.format(time=current_time)
            full_prompt = f"{system_prompt}\n\n{time_info}"
        else:
            full_prompt = system_prompt
        
        # Add real-time data if available
        if real_time_data:
            full_prompt += f"\n\nDỮ LIỆU THỰC TẾ:\n{real_time_data}\n"
        
        full_prompt += f"\n\nUser: {message}"
        
        return full_prompt
    
    def _format_success_response(self, content: str, provider: AIProvider) -> Dict[str, Any]:
        """Format successful AI response"""
        return {
            'success': True,
            'content': content,
            'provider': provider.value,
            'timestamp': datetime.now().isoformat(),
            'fallback_used': False
        }
    
    def _generate_fallback_response(self, message: str, real_time_data: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate fallback response khi tất cả AI providers fail"""
        logger.info("Using fallback response")
        
        if real_time_data:
            # Nếu có real-time data, sử dụng nó
            fallback_content = real_time_data
        else:
            # Sử dụng fallback message
            fallback_content = self.fallback_messages['default'].format(
                user_input=message[:100] + "..." if len(message) > 100 else message
            )
        
        return {
            'success': True,
            'content': fallback_content,
            'provider': 'fallback',
            'timestamp': datetime.now().isoformat(),
            'fallback_used': True,
            'original_message': message
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check endpoint cho monitoring"""
        await self._refresh_health_check()
        
        status_info = self.get_service_status()
        
        # Thêm thông tin chi tiết
        status_info.update({
            'uptime': 'calculated_elsewhere',  # App sẽ tính
            'ollama_gemma3n_configured': bool(self.ollama_gemma3n_client),
            'ollama_gemma2_configured': bool(self.ollama_gemma2_client),
            'ollama_server_reachable': self._check_ollama_server(),
            'ollama_primary_model': settings.ollama_model,
            'ollama_fallback_model': settings.ollama_fallback_model,
            'weather_service_available': bool(weather_service.api_key),
            'news_service_available': bool(news_service.api_key)
        })
        
        return status_info

# Singleton instance
enhanced_ai_service = EnhancedAIService()

# Helper functions để sử dụng trong các endpoints khác
async def get_ai_response(message: str, **kwargs) -> Dict[str, Any]:
    """Helper function để generate AI response"""
    return await enhanced_ai_service.generate_response(message, **kwargs)

def get_service_health() -> Dict[str, Any]:
    """Helper function để lấy service health"""
    return enhanced_ai_service.get_service_status()

async def refresh_ai_providers():
    """Helper function để refresh tất cả providers"""
    enhanced_ai_service._initialize_providers()
    enhanced_ai_service._determine_active_provider()