import logging
from datetime import datetime
from fastapi import HTTPException
from models.schemas import MessageIn, ChatResponse, MessageOut
from services.ai_service import ai_service
from services.conversation_service import conversation_service
from services.message_service import message_service
from config.database import get_db

logger = logging.getLogger(__name__)

class ChatService:
    """Enhanced Service xử lý chat logic với multiple AI providers"""
    
    # FILE: services/chat_service.py
    # ACTION: CẬP NHẬT method process_chat - THAY THẾ method này trong file hiện tại

    def process_chat(self, msg: MessageIn) -> ChatResponse:
        """Xử lý chat message và trả về response"""
        logger.info(f"START - Processing chat message from user")
        logger.debug(f"Message content: {msg.user[:100]}...")
        
        conn = None
        try:
            conn = get_db()
            cur = conn.cursor()
            
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
            
            # Lấy phản hồi từ AI với lịch sử hội thoại
            logger.info("Getting AI response with conversation history")
            ai_response_data = ai_service.get_response_with_history(msg.user, history)
            
            ai_content = ai_response_data["content"]
            provider_used = ai_response_data.get("provider", "unknown")
            model_used = ai_response_data.get("model", "unknown")
            
            logger.info(f"AI response received from {provider_used} ({model_used}): {len(ai_content)} characters")
            
            # Lưu phản hồi AI với thông tin provider
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
            
            logger.info(f"END - Chat processing completed successfully for conversation {conversation_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error in chat processing: {e}")
            if conn:
                conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")
        finally:
            if conn:
                conn.close()

        """Xử lý chat message và trả về response"""
        logger.info(f"START - Processing chat message from user")
        logger.debug(f"Message content: {msg.user[:100]}...")
        
        conn = None
        try:
            conn = get_db()
            cur = conn.cursor()
            
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
            
            # Lấy phản hồi từ AI với lịch sử hội thoại
            logger.info("Getting AI response with conversation history")
            ai_response_data = ai_service.get_response_with_history(msg.user, history)
            
            ai_content = ai_response_data["content"]
            provider_used = ai_response_data.get("provider", "unknown")
            model_used = ai_response_data.get("model", "unknown")
            
            logger.info(f"AI response received from {provider_used} ({model_used}): {len(ai_content)} characters")
            
            # Lưu phản hồi AI với thông tin provider
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
            
            logger.info(f"END - Chat processing completed successfully for conversation {conversation_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error in chat processing: {e}")
            if conn:
                conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")
        finally:
            if conn:
                conn.close()
    
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

# Global chat service instance
chat_service = ChatService()