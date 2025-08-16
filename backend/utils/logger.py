import logging
import sys
from datetime import datetime

def setup_logging():
    """Cấu hình logging cho toàn bộ ứng dụng"""
    
    # Tạo formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # File handler (optional)
    try:
        log_filename = f"logs/chatbot_{datetime.now().strftime('%Y%m%d')}.log"
        import os
        os.makedirs('logs', exist_ok=True)
        
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
    except Exception as e:
        file_handler = None
        print(f"Warning: Could not create file handler: {e}")
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    if file_handler:
        root_logger.addHandler(file_handler)
    
    # Specific loggers
    loggers = [
        'main',
        'config.settings',
        'config.database', 
        'services.ai_service',
        'services.conversation_service',
        'services.message_service',
        'services.chat_service',
        'api.chat',
        'api.conversations',
        'api.system',
        'api.debug'
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
    
    # Suppress some verbose loggers
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    logging.info("Logging configuration completed")