# 🎤 Vosk Model Docker Setup Guide

Hướng dẫn setup tự động download và sử dụng Vosk models trong Docker environment.

## 📋 Tổng quan

Hệ thống đã được cấu hình để:
- ✅ Tự động download Vosk models khi build Docker image
- ✅ Kiểm tra và download models khi container khởi động (nếu cần)
- ✅ Persist models qua Docker volumes
- ✅ Hỗ trợ cả Vietnamese và English models

## 🚀 Quick Start

### 1. Build và chạy với Docker Compose
```bash
# Build và start tất cả services
docker-compose up --build

# Hoặc chạy trong background
docker-compose up --build -d
```

### 2. Kiểm tra logs
```bash
# Xem logs của backend service
docker-compose logs backend

# Follow logs real-time
docker-compose logs -f backend
```

## 🔧 Cấu hình

### Environment Variables

| Variable | Default | Mô tả |
|----------|---------|-------|
| `VOSK_MODEL_PATH` | `/app/data/models/vosk-vi` | Đường dẫn đến model Vietnamese |
| `DOWNLOAD_MODELS_ON_START` | `true` | Tự động download models khi start |

### Docker Volumes

- `vosk_models`: Persist Vosk models giữa các lần restart
- `db_data`: Persist database data

## 📥 Models được hỗ trợ

### Vietnamese Model
- **Model**: `vosk-model-vi-0.4`
- **Size**: ~78MB
- **URL**: https://alphacephei.com/vosk/models/vosk-model-vi-0.4.zip
- **Path**: `/app/data/models/vosk-vi`

### English Models
- **Small Model**: `vosk-model-small-en-us-0.15` (~40MB)
- **Full Model**: `vosk-model-en-us-0.22` (~1.8GB)
- **Path**: `/app/data/models/vosk-en`

## 🛠️ Manual Model Management

### Download specific models
```bash
# Vào container
docker-compose exec backend bash

# Download Vietnamese model
python /app/scripts/download_vosk_model.py vi

# Download English small model
python /app/scripts/download_vosk_model.py en-small

# Download English full model
python /app/scripts/download_vosk_model.py en

# Download multiple models
python /app/scripts/download_vosk_model.py vi,en-small
```

### Check model status
```bash
# List installed models
docker-compose exec backend ls -la /app/data/models/

# Check model details
docker-compose exec backend du -sh /app/data/models/*

# Verify model files
docker-compose exec backend find /app/data/models/vosk-vi -name "*.mdl" -o -name "*.fst"
```

## 🔍 Troubleshooting

### 1. Model download fails
```bash
# Check internet connection
docker-compose exec backend ping -c 3 alphacephei.com

# Check disk space
docker-compose exec backend df -h

# Manual download
docker-compose exec backend python /app/scripts/download_vosk_model.py vi
```

### 2. Model not found error
```bash
# Check if model directory exists
docker-compose exec backend ls -la /app/data/models/

# Check environment variables
docker-compose exec backend env | grep VOSK

# Restart with model download
docker-compose down
docker-compose up --build
```

### 3. Voice recognition not working
```bash
# Test Vosk import
docker-compose exec backend python -c "import vosk; print('Vosk OK')"

# Test model loading
docker-compose exec backend python -c "
from vosk import Model
model = Model('/app/data/models/vosk-vi')
print('Model loaded successfully')
"

# Check voice service health
curl http://localhost:8000/chat/api/voice/health
```

### 4. Container startup issues
```bash
# Check container logs
docker-compose logs backend

# Check startup script
docker-compose exec backend cat /app/scripts/startup.sh

# Run startup script manually
docker-compose exec backend /app/scripts/startup.sh echo "Test"
```

## 📊 Performance Optimization

### 1. Model Selection
- **Vietnamese only**: Sử dụng `vi` model (~78MB)
- **English small**: Sử dụng `en-small` model (~40MB) 
- **English full**: Sử dụng `en` model (~1.8GB) cho accuracy cao hơn

### 2. Docker Build Optimization
```dockerfile
# Build với cache
docker-compose build --no-cache backend

# Build với specific model
docker-compose build --build-arg VOSK_MODELS=vi,en-small backend
```

### 3. Volume Management
```bash
# Backup models
docker run --rm -v chatbot_vosk_models:/data -v $(pwd):/backup alpine tar czf /backup/vosk_models_backup.tar.gz -C /data .

# Restore models
docker run --rm -v chatbot_vosk_models:/data -v $(pwd):/backup alpine tar xzf /backup/vosk_models_backup.tar.gz -C /data
```

## 🔒 Security Considerations

### 1. Model Integrity
- Models được download từ official Vosk repository
- Checksum verification có thể được thêm vào script

### 2. Network Security
- Download chỉ từ trusted sources
- Có thể configure proxy nếu cần

### 3. Storage Security
- Models được store trong Docker volumes
- Không expose sensitive paths

## 🚀 Production Deployment

### 1. Pre-built Images
```bash
# Build image với models
docker build -t chatbot-backend:latest ./backend

# Push to registry
docker tag chatbot-backend:latest your-registry/chatbot-backend:latest
docker push your-registry/chatbot-backend:latest
```

### 2. Environment Configuration
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  backend:
    image: your-registry/chatbot-backend:latest
    environment:
      - DOWNLOAD_MODELS_ON_START=false  # Models already in image
      - VOSK_MODEL_PATH=/app/data/models/vosk-vi
    volumes:
      - vosk_models:/app/data/models:ro  # Read-only in production
```

### 3. Health Checks
```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/chat/api/voice/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

## 📋 Checklist

### Build Time ✅
- [ ] Dockerfile includes model download
- [ ] Required system dependencies installed
- [ ] Python packages installed
- [ ] Scripts have execute permissions
- [ ] Model verification passes

### Runtime ✅
- [ ] Startup script runs successfully
- [ ] Models are accessible
- [ ] Environment variables set correctly
- [ ] Voice service health check passes
- [ ] API endpoints respond correctly

### Testing ✅
- [ ] Voice recognition works
- [ ] Text-to-speech works
- [ ] Model loading performance acceptable
- [ ] Error handling works correctly
- [ ] Container restarts properly

## 🎯 Next Steps

1. **Monitor Performance**: Theo dõi memory usage và response time
2. **Add More Languages**: Thêm support cho các ngôn ngữ khác
3. **Model Updates**: Setup auto-update mechanism cho models
4. **Caching**: Implement model caching strategies
5. **Monitoring**: Add metrics và alerting

## 📞 Support

Nếu gặp vấn đề:

1. **Check Logs**: `docker-compose logs backend`
2. **Verify Models**: `docker-compose exec backend ls -la /app/data/models/`
3. **Test Components**: Use health check endpoints
4. **Rebuild**: `docker-compose up --build --force-recreate`

**Common Issues:**
- Network timeout → Check internet connection
- Disk space → Clean up unused Docker images/volumes
- Permission denied → Check file permissions in scripts/
- Model not found → Verify VOSK_MODEL_PATH environment variable

---

✅ **Setup Complete!** Your ChatBot now has automatic Vosk model management in Docker! 🎉