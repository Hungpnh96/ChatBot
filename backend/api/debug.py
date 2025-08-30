from fastapi import APIRouter, HTTPException
from typing import List, Optional
from config.database import get_db, get_db_stats, verify_database_integrity, backup_database
from services.conversation_service import conversation_service
from services.message_service import message_service
import logging
import os

router = APIRouter(prefix="/chat/api/debug", tags=["debug"])
logger = logging.getLogger(__name__)

@router.get("/db-stats")
def get_database_stats():
    """Lấy thống kê chi tiết database"""
    try:
        stats = get_db_stats()
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/db-integrity")
def check_database_integrity():
    """Kiểm tra tính toàn vẹn database"""
    try:
        is_ok = verify_database_integrity()
        return {
            "status": "success",
            "integrity_ok": is_ok,
            "message": "Database integrity is OK" if is_ok else "Database integrity check failed"
        }
    except Exception as e:
        logger.error(f"Error checking database integrity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations-raw")
def get_conversations_raw():
    """Lấy raw data của conversations từ database"""
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM conversations ORDER BY started_at DESC")
        conversations = [dict(row) for row in cur.fetchall()]
        
        return {
            "status": "success",
            "count": len(conversations),
            "conversations": conversations
        }
        
    except Exception as e:
        logger.error(f"Error getting raw conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@router.get("/messages-raw")
def get_messages_raw(conversation_id: Optional[int] = None):
    """Lấy raw data của messages từ database"""
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        
        if conversation_id:
            cur.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp", 
                (conversation_id,)
            )
        else:
            cur.execute("SELECT * FROM messages ORDER BY timestamp DESC LIMIT 100")
            
        messages = [dict(row) for row in cur.fetchall()]
        
        return {
            "status": "success",
            "count": len(messages),
            "conversation_id": conversation_id,
            "messages": messages
        }
        
    except Exception as e:
        logger.error(f"Error getting raw messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@router.get("/test-conversation/{conversation_id}")
def test_conversation_operations(conversation_id: int):
    """Test các operations của conversation"""
    try:
        # Test conversation exists
        exists = conversation_service.conversation_exists(conversation_id)
        
        # Test get conversation detail
        detail = None
        if exists:
            try:
                detail = conversation_service.get_conversation_detail(conversation_id)
            except Exception as e:
                detail = f"Error getting detail: {str(e)}"
        
        # Test get messages
        messages = None
        if exists:
            try:
                messages = message_service.get_messages(conversation_id)
            except Exception as e:
                messages = f"Error getting messages: {str(e)}"
        
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "exists": exists,
            "detail": detail,
            "messages": messages
        }
        
    except Exception as e:
        logger.error(f"Error testing conversation operations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backup-db")
def backup_database_endpoint():
    """Backup database"""
    try:
        backup_path = backup_database()
        return {
            "status": "success",
            "message": "Database backed up successfully",
            "backup_path": backup_path
        }
    except Exception as e:
        logger.error(f"Error backing up database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/db-info")
def get_database_info():
    """Lấy thông tin cơ bản database"""
    try:
        from config.settings import settings
        
        db_path = settings.db_path
        db_exists = os.path.exists(db_path)
        db_size = os.path.getsize(db_path) if db_exists else 0
        
        conn = None
        tables_info = {}
        if db_exists:
            try:
                conn = get_db()
                cur = conn.cursor()
                
                # Lấy thông tin các bảng
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cur.fetchall()]
                
                for table in tables:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    
                    cur.execute(f"PRAGMA table_info({table})")
                    columns = [{"name": col[1], "type": col[2], "notnull": col[3]} for col in cur.fetchall()]
                    
                    tables_info[table] = {
                        "row_count": count,
                        "columns": columns
                    }
                    
            except Exception as e:
                tables_info = {"error": str(e)}
            finally:
                if conn:
                    conn.close()
        
        return {
            "status": "success",
            "database": {
                "path": db_path,
                "exists": db_exists,
                "size_bytes": db_size,
                "size_mb": round(db_size / (1024 * 1024), 2),
                "tables": tables_info
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fix-database")
def fix_database_issues():
    """Cố gắng fix các vấn đề database thường gặp"""
    try:
        from config.database import init_db
        
        results = []
        
        # 1. Re-initialize database
        try:
            init_db()
            results.append("Database re-initialized successfully")
        except Exception as e:
            results.append(f"Database init failed: {str(e)}")
        
        # 2. Check and fix foreign keys
        conn = None
        try:
            conn = get_db()
            cur = conn.cursor()
            
            # Enable foreign keys
            cur.execute("PRAGMA foreign_keys = ON")
            
            # Check for orphaned messages
            cur.execute("""
                SELECT COUNT(*) FROM messages m 
                LEFT JOIN conversations c ON m.conversation_id = c.id 
                WHERE c.id IS NULL
            """)
            orphaned_count = cur.fetchone()[0]
            
            if orphaned_count > 0:
                # Delete orphaned messages
                cur.execute("""
                    DELETE FROM messages 
                    WHERE conversation_id NOT IN (SELECT id FROM conversations)
                """)
                conn.commit()
                results.append(f"Removed {orphaned_count} orphaned messages")
            else:
                results.append("No orphaned messages found")
                
        except Exception as e:
            results.append(f"Foreign key check failed: {str(e)}")
        finally:
            if conn:
                conn.close()
        
        # 3. Vacuum database
        try:
            conn = get_db()
            conn.execute("VACUUM")
            conn.close()
            results.append("Database vacuumed successfully")
        except Exception as e:
            results.append(f"Database vacuum failed: {str(e)}")
        
        return {
            "status": "success",
            "message": "Database fix operations completed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error fixing database: {e}")
        raise HTTPException(status_code=500, detail=str(e))