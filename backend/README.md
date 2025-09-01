# ChatBot Backend

Hệ thống backend cho ChatBot AI với khả năng chat text và voice.

## 🚀 Tính năng

- **AI Chat**: Hỗ trợ nhiều provider AI (Ollama, GitHub Copilot)
- **Voice Processing**: Nhận diện giọng nói và chuyển đổi text-to-speech
- **Database**: Lưu trữ lịch sử chat và conversation
- **RESTful API**: API đầy đủ cho frontend
- **Auto-setup**: Tự động cài đặt và cấu hình models

## 🏗️ Kiến trúc

```
backend/
├── api/                # API endpoints
├── config/             # Database và settings
├── services/           # Business logic
├── utils/              # Helper functions
├── data/               # SQLite database
└── main.py            # FastAPI application
```

## 📋 Requirements

- Python 3.9+
- FastAPI
- SQLite
- Ollama (for local AI)
- Vosk (for voice recognition)

## 🛠️ Installation

### 1. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 2. Cấu hình
```bash
cp config.json.example config.json
cp env.example .env
```

### 3. Khởi động
```bash
python main.py
```

## 🔧 Configuration

### config.json
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

### Environment Variables
```bash
# AI Configuration
PREFERRED_AI_PROVIDER=ollama
OLLAMA_MODEL=gemma2:2b
AUTO_FALLBACK=true

# Voice Configuration  
VOSK_MODEL_PATH=/app/data/models/vosk-vi
VOSK_LANGUAGE=vi

# Database
DATABASE_PATH=/app/data/chatbot.db
```

## 📡 API Endpoints

### Health & Status
- `GET /api/health` - System health check
- `GET /api/ai/status` - AI service status
- `GET /api/voice/capabilities` - Voice service status

### Chat
- `POST /chat/message` - Send message to AI
- `GET /chat/history` - Get chat history
- `POST /api/conversations` - Create new conversation
- `PUT /api/conversations/{id}/title` - Update conversation title
- `DELETE /api/conversations/{id}` - Delete conversation

### Voice
- `POST /voice/transcribe` - Audio to text
- `GET /api/voice/capabilities` - Voice capabilities

### Models
- `GET /models/status` - Available models status

## 🤖 AI Services

### Ollama Integration
- Gemma2 2B: Lightweight Vietnamese model
- Gemma3N E4B: Advanced model (requires more memory)
- Auto-fallback between models

### Enhanced AI Service
- Context-aware responses
- Vietnamese language optimized
- Weather and news integration
- Personal information service

## 🎤 Voice Services

### Speech Recognition
- Vosk offline recognition
- Google Speech API fallback
- Vietnamese language support

### Text-to-Speech
- pyttsx3 engine
- Vietnamese voice support
- Adjustable speed and pitch

## 🗄️ Database Schema

### Conversations
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Messages
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER,
    sender TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ai_provider TEXT,
    ai_model TEXT,
    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
);
```

## 🐛 Troubleshooting

### Common Issues

1. **Ollama model failed to load**
   ```bash
   # Check memory usage
   docker stats
   # Reduce model size in docker-compose.yml
   OLLAMA_MODEL=gemma2:2b
   ```

2. **Voice service not available**
   ```bash
   # Install voice dependencies
   pip install SpeechRecognition pyttsx3 pydub vosk
   ```

3. **Database locked error**
   ```bash
   # Remove database lock
   rm /app/data/chatbot.db-wal
   rm /app/data/chatbot.db-shm
   ```

### Logs
```bash
# View application logs
docker-compose logs backend

# Check specific service logs
tail -f /app/logs/chatbot.log
```

## 🔄 Development

### Run in development mode
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Health check
curl http://localhost:8000/api/health

# Test chat
curl -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Xin chào!"}'
```

## 📈 Performance

### Resource Usage
- **Memory**: 2-8GB (depending on AI model)
- **CPU**: 1-4 cores
- **Storage**: ~10GB for models + database

### Optimization Tips
1. Use smaller AI models for faster response
2. Enable model caching for repeated requests  
3. Limit conversation history length
4. Use connection pooling for database

## 🔒 Security

- No API keys exposed in code
- Database stored locally
- CORS configured for frontend only
- Input validation on all endpoints

## 📚 Dependencies

### Core
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sqlite3` - Database
- `langchain` - AI framework

### AI
- `ollama` - Local AI models
- `requests` - HTTP client

### Voice
- `SpeechRecognition` - Speech to text
- `pyttsx3` - Text to speech
- `pydub` - Audio processing
- `vosk` - Offline speech recognition

### Utilities
- `python-multipart` - File uploads
- `python-dotenv` - Environment variables
- `Pillow` - Image processing
