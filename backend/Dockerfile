# backend/Dockerfile - Complete Auto Setup
FROM python:3.11-slim

# Install ALL system dependencies
RUN apt-get update && apt-get install -y \
    # Basic utilities
    curl \
    wget \
    unzip \
    git \
    build-essential \
    # Audio dependencies for Vosk and TTS
    ffmpeg \
    flac \
    libatomic1 \
    alsa-utils \
    # Speech synthesis dependencies  
    espeak-ng \
    libespeak-ng1 \
    libasound2 \
    # Additional utilities
    tzdata \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Set environment
ENV TZ=Asia/Ho_Chi_Minh
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements và install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional packages that might be missing
RUN pip install --no-cache-dir \
    vosk \
    pyttsx3 \
    langchain-ollama \
    langchain-openai \
    requests \
    aiofiles \
    python-multipart

# Copy source code
COPY . .

# Create all necessary directories
RUN mkdir -p /app/data/models /app/logs /app/temp

# Create comprehensive setup script
RUN cat > /app/auto_setup.py << 'EOF'
#!/usr/bin/env python3
"""
Auto setup script - Tự động cài đặt tất cả dependencies
"""
import os
import sys
import subprocess
import requests
import zipfile
import shutil
import json
import time
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutoSetup:
    def __init__(self):
        self.base_dir = Path("/app")
        self.data_dir = self.base_dir / "data"
        self.models_dir = self.data_dir / "models"
        self.logs_dir = self.base_dir / "logs"
        
        # Create directories
        self.data_dir.mkdir(exist_ok=True)
        self.models_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
    
    def setup_config(self):
        """Setup configuration files"""
        logger.info("🔧 Setting up configuration...")
        
        config_file = self.base_dir / "config.json"
        config_example = self.base_dir / "config.json.example"
        
        try:
            if not config_file.exists() and config_example.exists():
                shutil.copy(config_example, config_file)
                logger.info("✅ Created config.json from example")
            elif config_file.exists():
                logger.info("✅ Config file already exists")
            else:
                # Create minimal config
                minimal_config = {
                    "DB_PATH": "/app/data/chatbot.db",
                    "PREFERRED_AI_PROVIDER": "ollama",
                    "AUTO_FALLBACK": True,
                    "TEMPERATURE": 0.7,
                    "MAX_TOKENS": 1000,
                    "SYSTEM_PROMPT": "Bạn là trợ lý ảo Bixby thân thiện, trả lời bằng tiếng Việt.",
                    "FALLBACK_MESSAGE": "Em là Bixby! Hiện tại em chưa kết nối được với AI, nhưng em vẫn có thể giúp anh!"
                }
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(minimal_config, f, indent=2, ensure_ascii=False)
                logger.info("✅ Created minimal config.json")
            
            # Validate config file exists and is readable
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    json.load(f)  # Test JSON parsing
                return True
            else:
                logger.error("❌ Config file not found after setup")
                return False
                
        except Exception as e:
            logger.error(f"❌ Config setup failed: {e}")
            return False
    
    def install_ollama(self):
        """Install Ollama if not present"""
        logger.info("🤖 Checking Ollama installation...")
        
        if shutil.which('ollama'):
            logger.info("✅ Ollama already installed")
            return True
        
        try:
            logger.info("📥 Installing Ollama...")
            
            # Download and install Ollama
            install_script = subprocess.run([
                'curl', '-fsSL', 'https://ollama.ai/install.sh'
            ], capture_output=True, text=True, timeout=60)
            
            if install_script.returncode == 0:
                # Run install script
                subprocess.run(['sh'], input=install_script.stdout, text=True, timeout=300)
                
                if shutil.which('ollama'):
                    logger.info("✅ Ollama installed successfully")
                    return True
            
            logger.warning("⚠️ Ollama installation failed")
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Ollama installation error: {e}")
            return False
    
    def start_ollama_server(self):
        """Start Ollama server"""
        logger.info("🔄 Starting Ollama server...")
        
        try:
            # Check if already running
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code == 200:
                    logger.info("✅ Ollama server already running")
                    return True
            except:
                pass
            
            # Start Ollama server
            subprocess.Popen(
                ['ollama', 'serve'],
                stdout=open('/app/logs/ollama.log', 'w'),
                stderr=subprocess.STDOUT
            )
            
            # Wait for server to start
            for i in range(30):
                try:
                    response = requests.get("http://localhost:11434/api/tags", timeout=2)
                    if response.status_code == 200:
                        logger.info("✅ Ollama server started successfully")
                        return True
                except:
                    time.sleep(2)
            
            logger.warning("⚠️ Ollama server start timeout")
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to start Ollama server: {e}")
            return False
    
    def download_ollama_model(self, model_name="gemma2:9b"):
        """Download Ollama model"""
        logger.info(f"🤖 Checking Ollama model: {model_name}")
        
        try:
            # Check if model exists
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
            if model_name in result.stdout:
                logger.info(f"✅ Ollama model {model_name} already exists")
                return True
            
            # Download model
            logger.info(f"📥 Downloading Ollama model: {model_name}")
            result = subprocess.run(['ollama', 'pull', model_name], timeout=1800)
            
            if result.returncode == 0:
                logger.info(f"✅ Ollama model {model_name} downloaded successfully")
                return True
            else:
                logger.warning(f"⚠️ Failed to download Ollama model: {model_name}")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ Ollama model download error: {e}")
            return False
    
    def download_vosk_model(self, language="vi"):
        """Download Vosk model"""
        logger.info(f"🎤 Checking Vosk model: {language}")
        
        vosk_models = {
            "vi": {
                "url": "https://alphacephei.com/vosk/models/vosk-model-small-vi-0.4.zip",
                "name": "vosk-model-small-vi-0.4",
                "target": "vosk-vi"
            },
            "en": {
                "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip", 
                "name": "vosk-model-small-en-us-0.15",
                "target": "vosk-en"
            }
        }
        
        if language not in vosk_models:
            logger.warning(f"⚠️ Unsupported Vosk language: {language}")
            return False
        
        model_info = vosk_models[language]
        target_dir = self.models_dir / model_info["target"]
        
        # Check if model already exists
        if target_dir.exists() and any(target_dir.iterdir()):
            logger.info(f"✅ Vosk model {language} already exists")
            return True
        
        try:
            logger.info(f"📥 Downloading Vosk model: {language}")
            
            # Download model
            temp_zip = self.models_dir / f"vosk_{language}.zip"
            
            response = requests.get(model_info["url"], stream=True, timeout=60)
            response.raise_for_status()
            
            with open(temp_zip, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Extract model
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(self.models_dir)
            
            # Rename to target directory
            extracted_dir = self.models_dir / model_info["name"]
            if extracted_dir.exists():
                extracted_dir.rename(target_dir)
            
            # Cleanup
            temp_zip.unlink()
            
            logger.info(f"✅ Vosk model {language} downloaded successfully")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to download Vosk model {language}: {e}")
            return False
    
    def initialize_database(self):
        """Initialize database"""
        logger.info("🗄️ Initializing database...")
        
        try:
            sys.path.append('/app')
            from config.database import init_db
            init_db()
            logger.info("✅ Database initialized successfully")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Database initialization failed: {e}")
            # Create minimal database setup
            try:
                import sqlite3
                db_path = "/app/data/chatbot.db"
                conn = sqlite3.connect(db_path)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        message TEXT,
                        response TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                conn.close()
                logger.info("✅ Minimal database created")
                return True
            except Exception as e2:
                logger.error(f"❌ Failed to create minimal database: {e2}")
                return False
    
    def run_setup(self):
        """Run complete setup process"""
        logger.info("🚀 Starting complete auto setup...")
        
        setup_results = {}
        
        # 1. Setup configuration
        setup_results['config'] = self.setup_config()
        
        # 2. Initialize database
        setup_results['database'] = self.initialize_database()
        
        # 3. Install Ollama (optional, không critical)
        setup_results['ollama_install'] = self.install_ollama()
        
        # 4. Start Ollama server (nếu cài đặt thành công)
        if setup_results['ollama_install']:
            setup_results['ollama_server'] = self.start_ollama_server()
            
            # 5. Download Ollama model (nếu server chạy thành công)
            if setup_results['ollama_server']:
                setup_results['ollama_model'] = self.download_ollama_model()
            else:
                setup_results['ollama_model'] = False
        else:
            setup_results['ollama_server'] = False
            setup_results['ollama_model'] = False
        
        # 6. Download Vosk model (optional, không critical)
        setup_results['vosk_model'] = self.download_vosk_model()
        
        # Print summary
        logger.info("\n📊 Setup Summary:")
        for component, success in setup_results.items():
            status = "✅" if success else "⚠️"
            logger.info(f"  {status} {component}")
        
        # Determine if we can start the application
        critical_components = ['config', 'database']
        critical_success = all(setup_results[comp] for comp in critical_components)
        
        if critical_success:
            logger.info("🎉 Critical components ready - starting application")
            return True
        else:
            logger.error("❌ Critical components failed - cannot start")
            return False

if __name__ == "__main__":
    setup = AutoSetup()
    if setup.run_setup():
        sys.exit(0)
    else:
        sys.exit(1)
EOF

# Make setup script executable
RUN chmod +x /app/auto_setup.py

# Create smart startup script
RUN cat > /app/smart_start.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Smart ChatBot Startup..."

# Run auto setup
python /app/auto_setup.py

# Start application regardless of setup results
echo "🎯 Starting FastAPI application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
EOF

RUN chmod +x /app/smart_start.sh

# Expose ports
EXPOSE 8000 11434

# Health check
HEALTHCHECK --interval=30s --timeout=15s --start-period=180s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use smart startup
CMD ["/app/smart_start.sh"]