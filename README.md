# 🤖 Bixby ChatBot

Hệ thống ChatBot AI thông minh với khả năng chat text và voice, hỗ trợ tiếng Việt.

## ✨ Tính năng chính

- 🤖 **AI Chat**: Ollama (Gemma2, Gemma3N) với fallback thông minh
- 🎤 **Voice Chat**: Nhận diện giọng nói và chuyển đổi text-to-speech
- 💬 **Conversation Management**: Quản lý lịch sử chat với database
- 🌐 **Modern Web UI**: Dark theme, responsive design
- 🐳 **Docker Deployment**: One-click deployment với auto-setup
- 🔄 **Auto Fallback**: Tự động chuyển đổi giữa các AI provider

## 🚀 Quick Start

### Cách 1: Docker (Khuyến nghị)

```bash
# Clone repository
git clone <repository-url>
cd ChatBot

# Start với Docker Compose
docker-compose up -d

# Truy cập ứng dụng
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Cách 2: Development

```bash
# Backend
cd backend
pip install -r requirements.txt
python main.py

# Frontend (terminal mới)
cd frontend
npm install
npm start
```

## 🏗️ Kiến trúc hệ thống

```
ChatBot/
├── backend/               # FastAPI Python backend
│   ├── api/              # REST API endpoints
│   ├── services/         # AI, Voice, Database services
│   ├── config/           # Configuration & database
│   └── data/             # SQLite DB & models
├── frontend/             # React TypeScript frontend
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── hooks/        # Custom React hooks
│   │   └── utils/        # Helper functions
└── scripts/              # Deployment & utility scripts
```

## 🔧 Configuration

### Docker Compose (docker-compose.yml)

Hệ thống tự động cấu hình với các environment variables:

```yaml
environment:
  # AI Configuration
  - PREFERRED_AI_PROVIDER=ollama
  - OLLAMA_MODEL=gemma2:2b
  - OLLAMA_FALLBACK_MODEL=gemma3n:e4b
  
  # Voice Configuration
  - VOSK_MODEL_PATH=/app/data/models/vosk-vi
  - VOSK_LANGUAGE=vi
  
  # Auto Setup
  - AUTO_SETUP_ENABLED=true
  - DOWNLOAD_MODELS_ON_START=true
```

### Manual Configuration

#### Backend (backend/config.json)
```json
{
  "ai": {
    "preferred_provider": "ollama",
    "ollama_model": "gemma2:2b",
    "fallback_enabled": true
  },
  "voice": {
    "vosk_model_path": "/app/data/models/vosk-vi",
    "language": "vi-VN"
  }
}
```

#### Frontend (.env)
```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

## 📡 API Endpoints

### System Health
- `GET /api/health` - System health check
- `GET /models/status` - AI models status
- `GET /api/voice/capabilities` - Voice service status

### Chat Features
- `POST /chat/message` - Send message to AI
- `GET /chat/history` - Get conversation history
- `POST /voice/transcribe` - Audio to text transcription

### Conversation Management
- `POST /api/conversations` - Create conversation
- `PUT /api/conversations/{id}/title` - Update title
- `DELETE /api/conversations/{id}` - Delete conversation

## 🤖 AI Models

### Ollama Models (Default)
- **Gemma2 2B**: Fast, lightweight, good for basic chat
- **Gemma3N E4B**: Advanced model, better understanding

### Auto-Setup Features
- Tự động download và cài đặt Ollama
- Download AI models automatically
- Setup Vosk Vietnamese model
- Database initialization

## 🎤 Voice Features

### Speech Recognition
- **Vosk**: Offline Vietnamese recognition
- **Google Speech API**: Online fallback
- **Browser SpeechRecognition**: Web API fallback

### Text-to-Speech
- **pyttsx3**: Server-side TTS
- **Browser speechSynthesis**: Client-side TTS
- Vietnamese voice support

### Voice Settings
- Language selection (vi-VN, en-US, ja-JP, ko-KR)
- Speech speed control
- Auto-speak responses
- Voice-to-voice conversation

## 🗄️ Database

### SQLite Database
- **conversations**: Chat sessions
- **messages**: Individual messages với metadata
- **Auto-backup**: Persistent volumes

### Database Schema
```sql
-- Conversations
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Messages
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER REFERENCES conversations(id),
    sender TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ai_provider TEXT,
    ai_model TEXT
);
```

