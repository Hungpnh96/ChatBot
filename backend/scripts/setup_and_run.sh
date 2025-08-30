#!/bin/bash
# setup_and_run.sh - Script setup và chạy ChatBot hoàn chỉnh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "🚀 ChatBot Complete Setup & Run"
echo "================================"

# Function: Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed!"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed!"
        exit 1
    fi
    
    log_success "Prerequisites OK"
}

# Function: Create project structure
create_project_structure() {
    log_info "Creating project structure..."
    
    # Create directories
    mkdir -p backend/scripts backend/config backend/services backend/models backend/routes
    mkdir -p frontend/src/components frontend/src/services frontend/src/utils
    mkdir -p data logs ollama_models nginx
    
    # Create logs directory with proper permissions
    chmod 755 logs data ollama_models
    
    log_success "Project structure created"
}

# Function: Setup configuration files
setup_configuration() {
    log_info "Setting up configuration files..."
    
    # Backend config
    if [ ! -f "backend/config.json" ]; then
        cat > backend/config.json << 'EOF'
{
  "DB_PATH": "/app/data/chatbot.db",
  
  "API_KEY": "your_github_token_here",
  "BASE_URL": "https://models.github.ai/inference", 
  "MODEL": "openai/gpt-4o-mini",
  
  "OLLAMA_BASE_URL": "http://localhost:11434",
  "OLLAMA_MODEL": "gemma2:9b",
  "OLLAMA_MAX_TOKENS": 2000,
  
  "PREFERRED_AI_PROVIDER": "ollama",
  "AUTO_FALLBACK": true,
  
  "TEMPERATURE": 0.7,
  "MAX_TOKENS": 1000,
  "REQUEST_TIMEOUT": 60,
  
  "TIMEZONE": "Asia/Ho_Chi_Minh",
  "SYSTEM_PROMPT": "Bạn là một trợ lý ảo Bixby thông minh, thân thiện, dễ thương, giúp người dùng trả lời câu hỏi và giải quyết vấn đề. Bạn có khả năng tìm kiếm thông tin mới nhất từ internet khi cần thiết và có thể truy cập thông tin cá nhân để cá nhân hóa câu trả lời. Luôn xưng hô là 'Em' hoặc tên 'Bixby' và không sử dụng từ 'Bạn', Luôn trả lời bằng Tiếng việt.",
  "FALLBACK_MESSAGE": "Em là Bixby! Em đã nhận được tin nhắn: '{user_input}'. Hiện tại em chưa kết nối được với AI, nhưng em sẽ sớm có thể trò chuyện thông minh hơn!",
  "ERROR_MESSAGE": "Em là Bixby! Xin lỗi, em gặp chút vấn đề kỹ thuật khi xử lý câu hỏi của anh. Em đã ghi nhận: '{user_input}' và sẽ cố gắng trả lời tốt hơn!"
}
EOF
        log_success "Created backend/config.json"
    fi
    
    # Main environment file
    if [ ! -f ".env" ]; then
        cat > .env << 'EOF'
# ChatBot Environment Configuration

# Development/Production
NODE_ENV=development

# API Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000

# Auto Setup
AUTO_SETUP_ENABLED=true
DOWNLOAD_MODELS_ON_START=true
INSTALL_OLLAMA=true

# AI Configuration
PREFERRED_AI_PROVIDER=ollama
AUTO_FALLBACK=true
EOF
        log_success "Created .env file"
    fi
    
    # Frontend env
    if [ ! -f "frontend/.env" ]; then
        cat > frontend/.env << 'EOF'
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
GENERATE_SOURCEMAP=false
EOF
        log_success "Created frontend/.env"
    fi
}

