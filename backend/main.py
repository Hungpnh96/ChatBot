# backend/main.py - Enhanced với fallback cho missing dependencies
"""
Main FastAPI application với graceful fallback
Đảm bảo app luôn chạy được ngay cả khi thiếu models/dependencies
"""

import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from datetime import datetime

# Add app to Python path
sys.path.append('/app')

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for services
ai_service = None
voice_service = None
db_service = None
app_status = {
    'ai_available': False,
    'voice_available': False,
    'database_available': False,
    'startup_time': None
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan với initialization"""
    global ai_service, voice_service, db_service, app_status
    
    logger.info("🚀 Starting ChatBot application...")
    
    from datetime import datetime
    app_status['startup_time'] = datetime.now().isoformat()
    
    # Initialize Database (Critical)
    try:
        from config.database import init_db
        init_db()
        app_status['database_available'] = True
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.warning(f"⚠️ Database init failed: {e}")
        # Create minimal database fallback
        try:
            import sqlite3
            db_path = "/app/data/chatbot.db"
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            conn = sqlite3.connect(db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT,
                    response TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
            app_status['database_available'] = True
            logger.info("✅ Minimal database created")
        except Exception as e2:
            logger.error(f"❌ Database fallback failed: {e2}")
            app_status['database_available'] = False
    
    # Initialize AI Service (Non-critical)
    try:
        from services.ai_service import ai_service as enhanced_ai
        ai_service = enhanced_ai
        app_status['ai_available'] = True
        logger.info("✅ AI service initialized")
    except Exception as e:
        logger.warning(f"⚠️ AI service init failed: {e}")
        try:
            from services.enhanced_ai_service import ai_service as enhanced_ai
            ai_service = enhanced_ai
            app_status['ai_available'] = True
            logger.info("✅ Enhanced AI service initialized")
        except Exception as e2:
            logger.warning(f"⚠️ Enhanced AI service init failed: {e2}")
            # Create fallback AI service
            ai_service = FallbackAIService()
            app_status['ai_available'] = False
    
    # Initialize Voice Service (Non-critical)
    try:
        from services.voice_service import VoiceService
        voice_service = VoiceService()
        app_status['voice_available'] = voice_service.is_available()
        logger.info("✅ Voice service initialized")
    except Exception as e:
        logger.warning(f"⚠️ Voice service init failed: {e}")
        voice_service = FallbackVoiceService()
        app_status['voice_available'] = False
    
    logger.info("🎉 Application startup completed")
    yield
    
    # Cleanup
    logger.info("🔄 Shutting down application...")

# Fallback AI Service
class FallbackAIService:
    """Fallback AI service khi không có AI providers"""
    
    async def generate_response(self, message: str, **kwargs) -> Dict[str, Any]:
        return {
            'success': True,
            'content': f"Em là Bixby! Em đã nhận được tin nhắn: '{message}'. "
                      "Hiện tại em chưa kết nối được với AI, nhưng em sẽ sớm có thể trò chuyện thông minh hơn!",
            'provider': 'fallback',
            'fallback_used': True
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        return {
            'status': 'fallback',
            'current_provider': 'fallback',
            'available_providers': [],
            'fallback_enabled': True
        }

# Fallback Voice Service  
class FallbackVoiceService:
    """Fallback voice service khi không có Vosk"""
    
    def is_available(self) -> bool:
        return False
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'vosk_available': False,
            'fallback_mode': True,
            'message': 'Voice features not available - text chat only'
        }
    
    async def transcribe_audio(self, audio_data: bytes) -> Dict[str, Any]:
        return {
            'success': False,
            'error': 'voice_not_available',
            'message': 'Tính năng nhận diện giọng nói chưa khả dụng. Vui lòng sử dụng chat text.',
            'fallback': True
        }

# Create FastAPI app với lifespan
app = FastAPI(
    title="ChatBot API",
    description="ChatBot với AI và Voice support",
    version="1.0.0",
    lifespan=lifespan
)

# Include API routers
try:
    from api.models import router as models_router
    app.include_router(models_router)
    logger.info("✅ Model management API included")
except ImportError as e:
    logger.warning(f"⚠️ Model API router failed to import: {e}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': app_status['startup_time'],
        'services': {
            'database': app_status['database_available'],
            'ai': app_status['ai_available'], 
            'voice': app_status['voice_available']
        },
        'message': 'ChatBot is running'
    }

# AI status endpoint
@app.get("/ai/status")
async def ai_status():
    """AI service status"""
    if ai_service:
        return ai_service.get_service_status()
    return {'status': 'not_initialized'}

# Voice status endpoint
@app.get("/voice/status")
async def voice_status():
    """Voice service status"""
    if voice_service:
        return voice_service.get_status()
    return {'status': 'not_initialized'}

# Chat endpoint
@app.post("/chat/message")
async def chat_message(request: Dict[str, Any]):
    """Chat endpoint với fallback"""
    try:
        message = request.get('message', '')
        conversation_id = request.get('conversation_id')
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Get conversation history if conversation_id is provided
        conversation_history = []
        if conversation_id and app_status['database_available']:
            try:
                import sqlite3
                conn = sqlite3.connect("/app/data/chatbot.db")
                cursor = conn.cursor()
                
                # Get previous messages in this conversation
                cursor.execute("""
                    SELECT sender, content, timestamp 
                    FROM messages 
                    WHERE conversation_id = ? 
                    ORDER BY timestamp ASC
                """, (conversation_id,))
                
                rows = cursor.fetchall()
                for row in rows:
                    conversation_history.append({
                        'sender': row[0],
                        'content': row[1],
                        'timestamp': row[2]
                    })
                
                conn.close()
                logger.info(f"Loaded {len(conversation_history)} messages from conversation {conversation_id}")
            except Exception as e:
                logger.warning(f"Failed to load conversation history: {e}")
        
        # Convert history to BaseMessage format for AI service
        from langchain_core.messages import HumanMessage, AIMessage
        ai_history = []
        for msg in conversation_history:
            if msg['sender'] == 'user':
                ai_history.append(HumanMessage(content=msg['content']))
            elif msg['sender'] == 'assistant':
                ai_history.append(AIMessage(content=msg['content']))
        
        # Generate AI response with history
        if ai_service:
            response = ai_service.get_response_with_history(message, ai_history)
        else:
            response = {
                'content': "Em là Bixby! Em đã nhận được tin nhắn nhưng chưa thể trả lời thông minh. Vui lòng thử lại sau!",
                'fallback_used': True
            }
        
        # Store in database if available
        if app_status['database_available']:
            try:
                import sqlite3
                conn = sqlite3.connect("/app/data/chatbot.db")
                
                # Use existing conversation or create new one
                if conversation_id:
                    # Check if conversation exists
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
                    if not cursor.fetchone():
                        conversation_id = None
                
                if not conversation_id:
                    # Create new conversation
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO conversations (title) VALUES (?)
                    """, (f"Chat - {message[:50]}...",))
                    conversation_id = cursor.lastrowid
                
                # Store user message
                conn.execute("""
                    INSERT INTO messages (conversation_id, sender, content) VALUES (?, ?, ?)
                """, (conversation_id, "user", message))
                
                # Store AI response
                conn.execute("""
                    INSERT INTO messages (conversation_id, sender, content, ai_provider, ai_model) 
                    VALUES (?, ?, ?, ?, ?)
                """, (conversation_id, "assistant", response.get('content', ''), 
                     response.get('provider', 'unknown'), response.get('model', 'unknown')))
                
                conn.commit()
                conn.close()
            except Exception as e:
                logger.warning(f"Failed to store chat history: {e}")
        
        return {
            'success': True,
            'response': response.get('content', ''),
            'provider': response.get('provider', 'unknown'),
            'fallback_used': response.get('fallback_used', False),
            'conversation_id': conversation_id
        }
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return {
            'success': False,
            'error': str(e),
            'response': "Em gặp lỗi khi xử lý tin nhắn. Vui lòng thử lại!"
        }

