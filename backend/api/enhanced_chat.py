# api/enhanced_chat.py - Enhanced Chat API với Search và Personal Info
from fastapi import APIRouter
from typing import Optional
from models.schemas import MessageIn, ChatResponse, TestAIRequest, TestAIResponse, AIProviderRequest, AIProviderResponse
from services.enhanced_chat_service import enhanced_chat_service
from services.enhanced_ai_service import enhanced_ai_service
from services.realtime_search_service import realtime_search_service
from services.personal_info_service import personal_info_service

router = APIRouter(prefix="/chat/api", tags=["enhanced-chat"])

@router.post("/chat", response_model=ChatResponse)
async def enhanced_chat(msg: MessageIn):
    """
    Enhanced chat endpoint với realtime search và personal info
    
    Features:
    - Tự động tìm kiếm thông tin mới khi cần (vd: "ai là chủ tịch nước VN hiện tại?")
    - Tự động lấy thông tin cá nhân khi được hỏi (vd: "thông tin về tôi")
    - Backward compatible với API cũ
    
    Request body:
    - {"user": "message", "conversation_id": 1} - như cũ
    - {"user": "message", "conversation_id": 1, "ai_provider": "ollama"} - với provider selection
    - {"user": "message", "conversation_id": 1, "user_id": "user123"} - với user context
    """
    
    # Kiểm tra nếu có ai_provider trong request
    if hasattr(msg, 'ai_provider') and msg.ai_provider:
        # Switch provider tạm thời cho request này
        original_provider = enhanced_ai_service.current_provider
        switch_result = enhanced_ai_service.switch_provider(msg.ai_provider)
        
        if switch_result["status"] == "error":
            # Nếu không switch được, log warning nhưng vẫn tiếp tục
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not switch to provider {msg.ai_provider}: {switch_result.get('message', 'Unknown error')}")
    
    # Process enhanced chat
    result = await enhanced_chat_service.process_enhanced_chat(msg)
    
    # Restore provider nếu đã switch
    if hasattr(msg, 'ai_provider') and msg.ai_provider:
        enhanced_ai_service.current_provider = original_provider
    
    return result

@router.post("/test-ai", response_model=TestAIResponse)
def test_enhanced_ai(test_msg: TestAIRequest):
    """Test enhanced AI connection với search và personal info capabilities"""
    result = enhanced_ai_service.test_connection(test_msg.message, test_msg.with_history)
    return TestAIResponse(**result)

@router.post("/test-ai/{provider}")
def test_ai_provider(provider: str, test_msg: TestAIRequest):
    """Test specific AI provider với enhanced features"""
    result = enhanced_ai_service.test_connection(test_msg.message, test_msg.with_history, provider)
    return result

# === SEARCH ENDPOINTS ===

@router.post("/search/test")
async def test_search_capability(query: str = "ai là chủ tịch nước Việt Nam hiện tại"):
    """Test khả năng tìm kiếm thông tin thời gian thực"""
    try:
        result = await realtime_search_service.search_and_get_info(query)
        
        return {
            "status": "success",
            "query": query,
            "search_needed": result is not None,
            "result": result,
            "search_stats": realtime_search_service.get_search_stats()
        }
    except Exception as e:
        return {
            "status": "error",
            "query": query,
            "error": str(e)
        }

@router.get("/search/stats")
def get_search_stats():
    """Lấy thống kê search service"""
    return realtime_search_service.get_search_stats()

@router.post("/search/manual")
async def manual_search(query: str, num_results: int = 3):
    """Tìm kiếm thủ công (để test)"""
    try:
        google_results = await realtime_search_service.search_google(query, num_results)
        bing_results = await realtime_search_service.search_bing(query, num_results)
        
        return {
            "status": "success",
            "query": query,
            "google_results": google_results,
            "bing_results": bing_results,
            "google_count": len(google_results),
            "bing_count": len(bing_results)
        }
    except Exception as e:
        return {
            "status": "error",
            "query": query,
            "error": str(e)
        }

# === PERSONAL INFO ENDPOINTS ===

@router.post("/personal-info/test")
async def test_personal_info_capability(
    query: str = "thông tin cơ bản về tôi", 
    user_id: str = "default"
):
    """Test khả năng lấy thông tin cá nhân"""
    try:
        result = await personal_info_service.get_personal_info_for_query(query, user_id)
        
        return {
            "status": "success",
            "query": query,
            "user_id": user_id,
            "personal_info_needed": result is not None,
            "result": result,
            "service_stats": personal_info_service.get_service_stats()
        }
    except Exception as e:
        return {
            "status": "error",
            "query": query,
            "user_id": user_id,
            "error": str(e)
        }

