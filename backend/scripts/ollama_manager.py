#!/usr/bin/env python3
"""
Ollama Model Manager - Tự động kiểm tra và tải model
"""

import os
import sys
import json
import time
import requests
import subprocess
import logging
from typing import List, Dict, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OllamaManager:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        
    def is_server_running(self) -> bool:
        """Kiểm tra Ollama server có chạy không"""
        try:
            response = requests.get(f"{self.api_base}/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Server check failed: {e}")
            return False
    
    def list_models(self) -> List[Dict]:
        """Lấy danh sách models đã cài đặt"""
        try:
            if not self.is_server_running():
                return []
                
            response = requests.get(f"{self.api_base}/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('models', [])
            return []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def model_exists(self, model_name: str) -> bool:
        """Kiểm tra model có tồn tại không"""
        models = self.list_models()
        for model in models:
            if model.get('name', '').startswith(model_name):
                return True
        return False
    
    def pull_model(self, model_name: str, timeout: int = 1800) -> bool:
        """Tải model từ Ollama registry"""
        try:
            logger.info(f"Pulling model: {model_name}")
            
            # Sử dụng subprocess để có thể theo dõi progress
            process = subprocess.Popen(
                ['ollama', 'pull', model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Đợi process hoàn thành với timeout
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                if process.returncode == 0:
                    logger.info(f"Successfully pulled model: {model_name}")
                    return True
                else:
                    logger.error(f"Failed to pull model {model_name}: {stderr}")
                    return False
            except subprocess.TimeoutExpired:
                process.kill()
                logger.error(f"Model pull timeout after {timeout} seconds")
                return False
                
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            return False
    
    def test_model(self, model_name: str) -> bool:
        """Test model với một câu hỏi đơn giản"""
        try:
            payload = {
                "model": model_name,
                "prompt": "Hello, respond with 'OK' if you can understand this.",
                "stream": False
            }
            
            response = requests.post(
                f"{self.api_base}/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('response'):
                    logger.info(f"Model {model_name} test successful")
                    return True
            
            logger.warning(f"Model {model_name} test failed")
            return False
            
        except Exception as e:
            logger.error(f"Model test error: {e}")
            return False
    
    def ensure_model(self, model_name: str) -> bool:
        """Đảm bảo model có sẵn và hoạt động"""
        logger.info(f"Ensuring model availability: {model_name}")
        
        # Kiểm tra server
        if not self.is_server_running():
            logger.error("Ollama server is not running")
            return False
        
        # Kiểm tra model tồn tại
        if self.model_exists(model_name):
            logger.info(f"Model {model_name} already exists")
            # Test model
            if self.test_model(model_name):
                return True
            else:
                logger.warning(f"Model {model_name} exists but not working properly")
        
        # Tải model nếu chưa có hoặc không hoạt động
        logger.info(f"Downloading model: {model_name}")
        if self.pull_model(model_name):
            # Test model sau khi tải
            time.sleep(5)  # Đợi model load
            return self.test_model(model_name)
        
        return False
    
    def get_recommended_models(self) -> List[str]:
        """Lấy danh sách models khuyến nghị cho ChatBot"""
        return [
            "gemma2:9b",      # Model mặc định, cân bằng tốt
            "llama3.1:8b",    # Model phổ biến, nhanh
            "qwen2.5:7b",     # Model tốt cho tiếng Việt
            "gemma2:2b",      # Model nhẹ cho server yếu
        ]
    
    def auto_select_model(self) -> Optional[str]:
        """Tự động chọn model phù hợp"""
        recommended = self.get_recommended_models()
        
        logger.info("Auto-selecting best available model...")
        
        for model in recommended:
            logger.info(f"Trying model: {model}")
            if self.ensure_model(model):
                logger.info(f"Selected model: {model}")
                return model
            else:
                logger.warning(f"Model {model} failed, trying next...")
        
        logger.error("No suitable model found")
        return None

def load_config() -> Dict:
    """Load cấu hình từ config.json"""
    config_path = "/app/config.json"
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
    
    # Fallback config
    return {
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "OLLAMA_MODEL": "gemma2:9b"
    }

def main():
    """Main function"""
    logger.info("=== Ollama Model Manager ===")
    
    # Load configuration
    config = load_config()
    base_url = config.get("OLLAMA_BASE_URL", "http://localhost:11434")
    target_model = config.get("OLLAMA_MODEL", "gemma2:9b")
    
    # Initialize manager
    manager = OllamaManager(base_url)
    
    # Wait for Ollama server
    logger.info("Waiting for Ollama server...")
    max_wait = 60  # 60 seconds
    waited = 0
    
    while not manager.is_server_running() and waited < max_wait:
        time.sleep(2)
        waited += 2
        logger.info(f"Waiting... ({waited}/{max_wait}s)")
    
    if not manager.is_server_running():
        logger.error("Ollama server not available")
        sys.exit(1)
    
    # Ensure target model
    logger.info(f"Target model: {target_model}")
    
    if manager.ensure_model(target_model):
        logger.info("✅ Model setup successful!")
        sys.exit(0)
    else:
        logger.warning("Target model failed, trying auto-select...")
        
        # Auto select alternative
        selected_model = manager.auto_select_model()
        if selected_model:
            logger.info(f"✅ Auto-selected model: {selected_model}")
            # Update config with selected model
            config["OLLAMA_MODEL"] = selected_model
            try:
                with open("/app/config.json", 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                logger.info("Updated config.json with new model")
            except Exception as e:
                logger.error(f"Failed to update config: {e}")
            sys.exit(0)
        else:
            logger.error("❌ No model available!")
            sys.exit(1)

if __name__ == "__main__":
    main()