# Function: Create minimal main.py if not exists
create_main_app() {
    if [ ! -f "backend/main.py" ]; then
        log_info "Creating minimal main.py..."
        
        cat > backend/main.py << 'EOF'
# Minimal main.py để test
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from datetime import datetime

app = FastAPI(title="ChatBot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "ChatBot API is running"
    }

@app.post("/chat/message")
async def chat(request: dict):
    message = request.get("message", "")
    
    # Simple fallback response
    response = f"Em là Bixby! Em đã nhận được: '{message}'. Hiện em đang trong chế độ fallback!"
    
    return {
        "success": True,
        "response": response,
        "provider": "fallback"
    }

@app.get("/")
async def root():
    return {"message": "ChatBot API", "status": "running"}
EOF
        log_success "Created minimal main.py"
    fi
}

# Function: Create minimal requirements.txt
create_requirements() {
    if [ ! -f "backend/requirements.txt" ]; then
        log_info "Creating requirements.txt..."
        
        cat > backend/requirements.txt << 'EOF'
# Minimal requirements để app chạy được
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
requests==2.31.0

# Optional - sẽ được install trong Docker
langchain-ollama
langchain-openai  
vosk
pyttsx3
aiofiles
EOF
        log_success "Created requirements.txt"
    fi
}

# Function: Create simple frontend
create_simple_frontend() {
    if [ ! -f "frontend/Dockerfile" ]; then
        log_info "Creating simple frontend..."
        
        mkdir -p frontend/public frontend/src
        
        # Frontend Dockerfile
        cat > frontend/Dockerfile << 'EOF'
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF
        
        # Simple HTML page
        cat > frontend/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>ChatBot</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .chat-container { max-width: 600px; margin: 0 auto; }
        .chat-box { border: 1px solid #ddd; height: 400px; overflow-y: auto; padding: 10px; margin-bottom: 10px; }
        .input-container { display: flex; }
        .message-input { flex: 1; padding: 10px; }
        .send-button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }
        .message { margin: 10px 0; }
        .user { text-align: right; color: #007bff; }
        .bot { text-align: left; color: #28a745; }
    </style>
</head>
<body>
    <div class="chat-container">
        <h1>🤖 ChatBot</h1>
        <div id="chatBox" class="chat-box"></div>
        <div class="input-container">
            <input type="text" id="messageInput" class="message-input" placeholder="Nhập tin nhắn..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()" class="send-button">Gửi</button>
        </div>
        <p><strong>Status:</strong> <span id="status">Connecting...</span></p>
    </div>

    <script>
        const API_URL = 'http://localhost:8000';
        const chatBox = document.getElementById('chatBox');
        const messageInput = document.getElementById('messageInput');
        const statusElement = document.getElementById('status');

        // Check API health
        async function checkHealth() {
            try {
                const response = await fetch(`${API_URL}/health`);
                const data = await response.json();
                statusElement.textContent = 'Connected ✅';
                statusElement.style.color = 'green';
            } catch (error) {
                statusElement.textContent = 'Disconnected ❌';
                statusElement.style.color = 'red';
            }
        }

        // Send message
        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            // Add user message to chat
            addMessage(message, 'user');
            messageInput.value = '';

            try {
                const response = await fetch(`${API_URL}/chat/message`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });

                const data = await response.json();
                
                if (data.success) {
                    addMessage(data.response, 'bot');
                } else {
                    addMessage('Lỗi: ' + (data.error || 'Unknown error'), 'bot');
                }
            } catch (error) {
                addMessage('Không thể kết nối với server', 'bot');
            }
        }

        // Add message to chat box
        function addMessage(message, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            messageDiv.textContent = `${sender === 'user' ? 'Bạn' : 'Bixby'}: ${message}`;
            chatBox.appendChild(messageDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        // Handle Enter key
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        // Check health on load
        checkHealth();
        setInterval(checkHealth, 30000); // Check every 30 seconds
    </script>
</body>
</html>
EOF
        log_success "Created simple frontend"
    fi
}

# Function: Deploy application
deploy_application() {
    log_info "Deploying ChatBot application..."
    
    # Stop existing containers
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # Build và start
    log_info "Building containers..."
    docker-compose build --no-cache
    
    log_info "Starting services..."
    docker-compose up -d
    
    log_success "Application deployed"
}

# Function: Monitor startup
monitor_startup() {
    log_info "Monitoring startup process..."
    
    # Wait for backend to be responsive
    local max_wait=300  # 5 minutes
    local waited=0
    
    while [ $waited -lt $max_wait ]; do
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            log_success "Backend is responding!"
            break
        fi
        
        # Show logs every 30 seconds
        if [ $((waited % 30)) -eq 0 ]; then
            log_info "Waiting for backend... ($waited/${max_wait}s)"
            echo "Recent logs:"
            docker-compose logs --tail=5 backend | head -10
            echo "---"
        fi
        
        sleep 5
        waited=$((waited + 5))
    done
    
    if [ $waited -ge $max_wait ]; then
        log_warning "Backend startup timeout, but continuing..."
    fi
}

# Function: Test services
test_services() {
    log_info "Testing services..."
    
    # Test backend health
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        log_success "✅ Backend health check passed"
        
        # Test chat endpoint
        CHAT_RESPONSE=$(curl -s -X POST http://localhost:8000/chat/message \
            -H "Content-Type: application/json" \
            -d '{"message": "hello"}' | jq -r '.response' 2>/dev/null || echo "Chat test failed")
        
        if [ "$CHAT_RESPONSE" != "Chat test failed" ]; then
            log_success "✅ Chat endpoint working"
            echo "   Response: $CHAT_RESPONSE"
        else
            log_warning "⚠️ Chat endpoint may have issues"
        fi
    else
        log_warning "⚠️ Backend health check failed"
    fi
    
    # Test frontend
    if curl -sf http://localhost:3000 > /dev/null 2>&1; then
        log_success "✅ Frontend accessible"
    else
        log_warning "⚠️ Frontend not accessible"
    fi
}

# Function: Show status and instructions
show_final_status() {
    echo
    echo "🎉 ChatBot Setup Complete!"
    echo "=========================="
    echo
    
    # Show service URLs
    echo "📍 Services:"
    echo "   Frontend:  http://localhost:3000"
    echo "   Backend:   http://localhost:8000" 
    echo "   API Docs:  http://localhost:8000/docs"
    echo "   Health:    http://localhost:8000/health"
    echo
    
    # Show service status
    echo "📊 Status:"
    docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    echo
    
    # Show useful commands
    echo "🔧 Useful Commands:"
    echo "   View logs:     docker-compose logs -f backend"
    echo "   Restart:       docker-compose restart"
    echo "   Stop:          docker-compose down"
    echo "   Rebuild:       docker-compose up --build -d"
    echo "   Shell access:  docker-compose exec backend bash"
    echo
    
    # Show AI status
    echo "🤖 AI Status:"
    AI_STATUS=$(curl -s http://localhost:8000/ai/status 2>/dev/null || echo '{"status": "unknown"}')
    echo "   $AI_STATUS"
    echo
    
    echo "🎯 Next Steps:"
    echo "   1. Open http://localhost:3000 to use ChatBot"
    echo "   2. Edit backend/config.json to configure AI providers"
    echo "   3. Monitor logs: docker-compose logs -f"
    echo "   4. Check /health endpoint for detailed status"
    echo
    
    log_success "Setup completed successfully! 🚀"
}

# Main execution
main() {
    check_prerequisites
    create_project_structure
    setup_configuration
    create_requirements
    create_main_app
    create_simple_frontend
    
    echo
    log_info "Ready to deploy application..."
    read -p "Do you want to start the ChatBot now? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        deploy_application
        monitor_startup
        test_services
        show_final_status
    else
        log_info "Setup completed. Run 'docker-compose up -d' when ready."
        echo
        echo "Files created:"
        echo "  ✅ backend/config.json"
        echo "  ✅ backend/main.py"
        echo "  ✅ backend/requirements.txt"
        echo "  ✅ frontend/Dockerfile"
        echo "  ✅ frontend/index.html"
        echo "  ✅ .env"
    fi
}

# Run main function
main "$@"