@router.get("/personal-info/stats")
def get_personal_info_stats():
    """Lấy thống kê personal info service"""
    return personal_info_service.get_service_stats()

@router.post("/personal-info/clear-cache/{user_id}")
def clear_user_cache(user_id: str):
    """Xóa cache thông tin của user"""
    try:
        personal_info_service.clear_user_cache(user_id)
        return {
            "status": "success",
            "message": f"Cache cleared for user: {user_id}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/personal-info/user/{user_id}/basic")
async def get_user_basic_info_direct(user_id: str):
    """Lấy thông tin cơ bản của user (direct API call)"""
    try:
        result = await personal_info_service.get_user_basic_info(user_id)
        return {
            "status": "success",
            "user_id": user_id,
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "user_id": user_id,
            "error": str(e)
        }

# === PROVIDER MANAGEMENT ===

@router.post("/switch-provider", response_model=AIProviderResponse)
def switch_ai_provider(request: AIProviderRequest):
    """Chuyển đổi AI provider"""
    result = enhanced_ai_service.switch_provider(request.provider)
    return AIProviderResponse(**result)

@router.get("/provider-info")
def get_enhanced_provider_info():
    """Lấy thông tin các AI providers và enhanced features"""
    provider_info = enhanced_ai_service.get_current_provider_info()
    
    # Thêm thông tin về enhanced features
    from config.settings import settings
    
    enhanced_info = {
        **provider_info,
        "enhanced_features": {
            "realtime_search": {
                "enabled": settings.enable_realtime_search,
                "google_available": bool(settings.google_search_api_key),
                "bing_available": bool(settings.bing_search_api_key),
                "stats": realtime_search_service.get_search_stats()
            },
            "personal_info": {
                "enabled": settings.enable_personal_info,
                "api_available": bool(settings.personal_api_base_url),
                "stats": personal_info_service.get_service_stats()
            }
        }
    }
    
    return enhanced_info

@router.post("/refresh-connections")
def refresh_enhanced_connections():
    """Làm mới tất cả AI connections và services"""
    return enhanced_ai_service.refresh_connections()

# === DEMO ENDPOINTS ===

@router.post("/demo/realtime-question")
async def demo_realtime_question(question: str = "Ai là chủ tịch nước Việt Nam hiện tại?"):
    """Demo: Câu hỏi thời gian thực sẽ được AI trả lời với thông tin mới nhất"""
    from models.schemas import MessageIn
    
    try:
        # Tạo message demo
        demo_msg = MessageIn(
            user=question,
            conversation_id=None  # Tạo conversation mới
        )
        
        # Process qua enhanced chat
        result = await enhanced_chat_service.process_enhanced_chat(demo_msg)
        
        return {
            "status": "success",
            "demo_type": "realtime_question",
            "question": question,
            "ai_response": result.message.content,
            "conversation_id": result.conversation_id,
            "provider_used": result.ai_provider,
            "note": "AI đã tự động tìm kiếm thông tin mới nhất để trả lời"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "demo_type": "realtime_question", 
            "question": question,
            "error": str(e)
        }

@router.post("/demo/personal-question")
async def demo_personal_question(
    question: str = "Thông tin cơ bản về tôi là gì?",
    user_id: str = "demo_user"
):
    """Demo: Câu hỏi cá nhân sẽ được AI trả lời với thông tin từ API"""
    from models.schemas import MessageIn
    
    try:
        # Tạo message demo với user_id
        demo_msg = MessageIn(
            user=question,
            conversation_id=None
        )
        
        # Thêm user_id vào message (giả lập)
        demo_msg.user_id = user_id
        
        # Process qua enhanced chat
        result = await enhanced_chat_service.process_enhanced_chat(demo_msg)
        
        return {
            "status": "success",
            "demo_type": "personal_question",
            "question": question,
            "user_id": user_id,
            "ai_response": result.message.content,
            "conversation_id": result.conversation_id,
            "provider_used": result.ai_provider,
            "note": "AI đã tự động lấy thông tin cá nhân từ API để trả lời"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "demo_type": "personal_question",
            "question": question,
            "user_id": user_id,
            "error": str(e)
        }