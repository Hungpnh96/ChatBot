import sqlite3
import os
import logging
from fastapi import HTTPException
from .settings import settings

logger = logging.getLogger(__name__)

def ensure_data_directory():
    """Đảm bảo thư mục data tồn tại"""
    db_dir = os.path.dirname(settings.db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        logger.info(f"Created data directory: {db_dir}")

def init_db():
    """Khởi tạo database và tạo các bảng cần thiết"""
    logger.info("START - Initializing database")
    try:
        # Đảm bảo thư mục data tồn tại
        ensure_data_directory()
        
        conn = sqlite3.connect(settings.db_path)
        cur = conn.cursor()
        
        # Enable foreign keys
        cur.execute("PRAGMA foreign_keys = ON")
        
        # Tạo bảng conversations với title
        cur.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT DEFAULT 'Chat mới',
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Thêm cột title nếu chưa có (cho database cũ)
        cur.execute("PRAGMA table_info(conversations)")
        columns = [column[1] for column in cur.fetchall()]
        if 'title' not in columns:
            cur.execute("ALTER TABLE conversations ADD COLUMN title TEXT DEFAULT 'Chat mới'")
            logger.info("Added title column to conversations table")
        
        # Tạo bảng messages với AI provider metadata
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                sender TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ai_provider TEXT,
                ai_model TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
            )
        """)
        
        # Thêm cột ai_provider và ai_model nếu chưa có
        cur.execute("PRAGMA table_info(messages)")
        columns = [column[1] for column in cur.fetchall()]
        if 'ai_provider' not in columns:
            cur.execute("ALTER TABLE messages ADD COLUMN ai_provider TEXT")
            logger.info("Added ai_provider column to messages table")
        if 'ai_model' not in columns:
            cur.execute("ALTER TABLE messages ADD COLUMN ai_model TEXT")
            logger.info("Added ai_model column to messages table")
        
        # Tạo indexes để tăng performance
        cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_conversations_started_at ON conversations(started_at)")
        
        conn.commit()
        
        # Kiểm tra và log thông tin database
        cur.execute("SELECT COUNT(*) FROM conversations")
        conv_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM messages")
        msg_count = cur.fetchone()[0]
        
        logger.info(f"Database initialized successfully at {settings.db_path}")
        logger.info(f"Database stats - Conversations: {conv_count}, Messages: {msg_count}")
        
        conn.close()
        logger.info("END - Database initialization completed")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def check_db_exists() -> bool:
    """Kiểm tra database có tồn tại không"""
    if not os.path.exists(settings.db_path):
        logger.warning(f"Database file not found at {settings.db_path}")
        return False
    return True

def get_db():
    """Tạo kết nối database với error handling và connection pooling"""
    try:
        if not check_db_exists():
            logger.warning("Database not found, initializing...")
            init_db()
            
        conn = sqlite3.connect(
            settings.db_path,
            timeout=30.0,  # Tăng timeout
            check_same_thread=False  # Cho phép multi-threading
        )
        conn.row_factory = sqlite3.Row
        
        # Enable foreign keys và optimizations
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")  # Better concurrency
        conn.execute("PRAGMA synchronous = NORMAL")  # Balance between safety and speed
        conn.execute("PRAGMA cache_size = 1000")  # Increase cache
        
        return conn
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

def get_db_stats() -> dict:
    """Lấy thống kê database với error handling"""
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Đếm conversations
        cur.execute("SELECT COUNT(*) FROM conversations")
        conv_count = cur.fetchone()[0]
        
        # Đếm messages
        cur.execute("SELECT COUNT(*) FROM messages")
        msg_count = cur.fetchone()[0]
        
        # Đếm messages theo sender
        cur.execute("SELECT sender, COUNT(*) FROM messages GROUP BY sender")
        sender_stats = dict(cur.fetchall())
        
        # Conversation gần nhất
        cur.execute("""
            SELECT id, title, started_at 
            FROM conversations 
            ORDER BY started_at DESC 
            LIMIT 1
        """)
        latest_conv = cur.fetchone()
        
        # Database file size
        db_size = os.path.getsize(settings.db_path) if os.path.exists(settings.db_path) else 0
        
        return {
            "conversations": conv_count,
            "messages": msg_count,
            "messages_by_sender": sender_stats,
            "latest_conversation": dict(latest_conv) if latest_conv else None,
            "db_path": settings.db_path,
            "db_size_bytes": db_size,
            "db_size_mb": round(db_size / (1024 * 1024), 2)
        }
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {
            "error": str(e),
            "db_path": settings.db_path,
            "conversations": 0,
            "messages": 0,
            "messages_by_sender": {},
            "latest_conversation": None
        }
    finally:
        if conn:
            conn.close()

def verify_database_integrity():
    """Kiểm tra tính toàn vẹn của database"""
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # PRAGMA integrity_check
        cur.execute("PRAGMA integrity_check")
        result = cur.fetchone()[0]
        
        if result == "ok":
            logger.info("Database integrity check passed")
            return True
        else:
            logger.error(f"Database integrity check failed: {result}")
            return False
            
    except Exception as e:
        logger.error(f"Error checking database integrity: {e}")
        return False
    finally:
        if conn:
            conn.close()

def backup_database(backup_path: str = None):
    """Backup database"""
    if not backup_path:
        backup_path = f"{settings.db_path}.backup"
    
    try:
        conn = get_db()
        backup_conn = sqlite3.connect(backup_path)
        conn.backup(backup_conn)
        backup_conn.close()
        conn.close()
        logger.info(f"Database backed up to {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Error backing up database: {e}")
        raise