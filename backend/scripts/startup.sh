#!/bin/bash
# backend/scripts/startup.sh - Script startup cho backend container

set -e

echo "🚀 Starting ChatBot Backend..."

# Colors for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function: Check if model exists and is valid
check_model() {
    local model_path="$1"
    local model_name="$2"
    
    if [ -d "$model_path" ] && [ "$(ls -A $model_path)" ]; then
        log_success "$model_name model found at $model_path"
        return 0
    else
        log_warning "$model_name model not found or empty at $model_path"
        return 1
    fi
}

# Function: Setup directories
setup_directories() {
    log_info "Setting up directories..."
    
    # Create necessary directories
    mkdir -p /app/data/models
    mkdir -p /app/logs
    
    # Set permissions
    chmod 755 /app/data /app/logs
    
    log_success "Directories setup completed"
}

# Function: Check and download Vosk models
setup_vosk_models() {
    log_info "Checking Vosk models..."
    
    local vosk_vi_path="/app/data/models/vosk-vi"
    local download_on_start=${DOWNLOAD_MODELS_ON_START:-false}
    
    # Check Vietnamese model
    if ! check_model "$vosk_vi_path" "Vietnamese"; then
        if [ "$download_on_start" = "true" ]; then
            log_info "Downloading Vietnamese Vosk model..."
            
            # Check if download script exists
            if [ -f "/app/scripts/download_vosk_model.py" ]; then
                python /app/scripts/download_vosk_model.py vi
                
                if check_model "$vosk_vi_path" "Vietnamese"; then
                    log_success "Vietnamese model downloaded successfully"
                else
                    log_error "Failed to download Vietnamese model"
                    log_warning "Voice recognition may not work properly"
                fi
            else
                log_warning "Download script not found, skipping model download"
            fi
        else
            log_warning "Vietnamese model not found and DOWNLOAD_MODELS_ON_START is not enabled"
            log_info "Set DOWNLOAD_MODELS_ON_START=true to auto-download models"
        fi
    fi
}

# Function: Check Ollama installation and setup
setup_ollama() {
    log_info "Checking Ollama setup..."
    
    # Check if Ollama should be installed
    local install_ollama=${INSTALL_OLLAMA:-false}
    
    if [ "$install_ollama" = "true" ]; then
        log_info "Installing Ollama..."
        
        # Install Ollama if not present
        if ! command -v ollama &> /dev/null; then
            log_info "Downloading and installing Ollama..."
            curl -fsSL https://ollama.ai/install.sh | sh
            
            if command -v ollama &> /dev/null; then
                log_success "Ollama installed successfully"
            else
                log_error "Failed to install Ollama"
                return 1
            fi
        else
            log_success "Ollama already installed"
        fi
        
        # Start Ollama server in background
        log_info "Starting Ollama server..."
        nohup ollama serve > /app/logs/ollama.log 2>&1 &
        
        # Wait for Ollama to start
        local max_wait=30
        local waited=0
        
        while [ $waited -lt $max_wait ]; do
            if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
                log_success "Ollama server is running"
                break
            fi
            
            log_info "Waiting for Ollama server to start... ($waited/${max_wait}s)"
            sleep 2
            waited=$((waited + 2))
        done
        
        if [ $waited -ge $max_wait ]; then
            log_warning "Ollama server may not be fully ready"
        fi
        
        # Download model if specified
        local ollama_model=${OLLAMA_MODEL:-""}
        if [ -n "$ollama_model" ]; then
            log_info "Checking Ollama model: $ollama_model"
            
            if ! ollama list | grep -q "$ollama_model"; then
                log_info "Downloading Ollama model: $ollama_model"
                ollama pull "$ollama_model" || log_warning "Failed to download model: $ollama_model"
            else
                log_success "Ollama model already exists: $ollama_model"
            fi
        fi
    else
        log_info "Ollama installation skipped (INSTALL_OLLAMA not set to true)"
    fi
}

# Function: Initialize database if needed
setup_database() {
    log_info "Checking database setup..."
    
    # Check if database initialization script exists
    if [ -f "/app/scripts/init_db.py" ]; then
        log_info "Running database initialization..."
        python /app/scripts/init_db.py || log_warning "Database initialization failed"
    elif [ -f "/app/config/database.py" ]; then
        log_info "Running database setup from config..."
        python -c "
import sys
sys.path.append('/app')
from config.database import init_db
print('Initializing database...')
init_db()
print('Database initialized successfully')
        " || log_warning "Database setup failed"
    else
        log_warning "No database initialization script found"
    fi
}

# Function: Cleanup old processes
cleanup_old_processes() {
    log_info "Cleaning up old processes..."
    
    # Kill any existing Python processes (except current)
    pkill -f "uvicorn" || true
    pkill -f "python.*main" || true
    
    # Wait a moment for cleanup
    sleep 2
}

# Function: Health check before starting
pre_start_health_check() {
    log_info "Performing pre-start health checks..."
    
    # Check Python environment
    python --version
    
    # Check if main.py exists
    if [ ! -f "/app/main.py" ]; then
        log_error "main.py not found!"
        exit 1
    fi
    
    # Check if config files exist
    if [ ! -f "/app/config.json" ] && [ -f "/app/config.json.example" ]; then
        log_warning "config.json not found, creating from example..."
        cp /app/config.json.example /app/config.json
    fi
    
    log_success "Pre-start health checks passed"
}

# Main startup sequence
main() {
    log_info "=== ChatBot Backend Startup ==="
    
    # Setup phase
    setup_directories
    cleanup_old_processes
    pre_start_health_check
    setup_database
    setup_vosk_models
    setup_ollama
    
    log_success "=== Startup sequence completed ==="
    
    # Start the application with provided arguments or default command
    if [ "$#" -eq 0 ]; then
        log_info "Starting FastAPI application..."
        exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    else
        log_info "Executing provided command: $*"
        exec "$@"
    fi
}

# Trap signals for graceful shutdown
cleanup_on_exit() {
    log_info "Shutting down services..."
    pkill -f "ollama serve" || true
    pkill -f "uvicorn" || true
    exit 0
}

trap cleanup_on_exit SIGTERM SIGINT

# Run main function
main "$@"