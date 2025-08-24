#!/usr/bin/env python3
"""
Script to download Vosk models for speech recognition
Supports Vietnamese and English models
"""

import os
import sys
import zipfile
import requests
from pathlib import Path
import logging
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Model configurations
VOSK_MODELS = {
    "vi": {
        "name": "vosk-model-vn-0.4",
        "url": "https://alphacephei.com/vosk/models/vosk-model-vn-0.4.zip",
        "size_mb": 78,
        "description": "Vietnamese model (78MB)"
    },
    "en-small": {
        "name": "vosk-model-small-en-us-0.15",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip", 
        "size_mb": 40,
        "description": "Small English US model (40MB)"
    },
    "en": {
        "name": "vosk-model-en-us-0.22",
        "url": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip",
        "size_mb": 1800,
        "description": "Full English US model (1.8GB)"
    }
}

def download_file(url: str, destination: Path, description: str = "") -> bool:
    """Download file with progress bar"""
    try:
        logger.info(f"Downloading {description} from {url}")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\rProgress: {progress:.1f}% ({downloaded // (1024*1024)}MB/{total_size // (1024*1024)}MB)", end='', flush=True)
        
        print()  # New line after progress
        logger.info(f"✅ Downloaded {description} successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to download {description}: {e}")
        if destination.exists():
            destination.unlink()
        return False

def extract_zip(zip_path: Path, extract_to: Path) -> bool:
    """Extract zip file"""
    try:
        logger.info(f"Extracting {zip_path.name}...")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        
        logger.info(f"✅ Extracted {zip_path.name} successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to extract {zip_path.name}: {e}")
        return False

def setup_model_directory(model_key: str, models_dir: Path) -> bool:
    """Download and setup a specific model"""
    model_config = VOSK_MODELS[model_key]
    model_name = model_config["name"]
    model_url = model_config["url"]
    description = model_config["description"]
    
    # Determine target directory based on language
    if model_key == "vi":
        target_dir = models_dir / "vosk-vi"
    else:
        target_dir = models_dir / "vosk-en"
    
    # Check if model already exists
    if target_dir.exists() and any(target_dir.iterdir()):
        logger.info(f"✅ Model already exists at {target_dir}")
        return True
    
    # Create directories
    models_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = models_dir / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Download model
        zip_path = temp_dir / f"{model_name}.zip"
        if not download_file(model_url, zip_path, description):
            return False
        
        # Extract model
        if not extract_zip(zip_path, temp_dir):
            return False
        
        # Move extracted model to target directory
        extracted_model_dir = temp_dir / model_name
        if not extracted_model_dir.exists():
            logger.error(f"❌ Extracted model directory not found: {extracted_model_dir}")
            return False
        
        # Remove target directory if it exists
        if target_dir.exists():
            shutil.rmtree(target_dir)
        
        # Move model to target location
        shutil.move(str(extracted_model_dir), str(target_dir))
        logger.info(f"✅ Model installed at {target_dir}")
        
        # Cleanup
        zip_path.unlink()
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to setup model {model_key}: {e}")
        # Cleanup on failure
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        return False

def check_disk_space(required_mb: int) -> bool:
    """Check if there's enough disk space"""
    try:
        statvfs = os.statvfs('.')
        free_bytes = statvfs.f_frsize * statvfs.f_bavail
        free_mb = free_bytes / (1024 * 1024)
        
        if free_mb < required_mb:
            logger.error(f"❌ Insufficient disk space. Required: {required_mb}MB, Available: {free_mb:.0f}MB")
            return False
        
        logger.info(f"✅ Disk space check passed. Required: {required_mb}MB, Available: {free_mb:.0f}MB")
        return True
        
    except Exception as e:
        logger.warning(f"⚠️ Could not check disk space: {e}")
        return True  # Proceed anyway

def main():
    """Main function"""
    # Parse command line arguments
    models_to_download = ["vi"]  # Default to Vietnamese
    
    if len(sys.argv) > 1:
        models_to_download = sys.argv[1].split(",")
    
    # Validate model keys
    for model_key in models_to_download:
        if model_key not in VOSK_MODELS:
            logger.error(f"❌ Unknown model: {model_key}. Available: {list(VOSK_MODELS.keys())}")
            sys.exit(1)
    
    # Determine models directory
    models_dir = Path("/app/data/models")
    if not models_dir.exists():
        # Fallback for local development
        models_dir = Path("./data/models")
    
    logger.info(f"Models directory: {models_dir}")
    
    # Check disk space
    total_size_mb = sum(VOSK_MODELS[key]["size_mb"] for key in models_to_download)
    if not check_disk_space(total_size_mb + 100):  # Add 100MB buffer
        sys.exit(1)
    
    # Download and setup models
    success_count = 0
    for model_key in models_to_download:
        logger.info(f"\n📥 Setting up {VOSK_MODELS[model_key]['description']}...")
        
        if setup_model_directory(model_key, models_dir):
            success_count += 1
        else:
            logger.error(f"❌ Failed to setup model: {model_key}")
    
    # Summary
    logger.info(f"\n🎯 Summary: {success_count}/{len(models_to_download)} models installed successfully")
    
    if success_count == len(models_to_download):
        logger.info("✅ All models installed successfully!")
        
        # List installed models
        logger.info("\n📋 Installed models:")
        for model_dir in models_dir.glob("vosk-*"):
            if model_dir.is_dir():
                size_mb = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file()) / (1024*1024)
                logger.info(f"  - {model_dir.name}: {size_mb:.1f}MB")
        
        sys.exit(0)
    else:
        logger.error("❌ Some models failed to install")
        sys.exit(1)

if __name__ == "__main__":
    main()