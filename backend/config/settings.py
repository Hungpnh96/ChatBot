# config/settings.py - Tương thích với config.json + Enhanced Features
import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

class Settings:
    """Quản lý tất cả cấu hình của ứng dụng với hỗ trợ multiple AI providers + Enhanced Features"""
    
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
    
    # === ORIGINAL SETTINGS (giữ nguyên) ===
    
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
    
    # === NEW ENHANCED FEATURES SETTINGS ===
    
    # === REALTIME SEARCH SETTINGS (FREE) ===
    @property
    def enable_realtime_search(self) -> bool:
        """Bật/tắt tìm kiếm thời gian thực (FREE)"""
        return self.config.get('ENABLE_REALTIME_SEARCH', True)
    
    @property
    def search_language_preference(self) -> str:
        """Ngôn ngữ ưu tiên cho search"""
        return self.config.get('SEARCH_LANGUAGE', 'vi')
    
    @property
    def max_search_results(self) -> int:
        """Số kết quả search tối đa"""
        return self.config.get('MAX_SEARCH_RESULTS', 5)
    
    @property
    def search_cache_ttl_minutes(self) -> int:
        """Cache TTL cho search results (phút)"""
        return self.config.get('SEARCH_CACHE_TTL_MINUTES', 60)
    
    @property
    def search_timeout_seconds(self) -> int:
        """Timeout cho search requests (giây)"""
        return self.config.get('SEARCH_TIMEOUT_SECONDS', 10)
    
    # === PERSONAL INFO API SETTINGS ===
    @property
    def enable_personal_info(self) -> bool:
        """Bật/tắt tính năng thông tin cá nhân"""
        return self.config.get('ENABLE_PERSONAL_INFO', False)
    
    @property
    def personal_api_base_url(self) -> str:
        """Base URL của Personal Info API"""
        return self.config.get('PERSONAL_API_BASE_URL', '')
    
    @property
    def personal_api_token(self) -> str:
        """Token cho Personal Info API"""
        return self.config.get('PERSONAL_API_TOKEN', '')
    
    @property
    def personal_api_timeout(self) -> int:
        """Timeout cho Personal API (giây)"""
        return self.config.get('PERSONAL_API_TIMEOUT', 10)
    
    @property
    def personal_info_cache_ttl_minutes(self) -> int:
        """Cache TTL cho personal info (phút)"""
        return self.config.get('PERSONAL_INFO_CACHE_TTL', 30)
    
    # === PERFORMANCE SETTINGS ===
    @property
    def enable_caching(self) -> bool:
        """Bật/tắt caching"""
        return self.config.get('ENABLE_CACHING', True)
    
    @property
    def cache_ttl_seconds(self) -> int:
        """Cache TTL chung (giây)"""
        return self.config.get('CACHE_TTL_SECONDS', 3600)
    
    @property
    def rate_limit_requests(self) -> int:
        """Số requests tối đa trong rate limit window"""
        return self.config.get('RATE_LIMIT_REQUESTS', 100)
    
    @property
    def rate_limit_window_minutes(self) -> int:
        """Rate limit window (phút)"""
        return self.config.get('RATE_LIMIT_WINDOW', 60)
    
    # === VOICE SETTINGS ===
    @property
    def voice_enabled(self) -> bool:
        """Bật/tắt voice features"""
        return self.config.get('VOICE_ENABLED', True)
    
    @property
    def default_voice_language(self) -> str:
        """Ngôn ngữ mặc định cho voice"""
        return self.config.get('DEFAULT_VOICE_LANGUAGE', 'vi-VN')
    
    # === LOGGING SETTINGS ===
    @property
    def log_level(self) -> str:
        """Log level"""
        return self.config.get('LOG_LEVEL', 'INFO')
    
    @property
    def log_file(self) -> str:
        """Log file path (empty = console only)"""
        return self.config.get('LOG_FILE', '')
    
    # === METHODS ===
    
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
        """Trả về config an toàn (ẩn sensitive data) bao gồm enhanced features"""
        safe_config = {}
        for key, value in self.config.items():
            if any(sensitive in key.upper() for sensitive in self.sensitive_keys):
                safe_config[key] = "***hidden***"
            else:
                safe_config[key] = value
        
        # Thêm computed values cho enhanced features
        safe_config.update({
            "enhanced_features_status": {
                "realtime_search_enabled": self.enable_realtime_search,
                "personal_info_enabled": self.enable_personal_info,
                "voice_enabled": self.voice_enabled,
                "caching_enabled": self.enable_caching
            }
        })
        
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
    
    def get_search_config(self) -> Dict[str, Any]:
        """Lấy config cho FREE search features"""
        return {
            "realtime_search_enabled": self.enable_realtime_search,
            "search_method": "free",
            "search_sources": ["Wikipedia", "DuckDuckGo", "News Scraping", "Google Scraping"],
            "search_language": self.search_language_preference,
            "max_results": self.max_search_results,
            "cache_ttl_minutes": self.search_cache_ttl_minutes,
            "timeout_seconds": self.search_timeout_seconds,
            "cost": "FREE"
        }
    
    def get_personal_info_config(self) -> Dict[str, Any]:
        """Lấy config cho personal info features"""
        return {
            "personal_info_enabled": self.enable_personal_info,
            "personal_api_enabled": bool(self.personal_api_base_url and self.personal_api_token),
            "cache_ttl_minutes": self.personal_info_cache_ttl_minutes,
            "api_timeout_seconds": self.personal_api_timeout,
            "api_base_url": self.personal_api_base_url if self.personal_api_base_url else None
        }
    
    def get_feature_status(self) -> Dict[str, Any]:
        """Lấy status của tất cả features"""
        return {
            "core_features": {
                "github_ai": bool(self.api_key),
                "ollama_ai": True,  # Assume available
                "voice_chat": self.voice_enabled,
                "conversation_management": True,
                "database": os.path.exists(self.db_path)
            },
            "enhanced_features": {
                "realtime_search": self.enable_realtime_search,
                "personal_info": self.enable_personal_info and bool(self.personal_api_base_url),
                "free_search": True,  # Always available
                "caching": self.enable_caching
            },
            "performance_features": {
                "caching": self.enable_caching,
                "rate_limiting": True
            }
        }
    
    def validate_configuration(self) -> List[str]:
        """Validate cấu hình và trả về list các warnings"""
        warnings = []
        
        # Core validations
        if not self.api_key:
            warnings.append("⚠️  GitHub API_KEY not configured - GitHub AI unavailable")
        
        if not os.path.exists(os.path.dirname(self.db_path)):
            warnings.append(f"⚠️  Database directory does not exist: {os.path.dirname(self.db_path)}")
        
        # Enhanced features validations
        if self.enable_personal_info:
            if not self.personal_api_base_url:
                warnings.append("⚠️  Personal info enabled but no API base URL configured")
            
            if not self.personal_api_token:
                warnings.append("⚠️  Personal info enabled but no API token configured")
        
        # Performance warnings
        if self.search_cache_ttl_minutes < 5:
            warnings.append("⚠️  Search cache TTL very low - may cause performance issues")
        
        if self.max_search_results > 10:
            warnings.append("⚠️  Max search results very high - may slow down responses")
        
        # Timezone validation
        try:
            ZoneInfo(self.timezone)
        except:
            warnings.append(f"⚠️  Invalid timezone: {self.timezone}")
        
        return warnings
    
    def log_config(self):
        """Log thông tin cấu hình bao gồm enhanced features"""
        logger.info("=== BIXBY CHATBOT CONFIGURATION ===")
        
        # Core configuration
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
        
        # Enhanced Features
        logger.info("=== ENHANCED FEATURES ===")
        logger.info(f"  - Realtime Search: {self.enable_realtime_search} (FREE)")
        logger.info(f"  - Personal Info: {self.enable_personal_info}")
        logger.info(f"  - Voice Features: {self.voice_enabled}")
        logger.info(f"  - Caching: {self.enable_caching}")
        logger.info(f"  - Search Language: {self.search_language_preference}")
        logger.info(f"  - Max Search Results: {self.max_search_results}")
        
        # Personal Info config
        if self.enable_personal_info:
            logger.info(f"  - Personal API URL: {self.personal_api_base_url}")
            if self.personal_api_token:
                logger.info("  - Personal API Token: configured")
            else:
                logger.warning("  - Personal API Token: not configured")
        
        # Warnings
        warnings = self.validate_configuration()
        if warnings:
            logger.warning("=== CONFIGURATION WARNINGS ===")
            for warning in warnings:
                logger.warning(f"  {warning}")
        
        logger.info("=====================================")

# Global settings instance
settings = Settings()