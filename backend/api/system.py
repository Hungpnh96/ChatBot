# FILE: api/system.py
# ACTION: TÌM VÀ THAY THẾ các endpoints để sửa lỗi f-string

from fastapi import APIRouter
from models.schemas import StatsResponse, ConfigResponse, APIResponse
from config.settings import settings
from config.database import check_db_exists, get_db_stats
from services.ai_service import ai_service

router = APIRouter(prefix="/chat/api", tags=["system"])

@router.get("/Healthcheck", response_model=APIResponse)
def root():
    """Enhanced health check endpoint with AI provider info"""
    provider_info = ai_service.get_current_provider_info()
    
    return APIResponse(
        message="Bixby Chatbot API is running",
        status="healthy",
        data={
            "ai_available": ai_service.is_available(),
            "providers": {
                "github": provider_info["github_available"],
                "ollama": provider_info["ollama_available"],
                "current": provider_info["current_provider"]
            }
        }
    )

@router.get("/config", response_model=ConfigResponse)
def get_config():
    """Lấy thông tin config với AI providers info"""
    provider_info = ai_service.get_current_provider_info()
    
    # Sửa lỗi f-string ở đây
    current_provider = provider_info['current_provider']
    model_key = f'{current_provider}_model'
    current_model = provider_info.get(model_key, 'unknown')
    
    return ConfigResponse(
        config=settings.get_safe_config(),
        db_path=settings.db_path,
        db_exists=check_db_exists(),
        ai_status="available" if ai_service.is_available() else "unavailable",
        model=f"{current_provider}:{current_model}",
        timezone=settings.timezone,
        ai_providers=settings.get_ai_providers_config()
    )

@router.get("/stats", response_model=StatsResponse)
def get_stats():
    """Lấy thống kê database với AI info"""
    db_stats = get_db_stats()
    provider_info = ai_service.get_current_provider_info()
    
    return StatsResponse(
        **db_stats,
        ai_status="available" if ai_service.is_available() else "unavailable",
        ai_providers=provider_info
    )

@router.get("/database-path")
def get_database_path():
    """Lấy thông tin database path hiện tại"""
    from config.settings import settings
    import os
    
    db_path = settings.db_path
    db_exists = os.path.exists(db_path)
    db_dir = os.path.dirname(db_path)
    
    return {
        "database_path": db_path,
        "database_exists": db_exists,
        "database_directory": db_dir,
        "directory_exists": os.path.exists(db_dir),
        "current_working_directory": os.getcwd(),
        "files_in_db_dir": os.listdir(db_dir) if os.path.exists(db_dir) else []
    }