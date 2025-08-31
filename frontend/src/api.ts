// api.ts - Complete Enhanced API with Voice Chat Integration
declare const process: { env: { REACT_APP_API_URL?: string } };
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// ===== EXISTING INTERFACES =====
export interface Message {
  sender: string;
  content: string;
  timestamp: string;
  ai_provider?: string;
  ai_model?: string;
}

export interface Conversation {
  id: number;
  title: string;
  started_at: string;
  last_message?: string;
  message_count: number;
}

export interface ChatResponse {
  conversation_id: number;
  message: Message;
  conversation_title: string;
  ai_provider?: string;
  ai_model?: string;
}

export interface ProviderInfo {
  current_provider: string;
  github_available: boolean;
  ollama_available: boolean;
  github_model?: string;
  ollama_model?: string;
}

export interface HealthCheckResponse {
  message: string;
  status: string;
  data: {
    ai_available: boolean;
    providers: {
      github: boolean;
      ollama: boolean;
      current: string;
    };
  };
  voice_health?: {
    speech_recognition_available: boolean;
    text_to_speech_available: boolean;
    status: string;
  };
}

// ===== VOICE INTERFACES =====
export interface VoiceTranscriptResponse {
  success: boolean;
  transcript?: string;
  message?: string;
  error?: string;
  fallback?: boolean;
}

export interface VoiceChatResponse {
  transcript: string;
  ai_response: string;
  conversation_id: number;
  ai_provider?: string;
  ai_model?: string;
  audio_duration?: number;
  has_audio_response?: boolean;
}

export interface VoiceCapabilities {
  speech_recognition_available: boolean;
  text_to_speech_available: boolean;
  supported_languages: string[];
  available_voices: Array<{
    id: string;
    name: string;
    languages: string[];
    gender: string;
    is_vietnamese?: boolean;
  }>;
  offline_mode: boolean;
  max_audio_size_mb: number;
  max_text_length: number;
  supported_audio_formats: string[];
  health_status: string;
}

export interface BrowserVoiceSupport {
  speechRecognition: boolean;
  speechSynthesis: boolean;
  webRTC: boolean;
  mediaRecorder: boolean;
  fullSupport: boolean;
}

// ===== ERROR HANDLING =====
class APIError extends Error {
  constructor(public status: number, message: string, public response?: any) {
    super(message);
    this.name = 'APIError';
  }
}

