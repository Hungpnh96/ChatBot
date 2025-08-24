#!/bin/bash

# Startup script for ChatBot backend
# Checks for Vosk models and downloads if missing

set -e

echo "🚀 Starting ChatBot Backend..."

# Function to check if model exists and is valid
check_model() {
    local model_path="$1"
    local model_name="$2"
    
    if [ -d "$model_path" ] && [ "$(ls -A $model_path)" ]; then
        echo "✅ $model_name model found at $model_path"
        return 0
    else
        echo "❌ $model_name model not found or empty at $model_path"
        return 1
    fi
}

# Check and download Vietnamese Vosk model
echo "🔍 Checking Vosk models..."

VOSK_VI_PATH="/app/data/models/vosk-vi"
VOSK_EN_PATH="/app/data/models/vosk-en"

# Create models directory if it doesn't exist
mkdir -p /app/data/models

# Check if we should download models on start
DOWNLOAD_ON_START=${DOWNLOAD_MODELS_ON_START:-false}

# Check Vietnamese model
if ! check_model "$VOSK_VI_PATH" "Vietnamese"; then
    if [ "$DOWNLOAD_ON_START" = "true" ]; then
        echo "📥 Downloading Vietnamese Vosk model..."
        python /app/scripts/download_vosk_model.py vi
        
        if check_model "$VOSK_VI_PATH" "Vietnamese"; then
            echo "✅ Vietnamese model downloaded successfully"
        else
            echo "❌ Failed to download Vietnamese model"
            echo "⚠️  Voice recognition may not work properly"
        fi
    else
        echo "⚠️  Vietnamese model not found and DOWNLOAD_MODELS_ON_START is not enabled"
        echo "💡 Set DOWNLOAD_MODELS_ON_START=true to auto-download models"
    fi
fi

# Optional: Check English model (uncomment if needed)
# if ! check_model "$VOSK_EN_PATH" "English"; then
#     echo "📥 Downloading English Vosk model..."
#     python /app/scripts/download_vosk_model.py en-small
# fi

# Verify model files
echo "📋 Model verification:"
for model_dir in /app/data/models/vosk-*; do
    if [ -d "$model_dir" ]; then
        model_name=$(basename "$model_dir")
        file_count=$(find "$model_dir" -type f | wc -l)
        size_mb=$(du -sm "$model_dir" | cut -f1)
        echo "  - $model_name: $file_count files, ${size_mb}MB"
        
        # Check for essential model files
        if [ -f "$model_dir/am/final.mdl" ] && [ -f "$model_dir/graph/HCLG.fst" ]; then
            echo "    ✅ Essential model files present"
        else
            echo "    ⚠️  Some essential model files may be missing"
        fi
    fi
done

# Set environment variables
export VOSK_MODEL_PATH="/app/data/models/vosk-vi"
export PYTHONPATH="/app:$PYTHONPATH"

echo "🔧 Environment setup:"
echo "  - VOSK_MODEL_PATH: $VOSK_MODEL_PATH"
echo "  - PYTHONPATH: $PYTHONPATH"
echo "  - Working directory: $(pwd)"

# Test Python imports
echo "🧪 Testing Python imports..."
python -c "
import sys
import os
print(f'Python version: {sys.version}')

try:
    import vosk
    print('✅ Vosk import successful')
except ImportError as e:
    print(f'❌ Vosk import failed: {e}')
    sys.exit(1)

try:
    import speech_recognition as sr
    print('✅ SpeechRecognition import successful')
except ImportError as e:
    print(f'❌ SpeechRecognition import failed: {e}')

try:
    import pydub
    print('✅ Pydub import successful')
except ImportError as e:
    print(f'❌ Pydub import failed: {e}')

try:
    import pyttsx3
    print('✅ Pyttsx3 import successful')
except ImportError as e:
    print(f'❌ Pyttsx3 import failed: {e}')

try:
    from vosk import Model
    model_path = '/app/data/models/vosk-vi'
    if os.path.exists(model_path):
        model = Model(model_path)
        print('✅ Vosk model loading test successful')
    else:
        print('⚠️  Vosk model path not found for testing')
except Exception as e:
    print(f'❌ Vosk model loading test failed: {e}')
"

if [ $? -ne 0 ]; then
    echo "❌ Python import tests failed"
    exit 1
fi

echo "✅ All checks passed! Starting application..."

# Start the application
exec "$@"