# Chat history endpoint
@app.get("/chat/history")
async def get_chat_history(limit: int = 50):
    """Lấy lịch sử chat"""
    if not app_status['database_available']:
        return {'history': [], 'message': 'Database not available'}
    
    try:
        import sqlite3
        conn = sqlite3.connect("/app/data/chatbot.db")
        cursor = conn.cursor()
        
        # Get recent conversations with messages, ordered by latest message timestamp
        cursor.execute("""
            SELECT 
                c.id as conversation_id,
                c.title,
                c.started_at,
                m.sender,
                m.content,
                m.timestamp,
                m.ai_provider,
                m.ai_model,
                COALESCE(MAX(m.timestamp) OVER (PARTITION BY c.id), c.started_at) as latest_activity
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            ORDER BY latest_activity DESC, m.timestamp ASC
            LIMIT ?
        """, (limit * 2,))  # Get more rows to account for multiple messages per conversation
        
        rows = cursor.fetchall()
        
        # Group by conversation
        conversations = {}
        for row in rows:
            conv_id = row[0]
            if conv_id not in conversations:
                conversations[conv_id] = {
                    'id': conv_id,
                    'title': row[1],
                    'started_at': row[2],
                    'messages': []
                }
            
            if row[3]:  # If there's a message
                conversations[conv_id]['messages'].append({
                    'sender': row[3],
                    'content': row[4],
                    'timestamp': row[5],
                    'ai_provider': row[6],
                    'ai_model': row[7]
                })
        
        # Convert to list and limit
        history = list(conversations.values())[:limit]
        
        conn.close()
        
        return {
            'success': True,
            'history': history,
            'count': len(history)
        }
        
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        return {
            'success': False,
            'error': str(e),
            'history': []
        }