const handleResponse = async (response: Response) => {
  if (!response.ok) {
    let errorMessage = `HTTP error! status: ${response.status}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      errorMessage = response.statusText || errorMessage;
    }
    throw new APIError(response.status, errorMessage, response);
  }
  return response;
};

// ===== VOICE SUPPORT DETECTION =====
export function checkVoiceSupport(): BrowserVoiceSupport {
  try {
    const speechRecognition = 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window;
    const speechSynthesis = 'speechSynthesis' in window;
    const webRTC = navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === 'function';
    
    let mediaRecorder = false;
    try {
      mediaRecorder = 'MediaRecorder' in window && webRTC;
      // Additional check for MediaRecorder support
      if (mediaRecorder) {
        const testTypes = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/wav'];
        mediaRecorder = testTypes.some(type => MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(type));
      }
    } catch (error) {
      console.warn('MediaRecorder detection failed:', error);
      mediaRecorder = false;
    }
    
    const fullSupport = speechRecognition && speechSynthesis && mediaRecorder && webRTC;
    
    return {
      speechRecognition,
      speechSynthesis,
      webRTC,
      mediaRecorder,
      fullSupport
    };
  } catch (error) {
    console.error('Voice support check failed:', error);
    return {
      speechRecognition: false,
      speechSynthesis: false,
      webRTC: false,
      mediaRecorder: false,
      fullSupport: false
    };
  }
}

// ===== DEBUG VOICE SUPPORT =====
export function debugVoiceSupport(): void {
  console.log('🔍 Voice Support Debug Information:');
  
  try {
    const support = checkVoiceSupport();
    console.log('✅ Voice support check completed:');
    console.log('  - Speech Recognition:', support.speechRecognition);
    console.log('  - Speech Synthesis:', support.speechSynthesis);
    console.log('  - WebRTC:', support.webRTC);
    console.log('  - Media Recorder:', support.mediaRecorder);
    console.log('  - Full Support:', support.fullSupport);
    
    // Additional debug info
    console.log('🔍 Browser details:');
    console.log('  - User Agent:', navigator.userAgent);
    console.log('  - Platform:', navigator.platform);
    console.log('  - Language:', navigator.language);
    
    // Test individual components
    console.log('🧪 Individual tests:');
    console.log('  - window.SpeechRecognition:', 'SpeechRecognition' in window);
    console.log('  - window.webkitSpeechRecognition:', 'webkitSpeechRecognition' in window);
    console.log('  - window.speechSynthesis:', 'speechSynthesis' in window);
    console.log('  - window.MediaRecorder:', 'MediaRecorder' in window);
    console.log('  - navigator.mediaDevices:', !!navigator.mediaDevices);
    console.log('  - getUserMedia function:', typeof navigator.mediaDevices?.getUserMedia);
    
    // Test MediaRecorder types
    if ('MediaRecorder' in window) {
      const testTypes = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/wav'];
      console.log('🎵 MediaRecorder support:');
      testTypes.forEach(type => {
        const supported = MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(type);
        console.log(`  - ${type}: ${supported}`);
      });
    }
    
  } catch (error) {
    console.error('❌ Voice support debug failed:', error);
  }
}

// ===== AUDIO RECORDER CLASS =====
export class AudioRecorder {
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private stream: MediaStream | null = null;
  private recordingStartTime: number = 0;

  async startRecording(options: MediaRecorderOptions = {}): Promise<void> {
    try {
      console.log('🎤 Starting audio recording...');
      
      // Get user media with audio constraints
      const constraints: MediaStreamConstraints = {
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        }
      };

      this.stream = await navigator.mediaDevices.getUserMedia(constraints);
      
      // Create MediaRecorder with optimal settings
      const defaultOptions: MediaRecorderOptions = {
        mimeType: this.getSupportedMimeType(),
        audioBitsPerSecond: 128000
      };

      this.mediaRecorder = new MediaRecorder(this.stream, { ...defaultOptions, ...options });
      this.audioChunks = [];
      this.recordingStartTime = Date.now();

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.start(100); // Collect data every 100ms
      console.log('✅ Recording started');
    } catch (error) {
      console.error('❌ Error starting recording:', error);
      await this.cleanup();
      throw new Error(this.getRecordingErrorMessage(error));
    }
  }

  async stopRecording(): Promise<Blob> {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder) {
        reject(new Error('No recording in progress'));
        return;
      }

      const recordingDuration = Date.now() - this.recordingStartTime;
      console.log(`🛑 Stopping recording after ${recordingDuration}ms`);

      this.mediaRecorder.onstop = () => {
        try {
          const mimeType = this.mediaRecorder?.mimeType || 'audio/wav';
          const audioBlob = new Blob(this.audioChunks, { type: mimeType });
          
          console.log(`✅ Recording complete: ${audioBlob.size} bytes, ${recordingDuration}ms`);
          
          // Add metadata to blob
          (audioBlob as any).recordingInfo = {
            duration: recordingDuration,
            size: audioBlob.size,
            mimeType: mimeType,
            chunkCount: this.audioChunks.length
          };

          this.cleanup();
          resolve(audioBlob);
        } catch (error) {
          this.cleanup();
          reject(error);
        }
      };

      this.mediaRecorder.onerror = (error) => {
        console.error('❌ Recording error:', error);
        this.cleanup();
        reject(new Error('Recording failed'));
      };

      this.mediaRecorder.stop();
    });
  }

  isRecording(): boolean {
    return this.mediaRecorder?.state === 'recording';
  }

  getRecordingDuration(): number {
    if (!this.recordingStartTime) return 0;
    return Date.now() - this.recordingStartTime;
  }

  private getSupportedMimeType(): string {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
      'audio/wav'
    ];

    for (const type of types) {
      if (MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(type)) {
        console.log(`🎵 Using MIME type: ${type}`);
        return type;
      }
    }

    console.warn('⚠️ No optimal MIME type supported, using default');
    return 'audio/wav';
  }

  private getRecordingErrorMessage(error: any): string {
    if (error.name === 'NotAllowedError') {
      return 'Quyền truy cập microphone bị từ chối. Vui lòng cho phép truy cập microphone.';
    }
    if (error.name === 'NotFoundError') {
      return 'Không tìm thấy microphone. Vui lòng kiểm tra thiết bị âm thanh.';
    }
    if (error.name === 'NotSupportedError') {
      return 'Trình duyệt không hỗ trợ ghi âm.';
    }
    return `Lỗi ghi âm: ${error.message || 'Unknown error'}`;
  }

  private async cleanup(): Promise<void> {
    try {
      if (this.stream) {
        this.stream.getTracks().forEach(track => {
          track.stop();
          console.log('🔇 Audio track stopped');
        });
        this.stream = null;
      }
      this.mediaRecorder = null;
      this.audioChunks = [];
      this.recordingStartTime = 0;
    } catch (error) {
      console.error('Error during cleanup:', error);
    }
  }
}

// ===== AUDIO UTILITIES =====
export async function playAudioBlob(audioBlob: Blob): Promise<void> {
  return new Promise((resolve, reject) => {
    const audio = new Audio();
    const audioUrl = URL.createObjectURL(audioBlob);
    
    audio.onloadeddata = () => {
      console.log('🎵 Audio loaded, duration:', audio.duration);
    };
    
    audio.onended = () => {
      URL.revokeObjectURL(audioUrl);
      console.log('✅ Audio playback completed');
      resolve();
    };
    
    audio.onerror = (error) => {
      URL.revokeObjectURL(audioUrl);
      console.error('❌ Audio playback error:', error);
      reject(error);
    };
    
    audio.src = audioUrl;
    audio.play().catch(reject);
  });
}

export function audioToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64 = reader.result as string;
      resolve(base64.split(',')[1]); // Remove data URL prefix
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

// ===== EXISTING API FUNCTIONS =====
export async function healthCheck(): Promise<HealthCheckResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    await handleResponse(res);
    return await res.json();
  } catch (error) {
    console.error('Error checking health:', error);
    throw error;
  }
}

export async function fetchConversations(): Promise<Conversation[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/chat/history`);
    await handleResponse(res);
    const data = await res.json();
    
    // Transform API response to match frontend interface
    const conversations = (data.history || []).map((conv: any) => ({
      id: conv.id,
      title: conv.title,
      started_at: conv.started_at,
      last_message: conv.messages && conv.messages.length > 0 
        ? conv.messages[conv.messages.length - 1].content.substring(0, 50) + '...'
        : 'Chưa có tin nhắn',
      message_count: conv.messages ? conv.messages.length : 0
    }));
    
    return conversations;
  } catch (error) {
    console.error('Error fetching conversations:', error);
    throw error;
  }
}