## 🎨 Frontend Features

### Modern UI/UX
- **Dark Theme**: Easy on the eyes
- **Responsive Design**: Mobile, tablet, desktop
- **Real-time Chat**: Instant AI responses
- **Voice Controls**: One-click recording

### Advanced Features
- **Provider Selection**: Choose AI model
- **Health Monitoring**: System status indicators
- **Voice Diagnostics**: Audio quality checking
- **Conversation Management**: Edit titles, delete chats

## 🐳 Docker Deployment

### Production Deployment

```bash
# Production build
docker-compose -f docker-compose.prod.yml up -d

# Scaling
docker-compose up -d --scale backend=2

# Monitoring
docker-compose logs -f backend
docker stats
```

### Resource Requirements
- **Memory**: 3-8GB (depending on AI model)
- **CPU**: 2-4 cores recommended
- **Storage**: 10GB+ for models and database
- **Network**: Internet for model downloads

### Health Checks
```bash
# System health
curl http://localhost:8000/api/health

# Models status  
curl http://localhost:8000/models/status

# Voice capabilities
curl http://localhost:8000/api/voice/capabilities
```

## 🔄 Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm start
# Runs on http://localhost:3000
```

### Testing
```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test

# System integration test
./scripts/test_system.sh
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Backend không khởi động
```bash
# Check logs
docker-compose logs backend

# Common fixes
docker-compose restart backend
docker system prune  # Clear cache
```

#### 2. AI Model lỗi memory
```bash
# Use smaller model
# In docker-compose.yml:
OLLAMA_MODEL=gemma2:2b  # Instead of gemma3n:e4b

# Increase memory limit
deploy:
  resources:
    limits:
      memory: 8G
```

#### 3. Voice không hoạt động
```bash
# Check browser permissions (microphone)
# Verify HTTPS connection (required for getUserMedia)
# Check voice service status:
curl http://localhost:8000/api/voice/capabilities
```

#### 4. Database locked
```bash
# Stop containers
docker-compose down

# Remove database locks
sudo rm -f ./backend/data/chatbot.db-wal
sudo rm -f ./backend/data/chatbot.db-shm

# Restart
docker-compose up -d
```

### Debug Mode

#### Enable debug logging
```bash
# Backend
export LOG_LEVEL=DEBUG

# Frontend
localStorage.setItem('debug', 'true');
```

#### Health checks
```bash
# Test script
./scripts/test_system.sh

# Manual checks
curl http://localhost:8000/api/health
curl http://localhost:3000  # Should show React app
```

## 📈 Performance Tips

### Resource Optimization
1. **Use appropriate AI model**: gemma2:2b cho basic chat, gemma3n:e4b cho advanced
2. **Limit conversation history**: Set max messages per conversation
3. **Enable model caching**: Faster subsequent responses
4. **Use SSD storage**: Better I/O for database operations

### Scaling Options
```bash
# Horizontal scaling
docker-compose up -d --scale backend=2

# Load balancer (nginx)
# Add nginx container to docker-compose.yml
```

## 🔒 Security

### Data Protection
- SQLite database với file permissions
- No API keys trong code
- Input validation on all endpoints
- CORS configured cho frontend only

### Privacy
- Voice data processed locally khi có thể
- No permanent audio storage
- Conversation data stays on your server

## 📚 Documentation

### Detailed Documentation
- [Backend README](./backend/README.md) - API, services, configuration
- [Frontend README](./frontend/README.md) - UI components, state management
- [Docker Documentation](./docker-compose.yml) - Deployment configuration

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contributing

### Development Setup
1. Fork repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

### Code Style
- **Backend**: Black formatting, type hints
- **Frontend**: Prettier, TypeScript strict mode
- **Commits**: Conventional commits format

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Ollama**: Local AI model serving
- **Vosk**: Offline speech recognition
- **React**: Modern frontend framework
- **FastAPI**: High-performance Python API framework
- **Docker**: Containerization platform

---

## 🆘 Support

Nếu bạn gặp vấn đề:

1. **Check logs**: `docker-compose logs backend`
2. **Run health check**: `curl http://localhost:8000/api/health`
3. **Restart services**: `docker-compose restart`
4. **Clear cache**: `docker system prune -a`

**System Requirements**: 4GB+ RAM, 10GB+ storage, modern browser with microphone support.