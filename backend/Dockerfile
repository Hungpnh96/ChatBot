# Use Python 3.11 slim image
FROM python:3.11-slim

# Build arguments
ARG DEBIAN_FRONTEND=noninteractive
ARG PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    git \
    build-essential \
    espeak \
    espeak-ng \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.prod.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies
RUN pip install --no-cache-dir \
    vosk \
    pyttsx3 \
    langchain-ollama

# Create necessary directories
RUN mkdir -p /app/data/models /app/logs /app/temp

# Copy application code (including auto_setup.py)
COPY . .

# Make setup script executable
RUN chmod +x /app/auto_setup.py

# Make startup script executable
RUN chmod +x /app/smart_start.sh

# Expose ports
EXPOSE 8000 11434

# Health check
HEALTHCHECK --interval=30s --timeout=15s --start-period=180s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use shell script for startup
CMD ["/bin/bash", "-c", "python /app/auto_setup.py && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]