#!/bin/bash
# fix_errors.sh - Script fix các lỗi thường gặp

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

echo "🔧 ChatBot Error Fix Script"
echo "=========================="

# Function: Fix Docker Compose volumes
fix_docker_compose() {
    log_info "Fixing Docker Compose volumes..."
    
    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        log_error "docker-compose.yml not found!"
        return 1
    fi
    
    # Check if volumes are properly defined
    if ! grep -q "ollama_models:" docker-compose.yml; then
        log_warning "ollama_models volume not defined, adding..."
        
        # Add missing volumes
        sed -i.bak '/^volumes:/a\
  ollama_models:\
    name: chatbot_ollama_models\
  vosk_models:\
    name: chatbot_vosk_models' docker-compose.yml
        
        log_success "Added missing volumes to docker-compose.yml"
    else
        log_success "Docker Compose volumes are properly configured"
    fi
}

# Function: Fix file permissions
fix_permissions() {
    log_info "Fixing file permissions..."
    
    # Make scripts executable
    chmod +x scripts/*.sh 2>/dev/null || true
    chmod +x backend/scripts/*.py 2>/dev/null || true
    
    # Fix directory permissions
    chmod 755 backend/data backend/logs 2>/dev/null || true
    
    log_success "File permissions fixed"
}

# Function: Create missing directories
create_directories() {
    log_info "Creating missing directories..."
    
    # Create necessary directories
    mkdir -p backend/data/models
    mkdir -p backend/logs
    mkdir -p logs
    mkdir -p data
    
    log_success "Directories created"
}

# Function: Fix Python imports
fix_python_imports() {
    log_info "Checking Python imports..."
    
    # Check if __init__.py files exist
    if [ ! -f "backend/api/__init__.py" ]; then
        log_warning "Creating missing __init__.py files..."
        touch backend/api/__init__.py
        touch backend/services/__init__.py
        touch backend/config/__init__.py
        touch backend/utils/__init__.py
    fi
    
    log_success "Python imports fixed"
}

# Function: Check and fix config
fix_config() {
    log_info "Checking configuration..."
    
    # Check if config.json exists
    if [ ! -f "backend/config.json" ]; then
        log_warning "config.json not found, creating from example..."
        if [ -f "backend/config.json.example" ]; then
            cp backend/config.json.example backend/config.json
            log_success "Created config.json from example"
        else
            log_error "Neither config.json nor config.json.example found!"
            return 1
        fi
    fi
    
    # Check if config is valid JSON
    if ! python3 -m json.tool backend/config.json > /dev/null 2>&1; then
        log_error "config.json is not valid JSON!"
        return 1
    fi
    
    log_success "Configuration is valid"
}

# Function: Clean up Docker
cleanup_docker() {
    log_info "Cleaning up Docker..."
    
    # Stop and remove existing containers
    docker-compose down 2>/dev/null || true
    
    # Remove old volumes if they exist
    docker volume rm chatbot_ollama_models chatbot_vosk_models 2>/dev/null || true
    
    # Clean up unused images
    docker image prune -f 2>/dev/null || true
    
    log_success "Docker cleanup completed"
}

# Function: Test setup
test_setup() {
    log_info "Testing setup..."
    
    # Test Docker Compose syntax
    if docker-compose config > /dev/null 2>&1; then
        log_success "Docker Compose syntax is valid"
    else
        log_error "Docker Compose syntax is invalid!"
        docker-compose config
        return 1
    fi
    
    # Test Python syntax
    if python3 -m py_compile backend/main.py 2>/dev/null; then
        log_success "Python syntax is valid"
    else
        log_error "Python syntax error in main.py!"
        return 1
    fi
    
    log_success "Setup test passed"
}

# Function: Show next steps
show_next_steps() {
    echo
    echo "🎉 Error Fix Completed!"
    echo "======================"
    echo
    echo "Next steps:"
    echo "1. Start the application:"
    echo "   docker-compose up --build"
    echo
    echo "2. Check logs:"
    echo "   docker-compose logs -f backend"
    echo
    echo "3. Test API:"
    echo "   curl http://localhost:8000/health"
    echo
    echo "4. Check model status:"
    echo "   curl http://localhost:8000/models/status"
    echo
    echo "5. If you encounter any issues:"
    echo "   - Check logs: docker-compose logs backend"
    echo "   - Restart: docker-compose restart backend"
    echo "   - Rebuild: docker-compose up --build --force-recreate"
    echo
}

# Main execution
main() {
    log_info "Starting error fix process..."
    
    # Change to ChatBot directory if needed
    if [ -d "ChatBot" ]; then
        cd ChatBot
        log_info "Changed to ChatBot directory"
    fi
    
    # Run all fix functions
    fix_docker_compose
    fix_permissions
    create_directories
    fix_python_imports
    fix_config
    cleanup_docker
    test_setup
    
    show_next_steps
    
    log_success "Error fix completed successfully! 🚀"
}

# Run main function
main "$@"
