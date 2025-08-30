# 🎤 Bixby Voice Chat Setup Guide

Complete installation guide for adding voice chat capabilities to your Bixby chatbot.

## 📋 Prerequisites

### System Requirements
- Python 3.8+
- Node.js 16+
- Modern browser with WebRTC support
- Microphone and speakers/headphones

### Operating System Specific Dependencies

#### Ubuntu/Debian
```bash
# Audio system dependencies
sudo apt-get update
sudo apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    ffmpeg \
    espeak espeak-data libespeak1 libespeak-dev \
    festival* \
    pulseaudio pulseaudio-utils

# Optional: ALSA utilities
sudo apt-get install -y alsa-utils
```

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install portaudio ffmpeg espeak

# Install Python dependencies
pip3 install pyaudio
```

#### Windows
```bash
# Install Visual Studio Build Tools (required for some packages)
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Install FFmpeg
# Download from: https://ffmpeg.org/download.html
# Add to PATH environment variable

# PyAudio wheel should install directly via pip
pip install pyaudio
```

## 🔧 Backend Setup

### 1. Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt

# If you encounter PyAudio installation issues:
# Ubuntu/Debian:
sudo apt-get install python3-pyaudio
# or
pip install --upgrade pyaudio

# macOS:
brew install portaudio
pip install pyaudio

# Windows:
pip install pipwin
pipwin install pyaudio
```

### 2. Test Voice Dependencies
```bash
# Test speech recognition
python3 -c "import speech_recognition as sr; print('Speech Recognition OK')"

# Test text-to-speech
python3 -c "import pyttsx3; print('TTS OK')"

# Test audio processing
python3 -c "import pydub; print('Audio Processing OK')"
```

### 3. Configure Voice Settings
Edit `backend/config.json`:
```json
{
  "VOICE_CONFIG": {
    "TTS_ENGINE": "pyttsx3",
    "TTS_RATE": 150,
    "TTS_VOLUME": 0.9,
    "SR_LANGUAGE": "vi-VN",
    "SR_TIMEOUT": 30,
    "AUDIO_FORMAT": "wav",
    "MAX_AUDIO_SIZE_MB": 10
  }
}
```

### 4. Update Main Application
Replace your `main.py` with the complete version that includes voice router:
```python
# The voice router is now included in main.py
from api.voice import router as voice_router
app.include_router(voice_router)
```

### 5. Test Backend Voice Services
```bash
# Start the backend
cd backend
python main.py

# Test voice endpoints (in another terminal)
curl http://localhost:8000/chat/api/voice/health
curl http://localhost:8000/chat/api/voice/capabilities
curl -X POST http://localhost:8000/chat/api/voice/test
```

## 🎨 Frontend Setup

### 1. Install Frontend Dependencies
```bash
cd frontend
npm install

# No additional packages needed - uses browser APIs
```

### 2. Add Voice Components
Copy the complete files:
- `hooks/useVoiceChat.ts`
- `components/VoiceChatButton.tsx`
- `api.ts` (updated with voice functions)
- `ChatUI.tsx` (enhanced with voice)

### 3. Update Environment Variables
Create/update `frontend/.env`:
```env
REACT_APP_API_BASE_URL=http://localhost:8000/chat
REACT_APP_VOICE_ENABLED=true
REACT_APP_DEFAULT_LANGUAGE=vi-VN
```

### 4. Test Frontend Voice Features
```bash
# Start frontend development server
npm start

# Open browser and test:
# 1. Voice mode toggle
# 2. Microphone permission
# 3. Speech recognition
# 4. Text-to-speech
```

## 🚀 Docker Setup (Optional)

### 1. Backend Dockerfile
Update `backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

# Install system dependencies for voice
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    ffmpeg \
    espeak espeak-data libespeak1 libespeak-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000
CMD ["python", "main.py"]
```

### 2. Docker Compose
Update `docker-compose.yml`:
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./data:/app/data
    devices:
      - /dev/snd:/dev/snd  # Audio device access
    environment:
      - PULSE_RUNTIME_PATH=/run/user/1000/pulse
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
    environment:
      - REACT_APP_API_BASE_URL=http://localhost:8000/chat
```

## 🔧 Configuration Options

### Voice Recognition Settings
```python
# backend/services/voice_service.py
class VoiceService:
    def _configure_recognizer(self):
        self.recognizer.energy_threshold = 300        # Microphone sensitivity
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8         # Pause detection
        self.recognizer.phrase_threshold = 0.3        # Phrase detection
        self.recognizer.non_speaking_duration = 0.8   # Silence duration
