import logging
from fastapi import HTTPException
from langchain_core.messages import HumanMessage, AIMessage
from models.schemas import MessageOut
from config.database import get_db

from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

class MessageService:
    """Enhanced Service quản lý messages với AI provider metadata"""
    
    def get_messages(self, conversation_id: int) -> List[MessageOut]:
        """Lấy tin nhắn của một conversation"""
        logger.info(f"START - Getting messages for conversation {conversation_id}")
        
        conn = None
        try:
            conn = get_db()
            cur = conn.cursor()
            
            # Kiểm tra conversation có tồn tại không
            cur.execute("SELECT COUNT(*) FROM conversations WHERE id=?", (conversation_id,))
            if cur.fetchone()[0] == 0:
                logger.warning(f"Conversation {conversation_id} not found")
                raise HTTPException(status_code=404, detail="Conversation not found")

            cur.execute(
                "SELECT sender, content, timestamp FROM messages WHERE conversation_id=? ORDER BY id", 
                (conversation_id,)
            )
            rows = cur.fetchall()
            
            messages = [MessageOut(sender=row["sender"], content=row["content"], timestamp=row["timestamp"]) for row in rows]
            
            logger.info(f"END - Retrieved {len(messages)} messages for conversation {conversation_id}")
            return messages
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            raise HTTPException(status_code=500, detail=f"Error getting messages: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def get_conversation_history(self, conversation_id: int, conn) -> List:
        """Lấy lịch sử hội thoại từ database (trả về LangChain messages)"""
        logger.info(f"Getting conversation history for ID: {conversation_id}")
        
        cur = conn.cursor()
        cur.execute(
            "SELECT sender, content FROM messages WHERE conversation_id=? ORDER BY id",
            (conversation_id,)
        )
        rows = cur.fetchall()
        
        history = []
        for row in rows:
            sender, content = row['sender'], row['content']
            if sender == 'user':
                history.append(HumanMessage(content=content))
            elif sender == 'ai':
                history.append(AIMessage(content=content))
        
        logger.info(f"Retrieved {len(history)} messages from history")
        return history
    
    def save_user_message(self, conversation_id: int, user_input: str, conn) -> None:
        """Lưu tin nhắn của user"""
        logger.info("Saving user message to database")
        
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO messages (conversation_id, sender, content) VALUES (?, ?, ?)",
            (conversation_id, "user", user_input)
        )
        conn.commit()
        logger.info("User message saved successfully")
    
    def save_ai_message(self, conversation_id: int, ai_content: str, conn) -> str:
        """Lưu tin nhắn AI và trả về timestamp (backward compatibility)"""
        return self.save_ai_message_with_metadata(conversation_id, ai_content, None, None, conn)
    
    def save_ai_message_with_metadata(self, conversation_id: int, ai_content: str, 
                                provider: str, model: str, conn) -> str:
        """Lưu tin nhắn AI với metadata và trả về timestamp"""
        logger.info(f"Saving AI response to database (provider: {provider}, model: {model})")
        
        cur = conn.cursor()
        
        # Check if metadata columns exist, add them if not
        self._ensure_metadata_columns(cur, conn)
        
        cur.execute(
            """INSERT INTO messages (conversation_id, sender, content, ai_provider, ai_model) 
            VALUES (?, ?, ?, ?, ?)""",
            (conversation_id, "ai", ai_content, provider, model)
        )
        conn.commit()
        logger.info("AI response with metadata saved successfully")
        
        # Lấy timestamp của tin nhắn AI
        cur.execute("SELECT timestamp FROM messages WHERE id = last_insert_rowid()")
        timestamp_row = cur.fetchone()
        return timestamp_row[0] if timestamp_row else None
    
    def _ensure_metadata_columns(self, cur, conn):
        """Đảm bảo các cột metadata tồn tại trong bảng messages"""
        try:
            # Kiểm tra structure của bảng messages
            cur.execute("PRAGMA table_info(messages)")
            columns = [column[1] for column in cur.fetchall()]
            
            # Thêm cột ai_provider nếu chưa có
            if 'ai_provider' not in columns:
                cur.execute("ALTER TABLE messages ADD COLUMN ai_provider TEXT")
                logger.info("Added ai_provider column to messages table")
            
            # Thêm cột ai_model nếu chưa có
            if 'ai_model' not in columns:
                cur.execute("ALTER TABLE messages ADD COLUMN ai_model TEXT")
                logger.info("Added ai_model column to messages table")
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error ensuring metadata columns: {e}")
            # Không raise exception để maintain backward compatibility
    
    def get_message_count(self, conversation_id: int, conn) -> int:
        """Đếm số tin nhắn trong conversation"""
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM messages WHERE conversation_id=?", (conversation_id,))
        return cur.fetchone()[0]
    
    def delete_messages_by_conversation(self, conversation_id: int, conn) -> int:
        """Xóa tất cả messages của một conversation"""
        cur = conn.cursor()
        cur.execute("DELETE FROM messages WHERE conversation_id=?", (conversation_id,))
        return cur.rowcount
    
    def get_ai_provider_stats(self, conversation_id: Optional[int] = None) -> Dict[str, Any]:
        """Lấy thống kê về AI providers được sử dụng"""
        conn = None
        try:
            conn = get_db()
            cur = conn.cursor()
            
            # Base query
            where_clause = ""
            params = []
            if conversation_id:
                where_clause = "WHERE conversation_id = ?"
                params = [conversation_id]
            
            # Đếm messages theo provider
            cur.execute(f"""
                SELECT ai_provider, COUNT(*) as count 
                FROM messages 
                WHERE sender = 'ai' {where_clause}
                GROUP BY ai_provider
            """, params)
            
            provider_stats = {}
            for row in cur.fetchall():
                provider = row[0] or "unknown"
                provider_stats[provider] = row[1]
            
            # Đếm tổng AI messages
            cur.execute(f"""
                SELECT COUNT(*) FROM messages 
                WHERE sender = 'ai' {where_clause}
            """, params)
            total_ai_messages = cur.fetchone()[0]
            
            return {
                "total_ai_messages": total_ai_messages,
                "by_provider": provider_stats,
                "conversation_id": conversation_id
            }
            
        except Exception as e:
            logger.error(f"Error getting AI provider stats: {e}")
            return {"error": str(e)}
        finally:
            if conn:
                conn.close()

# Global message service instance
message_service = MessageService()