export async function fetchMessages(conversationId: number): Promise<Message[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/chat/history`);
    await handleResponse(res);
    const data = await res.json();
    const conversation = data.history?.find((conv: any) => conv.id === conversationId);
    return conversation?.messages || [];
  } catch (error) {
    console.error('Error fetching messages:', error);
    throw error;
  }
}

export async function sendMessage(
  conversationId: number | null, 
  user: string, 
  aiProvider?: string
): Promise<ChatResponse> {
  try {
    const body: any = { 
      message: user 
    };
    
    if (conversationId) {
      body.conversation_id = conversationId;
    }
    
    if (aiProvider) {
      body.ai_provider = aiProvider;
    }
    
    const res = await fetch(`${API_BASE_URL}/chat/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    
    await handleResponse(res);
    const data = await res.json();
    
    // Transform response to match expected format
    return {
      conversation_id: data.conversation_id || conversationId || 1,
      message: {
        sender: 'assistant',
        content: data.response || '',
        timestamp: new Date().toISOString(),
        ai_provider: data.provider,
        ai_model: data.model
      },
      conversation_title: 'Chat',
      ai_provider: data.provider,
      ai_model: data.model
    };
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
}

export async function createConversation(title?: string): Promise<Conversation> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: title || "Chat mới" })
    });
    
    await handleResponse(res);
    return await res.json();
  } catch (error) {
    console.error('Error creating conversation:', error);
    throw error;
  }
}

export async function updateConversationTitle(conversationId: number, title: string): Promise<void> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/conversations/${conversationId}/title`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title })
    });
    
    await handleResponse(res);
  } catch (error) {
    console.error('Error updating conversation title:', error);
    throw error;
  }
}

export async function deleteConversation(conversationId: number): Promise<void> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/conversations/${conversationId}`, {
      method: 'DELETE'
    });
    
    await handleResponse(res);
  } catch (error) {
    console.error('Error deleting conversation:', error);
    throw error;
  }
}