```

### Text-to-Speech Settings
```python
# Customize TTS voice settings
def _initialize_tts(self):
    self.tts_engine.setProperty('rate', 150)    # Speaking speed
    self.tts_engine.setProperty('volume', 0.9)  # Volume level
    
    # Find Vietnamese voice
    voices = self.tts_engine.getProperty('voices')
    for voice in voices:
        if 'vietnamese' in voice.name.lower():
            self.tts_engine.setProperty('voice', voice.id)
```

### Frontend Voice Settings
```typescript
// hooks/useVoiceChat.ts
const voiceConfig = {
  language: 'vi-VN',           // Speech recognition language
  continuous: false,           // Continuous listening
  interimResults: true,        // Show interim results
  maxDuration: 30,            // Max recording duration (seconds)
  autoStop: true              // Auto-stop on silence
};
```

## 🎯 Testing Voice Features

### 1. Browser Compatibility Test
```javascript
// Test in browser console
const support = {
  webRTC: navigator.mediaDevices && navigator.mediaDevices.getUserMedia,
  speechRecognition: 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window,
  speechSynthesis: 'speechSynthesis' in window,
  mediaRecorder: 'MediaRecorder' in window
};
console.log('Voice Support:', support);
```

### 2. Microphone Permission Test
```javascript
// Test microphone access
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => {
    console.log('✅ Microphone access granted');
    stream.getTracks().forEach(track => track.stop());
  })
  .catch(err => console.error('❌ Microphone access denied:', err));
```

### 3. Speech Recognition Test
```javascript
// Test speech recognition
if ('webkitSpeechRecognition' in window) {
  const recognition = new webkitSpeechRecognition();
  recognition.lang = 'vi-VN';
  recognition.onresult = (event) => {
    console.log('Transcript:', event.results[0][0].transcript);
  };
  recognition.start();
} else {
  console.log('Speech recognition not supported');
}
```

### 4. Text-to-Speech Test
```javascript
// Test speech synthesis
if ('speechSynthesis' in window) {
  const utterance = new SpeechSynthesisUtterance('Xin chào! Tôi là Bixby.');
  utterance.lang = 'vi-VN';
  speechSynthesis.speak(utterance);
} else {
  console.log('Speech synthesis not supported');
}
```

## 🐛 Troubleshooting

### Common Issues & Solutions

#### 1. PyAudio Installation Fails
```bash
# Error: Microsoft Visual C++ 14.0 is required (Windows)
# Solution: Install Visual Studio Build Tools
# Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Error: portaudio.h not found (Linux)
sudo apt-get install portaudio19-dev

# Error: portaudio not found (macOS)
brew install portaudio
```

#### 2. Speech Recognition Not Working
```python
# Check microphone access
import speech_recognition as sr
r = sr.Recognizer()
with sr.Microphone() as source:
    print("Say something!")
    audio = r.listen(source, timeout=5)
    try:
        text = r.recognize_google(audio, language='vi-VN')
        print(f"You said: {text}")
    except sr.UnknownValueError:
        print("Could not understand audio")
    except sr.RequestError as e:
        print(f"Error: {e}")
```

#### 3. TTS Not Working
```python
# Test TTS engine
import pyttsx3
engine = pyttsx3.init()
voices = engine.getProperty('voices')
for voice in voices:
    print(f"Voice: {voice.name} - {voice.id}")
    
engine.say("Testing text to speech")
engine.runAndWait()
```

#### 4. Browser Microphone Permission
```javascript
// Check permission status
navigator.permissions.query({name: 'microphone'})
  .then(permission => {
    console.log('Microphone permission:', permission.state);
    // 'granted', 'denied', or 'prompt'
  });
```

#### 5. CORS Issues with Audio
```python
# backend/main.py - Add audio headers to CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Transcript", 
        "X-AI-Response", 
        "X-Conversation-ID",
        "Content-Disposition"
    ]
)
```

### Error Messages & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: pyaudio` | PyAudio not installed | Install system audio deps + pip install pyaudio |
| `Permission denied: microphone` | Browser blocking mic access | Allow microphone in browser settings |
| `Speech recognition timeout` | No speech detected | Check microphone, reduce background noise |
| `TTS engine failed` | No TTS voices available | Install espeak or festival |
| `Audio format not supported` | Unsupported audio codec | Use WAV or WebM format |

