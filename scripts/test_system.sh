#!/bin/bash
set -e

echo "🧪 Bixby ChatBot - System Test Suite"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="$3"
    
    print_status "Running: $test_name"
    
    if eval "$test_command" 2>/dev/null | grep -q "$expected_pattern"; then
        print_success "$test_name"
        ((TESTS_PASSED++))
    else
        print_error "$test_name"
        ((TESTS_FAILED++))
    fi
}

echo ""
print_status "Starting system tests..."

# Test 1: Backend Health
run_test "Backend Health Check" \
    "curl -s http://localhost:8000/" \
    "ChatBot API is running"

# Test 2: Frontend Accessibility
run_test "Frontend Accessibility" \
    "curl -s http://localhost:3000" \
    "Bixby ChatBot - AI Assistant"

# Test 3: Basic Chat
run_test "Basic Chat Functionality" \
    "curl -s -X POST http://localhost:8000/chat/message -H 'Content-Type: application/json' -d '{\"message\": \"test\"}'" \
    "success.*true"

# Test 4: Weather API
run_test "Weather API Integration" \
    "curl -s -X POST http://localhost:8000/chat/message -H 'Content-Type: application/json' -d '{\"message\": \"thời tiết\"}'" \
    "nhiệt độ"

# Test 5: AI Provider
run_test "AI Provider Detection" \
    "curl -s -X POST http://localhost:8000/chat/message -H 'Content-Type: application/json' -d '{\"message\": \"hello\"}' | jq -r '.provider'" \
    "ollama"

# Test 6: Database Storage
run_test "Database Storage" \
    "curl -s -X POST http://localhost:8000/chat/message -H 'Content-Type: application/json' -d '{\"message\": \"test db\"}' | jq -r '.conversation_id'" \
    "[0-9]"

# Test 7: API Documentation
run_test "API Documentation" \
    "curl -s http://localhost:8000/docs" \
    "Swagger UI"

# Test 8: Chat History
run_test "Chat History Endpoint" \
    "curl -s http://localhost:8000/chat/history" \
    "success"

echo ""
echo "📊 Test Results Summary:"
echo "========================"
echo "✅ Tests Passed: $TESTS_PASSED"
echo "❌ Tests Failed: $TESTS_FAILED"
echo "📈 Success Rate: $(( (TESTS_PASSED * 100) / (TESTS_PASSED + TESTS_FAILED) ))%"

echo ""
if [ $TESTS_FAILED -eq 0 ]; then
    print_success "All tests passed! System is working perfectly! 🎉"
else
    print_warning "Some tests failed. Check the logs for details."
fi

echo ""
print_status "System URLs:"
echo "  🌐 Frontend: http://localhost:3000"
echo "  🔧 Backend: http://localhost:8000"
echo "  📚 API Docs: http://localhost:8000/docs"

echo ""
print_status "Manual Test Commands:"
echo "  Chat: curl -X POST http://localhost:8000/chat/message -H 'Content-Type: application/json' -d '{\"message\": \"Xin chào!\"}'"
echo "  Weather: curl -X POST http://localhost:8000/chat/message -H 'Content-Type: application/json' -d '{\"message\": \"Thời tiết Hà Nội\"}'"
echo "  History: curl http://localhost:8000/chat/history"
