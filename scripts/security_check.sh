#!/bin/bash

# Security Check Script for ChatBot Project
# Kiểm tra các file nhạy cảm, keys, và file size lớn

echo "🔒 CHATBOT SECURITY CHECK"
echo "========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if we're in git repo
if [ ! -d ".git" ]; then
    print_status $RED "❌ Not in a git repository"
    exit 1
fi

print_status $BLUE "📋 Checking for sensitive files..."

# 1. Check for environment files
echo ""
print_status $YELLOW "🔍 Environment Files:"
env_files=$(find . -name ".env*" -type f | grep -v ".env.example")
if [ -n "$env_files" ]; then
    echo "$env_files" | while read file; do
        if git ls-files --error-unmatch "$file" >/dev/null 2>&1; then
            print_status $RED "❌ TRACKED: $file (contains secrets!)"
        else
            print_status $GREEN "✅ IGNORED: $file"
        fi
    done
else
    print_status $GREEN "✅ No .env files found"
fi

# 2. Check for API keys and secrets in tracked files
echo ""
print_status $YELLOW "🔍 Checking for API keys in tracked files:"
key_patterns="api[_-]?key|secret|token|password|credential"
suspicious_files=$(git ls-files | xargs grep -l -i -E "$key_patterns" 2>/dev/null | grep -v -E "\.(md|txt|example|template)$")

if [ -n "$suspicious_files" ]; then
    echo "$suspicious_files" | while read file; do
        print_status $RED "⚠️  SUSPICIOUS: $file may contain secrets"
        # Show lines with potential secrets (first 3 matches)
        git ls-files | xargs grep -i -E "$key_patterns" "$file" 2>/dev/null | head -3 | sed 's/^/    /'
    done
else
    print_status $GREEN "✅ No suspicious patterns found in tracked files"
fi

# 3. Check for large files
echo ""
print_status $YELLOW "🔍 Large files (>1MB):"
large_files=$(git ls-files | xargs ls -la 2>/dev/null | awk '$5 > 1048576 {printf "%.1fMB %s\n", $5/1048576, $9}' | sort -nr)

if [ -n "$large_files" ]; then
    echo "$large_files" | while read file; do
        print_status $YELLOW "⚠️  LARGE: $file"
    done
else
    print_status $GREEN "✅ No large files found"
fi

# 4. Check for model files
echo ""
print_status $YELLOW "🔍 AI Model files:"
model_patterns="\.(bin|model|pkl|h5|hdf5|onnx|pb|tflite|pt|pth|safetensors)$"
model_files=$(git ls-files | grep -E "$model_patterns")

if [ -n "$model_files" ]; then
    echo "$model_files" | while read file; do
        size=$(ls -lh "$file" 2>/dev/null | awk '{print $5}')
        print_status $RED "❌ MODEL FILE: $file ($size)"
    done
else
    print_status $GREEN "✅ No model files tracked"
fi

# 5. Check for database files
echo ""
print_status $YELLOW "🔍 Database files:"
db_files=$(git ls-files | grep -E "\.(db|sqlite|sqlite3)$")

if [ -n "$db_files" ]; then
    echo "$db_files" | while read file; do
        size=$(ls -lh "$file" 2>/dev/null | awk '{print $5}')
        print_status $RED "❌ DATABASE: $file ($size)"
    done
else
    print_status $GREEN "✅ No database files tracked"
fi

# 6. Check for log files
echo ""
print_status $YELLOW "🔍 Log files:"
log_files=$(git ls-files | grep -E "\.(log)$")

if [ -n "$log_files" ]; then
    echo "$log_files" | while read file; do
        size=$(ls -lh "$file" 2>/dev/null | awk '{print $5}')
        print_status $YELLOW "⚠️  LOG FILE: $file ($size)"
    done
else
    print_status $GREEN "✅ No log files tracked"
fi

# 7. Check .gitignore effectiveness
echo ""
print_status $YELLOW "🔍 .gitignore effectiveness:"

# Check if .gitignore exists
if [ ! -f ".gitignore" ]; then
    print_status $RED "❌ No .gitignore file found!"
else
    print_status $GREEN "✅ .gitignore file exists"
    
    # Check for common patterns
    patterns=("*.env" "*.key" "*.log" "*.db" "node_modules/" "__pycache__/" "*.pyc")
    for pattern in "${patterns[@]}"; do
        if grep -q "$pattern" .gitignore; then
            print_status $GREEN "✅ $pattern is ignored"
        else
            print_status $YELLOW "⚠️  $pattern not in .gitignore"
        fi
    done
fi

# 8. Check for untracked sensitive files
echo ""
print_status $YELLOW "🔍 Untracked sensitive files:"
untracked_sensitive=$(git status --porcelain | grep "^??" | awk '{print $2}' | grep -E "\.(env|key|pem|p12|pfx|db|sqlite)$")

if [ -n "$untracked_sensitive" ]; then
    echo "$untracked_sensitive" | while read file; do
        print_status $YELLOW "⚠️  UNTRACKED SENSITIVE: $file"
    done
else
    print_status $GREEN "✅ No untracked sensitive files"
fi

# 9. Summary and recommendations
echo ""
print_status $BLUE "📋 SECURITY RECOMMENDATIONS:"
echo ""
print_status $GREEN "✅ DO:"
echo "  - Use .env.example templates"
echo "  - Keep real .env files in .gitignore"
echo "  - Use config.json.example for templates"
echo "  - Store large models outside git (Docker volumes, LFS, etc.)"
echo "  - Regular security audits"
echo ""
print_status $RED "❌ DON'T:"
echo "  - Commit API keys or secrets"
echo "  - Track large binary files"
echo "  - Commit database files"
echo "  - Track log files"
echo "  - Ignore .gitignore warnings"

echo ""
print_status $BLUE "🔒 Security check completed!"
echo "========================="