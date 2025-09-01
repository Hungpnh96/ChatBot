#!/bin/bash
set -e

echo "🔍 Waiting for backend to be ready..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Wait for backend to be ready
max_attempts=60
attempt=1

while [ $attempt -le $max_attempts ]; do
    print_status "Attempt $attempt/$max_attempts - Checking backend health..."
    
    if curl -f http://localhost:8000/ > /dev/null 2>&1; then
        print_success "Backend is ready!"
        print_success "🌐 Frontend: http://localhost:3000"
        print_success "🔧 Backend API: http://localhost:8000"
        print_success "🤖 Ollama: http://localhost:11434"
        exit 0
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ Backend is not ready after $max_attempts attempts"
        echo "📋 Checking logs..."
        docker-compose logs backend | tail -20
        exit 1
    fi
    
    sleep 10
    attempt=$((attempt + 1))
done
