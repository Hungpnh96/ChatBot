# ChatBot Frontend

Modern React-based web interface cho ChatBot AI với dark theme và voice support.

## 🚀 Tính năng

- **Modern UI**: Dark theme với responsive design
- **Real-time Chat**: Chat trực tiếp với AI
- **Voice Chat**: Ghi âm và phát audio
- **Conversation Management**: Quản lý lịch sử chat
- **Multi-Provider**: Chọn AI provider (Ollama, GitHub)
- **Health Monitoring**: Hiển thị trạng thái hệ thống

## 🏗️ Kiến trúc

```
frontend/
├── public/             # Static files
├── src/
│   ├── components/     # React components
│   ├── hooks/          # Custom hooks
│   ├── utils/          # Helper functions
│   ├── api.ts          # API client
│   ├── App.tsx         # Main app component
│   └── ChatUI.tsx      # Main chat interface
└── package.json        # Dependencies
```

## 📋 Requirements

- Node.js 18+
- React 18+
- TypeScript
- Modern browser với Web APIs

## 🛠️ Installation

### 1. Install dependencies
```bash
npm install
```

### 2. Environment setup
```bash
# .env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

### 3. Development
```bash
npm start
```

### 4. Build for production
```bash
npm run build
```

## 🔧 Configuration

### Environment Variables
```bash
# API Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000

# Feature Flags
REACT_APP_ENABLE_VOICE=true
REACT_APP_ENABLE_NOTIFICATIONS=true
```

## 🎨 UI Components

### Main Components

#### ChatUI
- Main chat interface
- Message history
- Input handling
- Voice controls

#### Sidebar
- Conversation list
- New conversation button
- Settings panel

#### Message Components
- User/AI message bubbles
- Voice message indicators
- Provider/model info
- Timestamps

### Responsive Design
- **Desktop**: Full sidebar + chat area
- **Tablet**: Collapsible sidebar
- **Mobile**: Overlay sidebar, touch optimized

## 🎤 Voice Features

### Browser Voice Support Detection
```typescript
interface BrowserVoiceSupport {
  speechRecognition: boolean;
  speechSynthesis: boolean;
  webRTC: boolean;
  mediaRecorder: boolean;
  fullSupport: boolean;
}
```

### Audio Recording
- WebRTC MediaRecorder API
- Audio format conversion
- Real-time audio visualization
- Error handling và fallbacks

### Voice Settings
- Language selection (vi-VN, en-US, etc.)
- Speech speed control
- Auto-speak responses
- Server vs browser voice processing

## 📡 API Integration

### Core API Functions

#### Chat Operations
```typescript
sendMessage(conversationId, message, provider)
fetchConversations()
fetchMessages(conversationId)
createConversation(title)
updateConversationTitle(id, title)
deleteConversation(id)
```

#### Voice Operations
```typescript
transcribeAudio(audioBlob, language)
textToSpeech(text, language, voice, speed)
voiceChat(audioBlob, conversationId, provider)
getVoiceCapabilities()
```

#### System Status
```typescript
healthCheck()
getProviderInfo()
voiceHealthCheck()
```

### Error Handling
- Automatic retry logic
- Fallback responses
- User-friendly error messages
- Network connectivity detection

## 🔍 State Management

### React State Structure
```typescript
// Chat State
const [conversations, setConversations] = useState<Conversation[]>([]);
const [currentConv, setCurrentConv] = useState<Conversation | null>(null);
const [messages, setMessages] = useState<Message[]>([]);
const [loading, setLoading] = useState(false);

// System State
const [providerInfo, setProviderInfo] = useState<ProviderInfo | null>(null);
const [healthStatus, setHealthStatus] = useState<HealthCheckResponse | null>(null);
const [voiceCapabilities, setVoiceCapabilities] = useState<VoiceCapabilities | null>(null);

