#!/bin/bash
# deploy_production.sh - Production Deployment Script với Model Management

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

echo "🚀 ChatBot Production Deployment"
echo "================================"

# Configuration
PROJECT_NAME="chatbot"
DOCKER_REGISTRY=""
IMAGE_TAG="latest"
ENVIRONMENT="production"

# Function: Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed!"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed!"
        exit 1
    fi
    
    # Check disk space (minimum 10GB)
    DISK_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$DISK_SPACE" -lt 10 ]; then
        log_warning "Low disk space: ${DISK_SPACE}G available (recommended: 10G+)"
    fi
    
    # Check memory (minimum 4GB)
    MEMORY_GB=$(free -g | awk 'NR==2 {print $2}')
    if [ "$MEMORY_GB" -lt 4 ]; then
        log_warning "Low memory: ${MEMORY_GB}G available (recommended: 4G+)"
    fi
    
    log_success "Prerequisites OK"
}

# Function: Setup production environment
setup_production_env() {
    log_info "Setting up production environment..."
    
    # Create production config
    if [ ! -f ".env.production" ]; then
        cat > .env.production << 'EOF'
# Production Environment Configuration
NODE_ENV=production

# API Configuration
REACT_APP_API_URL=https://your-domain.com/api
REACT_APP_WS_URL=wss://your-domain.com/ws

# Model Management
AUTO_SETUP_ENABLED=true
DOWNLOAD_MODELS_ON_START=true
INSTALL_OLLAMA=true

# AI Configuration
PREFERRED_AI_PROVIDER=ollama
AUTO_FALLBACK=true
OLLAMA_MODEL=gemma2:9b
OLLAMA_BASE_URL=http://localhost:11434

# Performance
MAX_CONCURRENT_DOWNLOADS=2
MODEL_DOWNLOAD_TIMEOUT=1800

# Security
CORS_ORIGINS=["https://your-domain.com"]
LOG_LEVEL=INFO

# Database
DB_PATH=/app/data/chatbot.db

# Backup
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=7
EOF
        log_success "Created .env.production"
    fi
    
    # Create production docker-compose
    if [ ! -f "docker-compose.prod.yml" ]; then
        cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    container_name: chatbot_backend_prod
    restart: unless-stopped
    ports:
      - "8000:8000"
      - "11434:11434"
    volumes:
      - chatbot_data:/app/data
      - ollama_models:/root/.ollama
      - vosk_models:/app/data/models
      - ./logs:/app/logs
    environment:
      - NODE_ENV=production
      - PYTHONPATH=/app
      - PYTHONUNBUFFERED=1
      - AUTO_SETUP_ENABLED=true
      - DOWNLOAD_MODELS_ON_START=true
      - PREFERRED_AI_PROVIDER=ollama
      - OLLAMA_MODEL=gemma2:9b
      - OLLAMA_BASE_URL=http://localhost:11434
      - VOSK_MODEL_PATH=/app/data/models/vosk-vi
      - MAX_CONCURRENT_DOWNLOADS=2
      - MODEL_DOWNLOAD_TIMEOUT=1800
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 300s
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4.0'
        reservations:
          memory: 4G
          cpus: '2.0'

  frontend:
    build: 
      context: ./frontend
      dockerfile: Dockerfile
    container_name: chatbot_frontend_prod
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    environment:
      - NODE_ENV=production
      - REACT_APP_API_URL=https://your-domain.com/api
      - REACT_APP_WS_URL=wss://your-domain.com/ws
    depends_on:
      - backend
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'

  nginx:
    image: nginx:alpine
    container_name: chatbot_nginx_prod
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend

volumes:
  chatbot_data:
    name: chatbot_data_prod
  ollama_models:
    name: chatbot_ollama_models_prod
  vosk_models:
    name: chatbot_vosk_models_prod

networks:
  default:
    name: chatbot_network_prod
EOF
        log_success "Created docker-compose.prod.yml"
    fi
    
    # Create nginx config
    mkdir -p nginx
    if [ ! -f "nginx/nginx.conf" ]; then
        cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }
    
    upstream frontend {
        server frontend:80;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=chat:10m rate=5r/s;
    
    server {
        listen 80;
        server_name your-domain.com;
        
        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name your-domain.com;
        
        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
        
        # API routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # WebSocket
        location /ws/ {
            limit_req zone=chat burst=10 nodelay;
            proxy_pass http://backend/ws/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }
        
        # Frontend
        location / {
            proxy_pass http://frontend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF
        log_success "Created nginx configuration"
    fi
}

# Function: Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check if services are running
    if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        log_warning "Services are already running. Stopping them first..."
        docker-compose -f docker-compose.prod.yml down
    fi
    
    # Check disk space for models
    DISK_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    REQUIRED_SPACE=15  # GB for models + application
    
    if [ "$DISK_SPACE" -lt "$REQUIRED_SPACE" ]; then
        log_error "Insufficient disk space: ${DISK_SPACE}G available, ${REQUIRED_SPACE}G required"
        exit 1
    fi
    
    # Check if config files exist
    if [ ! -f "backend/config.json" ]; then
        log_error "backend/config.json not found!"
        exit 1
    fi
    
    log_success "Pre-deployment checks passed"
}

# Function: Build and deploy
build_and_deploy() {
    log_info "Building and deploying services..."
    
    # Build images
    log_info "Building Docker images..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # Start services
    log_info "Starting services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    check_service_health
}

# Function: Check service health
check_service_health() {
    log_info "Checking service health..."
    
    # Check backend health
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        log_success "✅ Backend is healthy"
    else
        log_warning "⚠️ Backend health check failed"
    fi
    
    # Check model status
    MODEL_STATUS=$(curl -s http://localhost:8000/models/health 2>/dev/null || echo '{"success": false}')
    if echo "$MODEL_STATUS" | jq -e '.success' > /dev/null 2>&1; then
        log_success "✅ Model management is healthy"
        echo "   Model status: $(echo "$MODEL_STATUS" | jq -r '.data.status')"
    else
        log_warning "⚠️ Model management health check failed"
    fi
    
    # Check frontend
    if curl -sf http://localhost:80 > /dev/null 2>&1; then
        log_success "✅ Frontend is accessible"
    else
        log_warning "⚠️ Frontend not accessible"
    fi
}

# Function: Setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Create monitoring script
    cat > monitor.sh << 'EOF'
#!/bin/bash
# monitor.sh - Production monitoring script

echo "📊 ChatBot Production Monitoring"
echo "================================"

# Service status
echo "🔍 Service Status:"
docker-compose -f docker-compose.prod.yml ps

echo

# Resource usage
echo "💾 Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

echo

# Model status
echo "🤖 Model Status:"
curl -s http://localhost:8000/models/status | jq '.data | {total_models, available_models, missing_required}'

echo

# Recent logs
echo "📝 Recent Logs:"
docker-compose -f docker-compose.prod.yml logs --tail=10 backend
EOF
    
    chmod +x monitor.sh
    log_success "Created monitoring script (monitor.sh)"
}

# Function: Setup backup
setup_backup() {
    log_info "Setting up backup system..."
    
    # Create backup script
    cat > backup.sh << 'EOF'
#!/bin/bash
# backup.sh - Production backup script

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="chatbot_backup_$DATE"

echo "💾 Creating backup: $BACKUP_NAME"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
echo "📊 Backing up database..."
docker-compose -f docker-compose.prod.yml exec -T backend sqlite3 /app/data/chatbot.db ".backup /app/data/chatbot_backup.db"
docker cp chatbot_backend_prod:/app/data/chatbot_backup.db "$BACKUP_DIR/${BACKUP_NAME}_db.sqlite"

# Backup models
echo "🤖 Backing up models..."
docker run --rm -v chatbot_ollama_models_prod:/data -v "$(pwd)/$BACKUP_DIR":/backup alpine tar czf "/backup/${BACKUP_NAME}_ollama_models.tar.gz" -C /data .
docker run --rm -v chatbot_vosk_models_prod:/data -v "$(pwd)/$BACKUP_DIR":/backup alpine tar czf "/backup/${BACKUP_NAME}_vosk_models.tar.gz" -C /data .

# Backup config
echo "⚙️ Backing up configuration..."
cp backend/config.json "$BACKUP_DIR/${BACKUP_NAME}_config.json"

# Create backup archive
tar czf "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" -C "$BACKUP_DIR" "${BACKUP_NAME}_db.sqlite" "${BACKUP_NAME}_ollama_models.tar.gz" "${BACKUP_NAME}_vosk_models.tar.gz" "${BACKUP_NAME}_config.json"

# Cleanup individual files
rm "$BACKUP_DIR/${BACKUP_NAME}_db.sqlite" "$BACKUP_DIR/${BACKUP_NAME}_ollama_models.tar.gz" "$BACKUP_DIR/${BACKUP_NAME}_vosk_models.tar.gz" "$BACKUP_DIR/${BACKUP_NAME}_config.json"

# Remove old backups (keep last 7 days)
find "$BACKUP_DIR" -name "chatbot_backup_*.tar.gz" -mtime +7 -delete

echo "✅ Backup completed: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
EOF
    
    chmod +x backup.sh
    log_success "Created backup script (backup.sh)"
    
    # Setup cron job for daily backup
    if ! crontab -l 2>/dev/null | grep -q "backup.sh"; then
        (crontab -l 2>/dev/null; echo "0 2 * * * cd $(pwd) && ./backup.sh >> logs/backup.log 2>&1") | crontab -
        log_success "Setup daily backup cron job (2 AM)"
    fi
}

# Function: Show deployment info
show_deployment_info() {
    echo
    echo "🎉 Production Deployment Complete!"
    echo "=================================="
    echo
    echo "📍 Services:"
    echo "   Frontend:  http://localhost (or https://your-domain.com)"
    echo "   Backend:   http://localhost:8000"
    echo "   API Docs:  http://localhost:8000/docs"
    echo "   Health:    http://localhost:8000/health"
    echo "   Models:    http://localhost:8000/models/status"
    echo
    echo "🔧 Management:"
    echo "   Monitor:   ./monitor.sh"
    echo "   Backup:    ./backup.sh"
    echo "   Logs:      docker-compose -f docker-compose.prod.yml logs -f"
    echo "   Restart:   docker-compose -f docker-compose.prod.yml restart"
    echo "   Stop:      docker-compose -f docker-compose.prod.yml down"
    echo
    echo "📊 Model Management:"
    echo "   Status:    curl http://localhost:8000/models/status"
    echo "   Download:  curl -X POST http://localhost:8000/models/ensure"
    echo "   Validate:  curl -X POST http://localhost:8000/models/validate"
    echo
    echo "🔒 Security Notes:"
    echo "   - Update SSL certificates in nginx/ssl/"
    echo "   - Change default passwords in config.json"
    echo "   - Configure firewall rules"
    echo "   - Set up monitoring alerts"
    echo
    log_success "Deployment completed successfully! 🚀"
}

# Main execution
main() {
    check_prerequisites
    setup_production_env
    pre_deployment_checks
    build_and_deploy
    setup_monitoring
    setup_backup
    show_deployment_info
}

# Run main function
main "$@"
