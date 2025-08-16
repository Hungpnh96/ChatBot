import React, { useEffect, useRef, useState } from 'react';
import {
  fetchConversations,
  fetchMessages,
  sendMessage,
  createConversation,
  updateConversationTitle,
  deleteConversation,
  getProviderInfo,
  healthCheck,
  voiceChat,
  getVoiceCapabilities,
  AudioRecorder,
  checkVoiceSupport,
  playAudioBlob,
  Conversation,
  Message,
  ChatResponse,
  ProviderInfo,
  HealthCheckResponse,
  VoiceCapabilities,
  BrowserVoiceSupport
} from './api.ts';
import { logAudioDiagnostics, validateAudioBeforeUpload, type AudioDiagnostics } from './utils/audio_diagnostics.ts';

interface MessageWithProvider extends Message {
  ai_provider?: string;
  ai_model?: string;
  voice_metadata?: {
    is_voice_message?: boolean;
    original_audio_duration?: number;
    transcription_confidence?: number;
  };
}

interface ChatResponseWithProvider extends ChatResponse {
  ai_provider?: string;
  ai_model?: string;
}

const ChatUI: React.FC = () => {
  // Conversations state
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConv, setCurrentConv] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<MessageWithProvider[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Input state
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  // Title edit state
  const [editingTitle, setEditingTitle] = useState<number | null>(null);
  const [newTitle, setNewTitle] = useState('');

  // Responsive + sidebar
  const [isMobile, setIsMobile] = useState(false);
  const [isTablet, setIsTablet] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Provider + health
  const [providerInfo, setProviderInfo] = useState<ProviderInfo | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<string>('auto');
  const [healthStatus, setHealthStatus] = useState<HealthCheckResponse | null>(null);
  const [isSystemHealthy, setIsSystemHealthy] = useState(false);

  // Voice support + recording
  const [voiceCapabilities, setVoiceCapabilities] = useState<VoiceCapabilities | null>(null);
  const [browserVoiceSupport, setBrowserVoiceSupport] = useState<BrowserVoiceSupport>({
    speechRecognition: false,
    speechSynthesis: false,
    webRTC: false,
    mediaRecorder: false,
    fullSupport: false
  });
  const [audioRecorder] = useState(new AudioRecorder());
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);

  // Settings panel
  const [showSettings, setShowSettings] = useState(false);
  const [voiceSettings, setVoiceSettings] = useState({
    autoSpeak: true,
    language: 'vi-VN',
    speed: 1.0,
    useServerVoice: true
  });

  // Diagnostics
  const [lastAudioDiagnostics, setLastAudioDiagnostics] = useState<AudioDiagnostics | null>(null);

  // Hover states for buttons
  const [plusHover, setPlusHover] = useState(false);
  const [voiceHover, setVoiceHover] = useState(false);
  const [sendHover, setSendHover] = useState(false);

  // Responsive detection
  useEffect(() => {
    const onResize = () => {
      const width = window.innerWidth;
      setIsMobile(width < 768);
      setIsTablet(width >= 768 && width < 1024);
      if (width >= 1024) setSidebarOpen(true);
    };
    onResize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  // Initialization
  useEffect(() => {
    const init = async () => {
      try {
        await loadConversations();
        const health = await healthCheck();
        setHealthStatus(health);
        setIsSystemHealthy((health as any)?.status === 'healthy');

        const provider = await getProviderInfo();
        setProviderInfo(provider);
        setSelectedProvider(provider.current_provider);

        try {
          const caps = await getVoiceCapabilities();
          setVoiceCapabilities(caps);
        } catch (e) {
          console.warn('Voice capabilities not available:', e);
        }

        const support = checkVoiceSupport();
        setBrowserVoiceSupport(support);
      } catch (e) {
        console.error('Initialization failed:', e);
      }
    };
    init();
  }, []);

  // Auto-scroll messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Data loaders
  const loadConversations = async () => {
    try {
      const convs = await fetchConversations();
      setConversations(convs);
    } catch (e) {
      console.error('Error loading conversations:', e);
    }
  };

  const loadMessages = async (conversationId: number) => {
    try {
      const msgs = await fetchMessages(conversationId);
      setMessages(msgs);
    } catch (e) {
      console.error('Error loading messages:', e);
      setMessages([]);
    }
  };

  // Helpers
  const formatDateTime = (iso?: string) => {
    if (!iso) return '';
    try {
      const d = new Date(iso);
      const dd = String(d.getDate()).padStart(2, '0');
      const mm = String(d.getMonth() + 1).padStart(2, '0');
      const yyyy = d.getFullYear();
      const hh = String(d.getHours()).padStart(2, '0');
      const mi = String(d.getMinutes()).padStart(2, '0');
      return `${hh}:${mi} ${dd}/${mm}/${yyyy}`;
    } catch {
      return iso;
    }
  };

  // Conversation handlers
  const handleSelectConversation = async (conv: Conversation) => {
    setCurrentConv(conv);
    await loadMessages(conv.id);
    if (isMobile) setSidebarOpen(false);
  };

  const handleNewConversation = async () => {
    try {
      const newConv = await createConversation();
      setCurrentConv(newConv);
      setMessages([]);
      await loadConversations();
      if (isMobile) setSidebarOpen(false);
    } catch (e) {
      console.error('Error creating conversation:', e);
    }
  };

  const handleDeleteConversation = async (convId: number) => {
    if (!window.confirm('Bạn có chắc muốn xóa cuộc trò chuyện này?')) return;
    try {
      await deleteConversation(convId);
      await loadConversations();
      if (currentConv?.id === convId) {
        setCurrentConv(null);
        setMessages([]);
      }
    } catch (e) {
      console.error('Error deleting conversation:', e);
    }
  };

  const handleEditTitle = (convId: number, currentTitle: string) => {
    setEditingTitle(convId);
    setNewTitle(currentTitle);
  };

  const handleSaveTitle = async (convId: number) => {
    try {
      await updateConversationTitle(convId, newTitle);
      await loadConversations();
      if (currentConv?.id === convId) {
        setCurrentConv(prev => (prev ? { ...prev, title: newTitle } : null));
      }
      setEditingTitle(null);
    } catch (e) {
      console.error('Error updating title:', e);
    }
  };

  const handleCancelEdit = () => {
    setEditingTitle(null);
    setNewTitle('');
  };

  // Text chat
  const handleSendMessage = async (text?: string) => {
    const messageText = text || input.trim();
    if (!messageText || loading) return;

    if (!text) setInput('');

    const userMessage: MessageWithProvider = {
      sender: 'user',
      content: messageText,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);

    setLoading(true);
    try {
      const response = await sendMessage(
        currentConv?.id || null,
        messageText,
        selectedProvider === 'auto' ? undefined : selectedProvider
      );

      const aiMessage: MessageWithProvider = {
        ...response.message,
        ai_provider: response.ai_provider,
        ai_model: response.ai_model
      };
      setMessages(prev => [...prev, aiMessage]);

      if (!currentConv) {
        setCurrentConv({
          id: response.conversation_id,
          title: response.conversation_title,
          started_at: new Date().toISOString(),
          message_count: 2
        });
        await loadConversations();
      }
    } catch (e) {
      console.error('Error sending message:', e);
      setMessages(prev => [
        ...prev,
        {
          sender: 'ai',
          content: 'Xin lỗi, có lỗi xảy ra khi xử lý tin nhắn.',
          timestamp: new Date().toISOString()
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Voice functionality
  const handleVoiceInput = async () => {
    if (isRecording) {
      try {
        const audioBlob = await audioRecorder.stopRecording();
        setIsRecording(false);
        await handleVoiceChat(audioBlob);
      } catch (error) {
        console.error('Error stopping recording:', error);
        setIsRecording(false);
      }
      return;
    }

    if (!browserVoiceSupport.mediaRecorder) {
      alert('Trình duyệt không hỗ trợ ghi âm.');
      return;
    }

    try {
      await audioRecorder.startRecording();
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Không thể bắt đầu ghi âm. Vui lòng kiểm tra quyền truy cập microphone.');
    }
  };

  const handleVoiceChat = async (audioBlob: Blob) => {
    const userPlaceholder: MessageWithProvider = {
      sender: 'user',
      content: '🎤 Đang xử lý tin nhắn thoại...',
      timestamp: new Date().toISOString(),
      voice_metadata: { is_voice_message: true }
    };
    setMessages(prev => [...prev, userPlaceholder]);

    try {
      const diag = await logAudioDiagnostics(audioBlob);
      setLastAudioDiagnostics(diag);
      const validation = await validateAudioBeforeUpload(audioBlob);
      if (!validation.ok) {
        setMessages(prev => {
          const updated = [...prev];
          const idx = updated.length - 1;
          if (updated[idx]?.sender === 'user') {
            updated[idx] = {
              ...updated[idx],
              content: `🎤 Voice message không hợp lệ: ${validation.reason}. Hãy thử nói rõ hơn hoặc ghi âm lại.`,
              voice_metadata: {
                is_voice_message: true,
                original_audio_duration: validation.diagnostics.durationSec
              }
            };
          }
          return updated;
        });
        return;
      }
    } catch (e) {
      console.warn('Audio diagnostics failed:', e);
    }

    setIsTranscribing(true);
    setLoading(true);

    try {
      const result = await voiceChat(
        audioBlob,
        currentConv?.id || null,
        selectedProvider === 'auto' ? undefined : selectedProvider,
        voiceSettings.language,
        voiceSettings.autoSpeak && voiceSettings.useServerVoice
      );

      const recordingInfo = (audioBlob as any).recordingInfo;
      const origDurationSec: number | undefined =
        recordingInfo?.duration
          ? Math.round((recordingInfo.duration as number) / 1000)
          : lastAudioDiagnostics?.durationSec
          ? Math.round(lastAudioDiagnostics.durationSec)
          : undefined;

      if (result instanceof Blob) {
        const metadata = (result as any).metadata || {};
        setMessages(prev => {
          const updated = [...prev];
          const lastUserIndex = updated.length - 1;
          if (updated[lastUserIndex]?.sender === 'user') {
            updated[lastUserIndex] = {
              sender: 'user',
              content: metadata.transcript || '(Không nhận diện được lời nói)',
              timestamp: updated[lastUserIndex].timestamp,
              voice_metadata: { is_voice_message: true, original_audio_duration: origDurationSec }
            };
          }
          return updated;
        });

        setMessages(prev => [
          ...prev,
          {
            sender: 'ai',
            content: metadata.ai_response || '',
            timestamp: new Date().toISOString(),
            ai_provider: metadata.ai_provider,
            ai_model: metadata.ai_model
          }
        ]);

        await playAudioBlob(result);

        if (!currentConv && metadata.conversation_id) {
          await loadConversations();
        }
      } else {
        const response = result as any;

        setMessages(prev => {
          const updated = [...prev];
          const lastUserIndex = updated.length - 1;
          if (updated[lastUserIndex]?.sender === 'user') {
            updated[lastUserIndex] = {
              sender: 'user',
              content: response.transcript || '(Không nhận diện được lời nói)',
              timestamp: updated[lastUserIndex].timestamp,
              voice_metadata: {
                is_voice_message: true,
                original_audio_duration: origDurationSec ?? response.audio_duration
              }
            };
          }
          return updated;
        });

        setMessages(prev => [
          ...prev,
          {
            sender: 'ai',
            content: response.ai_response,
            timestamp: new Date().toISOString(),
            ai_provider: response.ai_provider,
            ai_model: response.ai_model
          }
        ]);

        if (!currentConv && response.conversation_id) {
          await loadConversations();
        }
      }
    } catch (e) {
      console.error('Error in voice chat:', e);
      setMessages(prev => {
        const updated = [...prev];
        const idx = updated.length - 1;
        if (updated[idx]?.sender === 'user') {
          updated[idx] = {
            ...updated[idx],
            content: '🎤 Voice message (không xử lý được)'
          };
        }
        return updated;
      });
      setMessages(prev => [
        ...prev,
        {
          sender: 'ai',
          content: 'Xin lỗi, có lỗi xảy ra khi xử lý voice message.',
          timestamp: new Date().toISOString()
        }
      ]);
    } finally {
      setIsTranscribing(false);
      setLoading(false);
    }
  };

  // Settings Modal Component
  const SettingsModal = () => {
    if (!showSettings) return null;

    return (
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: 20
        }}
        onClick={() => setShowSettings(false)}
      >
        <div
          style={{
            backgroundColor: '#2a2a2a',
            borderRadius: 16,
            padding: 24,
            minWidth: 400,
            maxWidth: '90vw',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)',
            border: '1px solid #444'
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <h3 style={{ margin: 0, fontSize: 20, fontWeight: 600, color: '#ffffff' }}>Cài đặt Voice</h3>
            <button
              onClick={() => setShowSettings(false)}
              style={{
                background: 'none',
                border: 'none',
                fontSize: 24,
                cursor: 'pointer',
                color: '#888',
                padding: 4
              }}
            >
              ×
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Auto-speak */}
            <div>
              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', fontSize: 14, color: '#fff' }}>
                <input
                  type="checkbox"
                  checked={voiceSettings.autoSpeak}
                  onChange={(e) => setVoiceSettings(prev => ({ ...prev, autoSpeak: e.target.checked }))}
                  style={{
                    marginRight: 12,
                    width: 18,
                    height: 18,
                    accentColor: '#0084ff'
                  }}
                />
                <span style={{ fontWeight: 500 }}>Tự động đọc câu trả lời (TTS)</span>
              </label>
            </div>

            {/* Language */}
            <div>
              <label style={{ display: 'block', fontSize: 14, marginBottom: 8, fontWeight: 500, color: '#fff' }}>Ngôn ngữ</label>
              <select
                value={voiceSettings.language}
                onChange={(e) => setVoiceSettings(prev => ({ ...prev, language: e.target.value }))}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  border: '2px solid #444',
                  borderRadius: 8,
                  fontSize: 14,
                  backgroundColor: '#333',
                  color: '#fff',
                  outline: 'none',
                  transition: 'border-color 0.2s'
                }}
              >
                <option value="vi-VN">🇻🇳 Tiếng Việt</option>
                <option value="en-US">🇺🇸 English</option>
                <option value="ja-JP">🇯🇵 日本語</option>
                <option value="ko-KR">🇰🇷 한국어</option>
              </select>
            </div>

            {/* Speed */}
            <div>
              <label style={{ display: 'block', fontSize: 14, marginBottom: 8, fontWeight: 500, color: '#fff' }}>
                Tốc độ đọc: {voiceSettings.speed}x
              </label>
              <input
                type="range"
                min="0.5"
                max="2"
                step="0.1"
                value={voiceSettings.speed}
                onChange={(e) => setVoiceSettings(prev => ({ ...prev, speed: parseFloat(e.target.value) }))}
                style={{
                  width: '100%',
                  height: 6,
                  borderRadius: 3,
                  background: '#444',
                  outline: 'none',
                  accentColor: '#0084ff'
                }}
              />
            </div>

            {/* Capabilities Status */}
            <div
              style={{
                backgroundColor: '#333',
                padding: 16,
                borderRadius: 8,
                fontSize: 13,
                color: '#ccc'
              }}
            >
              <div style={{ fontWeight: 500, marginBottom: 8, color: '#fff' }}>Trạng thái hệ thống:</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <div>🎤 Ghi âm: {browserVoiceSupport.mediaRecorder ? '✅ Hỗ trợ' : '❌ Không hỗ trợ'}</div>
                <div>🔊 Server Voice: {voiceCapabilities?.speech_recognition_available ? '✅ Có sẵn' : '❌ Không có'}</div>
                <div>🏥 Hệ thống: {isSystemHealthy ? '✅ Khỏe mạnh' : '❌ Có vấn đề'}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Message Component
  const renderMessage = (msg: MessageWithProvider, index: number) => (
    <div
      key={index}
      style={{
        display: 'flex',
        flexDirection: msg.sender === 'user' ? 'row-reverse' : 'row',
        marginBottom: 20,
        alignItems: 'flex-start',
        gap: 12
      }}
    >
      <div
        style={{
          width: 40,
          height: 40,
          borderRadius: '50%',
          background: msg.sender === 'user'
            ? 'linear-gradient(135deg, #0084ff, #00a1ff)'
            : 'linear-gradient(135deg, #28a745, #20c997)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 18,
          flexShrink: 0,
          boxShadow: '0 2px 10px rgba(0, 0, 0, 0.3)'
        }}
      >
        {msg.sender === 'user' ? '👤' : '🤖'}
      </div>

      <div
        style={{
          maxWidth: isMobile ? '75%' : '70%',
          background: msg.sender === 'user' ? '#0084ff' : '#333333',
          color: msg.sender === 'user' ? 'white' : '#ffffff',
          padding: '16px 20px',
          borderRadius: msg.sender === 'user' ? '20px 20px 6px 20px' : '20px 20px 20px 6px',
          fontSize: 15,
          lineHeight: 1.5,
          wordWrap: 'break-word' as const,
          boxShadow: msg.sender === 'user' 
            ? '0 2px 15px rgba(0, 132, 255, 0.3)' 
            : '0 2px 15px rgba(0, 0, 0, 0.3)',
          border: msg.sender === 'ai' ? '1px solid #444' : 'none'
        }}
      >
        {msg.voice_metadata?.is_voice_message && (
          <div style={{ 
            fontSize: 12, 
            opacity: 0.8, 
            marginBottom: 8, 
            display: 'flex', 
            gap: 8, 
            alignItems: 'center',
            color: msg.sender === 'user' ? 'rgba(255,255,255,0.8)' : '#ccc'
          }}>
            🎤 Voice message
            {msg.voice_metadata.transcription_confidence && (
              <span>({Math.round(msg.voice_metadata.transcription_confidence * 100)}%)</span>
            )}
            {msg.voice_metadata.original_audio_duration && (
              <span>({Math.round(msg.voice_metadata.original_audio_duration)}s)</span>
            )}
          </div>
        )}

        {msg.content}

        {msg.sender === 'ai' && (msg.ai_provider || msg.ai_model) && (
          <div
            style={{
              fontSize: 11,
              opacity: 0.6,
              marginTop: 8,
              borderTop: '1px solid rgba(255,255,255,0.1)',
              paddingTop: 8,
              color: '#ccc'
            }}
          >
            {msg.ai_provider && `${msg.ai_provider}`}
            {msg.ai_model && ` • ${msg.ai_model}`}
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        fontFamily: "'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
        color: '#ffffff',
        backgroundColor: '#1a1a1a'
      }}
    >
      {/* Mobile overlay */}
      {isMobile && sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.6)',
            zIndex: 998
          }}
        />
      )}

      {/* Sidebar - DARK MODE */}
      <aside
        style={{
          width: sidebarOpen ? (isMobile ? '100%' : isTablet ? 320 : 360) : 0,
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: '#2a2a2a',
          boxShadow: sidebarOpen ? '4px 0 20px rgba(0,0,0,0.2)' : 'none',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          position: isMobile ? 'fixed' : 'relative',
          top: 0,
          left: 0,
          height: '100vh',
          zIndex: 999,
          overflow: 'hidden',
          borderRight: sidebarOpen ? '1px solid #444' : 'none'
        }}
      >
        {sidebarOpen && (
          <>
            {/* Sidebar Header */}
            <div
              style={{
                padding: '24px 20px',
                background: 'linear-gradient(135deg, #0084ff 0%, #00a1ff 100%)',
                color: 'white',
                borderBottom: '1px solid rgba(255,255,255,0.1)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <h2 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>💬 Bixby Chat</h2>
                
                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    onClick={() => setSidebarOpen(false)}
                    title="Thu gọn sidebar"
                    style={{
                      background: 'rgba(255,255,255,0.2)',
                      border: 'none',
                      borderRadius: 8,
                      width: 36,
                      height: 36,
                      color: 'white',
                      cursor: 'pointer',
                      fontSize: 18,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      transition: 'background 0.2s'
                    }}
                  >
                    «
                  </button>
                  
                  {isMobile && (
                    <button
                      onClick={() => setSidebarOpen(false)}
                      title="Đóng"
                      style={{
                        background: 'rgba(255,255,255,0.2)',
                        border: 'none',
                        borderRadius: 8,
                        width: 36,
                        height: 36,
                        color: 'white',
                        cursor: 'pointer',
                        fontSize: 18,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        transition: 'background 0.2s'
                      }}
                    >
                      ×
                    </button>
                  )}
                </div>
              </div>

              <button
                onClick={handleNewConversation}
                style={{
                  width: '100%',
                  padding: 14,
                  background: 'rgba(255,255,255,0.2)',
                  border: '1px solid rgba(255,255,255,0.3)',
                  borderRadius: 10,
                  color: 'white',
                  cursor: 'pointer',
                  fontSize: 15,
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 8,
                  transition: 'background 0.2s'
                }}
              >
                ➕ Cuộc trò chuyện mới
              </button>
            </div>

            {/* Conversation History */}
            <div style={{ 
              flex: 1, 
              overflow: 'auto', 
              padding: '16px 12px',
              backgroundColor: '#2a2a2a'
            }}>
              <h3 style={{ 
                margin: '0 0 12px 8px', 
                fontSize: 14, 
                fontWeight: 600, 
                color: '#888',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                Lịch sử trò chuyện
              </h3>
              
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => handleSelectConversation(conv)}
                  style={{
                    padding: 16,
                    margin: '8px 0',
                    borderRadius: 12,
                    cursor: 'pointer',
                    backgroundColor: currentConv?.id === conv.id ? '#404040' : '#333333',
                    border: currentConv?.id === conv.id ? '2px solid #0084ff' : '1px solid #444',
                    transition: 'all 0.2s ease',
                    boxShadow: currentConv?.id === conv.id 
                      ? '0 4px 12px rgba(0, 132, 255, 0.3)' 
                      : '0 1px 3px rgba(0, 0, 0, 0.3)'
                  }}
                >
                  {editingTitle === conv.id ? (
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <input
                        type="text"
                        value={newTitle}
                        onChange={(e) => setNewTitle(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleSaveTitle(conv.id);
                          if (e.key === 'Escape') handleCancelEdit();
                        }}
                        style={{
                          flex: 1,
                          padding: '8px 12px',
                          border: '2px solid #0084ff',
                          borderRadius: 8,
                          fontSize: 14,
                          outline: 'none',
                          backgroundColor: '#555',
                          color: '#fff'
                        }}
                        autoFocus
                      />
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSaveTitle(conv.id);
                        }}
                        style={{ 
                          background: '#0084ff', 
                          border: 'none', 
                          borderRadius: 6,
                          padding: '6px 8px',
                          cursor: 'pointer', 
                          fontSize: 12, 
                          color: 'white'
                        }}
                      >
                        ✓
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCancelEdit();
                        }}
                        style={{ 
                          background: '#ff4757', 
                          border: 'none', 
                          borderRadius: 6,
                          padding: '6px 8px',
                          cursor: 'pointer', 
                          fontSize: 12, 
                          color: 'white'
                        }}
                      >
                        ×
                      </button>
                    </div>
                  ) : (
                    <>
                      <div
                        style={{
                          fontWeight: currentConv?.id === conv.id ? 600 : 500,
                          fontSize: 15,
                          color: currentConv?.id === conv.id ? '#0084ff' : '#ffffff',
                          marginBottom: 8,
                          wordBreak: 'break-word' as const,
                          lineHeight: 1.4
                        }}
                      >
                        {conv.title}
                      </div>
                      <div style={{ 
                        fontSize: 12, 
                        color: '#888', 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center' 
                      }}>
                        <span>{conv.message_count} tin nhắn</span>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleEditTitle(conv.id, conv.title);
                            }}
                            style={{ 
                              background: 'none', 
                              border: 'none', 
                              cursor: 'pointer', 
                              fontSize: 14, 
                              color: '#0084ff',
                              padding: 4,
                              borderRadius: 4,
                              transition: 'background 0.2s'
                            }}
                            title="Chỉnh sửa tiêu đề"
                          >
                            ✏️
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteConversation(conv.id);
                            }}
                            style={{ 
                              background: 'none', 
                              border: 'none', 
                              cursor: 'pointer', 
                              fontSize: 14, 
                              color: '#ff4757',
                              padding: 4,
                              borderRadius: 4,
                              transition: 'background 0.2s'
                            }}
                            title="Xóa cuộc trò chuyện"
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>

            {/* Voice Settings in Sidebar Footer */}
            <div style={{
              padding: 16,
              borderTop: '1px solid #444',
              backgroundColor: '#2a2a2a'
            }}>
              <button
                onClick={() => setShowSettings(true)}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  background: '#404040',
                  border: '1px solid #555',
                  borderRadius: 10,
                  color: '#ffffff',
                  cursor: 'pointer',
                  fontSize: 14,
                  fontWeight: 500,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 8,
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = '#4a4a4a';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = '#404040';
                }}
              >
                ⚙️ Cài đặt Voice
              </button>
            </div>
          </>
        )}
      </aside>

      {/* Main Chat Area */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100vh' }}>
        {/* Header with detailed info */}
        <header
          style={{
            padding: '16px 24px',
            borderBottom: '1px solid #333',
            backgroundColor: '#1a1a1a',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 16,
            boxShadow: '0 1px 4px rgba(0, 0, 0, 0.3)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, minWidth: 0 }}>
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                title="Mở sidebar"
                style={{
                  background: '#333',
                  border: '1px solid #444',
                  borderRadius: 10,
                  padding: '10px 12px',
                  cursor: 'pointer',
                  fontSize: 16,
                  color: '#ccc',
                  transition: 'all 0.2s',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                ☰
              </button>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
                <h1
                  style={{
                    margin: 0,
                    fontSize: isMobile ? 18 : 20,
                    fontWeight: 700,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    maxWidth: isMobile ? 180 : 350,
                    color: '#ffffff'
                  }}
                  title={currentConv?.title || 'Bixby Chat'}
                >
                  {currentConv?.title || 'Bixby Chat'}
                </h1>
              </div>

              {/* Chat details in header */}
              <div style={{ 
                fontSize: 12, 
                color: '#888', 
                marginTop: 4,
                display: 'flex',
                alignItems: 'center',
                gap: 8
              }}>
                {currentConv ? (
                  <>
                    <span>{currentConv.message_count || messages.length} tin nhắn</span>
                    <span>•</span>
                    <span>Bắt đầu: {formatDateTime(currentConv.started_at)}</span>
                    {messages.length > 0 && (
                      <>
                        <span>•</span>
                        <span>Cập nhật: {formatDateTime(messages[messages.length - 1]?.timestamp)}</span>
                      </>
                    )}
                  </>
                ) : (
                  <span>Sẵn sàng trò chuyện với AI</span>
                )}
              </div>
            </div>
          </div>

          {/* Model Selection & Health Status */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div
                title={`Hệ thống ${isSystemHealthy ? 'Khỏe mạnh' : 'Có vấn đề'}`}
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  backgroundColor: isSystemHealthy ? '#28a745' : '#ff4757'
                }}
              />
              
              <select
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value)}
                title="Chọn AI Model"
                style={{
                  padding: '8px 12px',
                  border: '2px solid #444',
                  borderRadius: 8,
                  fontSize: 13,
                  backgroundColor: '#333',
                  color: '#fff',
                  cursor: 'pointer',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                  fontWeight: 500
                }}
              >
                <option value="auto">🤖 Auto</option>
                {providerInfo?.github_available && <option value="github">🐙 GitHub</option>}
                {providerInfo?.ollama_available && <option value="ollama">🦙 Ollama</option>}
              </select>
            </div>

            {!isMobile && (
              <div style={{
                padding: '6px 12px',
                border: '1px solid #444',
                borderRadius: 20,
                fontSize: 12,
                color: '#ccc',
                backgroundColor: '#333',
                fontWeight: 500
              }}>
                {selectedProvider === 'github'
                  ? providerInfo?.github_model || 'GitHub Model'
                  : selectedProvider === 'ollama'
                  ? providerInfo?.ollama_model || 'Ollama Model'
                  : providerInfo?.current_provider || 'Auto Model'}
              </div>
            )}
          </div>
        </header>

        {/* Messages Area */}
        <div style={{ 
          flex: 1, 
          overflow: 'auto', 
          padding: '24px',
          backgroundColor: '#1a1a1a'
        }}>
          {messages.length === 0 ? (
            <div
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                textAlign: 'center',
                color: '#888',
                height: '100%'
              }}
            >
              <div style={{ fontSize: 64, marginBottom: 24 }}>🤖</div>
              <h3 style={{ margin: '0 0 12px 0', fontSize: 24, fontWeight: 700, color: '#ffffff' }}>
                Chào mừng đến với Bixby!
              </h3>
              <p style={{ margin: 0, fontSize: 16, lineHeight: 1.5, maxWidth: 400, color: '#ccc' }}>
                Hãy nhập tin nhắn hoặc nhấn micro để nói chuyện với trợ lý AI thông minh của bạn.
              </p>
            </div>
          ) : (
            <>
              {messages.map(renderMessage)}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Area - ChatGPT Style */}
        <div
          style={{
            padding: '16px 24px 24px 24px',
            borderTop: '1px solid #333',
            backgroundColor: '#1a1a1a',
            boxShadow: '0 -2px 10px rgba(0, 0, 0, 0.3)'
          }}
        >
          <div
            style={{
              position: 'relative',
              maxWidth: '100%'
            }}
          >
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything"
              disabled={loading}
              style={{
                width: '100%',
                minHeight: 52,
                maxHeight: 160,
                padding: '16px 120px 16px 50px',
                border: '1px solid #424242',
                borderRadius: 26,
                fontSize: 16,
                resize: 'none',
                outline: 'none',
                fontFamily: 'inherit',
                backgroundColor: loading ? '#2a2a2a' : '#212121',
                color: '#ffffff',
                transition: 'border-color 0.2s, background-color 0.2s',
                lineHeight: 1.4,
                boxSizing: 'border-box'
              }}
              onFocus={(e) => e.target.style.borderColor = '#555'}
              onBlur={(e) => e.target.style.borderColor = '#424242'}
            />
            
            {/* Plus Icon (Left) */}
            <button
              style={{
                position: 'absolute',
                left: 16,
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: 'none',
                color: plusHover ? '#fff' : '#888',
                fontSize: 20,
                cursor: 'pointer',
                padding: 4,
                borderRadius: 4,
                transition: 'color 0.2s'
              }}
              onMouseEnter={() => setPlusHover(true)}
              onMouseLeave={() => setPlusHover(false)}
              title="Attach file"
            >
              +
            </button>

            {/* Right side buttons container */}
            <div
              style={{
                position: 'absolute',
                right: 12,
                top: '50%',
                transform: 'translateY(-50%)',
                display: 'flex',
                gap: 8,
                alignItems: 'center'
              }}
            >
              {/* Voice Button */}
              <button
                onClick={handleVoiceInput}
                disabled={loading || isTranscribing}
                title={isRecording ? 'Dừng ghi âm' : 'Ghi âm tin nhắn'}
                style={{
                  background: isRecording ? '#ef4444' : (voiceHover && !loading && !isTranscribing ? '#374151' : 'none'),
                  color: isRecording ? 'white' : (voiceHover && !loading && !isTranscribing ? '#fff' : '#888'),
                  border: 'none',
                  borderRadius: '50%',
                  width: 32,
                  height: 32,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: loading || isTranscribing ? 'not-allowed' : 'pointer',
                  fontSize: 16,
                  transition: 'all 0.2s ease',
                  opacity: loading || isTranscribing ? 0.5 : 1
                }}
                onMouseEnter={() => setVoiceHover(true)}
                onMouseLeave={() => setVoiceHover(false)}
              >
                🎤
              </button>

              {/* Send Button - Only show when there's text */}
              {input.trim() && (
                <button
                  onClick={() => handleSendMessage()}
                  disabled={loading}
                  title="Send message"
                  style={{
                    background: sendHover && !loading ? '#f3f4f6' : '#ffffff',
                    color: '#000000',
                    border: 'none',
                    borderRadius: '50%',
                    width: 28,
                    height: 28,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    fontSize: 14,
                    transition: 'all 0.2s ease',
                    opacity: loading ? 0.5 : 1,
                    fontWeight: 'bold'
                  }}
                  onMouseEnter={() => setSendHover(true)}
                  onMouseLeave={() => setSendHover(false)}
                >
                  ↑
                </button>
              )}
            </div>
            
            {/* Loading indicator overlay */}
            {(loading || isTranscribing) && (
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'rgba(33, 33, 33, 0.8)',
                borderRadius: 26,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                fontSize: 14,
                gap: 8
              }}>
                <div style={{
                  width: 12,
                  height: 12,
                  border: '2px solid #555',
                  borderTop: '2px solid #fff',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }} />
                {isTranscribing ? 'Processing voice...' : 'Sending...'}
              </div>
            )}
          </div>

          {/* Status Row */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: 12,
              fontSize: 12,
              color: '#666'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span>🎤 Mic: {browserVoiceSupport.mediaRecorder ? '✅' : '❌'}</span>
              {isRecording && <span style={{ color: '#ff4757', fontWeight: 600 }}>● Đang ghi âm</span>}
              {isTranscribing && <span style={{ color: '#0084ff', fontWeight: 600 }}>🔄 Đang xử lý</span>}
            </div>
            <div>
              AI: {providerInfo?.current_provider || 'auto'} | 
              Health: <span style={{ color: isSystemHealthy ? '#28a745' : '#ff4757', fontWeight: 600 }}>
                {isSystemHealthy ? '✅' : '❌'}
              </span>
            </div>
          </div>
        </div>
      </main>

      {/* Settings Modal */}
      <SettingsModal />

      {/* CSS Animations */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }

        /* Scrollbar styling for dark theme */
        ::-webkit-scrollbar {
          width: 6px;
        }
        
        ::-webkit-scrollbar-track {
          background: #2a2a2a;
          border-radius: 3px;
        }
        
        ::-webkit-scrollbar-thumb {
          background: #555;
          border-radius: 3px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
          background: #666;
        }
      `}</style>
    </div>
  );
};

export default ChatUI;