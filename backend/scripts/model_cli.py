#!/usr/bin/env python3
"""
Model Management CLI Tool
Quản lý models từ command line
"""

import sys
import json
import argparse
import logging
from pathlib import Path

# Add app to Python path
sys.path.append('/app')

from services.model_manager import model_manager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_status():
    """In status của tất cả models"""
    print("🔍 Model Status:")
    print("=" * 50)
    
    try:
        status = model_manager.get_model_status()
        
        print(f"Total Models: {status['total_models']}")
        print(f"Available: {status['available_models']}")
        print(f"Required: {status['required_models']}")
        print(f"Missing Required: {status['missing_required']}")
        print()
        
        # Print by type
        for model_type, models in status['models_by_type'].items():
            print(f"📦 {model_type.upper()} Models:")
            for model in models:
                status_icon = "✅" if model['status'] == 'available' else "❌"
                required_icon = "🔴" if model['required'] else "⚪"
                print(f"  {status_icon} {required_icon} {model['name']} ({model['size_mb']:.1f}MB)")
            print()
            
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        sys.exit(1)

def detect_models():
    """Detect tất cả models"""
    print("🔍 Detecting Models...")
    print("=" * 50)
    
    try:
        models = model_manager.detect_all_models()
        
        for model_key, model_info in models.items():
            status_icon = "✅" if model_info.status == 'available' else "❌"
            required_icon = "🔴" if model_info.required else "⚪"
            print(f"{status_icon} {required_icon} {model_key}")
            print(f"    Name: {model_info.name}")
            print(f"    Type: {model_info.type.value}")
            print(f"    Path: {model_info.path}")
            print(f"    Size: {model_info.size_mb:.1f}MB")
            print(f"    Status: {model_info.status}")
            print()
            
    except Exception as e:
        logger.error(f"Failed to detect models: {e}")
        sys.exit(1)

def download_models(model_keys=None):
    """Download models"""
    if model_keys:
        print(f"📥 Downloading specific models: {', '.join(model_keys)}")
    else:
        print("📥 Downloading required models...")
    print("=" * 50)
    
    try:
        if model_keys:
            # Download specific models
            all_models = model_manager.detect_all_models()
            for model_key in model_keys:
                if model_key in all_models:
                    model_info = all_models[model_key]
                    if model_info.status != 'available':
                        print(f"Downloading {model_key}...")
                        success = model_manager._download_model(model_key, model_info)
                        if success:
                            print(f"✅ {model_key} downloaded successfully")
                        else:
                            print(f"❌ Failed to download {model_key}")
                    else:
                        print(f"✅ {model_key} already available")
                else:
                    print(f"❌ Model {model_key} not found")
        else:
            # Download required models
            results = model_manager.ensure_required_models()
            for model_key, success in results.items():
                status = "✅" if success else "❌"
                print(f"{status} {model_key}")
                
    except Exception as e:
        logger.error(f"Failed to download models: {e}")
        sys.exit(1)

def validate_models():
    """Validate tất cả models"""
    print("🔍 Validating Models...")
    print("=" * 50)
    
    try:
        results = model_manager.validate_models()
        
        total = len(results)
        valid = sum(1 for v in results.values() if v)
        invalid = total - valid
        
        print(f"Total Models: {total}")
        print(f"Valid: {valid}")
        print(f"Invalid: {invalid}")
        print()
        
        for model_key, is_valid in results.items():
            status_icon = "✅" if is_valid else "❌"
            print(f"{status_icon} {model_key}")
            
    except Exception as e:
        logger.error(f"Failed to validate models: {e}")
        sys.exit(1)

def cleanup_models(keep_recent=3):
    """Cleanup old models"""
    print(f"🧹 Cleaning up old models (keeping {keep_recent} recent)...")
    print("=" * 50)
    
    try:
        results = model_manager.cleanup_old_models(keep_recent)
        
        if not results:
            print("No cleanup needed")
            return
            
        total = len(results)
        success = sum(1 for v in results.values() if v)
        failed = total - success
        
        print(f"Total processed: {total}")
        print(f"Successfully removed: {success}")
        print(f"Failed removals: {failed}")
        print()
        
        for model_key, success in results.items():
            status_icon = "✅" if success else "❌"
            print(f"{status_icon} {model_key}")
            
    except Exception as e:
        logger.error(f"Failed to cleanup models: {e}")
        sys.exit(1)

def show_recommended():
    """Show recommended models"""
    print("💡 Recommended Models:")
    print("=" * 50)
    
    try:
        recommended = {
            "ollama": [
                {
                    "name": "gemma2:2b",
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
        
        for category, models in recommended.items():
            print(f"📦 {category.upper()}:")
            for model in models:
                required_icon = "🔴" if model.get('required', False) else "⚪"
                print(f"  {required_icon} {model['name']} ({model['size_mb']}MB)")
                print(f"    {model['description']}")
                print(f"    Recommended for: {model['recommended_for']}")
                print()
                
    except Exception as e:
        logger.error(f"Failed to show recommended models: {e}")
        sys.exit(1)

def configure_models():
    """Configure model settings"""
    print("⚙️ Current Model Configuration:")
    print("=" * 50)
    
    try:
        config = model_manager.config
        
        print("Current settings:")
        for key, value in config.items():
            if 'key' in key.lower() or 'token' in key.lower():
                print(f"  {key}: ***hidden***")
            else:
                print(f"  {key}: {value}")
        print()
        
        print("To update configuration, edit backend/config.json")
        print("Or use the API endpoint: POST /models/configure")
        
    except Exception as e:
        logger.error(f"Failed to show configuration: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Model Management CLI Tool")
    parser.add_argument('command', choices=[
        'status', 'detect', 'download', 'validate', 'cleanup', 
        'recommended', 'configure'
    ], help='Command to execute')
    
    parser.add_argument('--models', nargs='+', help='Specific models to download')
    parser.add_argument('--keep', type=int, default=3, help='Number of recent models to keep (for cleanup)')
    
    args = parser.parse_args()
    
    print("🤖 ChatBot Model Management CLI")
    print("=" * 50)
    
    if args.command == 'status':
        print_status()
    elif args.command == 'detect':
        detect_models()
    elif args.command == 'download':
        download_models(args.models)
    elif args.command == 'validate':
        validate_models()
    elif args.command == 'cleanup':
        cleanup_models(args.keep)
    elif args.command == 'recommended':
        show_recommended()
    elif args.command == 'configure':
        configure_models()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()


