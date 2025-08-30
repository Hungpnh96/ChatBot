#!/usr/bin/env python3
"""
Enhanced Model Manager - Quản lý tất cả models độc lập
Hỗ trợ auto-download, auto-detection, và production deployment
"""

import os
import sys
import json
import time
import requests
import subprocess
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Set, Any
from enum import Enum
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Các loại model được hỗ trợ"""
    OLLAMA = "ollama"
    VOSK = "vosk"
    GITHUB = "github"
    LOCAL = "local"

@dataclass
class ModelInfo:
    """Thông tin model"""
    name: str
    type: ModelType
    path: str
    size_mb: float
    status: str  # "available", "downloading", "error", "not_found"
    description: str
    download_url: Optional[str] = None
    required: bool = False

class ModelManager:
    """Enhanced Model Manager với auto-detection và smart management"""
    
    def __init__(self, base_dir: str = "/app"):
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "data"
        self.models_dir = self.data_dir / "models"
        self.logs_dir = self.base_dir / "logs"
        
        # Tạo thư mục cần thiết
        self.data_dir.mkdir(exist_ok=True)
        self.models_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Cache cho models đã detect
        self._detected_models: Dict[str, ModelInfo] = {}
        self._model_status: Dict[str, str] = {}
        
        # Configuration
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load configuration từ config.json"""
        config_path = self.base_dir / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        
        # Default config
        return {
            "OLLAMA_BASE_URL": "http://localhost:11434",
            "OLLAMA_MODEL": "gemma2:9b",
            "VOSK_MODEL_PATH": "/app/data/models/vosk-vi",
            "PREFERRED_AI_PROVIDER": "ollama",
            "AUTO_DOWNLOAD_MODELS": True,
            "MODEL_DOWNLOAD_TIMEOUT": 1800,
            "MAX_CONCURRENT_DOWNLOADS": 2
        }
    
    def detect_all_models(self) -> Dict[str, ModelInfo]:
        """Detect tất cả models có sẵn trên hệ thống"""
        logger.info("🔍 Detecting all available models...")
        
        detected_models = {}
        
        # Detect Ollama models
        ollama_models = self._detect_ollama_models()
        detected_models.update(ollama_models)
        
        # Detect Vosk models
        vosk_models = self._detect_vosk_models()
        detected_models.update(vosk_models)
        
        # Detect local models
        local_models = self._detect_local_models()
        detected_models.update(local_models)
        
        # Detect GitHub models (nếu có API key)
        if self.config.get("API_KEY"):
            github_models = self._detect_github_models()
            detected_models.update(github_models)
        
        self._detected_models = detected_models
        logger.info(f"✅ Detected {len(detected_models)} models")
        
        return detected_models
    
    def _detect_ollama_models(self) -> Dict[str, ModelInfo]:
        """Detect Ollama models"""
        models = {}
        
        try:
            # Kiểm tra Ollama server
            base_url = self.config.get("OLLAMA_BASE_URL", "http://localhost:11434")
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                for model in data.get('models', []):
                    model_name = model.get('name', '')
                    model_info = ModelInfo(
                        name=model_name,
                        type=ModelType.OLLAMA,
                        path=f"ollama://{model_name}",
                        size_mb=model.get('size', 0) / (1024*1024),
                        status="available",
                        description=f"Ollama model: {model_name}",
                        required=(model_name == self.config.get("OLLAMA_MODEL"))
                    )
                    models[f"ollama:{model_name}"] = model_info
                    
                logger.info(f"Found {len(models)} Ollama models")
            else:
                logger.warning("Ollama server not responding")
                
        except Exception as e:
            logger.debug(f"Ollama detection failed: {e}")
        
        return models
    
    def _detect_vosk_models(self) -> Dict[str, ModelInfo]:
        """Detect Vosk models"""
        models = {}
        
        vosk_models = {
            "vi": {
                "path": "vosk-vi",
                "description": "Vietnamese Vosk model",
                "size_mb": 78,
                "url": "https://alphacephei.com/vosk/models/vosk-model-vn-0.4.zip"
            },
            "en": {
                "path": "vosk-en", 
                "description": "English Vosk model",
                "size_mb": 40,
                "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
            }
        }
        
        for lang, info in vosk_models.items():
            model_path = self.models_dir / info["path"]
            status = "available" if model_path.exists() and any(model_path.iterdir()) else "not_found"
            
            model_info = ModelInfo(
                name=f"vosk-{lang}",
                type=ModelType.VOSK,
                path=str(model_path),
                size_mb=info["size_mb"],
                status=status,
                description=info["description"],
                download_url=info["url"],
                required=(lang == "vi")  # Vietnamese là required
            )
            models[f"vosk:{lang}"] = model_info
        
        return models
    
    def _detect_local_models(self) -> Dict[str, ModelInfo]:
        """Detect local models trong thư mục models"""
        models = {}
        
        # Scan thư mục models cho các model tùy chỉnh
        for model_dir in self.models_dir.glob("*"):
            if model_dir.is_dir() and not model_dir.name.startswith("vosk-"):
                # Kiểm tra xem có phải là model không
                if self._is_valid_model_directory(model_dir):
                    model_info = ModelInfo(
                        name=model_dir.name,
                        type=ModelType.LOCAL,
                        path=str(model_dir),
                        size_mb=self._get_directory_size_mb(model_dir),
                        status="available",
                        description=f"Local model: {model_dir.name}"
                    )
                    models[f"local:{model_dir.name}"] = model_info
        
        return models
    
    def _detect_github_models(self) -> Dict[str, ModelInfo]:
        """Detect GitHub models (nếu có API key)"""
        models = {}
        
        if self.config.get("API_KEY"):
            model_name = self.config.get("MODEL", "openai/gpt-4o-mini")
            model_info = ModelInfo(
                name=model_name,
                type=ModelType.GITHUB,
                path=f"github://{model_name}",
                size_mb=0,  # Unknown size
                status="available",
                description=f"GitHub AI model: {model_name}",
                required=True
            )
            models[f"github:{model_name}"] = model_info
        
        return models
    
    def _is_valid_model_directory(self, model_dir: Path) -> bool:
        """Kiểm tra xem thư mục có phải là model hợp lệ không"""
        # Kiểm tra các file cần thiết cho model
        required_files = ["config.json", "model.bin", "tokenizer.json"]
        existing_files = [f.name for f in model_dir.iterdir() if f.is_file()]
        
        # Cần có ít nhất 2 file trong số required files
        return len(set(required_files) & set(existing_files)) >= 2
    
    def _get_directory_size_mb(self, directory: Path) -> float:
        """Tính kích thước thư mục theo MB"""
        try:
            total_size = sum(f.stat().st_size for f in directory.rglob('*') if f.is_file())
            return total_size / (1024 * 1024)
        except Exception:
            return 0.0
    
    def ensure_required_models(self) -> Dict[str, bool]:
        """Đảm bảo tất cả required models có sẵn"""
        logger.info("🔧 Ensuring required models...")
        
        # Detect models trước
        all_models = self.detect_all_models()
        
        # Tìm required models
        required_models = {k: v for k, v in all_models.items() if v.required}
        missing_models = {k: v for k, v in required_models.items() if v.status != "available"}
        
        results = {}
        
        if not missing_models:
            logger.info("✅ All required models are available")
            return {k: True for k in required_models.keys()}
        
        # Download missing models
        logger.info(f"📥 Downloading {len(missing_models)} missing models...")
        
        with ThreadPoolExecutor(max_workers=self.config.get("MAX_CONCURRENT_DOWNLOADS", 2)) as executor:
            future_to_model = {
                executor.submit(self._download_model, model_key, model_info): model_key
                for model_key, model_info in missing_models.items()
            }
            
            for future in as_completed(future_to_model):
                model_key = future_to_model[future]
                try:
                    success = future.result()
                    results[model_key] = success
                    status = "✅" if success else "❌"
                    logger.info(f"{status} {model_key}: {'Downloaded' if success else 'Failed'}")
                except Exception as e:
                    results[model_key] = False
                    logger.error(f"❌ {model_key}: Download error - {e}")
        
        return results
    
    def _download_model(self, model_key: str, model_info: ModelInfo) -> bool:
        """Download một model cụ thể"""
        logger.info(f"📥 Downloading {model_key}...")
        
        try:
            if model_info.type == ModelType.OLLAMA:
                return self._download_ollama_model(model_info.name)
            elif model_info.type == ModelType.VOSK:
                return self._download_vosk_model(model_key, model_info)
            elif model_info.type == ModelType.LOCAL:
                return self._download_local_model(model_key, model_info)
            else:
                logger.warning(f"Unknown model type: {model_info.type}")
                return False
                
        except Exception as e:
            logger.error(f"Download failed for {model_key}: {e}")
            return False
    
    def _download_ollama_model(self, model_name: str) -> bool:
        """Download Ollama model"""
        try:
            timeout = self.config.get("MODEL_DOWNLOAD_TIMEOUT", 1800)
            result = subprocess.run(
                ['ollama', 'pull', model_name],
                timeout=timeout,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Ollama model {model_name} downloaded successfully")
                return True
            else:
                logger.error(f"❌ Failed to download Ollama model {model_name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Download timeout for Ollama model {model_name}")
            return False
        except Exception as e:
            logger.error(f"❌ Error downloading Ollama model {model_name}: {e}")
            return False
    
    def _download_vosk_model(self, model_key: str, model_info: ModelInfo) -> bool:
        """Download Vosk model"""
        try:
            import zipfile
            
            # Tạo thư mục tạm
            temp_dir = self.models_dir / "temp"
            temp_dir.mkdir(exist_ok=True)
            
            # Download file
            zip_path = temp_dir / f"{model_info.name}.zip"
            
            response = requests.get(model_info.download_url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Extract
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Move to target location
            target_dir = Path(model_info.path)
            if target_dir.exists():
                shutil.rmtree(target_dir)
            
            # Find extracted directory
            extracted_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
            if extracted_dirs:
                shutil.move(str(extracted_dirs[0]), str(target_dir))
            
            # Cleanup
            zip_path.unlink()
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            
            logger.info(f"✅ Vosk model {model_key} downloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to download Vosk model {model_key}: {e}")
            return False
    
    def _download_local_model(self, model_key: str, model_info: ModelInfo) -> bool:
        """Download local model (placeholder)"""
        logger.warning(f"Local model download not implemented for {model_key}")
        return False
    
    def get_model_status(self) -> Dict[str, Any]:
        """Lấy status của tất cả models"""
        all_models = self.detect_all_models()
        
        status = {
            "total_models": len(all_models),
            "available_models": len([m for m in all_models.values() if m.status == "available"]),
            "required_models": len([m for m in all_models.values() if m.required]),
            "missing_required": len([m for m in all_models.values() if m.required and m.status != "available"]),
            "models_by_type": {},
            "model_details": {}
        }
        
        # Group by type
        for model_key, model_info in all_models.items():
            model_type = model_info.type.value
            if model_type not in status["models_by_type"]:
                status["models_by_type"][model_type] = []
            status["models_by_type"][model_type].append({
                "name": model_info.name,
                "status": model_info.status,
                "size_mb": model_info.size_mb,
                "required": model_info.required
            })
            
            # Detailed info
            status["model_details"][model_key] = {
                "name": model_info.name,
                "type": model_info.type.value,
                "path": model_info.path,
                "size_mb": model_info.size_mb,
                "status": model_info.status,
                "description": model_info.description,
                "required": model_info.required
            }
        
        return status
    
    def cleanup_old_models(self, keep_recent: int = 3) -> Dict[str, bool]:
        """Dọn dẹp models cũ (giữ lại keep_recent models mới nhất)"""
        logger.info(f"🧹 Cleaning up old models (keeping {keep_recent} recent)...")
        
        results = {}
        
        # Chỉ cleanup Ollama models
        ollama_models = {k: v for k, v in self._detected_models.items() if v.type == ModelType.OLLAMA}
        
        if len(ollama_models) <= keep_recent:
            logger.info("No cleanup needed")
            return results
        
        # Sort by modification time (nếu có)
        sorted_models = sorted(ollama_models.items(), key=lambda x: x[1].name)
        
        # Remove old models (trừ required và recent)
        for i, (model_key, model_info) in enumerate(sorted_models):
            if i < len(sorted_models) - keep_recent and not model_info.required:
                try:
                    result = subprocess.run(['ollama', 'rm', model_info.name], capture_output=True, text=True)
                    if result.returncode == 0:
                        results[model_key] = True
                        logger.info(f"✅ Removed old model: {model_info.name}")
                    else:
                        results[model_key] = False
                        logger.warning(f"⚠️ Failed to remove model: {model_info.name}")
                except Exception as e:
                    results[model_key] = False
                    logger.error(f"❌ Error removing model {model_info.name}: {e}")
        
        return results
    
    def validate_models(self) -> Dict[str, bool]:
        """Validate tất cả models"""
        logger.info("🔍 Validating models...")
        
        all_models = self.detect_all_models()
        results = {}
        
        for model_key, model_info in all_models.items():
            if model_info.status != "available":
                results[model_key] = False
                continue
            
            try:
                if model_info.type == ModelType.OLLAMA:
                    results[model_key] = self._validate_ollama_model(model_info)
                elif model_info.type == ModelType.VOSK:
                    results[model_key] = self._validate_vosk_model(model_info)
                elif model_info.type == ModelType.GITHUB:
                    results[model_key] = self._validate_github_model(model_info)
                else:
                    results[model_key] = True  # Assume local models are valid
                    
            except Exception as e:
                logger.error(f"Validation error for {model_key}: {e}")
                results[model_key] = False
        
        return results
    
    def _validate_ollama_model(self, model_info: ModelInfo) -> bool:
        """Validate Ollama model"""
        try:
            payload = {
                "model": model_info.name,
                "prompt": "Test",
                "stream": False
            }
            
            base_url = self.config.get("OLLAMA_BASE_URL", "http://localhost:11434")
            response = requests.post(
                f"{base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.debug(f"Ollama validation failed for {model_info.name}: {e}")
            return False
    
    def _validate_vosk_model(self, model_info: ModelInfo) -> bool:
        """Validate Vosk model"""
        try:
            model_path = Path(model_info.path)
            required_files = ["am", "conf", "graph", "ivector", "rescoring", "rnnlm"]
            
            # Kiểm tra thư mục và files cần thiết
            if not model_path.exists():
                return False
            
            # Kiểm tra ít nhất một số file quan trọng
            existing_dirs = [d.name for d in model_path.iterdir() if d.is_dir()]
            return len(set(required_files) & set(existing_dirs)) >= 3
            
        except Exception as e:
            logger.debug(f"Vosk validation failed for {model_info.name}: {e}")
            return False
    
    def _validate_github_model(self, model_info: ModelInfo) -> bool:
        """Validate GitHub model (kiểm tra API key)"""
        return bool(self.config.get("API_KEY"))

# Global model manager instance
model_manager = ModelManager()
