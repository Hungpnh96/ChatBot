# 🤖 Model Management System

Hệ thống quản lý models độc lập cho ChatBot với auto-detection, auto-download và production deployment.

## 📋 Tổng quan

Hệ thống Model Management được thiết kế để:

- ✅ **Tách biệt các model** hoạt động độc lập
- ✅ **Auto-detect** models có sẵn trên máy
- ✅ **Auto-download** models thiếu
- ✅ **Hỗ trợ production** deployment
- ✅ **Quản lý qua API** và CLI
- ✅ **Validation** và health check

## 🏗️ Kiến trúc

```
ModelManager
├── Model Detection
│   ├── Ollama Models
│   ├── Vosk Models  
│   ├── Local Models
│   └── GitHub Models
├── Model Download
│   ├── Concurrent Downloads
│   ├── Progress Tracking
│   └── Error Handling
├── Model Validation
│   ├── Health Checks
│   ├── Performance Tests
│   └── Integrity Verification
└── Model Management
    ├── Status Monitoring
    ├── Cleanup Operations
    └── Configuration Management
```

## 🚀 Quick Start

### 1. Kiểm tra status models
```bash
# Via API
curl http://localhost:8000/models/status

# Via CLI
python backend/scripts/model_cli.py status
```

### 2. Download required models
```bash
# Auto download required models
curl -X POST http://localhost:8000/models/ensure

# Download specific model
curl -X POST http://localhost:8000/models/download/ollama:gemma2:9b

# Via CLI
python backend/scripts/model_cli.py download
python backend/scripts/model_cli.py download --models ollama:gemma2:9b vosk:vi
```

### 3. Validate models
```bash
# Via API
curl -X POST http://localhost:8000/models/validate

# Via CLI
python backend/scripts/model_cli.py validate
```

## 📊 API Endpoints

### Model Status
```http
GET /models/status
```
Trả về status của tất cả models:
```json
{
  "success": true,
  "data": {
    "total_models": 5,
    "available_models": 4,
    "required_models": 2,
    "missing_required": 0,
    "models_by_type": {
      "ollama": [...],
      "vosk": [...],
      "github": [...]
    },
    "model_details": {...}
  }
}
```

### Detect Models
```http
GET /models/detect
```
Detect tất cả models có sẵn trên hệ thống.

### Download Models
```http
POST /models/ensure
```
Download tất cả required models (background task).

```http
POST /models/download/{model_key}
```
Download một model cụ thể.

### Validate Models
```http
POST /models/validate
```
Validate tất cả models và trả về kết quả.

### Cleanup Models
```http
POST /models/cleanup?keep_recent=3
```
Dọn dẹp models cũ, giữ lại `keep_recent` models mới nhất.

### Configure Models
```http
POST /models/configure
Content-Type: application/json

{
  "OLLAMA_MODEL": "gemma2:9b",
  "PREFERRED_AI_PROVIDER": "ollama",
  "AUTO_DOWNLOAD_MODELS": true
}
```

### Health Check
```http
GET /models/health
```
Health check cho model management system.

## 🛠️ CLI Commands

### Status
```bash
python backend/scripts/model_cli.py status
```

### Detect
```bash
python backend/scripts/model_cli.py detect
```

### Download
```bash
# Download required models
python backend/scripts/model_cli.py download

# Download specific models
python backend/scripts/model_cli.py download --models ollama:gemma2:9b vosk:vi
```

### Validate
```bash
python backend/scripts/model_cli.py validate
```

### Cleanup
```bash
# Cleanup with default (keep 3 recent)
python backend/scripts/model_cli.py cleanup

# Cleanup keeping 5 recent models
python backend/scripts/model_cli.py cleanup --keep 5
```

### Recommended Models
```bash
python backend/scripts/model_cli.py recommended
```

### Configuration
```bash
python backend/scripts/model_cli.py configure
```

## 📦 Supported Models

### Ollama Models
| Model | Size | Description | Recommended For |
|-------|------|-------------|-----------------|
| `gemma2:9b` | 5GB | Model mặc định, cân bằng | General purpose, Vietnamese |
| `llama3.1:8b` | 4.5GB | Model phổ biến, nhanh | Fast responses, English |
| `qwen2.5:7b` | 4GB | Tốt cho tiếng Việt | Vietnamese, multilingual |
| `gemma2:2b` | 1.5GB | Model nhẹ | Low resource servers |

### Vosk Models
| Model | Size | Description | Required |
|-------|------|-------------|----------|
| `vosk-vi` | 78MB | Vietnamese speech recognition | ✅ Yes |
| `vosk-en` | 40MB | English speech recognition | ❌ No |