## 📊 Performance Optimization

### 1. Audio Processing
```python
# Optimize audio settings for speech recognition
audio_segment = (audio_segment
    .set_frame_rate(16000)    # Optimal for speech
    .set_channels(1)          # Mono audio
    .set_sample_width(2))     # 16-bit
```

### 2. Backend Optimization
```python
# Use thread pool for voice processing
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=2)

# Async processing
async def process_audio():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, sync_function)
```

### 3. Frontend Optimization
```typescript
// Debounce audio processing
const debouncedProcess = useCallback(
  debounce((audio: Blob) => processAudio(audio), 300),
  []
);

// Cleanup audio resources
useEffect(() => {
  return () => {
    // Cleanup audio streams
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
  };
}, []);
```

## 🔒 Security Considerations

### 1. Audio Data Privacy
```python
# Don't store audio files
# Process in memory only
with tempfile.NamedTemporaryFile(delete=True) as temp_file:
    # Process audio
    pass  # File automatically deleted
```

### 2. Rate Limiting
```python
# Add rate limiting for voice endpoints
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@router.post("/transcribe")
@limiter.limit("10/minute")
async def transcribe_audio():
    pass
```

### 3. Input Validation
```python
# Validate audio file size and format
MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_TYPES = ['audio/wav', 'audio/mp3', 'audio/webm']

if audio.size > MAX_AUDIO_SIZE:
    raise HTTPException(400, "Audio file too large")
```

## 📱 Mobile Considerations

### iOS Safari
```javascript
// Handle iOS audio restrictions
const iosAudioFix = () => {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  audioContext.resume();
};

// Call on user interaction
button.addEventListener('click', iosAudioFix);
```

### Android Chrome
```javascript
// Handle Android permissions
const requestMicPermission = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach(track => track.stop());
    return true;
  } catch (error) {
    return false;
  }
};
```

## 🚀 Production Deployment

### 1. Environment Variables
```bash
# Production .env
VOICE_ENABLED=true
TTS_CACHE_ENABLED=true
AUDIO_PROCESSING_TIMEOUT=30
MAX_CONCURRENT_VOICE_REQUESTS=5
```

### 2. Nginx Configuration
```nginx
# nginx.conf - Handle audio uploads
client_max_body_size 10M;

location /chat/api/voice/ {
    proxy_pass http://backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_read_timeout 60s;
}
```

### 3. SSL Certificate (Required for HTTPS)
```bash
# Voice features require HTTPS in production
# Get SSL certificate from Let's Encrypt
sudo certbot --nginx -d yourdomain.com
```

## 📋 Feature Checklist

### Backend ✅
- [ ] Voice service implementation
- [ ] Speech recognition (Google + offline)
- [ ] Text-to-speech (pyttsx3)
- [ ] Audio processing (pydub)
- [ ] Voice API endpoints
- [ ] Error handling
- [ ] Health checks
- [ ] Rate limiting

### Frontend ✅
- [ ] Voice chat hook
- [ ] Voice button component
- [ ] Audio recording
- [ ] Speech recognition integration
- [ ] TTS integration
- [ ] Voice settings panel
- [ ] Mobile compatibility
- [ ] Error handling

### Testing ✅
- [ ] Unit tests for voice service
- [ ] Integration tests for API
- [ ] Browser compatibility tests
- [ ] Mobile device tests
- [ ] Performance tests
- [ ] Security tests

## 🎉 Success Verification

After completing setup, you should be able to:

1. ✅ Click voice mode toggle
2. ✅ Grant microphone permission
3. ✅ Record voice messages
4. ✅ See real-time transcription
5. ✅ Hear AI responses spoken aloud
6. ✅ Switch between text and voice modes
7. ✅ Adjust voice settings
8. ✅ Use voice on mobile devices

## 📞 Support

If you encounter issues:

1. Check browser console for errors
2. Verify microphone permissions
3. Test individual components
4. Review system dependencies
5. Check network connectivity

**Need Help?** 
- Browser support: Test in Chrome/Edge first
- Audio issues: Check system audio settings
- Permission issues: Reset browser permissions
- Performance issues: Check system resources

Congratulations! 🎉 Your Bixby chatbot now supports full voice chat capabilities!