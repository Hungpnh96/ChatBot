#!/usr/bin/env python3
"""
Model Management API - Quản lý models qua REST API
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import logging
from services.model_manager import model_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["Model Management"])

@router.get("/status")
async def get_model_status():
    """Lấy status của tất cả models"""
    try:
        status = model_manager.get_model_status()
        return {
            "success": True,
            "data": status,
            "message": "Model status retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model status: {str(e)}")

@router.get("/detect")
async def detect_models():
    """Detect tất cả models có sẵn"""
    try:
        models = model_manager.detect_all_models()
        
        # Convert to serializable format
        serializable_models = {}
        for key, model_info in models.items():
            serializable_models[key] = {
                "name": model_info.name,
                "type": model_info.type.value,
                "path": model_info.path,
                "size_mb": model_info.size_mb,
                "status": model_info.status,
                "description": model_info.description,
                "required": model_info.required
            }
        
        return {
            "success": True,
            "data": {
                "total_models": len(models),
                "models": serializable_models
            },
            "message": f"Detected {len(models)} models"
        }
    except Exception as e:
        logger.error(f"Error detecting models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to detect models: {str(e)}")

@router.post("/ensure")
async def ensure_required_models(background_tasks: BackgroundTasks):
    """Đảm bảo tất cả required models có sẵn (async)"""
    try:
        # Run in background để không block API
        background_tasks.add_task(model_manager.ensure_required_models)
        
        return {
            "success": True,
            "message": "Model download started in background. Check /models/status for progress."
        }
    except Exception as e:
        logger.error(f"Error ensuring models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ensure models: {str(e)}")

@router.post("/download/{model_key}")
async def download_specific_model(model_key: str, background_tasks: BackgroundTasks):
    """Download một model cụ thể"""
    try:
        # Detect models trước
        all_models = model_manager.detect_all_models()
        
        if model_key not in all_models:
            raise HTTPException(status_code=404, detail=f"Model {model_key} not found")
        
        model_info = all_models[model_key]
        
        if model_info.status == "available":
            return {
                "success": True,
                "message": f"Model {model_key} is already available"
            }
        
        # Download in background
        background_tasks.add_task(model_manager._download_model, model_key, model_info)
        
        return {
            "success": True,
            "message": f"Download started for {model_key}. Check /models/status for progress."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading model {model_key}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download model: {str(e)}")

@router.post("/validate")
async def validate_models():
    """Validate tất cả models"""
    try:
        validation_results = model_manager.validate_models()
        
        # Count results
        total = len(validation_results)
        valid = sum(1 for v in validation_results.values() if v)
        invalid = total - valid
        
        return {
            "success": True,
            "data": {
                "total_models": total,
                "valid_models": valid,
                "invalid_models": invalid,
                "validation_results": validation_results
            },
            "message": f"Validation complete: {valid}/{total} models are valid"
        }
    except Exception as e:
        logger.error(f"Error validating models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate models: {str(e)}")

@router.post("/cleanup")
async def cleanup_old_models(keep_recent: int = 3):
    """Dọn dẹp models cũ"""
    try:
        cleanup_results = model_manager.cleanup_old_models(keep_recent)
        
        # Count results
        total = len(cleanup_results)
        success = sum(1 for v in cleanup_results.values() if v)
        failed = total - success
        
        return {
            "success": True,
            "data": {
                "total_processed": total,
                "successfully_removed": success,
                "failed_removals": failed,
                "cleanup_results": cleanup_results
            },
            "message": f"Cleanup complete: {success}/{total} models removed successfully"
        }
    except Exception as e:
        logger.error(f"Error cleaning up models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup models: {str(e)}")

@router.get("/recommended")
async def get_recommended_models():
    """Lấy danh sách models khuyến nghị"""
    try:
        recommended = {
            "ollama": [
                {
                    "name": "gemma2:9b",
                    "description": "Model mặc định, cân bằng tốt về performance và accuracy",
                    "size_mb": 5000,
                    "recommended_for": "General purpose, Vietnamese language"
                },
                {
                    "name": "llama3.1:8b", 
                    "description": "Model phổ biến, nhanh và ổn định",
                    "size_mb": 4500,
                    "recommended_for": "Fast responses, English language"
                },
                {
                    "name": "qwen2.5:7b",
                    "description": "Model tốt cho tiếng Việt và đa ngôn ngữ",
                    "size_mb": 4000,
                    "recommended_for": "Vietnamese language, multilingual"
                },
                {
                    "name": "gemma2:2b",
                    "description": "Model nhẹ cho server yếu",
                    "size_mb": 1500,
                    "recommended_for": "Low resource servers, quick responses"
                }
            ],
            "vosk": [
                {
                    "name": "vosk-vi",
                    "description": "Vietnamese speech recognition model",
                    "size_mb": 78,
                    "required": True
                },
                {
                    "name": "vosk-en",
                    "description": "English speech recognition model", 
                    "size_mb": 40,
                    "required": False
                }
            ]
        }
        
        return {
            "success": True,
            "data": recommended,
            "message": "Recommended models retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting recommended models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommended models: {str(e)}")

@router.post("/configure")
async def configure_model_settings(settings: Dict[str, Any]):
    """Cấu hình model settings"""
    try:
        # Validate settings
        allowed_settings = {
            "OLLAMA_MODEL", "OLLAMA_BASE_URL", "VOSK_MODEL_PATH",
            "PREFERRED_AI_PROVIDER", "AUTO_DOWNLOAD_MODELS",
            "MODEL_DOWNLOAD_TIMEOUT", "MAX_CONCURRENT_DOWNLOADS"
        }
        
        invalid_settings = set(settings.keys()) - allowed_settings
        if invalid_settings:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid settings: {invalid_settings}. Allowed: {allowed_settings}"
            )
        
        # Update config
        model_manager.config.update(settings)
        
        # Save to config file
        try:
            import json
            config_path = model_manager.base_dir / "config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    current_config = json.load(f)
            else:
                current_config = {}
            
            current_config.update(settings)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(current_config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.warning(f"Failed to save config to file: {e}")
        
        return {
            "success": True,
            "message": f"Configuration updated successfully",
            "updated_settings": settings
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure models: {str(e)}")

@router.get("/health")
async def model_health_check():
    """Health check cho model management"""
    try:
        # Quick health check
        status = model_manager.get_model_status()
        
        # Check if critical models are available
        critical_models_available = status["missing_required"] == 0
        
        health_status = {
            "status": "healthy" if critical_models_available else "degraded",
            "critical_models_available": critical_models_available,
            "total_models": status["total_models"],
            "available_models": status["available_models"],
            "missing_required": status["missing_required"]
        }
        
        return {
            "success": True,
            "data": health_status,
            "message": "Model health check completed"
        }
    except Exception as e:
        logger.error(f"Error in model health check: {e}")
        return {
            "success": False,
            "data": {"status": "unhealthy"},
            "message": f"Model health check failed: {str(e)}"
        }