// Voice State
const [isRecording, setIsRecording] = useState(false);
const [isTranscribing, setIsTranscribing] = useState(false);
const [voiceSettings, setVoiceSettings] = useState({...});
```

## 🎯 User Experience

### Chat Experience
- **Auto-scroll**: Messages tự động scroll xuống
- **Typing indicators**: Hiển thị khi AI đang xử lý
- **Message status**: Success/error indicators
- **Provider info**: Hiển thị AI model đang sử dụng

### Voice Experience
- **Visual feedback**: Recording indicator
- **Audio diagnostics**: Kiểm tra chất lượng audio
- **Fallback options**: Text input khi voice không khả dụng
- **Settings panel**: Cấu hình voice chi tiết

### Responsive Behavior
- **Mobile-first**: Touch-friendly interface
- **Adaptive layout**: Sidebar behavior thay đổi theo screen size
- **Gesture support**: Swipe to open/close sidebar

## 🔧 Development

### Available Scripts
```bash
npm start          # Development server
npm run build      # Production build
npm test           # Run tests
npm run eject      # Eject CRA (irreversible)
```

### Code Structure
```typescript
// Component structure
const Component: React.FC = () => {
  // State declarations
  // Effect hooks
  // Event handlers
  // Helper functions
  // Render methods
  return JSX;
};
```

### TypeScript Types
```typescript
interface Message {
  sender: string;
  content: string;
  timestamp: string;
  ai_provider?: string;
  ai_model?: string;
}

interface Conversation {
  id: number;
  title: string;
  started_at: string;
  message_count: number;
}
```

## 🐛 Troubleshooting

### Common Issues

1. **API Connection Failed**
   ```typescript
   // Check REACT_APP_API_URL in .env
   // Verify backend is running on port 8000
   ```

2. **Voice Recording Not Working**
   ```typescript
   // Check browser permissions for microphone
   // Verify HTTPS connection (required for getUserMedia)
   // Check browser compatibility
   ```

3. **Sidebar Not Responsive**
   ```typescript
   // Check CSS media queries
   // Verify window resize listeners
   ```

### Debug Tools
```typescript
// Enable debug mode
localStorage.setItem('debug', 'true');

// Check voice support
import { debugVoiceSupport } from './api';
debugVoiceSupport();

// API call logging
console.log('API call:', method, url, data);
```

## 📱 Browser Support

### Minimum Requirements
- Chrome 60+
- Firefox 55+
- Safari 11+
- Edge 79+

### Voice Feature Requirements
- **MediaRecorder API**: Chrome 47+, Firefox 25+
- **getUserMedia**: Chrome 53+, Firefox 36+
- **SpeechRecognition**: Chrome 25+, Safari 14.1+

### Feature Fallbacks
- Voice → Text input
- Audio playback → Visual feedback only
- Advanced UI → Basic responsive layout

## 🔒 Security

### Data Protection
- No sensitive data stored in localStorage
- API calls use secure headers
- Input sanitization for chat messages
- CORS validation

### Privacy
- Voice data processed locally when possible
- No permanent audio storage
- Conversation data stays on user's server

## 📈 Performance

### Optimization
- **Code splitting**: React.lazy cho components lớn
- **Memoization**: React.memo cho expensive renders
- **Debouncing**: Input handlers và API calls
- **Asset optimization**: Images và audio compression

### Bundle Size
- Main bundle: ~500KB gzipped
- Voice features: ~200KB additional
- Total runtime: ~700KB

### Loading Performance
- Initial load: <2s
- Time to interactive: <3s
- Voice initialization: <1s

## 🚀 Deployment

### Production Build
```bash
npm run build
# Creates optimized build in /build directory
```

### Docker Deployment
```dockerfile
FROM nginx:alpine
COPY build/ /usr/share/nginx/html
EXPOSE 80
```

### Environment-specific Builds
```bash
# Development
npm start

# Staging
REACT_APP_API_URL=https://staging-api.example.com npm run build

# Production  
REACT_APP_API_URL=https://api.example.com npm run build
```

## 📚 Dependencies

### Core React
- `react` - UI library
- `react-dom` - DOM rendering
- `typescript` - Type safety

### Build Tools
- `react-scripts` - CRA build tools
- `web-vitals` - Performance monitoring

### No External UI Libraries
- Pure CSS styling
- Custom components
- Minimal dependencies for faster load times
