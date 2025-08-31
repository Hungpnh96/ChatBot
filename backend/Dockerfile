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

# Create necessary directories
RUN mkdir -p /app/data/models /app/logs /app/temp

# Copy application code (including auto_setup.py)
COPY . .

# Make setup script executable
RUN chmod +x /app/auto_setup.py

# Copy startup script
COPY smart_start.sh /app/smart_start.sh
RUN chmod +x /app/smart_start.sh

# Expose ports
EXPOSE 8000 11434

# Health check
HEALTHCHECK --interval=30s --timeout=15s --start-period=180s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use smart startup
CMD ["/app/smart_start.sh"]