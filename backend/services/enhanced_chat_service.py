# services/enhanced_chat_service.py - Cập nhật Chat Service để sử dụng Enhanced AI
import logging
from datetime import datetime
from fastapi import HTTPException
from models.schemas import MessageIn, ChatResponse, MessageOut
from services.enhanced_ai_service import enhanced_ai_service  # Thay thế ai_service
from services.conversation_service import conversation_service
from services.message_service import message_service
from config.database import get_db

logger = logging.getLogger(__name__)

class EnhancedChatService:
    """Enhanced Chat Service với tích hợp search và personal info"""
    
    def _extract_user_id_from_message(self, msg: MessageIn) -> str:
        """Trích xuất user_id từ message (có thể từ header, token, hoặc conversation)"""
        # TODO: Implement proper user identification
        # Hiện tại dùng default, sau này có thể lấy từ:
        # - JWT token trong header
        # - Session
        # - Conversation metadata
        return getattr(msg, 'user_id', 'default')
    
    async def process_enhanced_chat(self, msg: MessageIn) -> ChatResponse:
        """Xử lý chat message với enhanced features"""
        logger.info(f"START - Processing enhanced chat message from user")
        logger.debug(f"Message content: {msg.user[:100]}...")
        
        conn = None
        try:
            conn = get_db()
            cur = conn.cursor()
            
            # Extract user_id
            user_id = self._extract_user_id_from_message(msg)
            logger.info(f"Processing chat for user: {user_id}")
            
            # Xử lý conversation_id
            conversation_id = self._handle_conversation_id(msg.conversation_id, cur, conn)
            
            # Lấy lịch sử hội thoại TRƯỚC KHI lưu tin nhắn mới
            logger.info(f"Getting conversation history for conversation {conversation_id}")
            history = message_service.get_conversation_history(conversation_id, conn)
            logger.info(f"Found {len(history)} messages in history")
            
            # Debug: Log một vài tin nhắn gần nhất
            self._log_recent_history(history)
            
            # Lưu tin nhắn của user
            message_service.save_user_message(conversation_id, msg.user, conn)
            
            # Lấy phản hồi từ Enhanced AI với context bổ sung
            logger.info("Getting enhanced AI response with search and personal info")
            ai_response_data = await enhanced_ai_service.get_enhanced_response_with_history(
                user_input=msg.user,
                history=history,
                user_id=user_id
            )
            
            ai_content = ai_response_data["content"]
            provider_used = ai_response_data.get("provider", "unknown")
            model_used = ai_response_data.get("model", "unknown")
            has_additional_context = ai_response_data.get("has_additional_context", False)
            context_length = ai_response_data.get("context_length", 0)
            
            logger.info(f"Enhanced AI response received from {provider_used} ({model_used}): {len(ai_content)} characters")
            if has_additional_context:
                logger.info(f"✅ Response enhanced with {context_length} characters of additional context")
            
            # Lưu phản hồi AI với metadata
            timestamp = message_service.save_ai_message_with_metadata(
                conversation_id, ai_content, provider_used, model_used, conn
            )
            
            # Cập nhật title thông minh nếu cần
            updated_title = conversation_service.update_conversation_title_smart(
                conversation_id, msg.user, ai_content, conn
            )
            conn.commit()
            
            # Verify data was saved
            total_messages = message_service.get_message_count(conversation_id, conn)
            logger.info(f"Total messages in conversation {conversation_id}: {total_messages}")
            
            response = ChatResponse(
                conversation_id=conversation_id,
                message=MessageOut(
                    sender="ai", 
                    content=ai_content, 
                    timestamp=timestamp or datetime.now().isoformat()
                ),
                conversation_title=updated_title,
                ai_provider=provider_used,
                ai_model=model_used
            )
            
            # Thêm metadata về enhanced features (nếu cần)
            if hasattr(response, 'metadata'):
                response.metadata = {
                    "has_search_context": has_additional_context,
                    "context_length": context_length,
                    "enhanced_features_used": has_additional_context
                }
            
            logger.info(f"END - Enhanced chat processing completed successfully for conversation {conversation_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error in enhanced chat processing: {e}")
            if conn:
                conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error processing enhanced chat: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def process_chat(self, msg: MessageIn) -> ChatResponse:
        """Backward compatibility wrapper for enhanced chat"""
        import asyncio
        
        # Kiểm tra xem có đang trong async context không
        try:
            loop = asyncio.get_running_loop()
            # Nếu đang trong async context, tạo task mới
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.process_enhanced_chat(msg))
                return future.result()
        except RuntimeError:
            # Không có event loop, chạy trực tiếp
            return asyncio.run(self.process_enhanced_chat(msg))
    
    def _handle_conversation_id(self, conversation_id: int, cur, conn) -> int:
        """Xử lý conversation_id: tạo mới hoặc validate existing"""
        if conversation_id is None:
            logger.info("Creating new conversation with default title")
            cur.execute("INSERT INTO conversations (title) VALUES (?)", ("Chat mới",))
            new_conversation_id = cur.lastrowid
            logger.info(f"New conversation created with ID: {new_conversation_id}")
            return new_conversation_id
        else:
            logger.info(f"Using existing conversation ID: {conversation_id}")
            
            # Kiểm tra conversation có tồn tại không
            cur.execute("SELECT COUNT(*) FROM conversations WHERE id=?", (conversation_id,))
            if cur.fetchone()[0] == 0:
                logger.error(f"Conversation {conversation_id} not found!")
                raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
            
            return conversation_id
    
    def _log_recent_history(self, history: list) -> None:
        """Log một vài tin nhắn gần nhất để debug"""
        if history:
            from langchain_core.messages import HumanMessage
            for i, msg_hist in enumerate(history[-3:]):  # Log 3 tin nhắn cuối
                msg_type = "User" if isinstance(msg_hist, HumanMessage) else "AI"
                logger.debug(f"History {i}: {msg_type}: {msg_hist.content[:50]}...")

# Global enhanced chat service instance
enhanced_chat_service = EnhancedChatService()