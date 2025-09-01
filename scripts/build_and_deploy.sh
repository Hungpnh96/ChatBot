#!/bin/bash
set -e

echo "🚀 Bixby Chatbot - Build & Deploy Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    print_status "Checking Docker..."
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    print_success "Docker is running"
}

# Check if docker-compose is available
check_docker_compose() {
    print_status "Checking docker-compose..."
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed. Please install it first."
        exit 1
    fi
    print_success "docker-compose is available"
}

# Clean up old containers and images
cleanup() {
    print_status "Cleaning up old containers and images..."
    
    # Stop and remove containers
    docker-compose down --remove-orphans 2>/dev/null || true
    docker-compose -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true
    
    # Remove old images (optional)
    if [[ "$1" == "--clean-images" ]]; then
        print_warning "Removing old images..."
        docker image prune -f 2>/dev/null || true
    fi
    
    print_success "Cleanup completed"
}

# Build and start development environment
build_dev() {
    print_status "Building development environment..."
    
    # Build images
    docker-compose build --no-cache
    
    # Start services
    docker-compose up -d
    
    print_success "Development environment started"
    print_status "Backend: http://localhost:8000"
    print_status "Frontend: http://localhost:3000"
    print_status "Ollama: http://localhost:11434"
    
    # Show logs
    print_status "Showing logs (Ctrl+C to stop)..."
    docker-compose logs -f
}

# Build and start production environment
build_prod() {
    print_status "Building production environment..."
    
    # Build images
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # Start services
    docker-compose -f docker-compose.prod.yml up -d
    
    print_success "Production environment started"
    print_status "Backend: http://localhost:8000"
    print_status "Frontend: http://localhost:3000"
    print_status "Ollama: http://localhost:11434"
    
    # Show logs
    print_status "Showing logs (Ctrl+C to stop)..."
    docker-compose -f docker-compose.prod.yml logs -f
}

# Check system status
check_status() {
    print_status "Checking system status..."
    
    # Check if containers are running
    if docker-compose ps | grep -q "Up"; then
        print_success "Containers are running"
        
        # Check backend health
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Backend is healthy"
        else
            print_warning "Backend health check failed"
        fi
        
        # Check frontend
        if curl -f http://localhost:3000 > /dev/null 2>&1; then
            print_success "Frontend is accessible"
        else
            print_warning "Frontend is not accessible"
        fi
        
        # Check Ollama
        if curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then
            print_success "Ollama is running"
        else
            print_warning "Ollama is not accessible"
        fi
    else
        print_error "No containers are running"
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev          Build and start development environment"
    echo "  prod         Build and start production environment"
    echo "  status       Check system status"
    echo "  cleanup      Clean up containers and images"
    echo "  logs         Show logs"
    echo "  stop         Stop all containers"
    echo "  restart      Restart all containers"
    echo ""
    echo "Examples:"
    echo "  $0 dev                    # Start development"
    echo "  $0 prod                   # Start production"
    echo "  $0 dev --clean-images     # Clean images and start dev"
    echo "  $0 status                 # Check status"
}

# Main script
main() {
    case "$1" in
        "dev")
            check_docker
            check_docker_compose
            cleanup "$2"
            build_dev
            ;;
        "prod")
            check_docker
            check_docker_compose
            cleanup "$2"
            build_prod
            ;;
        "status")
            check_status
            ;;
        "cleanup")
            cleanup "$2"
            ;;
        "logs")
            if [[ "$2" == "prod" ]]; then
                docker-compose -f docker-compose.prod.yml logs -f
            else
                docker-compose logs -f
            fi
            ;;
        "stop")
            docker-compose down 2>/dev/null || true
            docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
            print_success "All containers stopped"
            ;;
        "restart")
            docker-compose restart 2>/dev/null || true
            docker-compose -f docker-compose.prod.yml restart 2>/dev/null || true
            print_success "All containers restarted"
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