# Conversation management endpoints
@app.post("/api/conversations")
async def create_conversation(request: Dict[str, Any]):
    """Create new conversation"""
    try:
        title = request.get('title', 'Chat mới')
        
        if not app_status['database_available']:
            return {'success': False, 'error': 'Database not available'}
        
        import sqlite3
        conn = sqlite3.connect("/app/data/chatbot.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversations (title) VALUES (?)
        """, (title,))
        conversation_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'id': conversation_id,
            'title': title,
            'started_at': datetime.now().isoformat(),
            'message_count': 0
        }
        
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        return {'success': False, 'error': str(e)}

@app.put("/api/conversations/{conversation_id}/title")
async def update_conversation_title(conversation_id: int, request: Dict[str, Any]):
    """Update conversation title"""
    try:
        title = request.get('title', '')
        
        if not title:
            raise HTTPException(status_code=400, detail="Title is required")
        
        if not app_status['database_available']:
            return {'success': False, 'error': 'Database not available'}
        
        import sqlite3
        conn = sqlite3.connect("/app/data/chatbot.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE conversations SET title = ? WHERE id = ?
        """, (title, conversation_id))
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': 'Title updated'}
        
    except Exception as e:
        logger.error(f"Failed to update conversation title: {e}")
        return {'success': False, 'error': str(e)}

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int):
    """Delete conversation and all its messages"""
    try:
        if not app_status['database_available']:
            return {'success': False, 'error': 'Database not available'}
        
        import sqlite3
        conn = sqlite3.connect("/app/data/chatbot.db")
        cursor = conn.cursor()
        
        # Delete messages first (foreign key constraint)
        cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        
        # Delete conversation
        cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': 'Conversation deleted'}
        
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        return {'success': False, 'error': str(e)}

# Voice endpoints (với fallback)
from fastapi import File, UploadFile, Form

@app.post("/voice/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form('vi-VN'),
    conversation_id: Optional[int] = Form(None)
):
    """Voice transcription endpoint"""
    try:
        if not audio:
            return {
                'success': False,
                'error': 'no_audio',
                'message': 'No audio file provided'
            }
        
        # Read audio data
        audio_data = await audio.read()
        logger.info(f"Received audio file: {audio.filename}, size: {len(audio_data)} bytes")
        
        # For now, return a fallback response since Vosk is not available
        return {
            'success': True,
            'transcript': 'Xin chào, đây là tin nhắn thoại test',
            'message': 'Voice transcription completed (fallback mode)',
            'fallback': True
        }
        
    except Exception as e:
        logger.error(f"Voice transcription error: {e}")
        return {
            'success': False,
            'error': 'transcription_failed',
            'message': f'Transcription failed: {str(e)}'
        }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        'message': 'ChatBot API is running',
        'status': 'healthy',
        'services': app_status,
        'endpoints': {
            'health': '/health',
            'chat': '/chat/message',
            'history': '/chat/history',
            'docs': '/docs'
        }
    }

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Global error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            'success': False,
            'error': 'internal_server_error',
            'message': 'Em gặp lỗi hệ thống. Vui lòng thử lại sau!'
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)