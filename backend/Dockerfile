# Backend Dockerfile with audio dependencies for voice features
FROM python:3.11-slim

# Install system dependencies required by pydub/pyttsx3 and vosk
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    flac \
    libatomic1 \
    espeak-ng \
    libespeak-ng1 \
    libasound2 \
    tzdata \
    wget \
    unzip \
    curl \
  && rm -rf /var/lib/apt/lists/*

ENV TZ=Asia/Ho_Chi_Minh
ENV VOSK_MODEL_PATH=/app/data/models/vosk-vi

# Set working dir
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy scripts first
COPY scripts/ /app/scripts/
RUN chmod +x /app/scripts/*.sh && chmod +x /app/scripts/*.py

# Create models directory (models will be downloaded at runtime if needed)
RUN mkdir -p /app/data/models

# Copy source code
COPY . .

# Expose API port
EXPOSE 8000

# Use startup script as entrypoint to handle runtime model checks
ENTRYPOINT ["bash", "/app/scripts/startup.sh"]

# Default command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
