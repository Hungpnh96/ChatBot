#!/bin/bash
# startup_with_ollama.sh - Tự động cài đặt và khởi động Ollama

set -e  # Exit on error

echo "🚀 Starting ChatBot with Auto Ollama Setup..."

# Màu sắc cho log
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function: Kiểm tra Ollama server
check_ollama_server() {
    local max_attempts=30
    local attempt=1
    
    log_info "Checking Ollama server status..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            log_success "Ollama server is running"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts: Waiting for Ollama server..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "Ollama server failed to start after $max_attempts attempts"
    return 1
}

# Function: Khởi động Ollama service
start_ollama() {
    log_info "Starting Ollama server..."
    
    # Kiểm tra xem Ollama đã chạy chưa
    if pgrep -f "ollama serve" > /dev/null; then
        log_warning "Ollama server already running"
        return 0
    fi
    
    # Start Ollama trong background
    nohup ollama serve > /app/logs/ollama.log 2>&1 &
    
    # Đợi Ollama khởi động
    sleep 5
    
    # Kiểm tra status
    if check_ollama_server; then
        log_success "Ollama server started successfully"
        return 0
    else
        log_error "Failed to start Ollama server"
        return 1
    fi
}

# Function: Kiểm tra và tải model
setup_ollama_model() {
    local model_name=${OLLAMA_MODEL:-"gemma2:9b"}
    
    log_info "Setting up Ollama model: $model_name"
    
    # Kiểm tra model có tồn tại không
    if ollama list | grep -q "$model_name"; then
        log_success "Model $model_name already exists"
        return 0
    fi
    
    log_info "Downloading model: $model_name..."
    
    # Download model với timeout
    if timeout 1800 ollama pull "$model_name"; then
        log_success "Model $model_name downloaded successfully"
        return 0
    else
        log_error "Failed to download model: $model_name"
        log_warning "ChatBot will run without AI model (fallback mode)"
        return 1
    fi
}

# Function: Kiểm tra cấu hình
check_configuration() {
    log_info "Checking configuration files..."
    
    # Kiểm tra config.json
    if [ ! -f "/app/config.json" ]; then
        if [ -f "/app/config.json.example" ]; then
            log_warning "config.json not found, creating from example..."
            cp /app/config.json.example /app/config.json
        else
            log_error "No configuration files found"
            return 1
        fi
    fi
    
    log_success "Configuration files OK"
    return 0
}

# Function: Cấp quyền cho thư mục
setup_permissions() {
    log_info "Setting up permissions..."
    
    # Tạo và cấp quyền cho các thư mục cần thiết
    mkdir -p /app/data /app/logs
    chmod 755 /app/data /app/logs
    
    log_success "Permissions set successfully"
}

# Main execution
main() {
    log_info "=== ChatBot Startup Process ==="
    
    # 1. Setup permissions
    setup_permissions
    
    # 2. Kiểm tra cấu hình
    if ! check_configuration; then
        log_error "Configuration check failed"
        exit 1
    fi
    
    # 3. Khởi động Ollama (có thể fail, không critical)
    if start_ollama; then
        # 4. Setup model nếu Ollama thành công
        setup_ollama_model
    else
        log_warning "Ollama setup failed, continuing in fallback mode"
    fi
    
    # 5. Khởi động ChatBot application
    log_info "Starting ChatBot application..."
    
    # Chạy migration nếu cần
    if [ -f "/app/scripts/init_db.py" ]; then
        log_info "Running database initialization..."
        python /app/scripts/init_db.py
    fi
    
    # Khởi động ứng dụng chính
    log_success "Starting main application on port 8000"
    exec python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
}

# Trap để cleanup khi exit
cleanup() {
    log_info "Cleaning up..."
    pkill -f "ollama serve" || true
    exit 0
}

trap cleanup SIGTERM SIGINT

# Chạy main function
main "$@"