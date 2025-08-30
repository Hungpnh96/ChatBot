import logging
from typing import List, Optional
from fastapi import HTTPException
from models.schemas import ConversationOut, ConversationCreateRequest
from config.database import get_db

logger = logging.getLogger(__name__)

class ConversationService:
    """Service quản lý conversations với improved error handling"""
    
    def generate_title_from_message(self, user_input: str) -> str:
        """Tạo title tự động từ tin nhắn đầu tiên"""
        # Làm sạch và rút gọn tin nhắn
        clean_input = user_input.strip()
        if len(clean_input) <= 30:
            return clean_input
        
        # Cắt tại từ gần nhất với 30 ký tự
        if len(clean_input) > 30:
            truncated = clean_input[:30]
            last_space = truncated.rfind(' ')
            if last_space > 15:  # Đảm bảo không cắt quá ngắn
                return truncated[:last_space] + "..."
            else:
                return truncated + "..."
        
        return clean_input
    
    def create_conversation(self, request: ConversationCreateRequest) -> ConversationOut:
        """Tạo conversation mới với title"""
        logger.info("START - Creating new conversation")
        
        conn = None
        try:
            conn = get_db()
            cur = conn.cursor()
            
            title = request.title or "Chat mới"
            
            cur.execute(
                "INSERT INTO conversations (title) VALUES (?)", 
                (title,)
            )
            conversation_id = cur.lastrowid
            conn.commit()
            
            # Lấy thông tin conversation vừa tạo
            cur.execute(
                "SELECT id, title, started_at FROM conversations WHERE id=?", 
                (conversation_id,)
            )
            row = cur.fetchone()
            
            if not row:
                raise Exception("Failed to retrieve created conversation")
            
            conversation = ConversationOut(
                id=row["id"],
                title=row["title"],
                started_at=row["started_at"],
                message_count=0
            )
            
            logger.info(f"END - Created conversation {conversation_id} with title: {title}")
            return conversation
            
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            if conn:
                conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating conversation: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def get_all_conversations(self) -> List[ConversationOut]:
        """Lấy danh sách conversations với thông tin chi tiết"""
        logger.info("START - Getting conversations list")
        
        conn = None
        try:
            conn = get_db()
            cur = conn.cursor()
            
            # Lấy conversations với message count và last message - FIX JOIN
            cur.execute("""
                SELECT 
                    c.id, 
                    c.title,
                    c.started_at,
                    COUNT(m.id) as message_count,
                    (SELECT content 
                     FROM messages 
                     WHERE conversation_id = c.id 
                     ORDER BY timestamp DESC 
                     LIMIT 1) as last_message
                FROM conversations c 
                LEFT JOIN messages m ON c.id = m.conversation_id 
                GROUP BY c.id, c.title, c.started_at 
                ORDER BY c.started_at DESC
            """)
            rows = cur.fetchall()
            
            conversations = []
            for row in rows:
                last_msg = row["last_message"]
                if last_msg and len(last_msg) > 60:
                    last_msg = last_msg[:60] + "..."
                
                conversations.append(ConversationOut(
                    id=row["id"],
                    title=row["title"] or "Chat mới",
                    started_at=row["started_at"],
                    message_count=row["message_count"] or 0,
                    last_message=last_msg
                ))
            
            logger.info(f"END - Retrieved {len(conversations)} conversations")
            return conversations
            
        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            raise HTTPException(status_code=500, detail=f"Error getting conversations: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def get_conversation_detail(self, conversation_id: int) -> ConversationOut:
        """Lấy chi tiết một conversation"""
        logger.info(f"Getting conversation detail for ID: {conversation_id}")
        
        conn = None
        try:
            conn = get_db()
            cur = conn.cursor()
            
            # Lấy thông tin conversation - IMPROVED QUERY
            cur.execute("""
                SELECT 
                    c.id, 
                    c.title,
                    c.started_at,
                    COUNT(m.id) as message_count,
                    (SELECT content 
                     FROM messages 
                     WHERE conversation_id = c.id 
                     ORDER BY timestamp DESC 
                     LIMIT 1) as last_message
                FROM conversations c 
                LEFT JOIN messages m ON c.id = m.conversation_id 
                WHERE c.id = ?
                GROUP BY c.id, c.title, c.started_at
            """, (conversation_id,))
            
            row = cur.fetchone()
            if not row:
                logger.warning(f"Conversation {conversation_id} not found")
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            last_msg = row["last_message"]
            if last_msg and len(last_msg) > 100:
                last_msg = last_msg[:100] + "..."
            
            conversation = ConversationOut(
                id=row["id"],
                title=row["title"] or "Chat mới",
                started_at=row["started_at"],
                message_count=row["message_count"] or 0,
                last_message=last_msg
            )
            
            logger.info(f"Retrieved conversation {conversation_id}: {conversation.title}")
            return conversation
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting conversation detail: {e}")
            raise HTTPException(status_code=500, detail=f"Error getting conversation: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def update_conversation_title(self, conversation_id: int, title: str) -> dict:
        """Cập nhật title của conversation - FIX BUG"""
        logger.info(f"Updating title for conversation {conversation_id} to: {title}")
        
        conn = None
        try:
            conn = get_db()
            cur = conn.cursor()
            
            # Kiểm tra conversation tồn tại
            cur.execute("SELECT id, title FROM conversations WHERE id=?", (conversation_id,))
            existing = cur.fetchone()
            if not existing:
                logger.warning(f"Conversation {conversation_id} not found for title update")
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            if not title.strip():
                raise HTTPException(status_code=400, detail="Title cannot be empty")
            
            # Update title
            cur.execute(
                "UPDATE conversations SET title=? WHERE id=?", 
                (title.strip(), conversation_id)
            )
            
            if cur.rowcount == 0:
                logger.warning(f"No rows updated for conversation {conversation_id}")
                raise HTTPException(status_code=404, detail="Conversation not found or no changes made")
            
            conn.commit()
            
            # Verify update
            cur.execute("SELECT title FROM conversations WHERE id=?", (conversation_id,))
            updated_row = cur.fetchone()
            updated_title = updated_row["title"] if updated_row else None
            
            logger.info(f"Successfully updated conversation {conversation_id} title to: {updated_title}")
            
            return {
                "message": "Title updated successfully", 
                "conversation_id": conversation_id, 
                "old_title": existing["title"],
                "new_title": updated_title
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating conversation title: {e}")
            if conn:
                conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error updating title: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def update_conversation_title_smart(self, conversation_id: int, user_input: str, ai_response: str, conn) -> str:
        """Cập nhật title thông minh cho conversation"""
        try:
            cur = conn.cursor()
            
            # Kiểm tra conversation hiện tại có title "Chat mới" không
            cur.execute("SELECT title FROM conversations WHERE id=?", (conversation_id,))
            row = cur.fetchone()
            if not row:
                logger.warning(f"Conversation {conversation_id} not found for smart title update")
                return "Chat mới"
                
            current_title = row["title"]
            
            if current_title == "Chat mới" or not current_title:
                # Sinh title từ tin nhắn đầu tiên
                new_title = self.generate_title_from_message(user_input)
                cur.execute(
                    "UPDATE conversations SET title=? WHERE id=?", 
                    (new_title, conversation_id)
                )
                logger.info(f"Auto-updated conversation {conversation_id} title to: {new_title}")
                return new_title
            
            return current_title
            
        except Exception as e:
            logger.error(f"Error in smart title update: {e}")
            return current_title if 'current_title' in locals() else "Chat mới"
    
    def delete_conversation(self, conversation_id: int) -> dict:
        """Xóa conversation và tất cả messages"""
        logger.info(f"Deleting conversation {conversation_id}")
        
        conn = None
        try:
            conn = get_db()
            cur = conn.cursor()
            
            # Kiểm tra conversation tồn tại
            cur.execute("SELECT COUNT(*) FROM conversations WHERE id=?", (conversation_id,))
            if cur.fetchone()[0] == 0:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            # Xóa messages trước (do foreign key constraint)
            cur.execute("DELETE FROM messages WHERE conversation_id=?", (conversation_id,))
            deleted_messages = cur.rowcount
            
            # Xóa conversation
            cur.execute("DELETE FROM conversations WHERE id=?", (conversation_id,))
            
            conn.commit()
            
            logger.info(f"Deleted conversation {conversation_id} with {deleted_messages} messages")
            return {
                "message": "Conversation deleted successfully", 
                "conversation_id": conversation_id, 
                "deleted_messages": deleted_messages
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            if conn:
                conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def conversation_exists(self, conversation_id: int) -> bool:
        """Kiểm tra conversation có tồn tại không"""
        conn = None
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM conversations WHERE id=?", (conversation_id,))
            exists = cur.fetchone()[0] > 0
            logger.debug(f"Conversation {conversation_id} exists: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking conversation existence: {e}")
            return False
        finally:
            if conn:
                conn.close()

# Global conversation service instance
conversation_service = ConversationService()