### GitHub Models
| Model | Size | Description | Required |
|-------|------|-------------|----------|
| `openai/gpt-4o-mini` | Unknown | GitHub AI model | ✅ Yes (if API key) |

## ⚙️ Configuration

### Environment Variables
```bash
# Model Management
AUTO_SETUP_ENABLED=true
DOWNLOAD_MODELS_ON_START=true
MAX_CONCURRENT_DOWNLOADS=2
MODEL_DOWNLOAD_TIMEOUT=1800

# AI Configuration
PREFERRED_AI_PROVIDER=ollama
OLLAMA_MODEL=gemma2:9b
OLLAMA_BASE_URL=http://localhost:11434

# Vosk Configuration
VOSK_MODEL_PATH=/app/data/models/vosk-vi
```

### Config.json
```json
{
  "OLLAMA_BASE_URL": "http://localhost:11434",
  "OLLAMA_MODEL": "gemma2:9b",
  "VOSK_MODEL_PATH": "/app/data/models/vosk-vi",
  "PREFERRED_AI_PROVIDER": "ollama",
  "AUTO_DOWNLOAD_MODELS": true,
  "MODEL_DOWNLOAD_TIMEOUT": 1800,
  "MAX_CONCURRENT_DOWNLOADS": 2
}
```

## 🚀 Production Deployment

### 1. Pre-deployment Setup
```bash
# Check prerequisites
./scripts/deploy_production.sh

# Setup production environment
docker-compose -f docker-compose.prod.yml up -d
```

### 2. Model Management in Production
```bash
# Check model status
curl https://your-domain.com/models/status

# Ensure required models
curl -X POST https://your-domain.com/models/ensure

# Monitor model health
curl https://your-domain.com/models/health
```

### 3. Monitoring
```bash
# Use monitoring script
./monitor.sh

# Check logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### 4. Backup
```bash
# Manual backup
./backup.sh

# Automatic backup (daily at 2 AM)
# Configured via cron job
```

## 🔧 Troubleshooting

### Models Not Downloading
```bash
# Check disk space
df -h

# Check network connectivity
ping registry.ollama.ai

# Check Ollama server
curl http://localhost:11434/api/tags

# Check logs
docker-compose logs backend | grep -i model
```

### Model Validation Failed
```bash
# Check model integrity
python backend/scripts/model_cli.py validate

# Re-download corrupted models
python backend/scripts/model_cli.py download --models ollama:gemma2:9b

# Check Ollama server status
curl http://localhost:11434/api/tags
```

### Performance Issues
```bash
# Check resource usage
docker stats

# Cleanup old models
python backend/scripts/model_cli.py cleanup --keep 2

# Monitor model performance
curl http://localhost:8000/models/status
```

## 📈 Monitoring & Metrics

### Health Checks
- Model availability status
- Download progress tracking
- Validation results
- Performance metrics

### Logs
```bash
# Model management logs
docker-compose logs backend | grep -i model

# Download progress
docker-compose logs backend | grep -i download

# Validation results
docker-compose logs backend | grep -i validate
```

### Metrics
- Total models count
- Available models count
- Missing required models
- Download success rate
- Validation success rate

## 🔒 Security Considerations

### Model Security
- Models downloaded from trusted sources only
- Checksum verification (planned)
- Model integrity validation
- Secure storage in Docker volumes

### API Security
- Rate limiting on download endpoints
- Authentication for configuration changes
- Input validation for model keys
- Error handling without sensitive data exposure

### Network Security
- HTTPS for production deployments
- Firewall rules for model downloads
- Proxy configuration support
- Network isolation for model containers

## 🚀 Future Enhancements

### Planned Features
- [ ] Model versioning and rollback
- [ ] Model performance benchmarking
- [ ] Automatic model updates
- [ ] Model sharing between instances
- [ ] Advanced caching strategies
- [ ] Model compression and optimization

### Integration Ideas
- [ ] Kubernetes operator for model management
- [ ] Prometheus metrics integration
- [ ] Grafana dashboards
- [ ] CI/CD pipeline integration
- [ ] Multi-cloud model distribution

## 📚 References

- [Ollama Documentation](https://ollama.ai/docs)
- [Vosk Documentation](https://alphacephei.com/vosk/)
- [GitHub AI Models](https://models.github.ai/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**Note**: Hệ thống Model Management được thiết kế để hoạt động độc lập và có thể mở rộng. Tất cả models được quản lý tự động và có thể được monitor qua API hoặc CLI tools.


