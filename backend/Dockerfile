# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies
RUN pip install --no-cache-dir \
    vosk \
    pyttsx3 \
    langchain-ollama \
    langchain-openai

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data/models /app/logs /app/temp

# Copy auto setup script
COPY auto_setup.py /app/auto_setup.py

# Make setup script executable
RUN chmod +x /app/auto_setup.py

# Create smart startup script
RUN cat > /app/smart_start.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Smart ChatBot Startup..."

# Run auto setup
python /app/auto_setup.py

# Start application regardless of setup results
echo "🎯 Starting FastAPI application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
EOF

RUN chmod +x /app/smart_start.sh

# Expose ports
EXPOSE 8000 11434

# Health check
HEALTHCHECK --interval=30s --timeout=15s --start-period=180s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use smart startup
CMD ["/app/smart_start.sh"]