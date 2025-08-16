import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

class Settings:
    """Quản lý tất cả cấu hình của ứng dụng với hỗ trợ multiple AI providers"""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.load_config()
        
    def load_config(self):
        """Load config từ file config.json"""
        try:
            config_path = 'config.json'  # Tìm trong thư mục hiện tại trước
            if not os.path.exists(config_path):
                config_path = './config.json'  # Fallback về thư mục cha
            
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config file not found at {config_path}")
            
            with open(config_path, encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info(f"Config loaded successfully from {config_path}")
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise SystemExit(f"Cannot start without config.json file. Please ensure config.json exists with required settings.")
    
    # Database Settings
    @property
    def db_path(self) -> str:
        return self.config.get('DB_PATH', 'chatbot.db')
    
    # GitHub AI Settings
    @property
    def api_key(self) -> Optional[str]:
        return self.config.get('API_KEY')
    
    @property
    def base_url(self) -> str:
        return self.config.get('BASE_URL', 'https://models.github.ai/inference')
    
    @property
    def model(self) -> str:
        return self.config.get('MODEL', 'openai/gpt-4o-mini')
    
    # Ollama Settings
    @property
    def ollama_base_url(self) -> str:
        return self.config.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    @property
    def ollama_model(self) -> str:
        return self.config.get('OLLAMA_MODEL', 'gemma2:9b')
    
    @property
    def ollama_max_tokens(self) -> Optional[int]:
        return self.config.get('OLLAMA_MAX_TOKENS')
    
    # AI Provider Settings
    @property
    def preferred_ai_provider(self) -> str:
        """Provider ưu tiên: 'github', 'ollama'"""
        return self.config.get('PREFERRED_AI_PROVIDER', 'github').lower()
    
    @property
    def auto_fallback(self) -> bool:
        """Tự động fallback sang provider khác nếu provider chính không khả dụng"""
        return self.config.get('AUTO_FALLBACK', True)
    
    # Common AI Settings
    @property
    def temperature(self) -> float:
        return self.config.get('TEMPERATURE', 0.7)
    
    @property
    def max_tokens(self) -> int:
        return self.config.get('MAX_TOKENS', 1000)
    
    @property
    def request_timeout(self) -> int:
        return self.config.get('REQUEST_TIMEOUT', 60)
    
    # System Settings
    @property
    def timezone(self) -> str:
        return self.config.get('TIMEZONE', 'Asia/Ho_Chi_Minh')
    
    @property
    def system_prompt(self) -> str:
        return self.config.get('SYSTEM_PROMPT', 
            "Bạn là một trợ lý ảo Bixby, thân thiện, dễ thương, giúp người dùng trả lời câu hỏi và giải quyết vấn đề, luôn xưng hô là 'Em' hoặc tên 'Bixby' và không sử dụng từ 'Bạn', Luôn trả lời bằng Tiếng việt.")
    
    @property
    def time_format(self) -> str:
        return self.config.get('TIME_FORMAT', 'Bây giờ là {time} ở Việt Nam.')
    
    @property
    def fallback_message(self) -> str:
        return self.config.get('FALLBACK_MESSAGE', 
            "Em là Bixby! Em đã nhận được tin nhắn: '{user_input}'. Hiện tại em chưa kết nối được với AI, nhưng em sẽ sớm có thể trò chuyện thông minh hơn!")
    
    @property
    def error_message(self) -> str:
        return self.config.get('ERROR_MESSAGE',
            "Em là Bixby! Xin lỗi, em gặp chút vấn đề kỹ thuật khi xử lý câu hỏi của anh. Em đã ghi nhận: '{user_input}' và sẽ cố gắng trả lời tốt hơn!")
    
    @property
    def sensitive_keys(self) -> list:
        return self.config.get('SENSITIVE_KEYS', ['API_KEY', 'PASSWORD', 'SECRET'])
    
    # CORS Settings
    @property
    def cors_origins(self) -> list:
        return self.config.get('CORS_ORIGINS', ["*"])
    
    def get_current_time(self) -> str:
        """Lấy thời gian hiện tại theo timezone từ config"""
        try:
            now = datetime.now(ZoneInfo(self.timezone))
            return now.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.warning(f"Error with timezone {self.timezone}: {e}, using default UTC+7")
            now = datetime.now(ZoneInfo('Asia/Ho_Chi_Minh'))
            return now.strftime("%Y-%m-%d %H:%M:%S")
    
    def get_safe_config(self) -> Dict[str, Any]:
        """Trả về config an toàn (ẩn sensitive data)"""
        safe_config = {}
        for key, value in self.config.items():
            if any(sensitive in key.upper() for sensitive in self.sensitive_keys):
                safe_config[key] = "***hidden***"
            else:
                safe_config[key] = value
        return safe_config
    
    def get_ai_providers_config(self) -> Dict[str, Any]:
        """Lấy thông tin config của các AI providers"""
        return {
            "github": {
                "base_url": self.base_url,
                "model": self.model,
                "api_key_configured": bool(self.api_key)
            },
            "ollama": {
                "base_url": self.ollama_base_url,
                "model": self.ollama_model,
                "max_tokens": self.ollama_max_tokens
            },
            "common": {
                "preferred_provider": self.preferred_ai_provider,
                "auto_fallback": self.auto_fallback,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "request_timeout": self.request_timeout
            }
        }
    
    def log_config(self):
        """Log thông tin cấu hình"""
        logger.info(f"Configuration loaded:")
        logger.info(f"  - Database: {self.db_path}")
        logger.info(f"  - Preferred AI Provider: {self.preferred_ai_provider}")
        logger.info(f"  - Auto Fallback: {self.auto_fallback}")
        
        # GitHub Config
        logger.info(f"  - GitHub Model: {self.model}")
        logger.info(f"  - GitHub Base URL: {self.base_url}")
        if not self.api_key:
            logger.warning("  - GitHub API_KEY not found in config.json!")
        else:
            logger.info("  - GitHub API_KEY found in config")
        
        # Ollama Config  
        logger.info(f"  - Ollama Model: {self.ollama_model}")
        logger.info(f"  - Ollama Base URL: {self.ollama_base_url}")
        
        # Common AI Settings
        logger.info(f"  - Temperature: {self.temperature}")
        logger.info(f"  - Max Tokens: {self.max_tokens}")
        logger.info(f"  - Timezone: {self.timezone}")

# Global settings instance
settings = Settings()