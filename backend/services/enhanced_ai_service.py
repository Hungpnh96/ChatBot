"""
Enhanced AI Service - Xử lý tách biệt AI provider và fallback
Đảm bảo service vẫn hoạt động khi AI không khả dụng
"""

import asyncio
import logging
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import requests

from config.settings import settings

logger = logging.getLogger(__name__)

class AIProvider(Enum):
    GITHUB = "github"
    OLLAMA = "ollama" 
    FALLBACK = "fallback"

class AIServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"  # Một số provider không khả dụng
    OFFLINE = "offline"    # Tất cả provider offline

class EnhancedAIService:
    """Enhanced AI Service với fallback và resilience patterns"""
    
    def __init__(self):
        self.github_client = None
        self.ollama_client = None
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
        
        # Initialize GitHub AI
        self._initialize_github_client()
        
        # Initialize Ollama
        self._initialize_ollama_client()
        
        # Update provider status
        self._update_provider_status()
    
    def _initialize_github_client(self):
        """Khởi tạo GitHub AI client"""
        try:
            if not settings.api_key:
                logger.warning("GitHub API key not configured")
                self.github_client = None
                return
                
            # Import here để tránh lỗi nếu thư viện không có
            from langchain_openai import ChatOpenAI
            
            self.github_client = ChatOpenAI(
                api_key=settings.api_key,
                base_url=settings.base_url,
                model=settings.model,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                request_timeout=settings.request_timeout
            )
            
            logger.info("GitHub AI client initialized")
            
        except ImportError as e:
            logger.error(f"Missing langchain_openai dependency: {e}")
            self.github_client = None
        except Exception as e:
            logger.error(f"Error initializing GitHub AI client: {e}")
            self.github_client = None
    
    def _initialize_ollama_client(self):
        """Khởi tạo Ollama client"""
        try:
            # Import here để tránh lỗi nếu thư viện không có
            from langchain_ollama import Ollama
            
            # Kiểm tra Ollama server trước
            if not self._check_ollama_server():
                logger.warning("Ollama server not available during initialization")
                self.ollama_client = None
                return
            
            self.ollama_client = Ollama(
                model=settings.ollama_model,
                base_url=settings.ollama_base_url,
                temperature=settings.temperature,
                num_predict=settings.ollama_max_tokens or settings.max_tokens
            )
            
            logger.info("Ollama client initialized")
            
        except ImportError as e:
            logger.error(f"Missing langchain_ollama dependency: {e}")
            self.ollama_client = None
        except Exception as e:
            logger.error(f"Error initializing Ollama client: {e}")
            self.ollama_client = None
    
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
        
        # Check GitHub
        if self.github_client:
            try:
                # Simple test call
                test_response = self.github_client.invoke("test")
                self.provider_status[AIProvider.GITHUB] = AIServiceStatus.HEALTHY
            except Exception as e:
                logger.warning(f"GitHub AI health check failed: {e}")
                self.provider_status[AIProvider.GITHUB] = AIServiceStatus.OFFLINE
        else:
            self.provider_status[AIProvider.GITHUB] = AIServiceStatus.OFFLINE
        
        # Check Ollama
        if self.ollama_client and self._check_ollama_server():
            try:
                # Simple test call
                test_response = self.ollama_client.invoke("test")
                self.provider_status[AIProvider.OLLAMA] = AIServiceStatus.HEALTHY
            except Exception as e:
                logger.warning(f"Ollama health check failed: {e}")
                self.provider_status[AIProvider.OLLAMA] = AIServiceStatus.OFFLINE
        else:
            self.provider_status[AIProvider.OLLAMA] = AIServiceStatus.OFFLINE
        
        # Update last check time
        self.last_health_check = {
            provider: current_time for provider in AIProvider if provider != AIProvider.FALLBACK
        }
        
        logger.info(f"Provider status: {self.provider_status}")
    
    def _determine_active_provider(self):
        """Xác định provider đang active"""
        preferred = getattr(settings, 'preferred_ai_provider', 'github').lower()
        
        # Kiểm tra preferred provider trước
        if preferred == 'github' and self.is_provider_healthy(AIProvider.GITHUB):
            self.current_provider = AIProvider.GITHUB
        elif preferred == 'ollama' and self.is_provider_healthy(AIProvider.OLLAMA):
            self.current_provider = AIProvider.OLLAMA
        # Fallback logic
        elif self.is_provider_healthy(AIProvider.GITHUB):
            self.current_provider = AIProvider.GITHUB
        elif self.is_provider_healthy(AIProvider.OLLAMA):
            self.current_provider = AIProvider.OLLAMA
        else:
            self.current_provider = AIProvider.FALLBACK
            logger.warning("No AI providers available, using fallback mode")
        
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
    
    def get_service_status(self) -> Dict[str, Any]:
        """Lấy trạng thái tổng quan của service"""
        healthy_providers = [
            provider.value for provider, status in self.provider_status.items() 
            if status == AIServiceStatus.HEALTHY
        ]
        
        if len(healthy_providers) >= 2:
            overall_status = AIServiceStatus.HEALTHY
        elif len(healthy_providers) >= 1:
            overall_status = AIServiceStatus.DEGRADED
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
        Generate AI response với fallback support
        Service sẽ luôn trả về response, không bao giờ fail hoàn toàn
        """
        # Refresh health check nếu cần
        await self._refresh_health_check()
        
        # Thử generate với current provider
        try:
            if self.current_provider == AIProvider.GITHUB and self.github_client:
                response = await self._generate_github_response(message, **kwargs)
                return self._format_success_response(response, AIProvider.GITHUB)
                
            elif self.current_provider == AIProvider.OLLAMA and self.ollama_client:
                response = await self._generate_ollama_response(message, **kwargs)
                return self._format_success_response(response, AIProvider.OLLAMA)
                
        except Exception as e:
            logger.error(f"Error with {self.current_provider.value}: {e}")
            
            # Nếu auto_fallback enabled, thử provider khác
            if self.fallback_enabled:
                fallback_response = await self._try_fallback_providers(message, **kwargs)
                if fallback_response:
                    return fallback_response
        
        # Cuối cùng, sử dụng fallback message
        return self._generate_fallback_response(message, **kwargs)
    
    async def _generate_github_response(self, message: str, **kwargs) -> str:
        """Generate response từ GitHub AI"""
        try:
            # Add system prompt và context
            full_prompt = self._build_full_prompt(message, **kwargs)
            response = await asyncio.to_thread(self.github_client.invoke, full_prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"GitHub AI generation failed: {e}")
            raise
    
    async def _generate_ollama_response(self, message: str, **kwargs) -> str:
        """Generate response từ Ollama"""
        try:
            full_prompt = self._build_full_prompt(message, **kwargs)
            response = await asyncio.to_thread(self.ollama_client.invoke, full_prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    async def _try_fallback_providers(self, message: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Thử các providers khác khi current provider fail"""
        providers_to_try = []
        
        if self.current_provider != AIProvider.GITHUB and self.is_provider_healthy(AIProvider.GITHUB):
            providers_to_try.append(AIProvider.GITHUB)
        
        if self.current_provider != AIProvider.OLLAMA and self.is_provider_healthy(AIProvider.OLLAMA):
            providers_to_try.append(AIProvider.OLLAMA)
        
        for provider in providers_to_try:
            try:
                logger.info(f"Trying fallback provider: {provider.value}")
                
                if provider == AIProvider.GITHUB and self.github_client:
                    response = await self._generate_github_response(message, **kwargs)
                    # Cập nhật current provider nếu thành công
                    self.current_provider = provider
                    return self._format_success_response(response, provider)
                
                elif provider == AIProvider.OLLAMA and self.ollama_client:
                    response = await self._generate_ollama_response(message, **kwargs)
                    self.current_provider = provider
                    return self._format_success_response(response, provider)
                    
            except Exception as e:
                logger.warning(f"Fallback provider {provider.value} also failed: {e}")
                continue
        
        return None
    
    def _build_full_prompt(self, message: str, **kwargs) -> str:
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
            full_prompt = f"{system_prompt}\n\n{time_info}\n\nUser: {message}"
        else:
            full_prompt = f"{system_prompt}\n\nUser: {message}"
        
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
    
    def _generate_fallback_response(self, message: str, **kwargs) -> Dict[str, Any]:
        """Generate fallback response khi tất cả AI providers fail"""
        logger.info("Using fallback response")
        
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
            'github_configured': bool(self.github_client),
            'ollama_configured': bool(self.ollama_client),
            'ollama_server_reachable': self._check_ollama_server()
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