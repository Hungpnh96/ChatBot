# main.py - Complete FastAPI app with Voice Chat support
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
# Thêm vào imports
from api.enhanced_chat import router as enhanced_chat_router

# Setup logging first
from utils.logger import setup_logging
setup_logging()

import logging
logger = logging.getLogger(__name__)

# Import configurations and services
from config.settings import settings
from config.database import init_db

# Import API routers
from api.chat import router as chat_router
from api.conversations import router as conversations_router
from api.system import router as system_router
from api.debug import router as debug_router
from api.voice import router as voice_router  # NEW: Voice chat router

# Import services for cleanup
from services.voice_service import voice_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown"""
    # Startup
    logger.info("🚀 START - Application startup")
    try:
        # Log configuration
        settings.log_config()
        
        # Initialize database
        init_db()
        
        # Initialize voice service health check
        voice_health = await voice_service.health_check()
        logger.info(f"Voice service status: {voice_health.get('status', 'unknown')}")
        
        logger.info("✅ END - Application startup completed successfully")
        
        yield  # Application runs here
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
        raise
    finally:
        # Shutdown
        logger.info("🔄 Application shutdown starting")
        try:
            # Cleanup voice service
            voice_service.cleanup()
            logger.info("✅ Voice service cleanup completed")
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")
        logger.info("✅ Application shutdown completed")


# Create FastAPI app with enhanced configuration
app = FastAPI(
    title="Bixby Chatbot API with Voice Chat", 
    version="2.0.0",
    description="Intelligent Vietnamese Chatbot API with conversation management and voice chat support",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS with enhanced settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Transcript", "X-AI-Response", "X-Conversation-ID", "X-AI-Provider", "X-AI-Model"]
)

# Include all routers
app.include_router(chat_router)
app.include_router(conversations_router)
app.include_router(system_router)
app.include_router(debug_router)
app.include_router(voice_router)  # NEW: Voice chat endpoints

# Enhanced root endpoint
@app.get("/")
def root():
    """Root endpoint with comprehensive API information"""
    return {
        "message": "Bixby Chatbot API with Voice Chat", 
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Text Chat with AI",
            "Voice Chat (Speech-to-Text & Text-to-Speech)",
            "Multi-AI Provider Support",
            "Conversation Management",
            "Vietnamese Language Optimized"
        ],
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/chat/api/health",
            "voice_capabilities": "/chat/api/voice/capabilities",
            "search_test": "/chat/api/search/test",
            "personal_info_test": "/chat/api/personal-info/test",
            "demo_realtime": "/chat/api/demo/realtime-question",
            "demo_personal": "/chat/api/demo/personal-question"
        },
        "supported_languages": ["vi-VN", "en-US", "ja-JP", "ko-KR", "zh-CN"],
        "ai_providers": ["github", "ollama", "auto"]
    }

# Enhanced health check endpoint
@app.get("/health")
async def comprehensive_health_check():
    """Comprehensive health check including voice services"""
    try:
        # Check voice service health
        voice_health = await voice_service.health_check()
        
        # Check AI service health (assuming this exists)
        from services.ai_service import ai_service
        ai_health = {
            "github_available": ai_service.is_github_available(),
            "ollama_available": ai_service.is_ollama_available(),
            "current_provider": ai_service.current_provider.value
        }
        
        # Overall health assessment
        overall_healthy = (
            voice_health.get("status") == "healthy" and
            (ai_health["github_available"] or ai_health["ollama_available"])
        )
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "timestamp": voice_health.get("timestamp"),
            "services": {
                "voice": voice_health,
                "ai": ai_health,
                "database": "healthy",  # Could add actual DB health check
                "api": "healthy"
            },
            "capabilities": {
                "text_chat": True,
                "voice_chat": voice_health.get("tts_available", False) and voice_health.get("speech_recognition_available", False),
                "multi_ai": ai_health["github_available"] or ai_health["ollama_available"]
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": logger.info("Health check failed")
        }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Endpoint not found",
        "message": "Check /docs for available endpoints",
        "available_endpoints": [
            "/chat/api/chat",
            "/chat/api/voice/transcribe",
            "/chat/api/voice/text-to-speech",
            "/chat/api/voice/voice-chat"
        ]
    }

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return {
        "error": "Internal server error",
        "message": "Something went wrong. Please try again later.",
        "support": "Check logs for details"
    }

# Development helpers
if __name__ == "__main__":
    logger.info("🎤 Starting Bixby Chatbot FastAPI application with Voice Chat")
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info",
        access_log=True
    )