export async function getProviderInfo(): Promise<ProviderInfo> {
  try {
    const res = await fetch(`${API_BASE_URL}/models/status`);
    await handleResponse(res);
    const data = await res.json();
    
    // Extract provider info from models data
    const ollama_available = data.data?.models_by_type?.ollama?.length > 0 || false;
    const github_available = data.data?.models_by_type?.github?.length > 0 || false;
    
    const ollama_model = ollama_available 
      ? data.data.models_by_type.ollama[0]?.name 
      : undefined;
    const github_model = github_available 
      ? data.data.models_by_type.github[0]?.name 
      : undefined;
    
    return {
      current_provider: ollama_available ? 'ollama' : github_available ? 'github' : 'unknown',
      github_available,
      ollama_available,
      github_model,
      ollama_model
    };
  } catch (error) {
    console.error('Error fetching provider info:', error);
    throw error;
  }
}

// ===== VOICE API FUNCTIONS =====
export async function transcribeAudio(
  audioBlob: Blob,
  conversationId?: number,
  language: string = 'vi-VN'
): Promise<VoiceTranscriptResponse> {
  try {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'audio.webm');
    formData.append('language', language);
    if (conversationId) {
      formData.append('conversation_id', conversationId.toString());
    }

    const res = await fetch(`${API_BASE_URL}/voice/transcribe`, {
      method: 'POST',
      body: formData
    });

    await handleResponse(res);
    return await res.json();
  } catch (error) {
    console.error('Error transcribing audio:', error);
    throw error;
  }
}

export async function textToSpeech(
  text: string,
  language: string = 'vi-VN',
  voice?: string,
  speed: number = 1.0
): Promise<Blob> {
  try {
    // Fallback to browser TTS since server TTS is not available
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language;
    utterance.rate = speed;
    if (voice) utterance.voice = speechSynthesis.getVoices().find(v => v.name === voice) || null;
    
    return new Promise((resolve, reject) => {
      utterance.onend = () => {
        // Return empty blob since we can't capture browser TTS audio
        resolve(new Blob([], { type: 'audio/wav' }));
      };
      utterance.onerror = reject;
      speechSynthesis.speak(utterance);
    });
  } catch (error) {
    console.error('Error generating speech:', error);
    throw error;
  }
}

export async function voiceChat(
  audioBlob: Blob,
  conversationId?: number | null,
  aiProvider?: string,
  language: string = 'vi-VN',
  autoSpeak: boolean = true
): Promise<VoiceChatResponse | Blob> {
  try {
    // First transcribe audio
    const transcriptResult = await transcribeAudio(audioBlob, conversationId || undefined, language);
    
    if (!transcriptResult.success) {
      throw new Error(transcriptResult.message || 'Transcription failed');
    }
    
    const transcript = transcriptResult.transcript;
    
    // Then send message to AI
    const messageResult = await sendMessage(conversationId || null, transcript || '', aiProvider);
    
    // Create response object
    const response: VoiceChatResponse = {
      transcript: transcript || '',
      ai_response: messageResult.message.content,
      conversation_id: messageResult.conversation_id,
      ai_provider: messageResult.ai_provider,
      ai_model: messageResult.ai_model,
      has_audio_response: false
    };
    
    // If auto-speak is enabled, generate speech
    if (autoSpeak) {
      try {
        await textToSpeech(messageResult.message.content, language);
      } catch (speechError) {
        console.warn('Text-to-speech failed:', speechError);
      }
    }
    
    return response;
  } catch (error) {
    console.error('Error in voice chat:', error);
    throw error;
  }
}

