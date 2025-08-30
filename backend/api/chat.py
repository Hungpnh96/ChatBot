from fastapi import APIRouter
from typing import Optional
from models.schemas import MessageIn, ChatResponse, TestAIRequest, TestAIResponse, AIProviderRequest, AIProviderResponse
# from services.chat_service import chat_service
# from services.ai_service import ai_service
from services.enhanced_ai_service import enhanced_ai_service as ai_service
from services.enhanced_chat_service import enhanced_chat_service as chat_service


router = APIRouter(prefix="/chat/api", tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
def chat(msg: MessageIn):
    """
    Enhanced chat endpoint với provider selection - BACKWARD COMPATIBLE
    
    Request body có thể là:
    - {"user": "message", "conversation_id": 1} - như cũ
    - {"user": "message", "conversation_id": 1, "ai_provider": "ollama"} - mới
    """
    
    # Kiểm tra nếu có ai_provider trong request
    if hasattr(msg, 'ai_provider') and msg.ai_provider:
        # Switch provider tạm thời cho request này
        original_provider = ai_service.current_provider
        switch_result = ai_service.switch_provider(msg.ai_provider)
        
        if switch_result["status"] == "error":
            # Nếu không switch được, log warning nhưng vẫn tiếp tục
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not switch to provider {msg.ai_provider}: {switch_result.get('message', 'Unknown error')}")
    
    # Process chat như bình thường
    result = chat_service.process_chat(msg)
    
    # Restore provider nếu đã switch
    if hasattr(msg, 'ai_provider') and msg.ai_provider:
        ai_service.current_provider = original_provider
    
    return result

@router.post("/test-ai", response_model=TestAIResponse)
def test_ai(test_msg: TestAIRequest):
    """Test AI connection với tin nhắn đơn giản"""
    result = ai_service.test_connection(test_msg.message, test_msg.with_history)
    return TestAIResponse(**result)

@router.post("/test-ai/{provider}")
def test_ai_provider(provider: str, test_msg: TestAIRequest):
    """Test specific AI provider"""
    result = ai_service.test_connection(test_msg.message, test_msg.with_history, provider)
    return result

@router.post("/switch-provider", response_model=AIProviderResponse)
def switch_ai_provider(request: AIProviderRequest):
    """Chuyển đổi AI provider"""
    result = ai_service.switch_provider(request.provider)
    return AIProviderResponse(**result)

@router.get("/provider-info")
def get_provider_info():
    """Lấy thông tin các AI providers"""
    return ai_service.get_current_provider_info()

@router.post("/refresh-connections")
def refresh_ai_connections():
    """Làm mới tất cả AI connections"""
    return ai_service.refresh_connections()

@router.get("/provider-stats")
def get_provider_stats(conversation_id: Optional[int] = None):
    """Lấy thống kê sử dụng AI providers"""
    from services.message_service import message_service
    return message_service.get_ai_provider_stats(conversation_id)