# services/enhanced_ai_service.py - Sử dụng FREE realtime_search_service
import logging
import requests
import json
from typing import List, Optional, Dict, Any
from enum import Enum
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from config.settings import settings

# Import services (realtime_search_service đã là FREE version)
from services.realtime_search_service import realtime_search_service  # FREE version
from services.personal_info_service import personal_info_service

logger = logging.getLogger(__name__)

class AIProvider(Enum):
    """Enum định nghĩa các AI provider"""
    GITHUB = "github"
    OLLAMA = "ollama"
    AUTO = "auto"

class EnhancedAIService:
    """Enhanced AI Service với FREE search và personal info"""
    
    def __init__(self):
        self.github_client: Optional[ChatOpenAI] = None
        self.ollama_client: Optional[Ollama] = None
        self.current_provider: AIProvider = AIProvider.AUTO
        self.initialize_clients()
    
    def initialize_clients(self):
        """Khởi tạo tất cả AI clients"""
        logger.info("Initializing Enhanced AI clients with FREE search...")
        
        # Khởi tạo GitHub client
        self._initialize_github_client()
        
        # Khởi tạo Ollama client
        self._initialize_ollama_client()
        
        # Xác định provider mặc định
        self._determine_default_provider()
        
        logger.info(f"Enhanced AI Service initialized with providers: GitHub={self.is_github_available()}, Ollama={self.is_ollama_available()}")
    
    def _initialize_github_client(self):
        """Khởi tạo GitHub AI client"""
        try:
            if not settings.api_key:
                logger.warning("GitHub API_KEY not configured!")
                self.github_client = None
            else:
                self.github_client = ChatOpenAI(
                    api_key=settings.api_key,
                    base_url=settings.base_url,
                    model=settings.model,
                    temperature=settings.temperature,
                    max_tokens=settings.max_tokens,
                    request_timeout=settings.request_timeout
                )
                logger.info("GitHub AI client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing GitHub AI client: {e}")
            self.github_client = None
    
    def _initialize_ollama_client(self):
        """Khởi tạo Ollama client"""
        try:
            # Kiểm tra Ollama có chạy không
            if not self._check_ollama_server():
                logger.warning("Ollama server not available")
                self.ollama_client = None
                return
                
            self.ollama_client = Ollama(
                model=settings.ollama_model,
                base_url=settings.ollama_base_url,
                temperature=settings.temperature,
                num_predict=settings.ollama_max_tokens or settings.max_tokens
            )
            
            # Test connection
            test_response = self.ollama_client.invoke("Test")
            logger.info("Ollama client initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Ollama client: {e}")
            self.ollama_client = None
    
    def _check_ollama_server(self) -> bool:
        """Kiểm tra Ollama server có chạy không"""
        try:
            response = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama server check failed: {e}")
            return False
    
    def _determine_default_provider(self):
        """Xác định provider mặc định dựa trên availability"""
        if settings.preferred_ai_provider == "github" and self.is_github_available():
            self.current_provider = AIProvider.GITHUB
        elif settings.preferred_ai_provider == "ollama" and self.is_ollama_available():
            self.current_provider = AIProvider.OLLAMA
        elif self.is_github_available():
            self.current_provider = AIProvider.GITHUB
        elif self.is_ollama_available():
            self.current_provider = AIProvider.OLLAMA
        else:
            self.current_provider = AIProvider.AUTO
            logger.warning("No AI providers available!")
    
    def is_github_available(self) -> bool:
        """Kiểm tra GitHub AI có sẵn không"""
        return self.github_client is not None
    
    def is_ollama_available(self) -> bool:
        """Kiểm tra Ollama có sẵn không"""
        return self.ollama_client is not None and self._check_ollama_server()
    
    def is_available(self) -> bool:
        """Kiểm tra có ít nhất một AI provider sẵn sàng"""
        return self.is_github_available() or self.is_ollama_available()
    
    async def _get_additional_context(self, user_input: str, user_id: str = "default") -> str:
        """
        Lấy thông tin bổ sung từ FREE search và personal info
        """
        context_parts = []
        
        try:
            # 1. Kiểm tra và lấy thông tin cá nhân
            logger.info("Checking for personal information needs...")
            personal_info = await personal_info_service.get_personal_info_for_query(user_input, user_id)
            
            if personal_info:
                context_parts.append("=== THÔNG TIN CÁ NHÂN ===")
                context_parts.append(personal_info)
                logger.info("✅ Added personal information to context")
            
            # 2. Kiểm tra và search thông tin mới (FREE)
            logger.info("Checking for FREE realtime search needs...")
            search_info = await realtime_search_service.search_and_get_info(user_input)
            
            if search_info:
                context_parts.append("=== THÔNG TIN TÌM KIẾM MỚI NHẤT (FREE) ===")
                context_parts.append(search_info)
                logger.info("✅ Added FREE search information to context")
            
            # 3. Kết hợp context
            if context_parts:
                additional_context = "\n\n".join(context_parts)
                
                # Thêm hướng dẫn cho AI
                instruction = """
=== HƯỚNG DẪN SỬ DỤNG THÔNG TIN ===
- Sử dụng thông tin trên để trả lời chính xác và cập nhật
- Nếu có thông tin cá nhân, ưu tiên sử dụng để cá nhân hóa câu trả lời
- Nếu có thông tin tìm kiếm mới, sử dụng để cung cấp dữ liệu mới nhất
- Luôn trích dẫn nguồn khi sử dụng thông tin tìm kiếm
- Trả lời một cách tự nhiên, không nhắc đến việc "tìm kiếm" hay "tra cứu"
- Thông tin tìm kiếm được lấy từ các nguồn miễn phí đáng tin cậy
"""
                
                full_context = f"{additional_context}\n\n{instruction}"
                
                logger.info(f"Built additional context (FREE): {len(full_context)} characters")
                return full_context
            
            logger.info("No additional context needed")
            return ""
            
        except Exception as e:
            logger.error(f"Error getting additional context: {e}")
            return ""
    
    def create_enhanced_prompt_with_history(self, history: List[BaseMessage], user_input: str, additional_context: str = "") -> ChatPromptTemplate:
        """Tạo prompt có tích hợp thông tin bổ sung"""
        logger.info("Creating enhanced prompt with conversation history and additional context")
        
        # System messages từ config
        messages = [
            ("system", settings.system_prompt),
            ("system", settings.time_format.format(time=settings.get_current_time())),
        ]
        
        # Thêm additional context nếu có
        if additional_context:
            messages.append(("system", f"THÔNG TIN BỔ SUNG:\n{additional_context}"))
            logger.info("Added additional context to prompt")
        
        # Thêm lịch sử hội thoại
        for msg in history:
            if isinstance(msg, HumanMessage):
                messages.append(("user", msg.content))
            elif isinstance(msg, AIMessage):
                messages.append(("assistant", msg.content))
        
        # Thêm câu hỏi mới
        messages.append(("user", user_input))
        
        prompt = ChatPromptTemplate.from_messages(messages)
        return prompt
    
    def _select_provider_for_request(self) -> AIProvider:
        """Chọn provider cho request hiện tại"""
        if self.current_provider == AIProvider.AUTO:
            # Auto mode: Ưu tiên theo config, fallback nếu cần
            if settings.preferred_ai_provider == "github" and self.is_github_available():
                return AIProvider.GITHUB
            elif settings.preferred_ai_provider == "ollama" and self.is_ollama_available():
                return AIProvider.OLLAMA
            elif self.is_github_available():
                return AIProvider.GITHUB
            elif self.is_ollama_available():
                return AIProvider.OLLAMA
            else:
                raise Exception("No AI providers available")
        
        elif self.current_provider == AIProvider.GITHUB:
            if self.is_github_available():
                return AIProvider.GITHUB
            elif self.is_ollama_available():
                logger.warning("GitHub not available, falling back to Ollama")
                return AIProvider.OLLAMA
            else:
                raise Exception("No AI providers available")
        
        elif self.current_provider == AIProvider.OLLAMA:
            if self.is_ollama_available():
                return AIProvider.OLLAMA
            elif self.is_github_available():
                logger.warning("Ollama not available, falling back to GitHub")
                return AIProvider.GITHUB
            else:
                raise Exception("No AI providers available")
    
    def _get_response_with_github(self, user_input: str, history: List[BaseMessage], additional_context: str = "") -> str:
        """Lấy response từ GitHub AI"""
        logger.info("Getting response from GitHub AI with enhanced context")
        
        prompt = self.create_enhanced_prompt_with_history(history, user_input, additional_context)
        chain = prompt | self.github_client
        response = chain.invoke({})
        
        return response.content
    
    def _get_response_with_ollama(self, user_input: str, history: List[BaseMessage], additional_context: str = "") -> str:
        """Lấy response từ Ollama"""
        logger.info("Getting response from Ollama with enhanced context")
        
        # Tạo context từ history và user input
        context_parts = [settings.system_prompt]
        context_parts.append(settings.time_format.format(time=settings.get_current_time()))
        
        # Thêm additional context nếu có
        if additional_context:
            context_parts.append(f"THÔNG TIN BỔ SUNG:\n{additional_context}")
        
        # Thêm lịch sử hội thoại
        for msg in history:
            if isinstance(msg, HumanMessage):
                context_parts.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                context_parts.append(f"Assistant: {msg.content}")
        
        # Thêm câu hỏi mới
        context_parts.append(f"User: {user_input}")
        context_parts.append("Assistant:")
        
        full_prompt = "\n\n".join(context_parts)
        response = self.ollama_client.invoke(full_prompt)
        
        return response
    
    async def get_enhanced_response_with_history(self, user_input: str, history: List[BaseMessage], user_id: str = "default") -> Dict[str, Any]:
        """
        Lấy phản hồi từ AI với khả năng FREE search và personal info
        """
        logger.info("START - Getting enhanced AI response with history")
        
        try:
            if not self.is_available():
                logger.warning("No AI providers available, returning fallback response")
                return {
                    "content": settings.fallback_message.format(user_input=user_input),
                    "provider": "fallback",
                    "model": "none",
                    "has_additional_context": False
                }
            
            # 1. Lấy thông tin bổ sung (FREE search + personal info)
            additional_context = await self._get_additional_context(user_input, user_id)
            
            # 2. Chọn provider cho request này
            selected_provider = self._select_provider_for_request()
            logger.info(f"Selected provider: {selected_provider.value}")
            
            # 3. Gọi AI tương ứng với context bổ sung
            if selected_provider == AIProvider.GITHUB:
                ai_content = self._get_response_with_github(user_input, history, additional_context)
                provider_info = {"provider": "github", "model": settings.model}
            
            elif selected_provider == AIProvider.OLLAMA:
                ai_content = self._get_response_with_ollama(user_input, history, additional_context)
                provider_info = {"provider": "ollama", "model": settings.ollama_model}
            
            logger.info(f"AI response received: {len(ai_content)} characters from {provider_info['provider']}")
            logger.info("END - Enhanced AI response completed")
            
            return {
                "content": ai_content,
                "has_additional_context": bool(additional_context),
                "context_length": len(additional_context) if additional_context else 0,
                **provider_info
            }
            
        except Exception as e:
            logger.error(f"Error getting enhanced AI response: {e}")
            return {
                "content": settings.error_message.format(user_input=user_input),
                "provider": "error",
                "model": "none",
                "error": str(e),
                "has_additional_context": False
            }
    
    # Backward compatibility methods
    def get_response_with_history(self, user_input: str, history: List[BaseMessage]) -> Dict[str, Any]:
        """Backward compatibility wrapper"""
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Nếu đang trong async context, tạo task mới
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.get_enhanced_response_with_history(user_input, history))
                return future.result()
        else:
            return asyncio.run(self.get_enhanced_response_with_history(user_input, history))
    
    def switch_provider(self, provider: str) -> Dict[str, Any]:
        """Chuyển đổi AI provider"""
        logger.info(f"Switching AI provider to: {provider}")
        
        if provider.lower() == "github":
            if self.is_github_available():
                self.current_provider = AIProvider.GITHUB
                return {"status": "success", "provider": "github", "model": settings.model}
            else:
                return {"status": "error", "message": "GitHub AI not available"}
        
        elif provider.lower() == "ollama":
            if self.is_ollama_available():
                self.current_provider = AIProvider.OLLAMA
                return {"status": "success", "provider": "ollama", "model": settings.ollama_model}
            else:
                return {"status": "error", "message": "Ollama not available"}
        
        elif provider.lower() == "auto":
            self.current_provider = AIProvider.AUTO
            return {"status": "success", "provider": "auto"}
        
        else:
            return {"status": "error", "message": f"Unknown provider: {provider}"}
    
    def get_current_provider_info(self) -> Dict[str, Any]:
        """Lấy thông tin provider hiện tại"""
        return {
            "current_provider": self.current_provider.value,
            "github_available": self.is_github_available(),
            "ollama_available": self.is_ollama_available(),
            "github_model": settings.model if self.is_github_available() else None,
            "ollama_model": settings.ollama_model if self.is_ollama_available() else None,
            "search_enabled": settings.enable_realtime_search,
            "search_method": "free",
            "personal_info_enabled": settings.enable_personal_info and bool(settings.personal_api_base_url)
        }
    
    def test_connection(self, message: str = "Xin chào Bixby!", with_history: bool = False, provider: str = None) -> dict:
        """Test kết nối AI với enhanced features"""
        logger.info(f"Testing enhanced AI connection with provider: {provider}")
        
        try:
            # Backup current provider if testing specific one
            original_provider = self.current_provider
            
            if provider:
                switch_result = self.switch_provider(provider)
                if switch_result["status"] == "error":
                    return switch_result
            
            # Test với lịch sử giả để kiểm tra context
            test_history = []
            if with_history:
                test_history = [
                    HumanMessage(content="Tôi tên Hùng"),
                    AIMessage(content="Xin chào anh Hùng! Em rất vui được làm quen với anh.")
                ]
            
            # Test enhanced response
            import asyncio
            response_data = asyncio.run(self.get_enhanced_response_with_history(message, test_history))
            
            # Restore original provider if we changed it
            if provider:
                self.current_provider = original_provider
            
            return {
                "status": "success",
                "user_input": message,
                "ai_response": response_data["content"],
                "provider_used": response_data.get("provider", "unknown"),
                "model_used": response_data.get("model", "unknown"),
                "history_length": len(test_history),
                "has_additional_context": response_data.get("has_additional_context", False),
                "context_length": response_data.get("context_length", 0),
                "providers_available": {
                    "github": self.is_github_available(),
                    "ollama": self.is_ollama_available()
                },
                "enhanced_features": {
                    "search_service": "available (FREE)",
                    "personal_info_service": "available"
                }
            }
            
        except Exception as e:
            logger.error(f"Error testing enhanced AI: {e}")
            return {
                "status": "error",
                "error": str(e),
                "providers_available": {
                    "github": self.is_github_available(),
                    "ollama": self.is_ollama_available()
                }
            }
    
    def refresh_connections(self) -> Dict[str, Any]:
        """Làm mới tất cả connections"""
        logger.info("Refreshing enhanced AI connections...")
        
        self.initialize_clients()
        
        return {
            "status": "success",
            "github_available": self.is_github_available(),
            "ollama_available": self.is_ollama_available(),
            "current_provider": self.current_provider.value,
            "search_service_stats": realtime_search_service.get_search_stats(),
            "personal_info_stats": personal_info_service.get_service_stats()
        }

# Global AI service instance
enhanced_ai_service = EnhancedAIService()