export async function getVoiceCapabilities(): Promise<VoiceCapabilities> {
  try {
    const res = await fetch(`${API_BASE_URL}/voice/status`);
    await handleResponse(res);
    const data = await res.json();
    
    // Transform voice status to capabilities format
    const browserSupport = checkVoiceSupport();
    return {
      speech_recognition_available: data.vosk_available || browserSupport.speechRecognition,
      text_to_speech_available: data.tts_available || browserSupport.speechSynthesis,
      supported_languages: ['vi-VN', 'en-US'],
      available_voices: [],
      offline_mode: data.vosk_available || false,
      max_audio_size_mb: 10,
      max_text_length: 1000,
      supported_audio_formats: ['webm', 'wav', 'mp3'],
      health_status: data.fallback_mode ? 'degraded' : 'healthy'
    };
  } catch (error) {
    console.error('Error getting voice capabilities:', error);
    // Return minimal capabilities on error
    const browserSupport = checkVoiceSupport();
    return {
      speech_recognition_available: browserSupport.speechRecognition,
      text_to_speech_available: browserSupport.speechSynthesis,
      supported_languages: ['vi-VN', 'en-US'],
      available_voices: [],
      offline_mode: false,
      max_audio_size_mb: 10,
      max_text_length: 1000,
      supported_audio_formats: ['webm', 'wav', 'mp3'],
      health_status: 'unknown'
    };
  }
}

export async function getAvailableVoices() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/voice/voices`);
    await handleResponse(res);
    return await res.json();
  } catch (error) {
    console.error('Error getting voices:', error);
    throw error;
  }
}

export async function getSupportedLanguages() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/voice/languages`);
    await handleResponse(res);
    return await res.json();
  } catch (error) {
    console.error('Error getting languages:', error);
    return {
      languages: [
        { code: 'vi-VN', name: 'Tiếng Việt', country: 'Vietnam' },
        { code: 'en-US', name: 'English', country: 'United States' }
      ],
      count: 2,
      default: 'vi-VN'
    };
  }
}

export async function voiceHealthCheck() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/voice/health`);
    await handleResponse(res);
    return await res.json();
  } catch (error) {
    console.error('Voice health check failed:', error);
    throw error;
  }
}

export async function testVoicePipeline() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/voice/test`, {
      method: 'POST'
    });
    await handleResponse(res);
    return await res.json();
  } catch (error) {
    console.error('Voice pipeline test failed:', error);
    throw error;
  }
}

// ===== SPEECH RECOGNITION UTILITIES =====
export function createSpeechRecognition(
  language: string = 'vi-VN',
  onResult?: (transcript: string, isFinal: boolean) => void,
  onError?: (error: string) => void,
  onEnd?: () => void
): any {
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  
  if (!SpeechRecognition) {
    throw new Error('Speech recognition not supported in this browser');
  }

  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = language;
  recognition.maxAlternatives = 1;

  recognition.onresult = (event: any) => {
    let finalTranscript = '';
    let interimTranscript = '';
    
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalTranscript += transcript;
      } else {
        interimTranscript += transcript;
      }
    }
    
    if (onResult) {
      if (finalTranscript) {
        onResult(finalTranscript.trim(), true);
      } else if (interimTranscript) {
        onResult(interimTranscript.trim(), false);
      }
    }
  };

  recognition.onerror = (event: any) => {
    console.error('Speech recognition error:', event.error);
    if (onError) {
      onError(event.error);
    }
  };

  recognition.onend = () => {
    console.log('Speech recognition ended');
    if (onEnd) {
      onEnd();
    }
  };

  return recognition;
}

// ===== ADDITIONAL UTILITY FUNCTIONS =====
export async function testAI(message: string = "Xin chào Bixby!"): Promise<any> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/test-ai`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    
    await handleResponse(res);
    return await res.json();
  } catch (error) {
    console.error('Error testing AI:', error);
    throw error;
  }
}

export async function fetchStats(): Promise<any> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/stats`);
    await handleResponse(res);
    return await res.json();
  } catch (error) {
    console.error('Error fetching stats:', error);
    throw error;
  }
}

// ===== EXPORT ALL =====
export default {
  // Text chat
  healthCheck,
  fetchConversations,
  fetchMessages,
  sendMessage,
  createConversation,
  updateConversationTitle,
  deleteConversation,
  getProviderInfo,
  testAI,
  fetchStats,

  // Voice chat
  transcribeAudio,
  textToSpeech,
  voiceChat,
  getVoiceCapabilities,
  getAvailableVoices,
  getSupportedLanguages,
  voiceHealthCheck,
  testVoicePipeline,

  // Voice utilities
  checkVoiceSupport,
  debugVoiceSupport,
  createSpeechRecognition,
  AudioRecorder,
  playAudioBlob,
  audioToBase64
};