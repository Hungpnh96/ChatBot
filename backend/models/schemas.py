# models/schemas.py - Complete schemas with Voice support
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


# ===== EXISTING MESSAGE SCHEMAS =====
class MessageIn(BaseModel):
    user: str
    conversation_id: Optional[int] = None
    ai_provider: Optional[str] = None  # "github", "ollama", "auto"

class MessageOut(BaseModel):
    sender: str  # "user" hoặc "ai"
    content: str
    timestamp: str

# Enhanced Chat Response with AI provider info
class ChatResponse(BaseModel):
    conversation_id: int
    message: MessageOut
    conversation_title: str
    ai_provider: Optional[str] = None  # "github", "ollama", "fallback", "error"
    ai_model: Optional[str] = None


# ===== CONVERSATION SCHEMAS =====
class ConversationCreateRequest(BaseModel):
    title: Optional[str] = None

class ConversationUpdateRequest(BaseModel):
    title: str

class ConversationOut(BaseModel):
    id: int
    title: str
    started_at: str
    message_count: int
    last_message: Optional[str] = None

# ===== AI PROVIDER SCHEMAS =====
class AIProviderRequest(BaseModel):
    provider: str  # "github", "ollama", "auto"

class AIProviderResponse(BaseModel):
    status: str  # "success" hoặc "error"
    provider: Optional[str] = None
    model: Optional[str] = None
    message: Optional[str] = None

# ===== TEST AI SCHEMAS =====
class TestAIRequest(BaseModel):
    message: str = "Xin chào Bixby!"
    with_history: bool = False
    provider: Optional[str] = None

class TestAIResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    status: str
    user_input: str
    ai_response: Optional[str] = None
    provider_used: Optional[str] = None
    model_used: Optional[str] = None
    history_length: Optional[int] = None
    providers_available: Optional[Dict[str, bool]] = None
    error: Optional[str] = None


# ===== VOICE SCHEMAS =====

# Voice Transcript schemas
class VoiceTranscriptRequest(BaseModel):
    language: str = "vi-VN"
    conversation_id: Optional[int] = None

class VoiceTranscriptResponse(BaseModel):
    text: str
    language: str
    confidence: float
    timestamp: str
    conversation_id: Optional[int] = None
    word_count: int = 0
    duration_estimate: float = 0.0
    error: Optional[str] = None

# Text-to-Speech schemas
class TextToSpeechRequest(BaseModel):
    text: str
    language: str = "vi-VN"
    voice: Optional[str] = None
    speed: float = 1.0
    pitch: float = 1.0

class VoiceSettings(BaseModel):
    auto_transcribe: bool = True
    auto_speak_response: bool = True
    voice_language: str = "vi-VN"
    speech_speed: float = 1.0
    voice_id: Optional[str] = None

# Voice Chat schemas
class VoiceChatRequest(BaseModel):
    conversation_id: Optional[int] = None
    ai_provider: Optional[str] = None
    language: str = "vi-VN"
    auto_speak: bool = True
    voice_settings: Optional[VoiceSettings] = None

class VoiceChatResponse(BaseModel):
    transcript: str
    ai_response: str
    conversation_id: int
    ai_provider: Optional[str] = None
    audio_duration: Optional[float] = None
    has_audio_response: bool = False

# Voice capabilities
class VoiceCapabilities(BaseModel):
    speech_recognition_available: bool
    text_to_speech_available: bool
    supported_languages: List[str]
    available_voices: List[Dict[str, Any]]
    offline_mode: bool = False
    max_audio_size_mb: int = 10
    max_text_length: int = 1000
    supported_audio_formats: List[str] = ["wav", "mp3", "m4a", "webm", "ogg"]
    health_status: str = "unknown"

# Voice message metadata
class VoiceMessageMetadata(BaseModel):
    is_voice_message: bool = False
    original_audio_duration: Optional[float] = None
    transcription_confidence: Optional[float] = None
    voice_language: Optional[str] = None
    tts_voice_used: Optional[str] = None


# ===== SYSTEM SCHEMAS =====
class ConfigResponse(BaseModel):
    config: Dict[str, Any]
    db_path: str
    db_exists: bool
    ai_status: str
    model: str
    timezone: str
    ai_providers: Optional[Dict[str, Any]] = None

class StatsResponse(BaseModel):
    conversations: int
    messages: int
    messages_by_sender: Dict[str, int]
    latest_conversation: Optional[Dict[str, Any]]
    db_path: str
    ai_status: str
    ai_providers: Optional[Dict[str, Any]] = None
    voice_stats: Optional[Dict[str, Any]] = None  # NEW: Voice usage stats

# Generic API Response
class APIResponse(BaseModel):
    message: str
    status: Optional[str] = "success"
    data: Optional[Dict[str, Any]] = None

# ===== DEBUG SCHEMAS =====
class DebugConversationResponse(BaseModel):
    conversation_id: int
    title: str
    started_at: str
    message_count: int
    messages: List[MessageOut]
    ai_provider_stats: Optional[Dict[str, Any]] = None
    voice_usage_stats: Optional[Dict[str, Any]] = None  # NEW: Voice stats per conversation

class DebugAllConversationsResponse(BaseModel):
    total_conversations: int
    conversations: List[ConversationOut]
    total_messages: int
    ai_provider_stats: Optional[Dict[str, Any]] = None
    voice_usage_stats: Optional[Dict[str, Any]] = None  # NEW: Overall voice stats

# ===== ENHANCED MESSAGE SCHEMAS WITH VOICE =====
class EnhancedMessageIn(MessageIn):
    """Enhanced message input with voice metadata"""
    voice_metadata: Optional[VoiceMessageMetadata] = None

class EnhancedMessageOut(MessageOut):
    """Enhanced message output with voice metadata"""
    voice_metadata: Optional[VoiceMessageMetadata] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None

class EnhancedChatResponse(ChatResponse):
    """Enhanced chat response with voice support"""
    voice_metadata: Optional[VoiceMessageMetadata] = None
    has_audio_response: bool = False

# ===== HEALTH CHECK SCHEMAS =====
class HealthCheckResponse(BaseModel):
    message: str
    status: str
    data: Dict[str, Any]
    voice_health: Optional[Dict[str, Any]] = None  # NEW: Voice service health

# ===== VOICE ANALYTICS SCHEMAS =====
class VoiceUsageStats(BaseModel):
    total_voice_messages: int = 0
    total_audio_duration: float = 0.0
    average_message_duration: float = 0.0
    most_used_language: str = "vi-VN"
    transcription_accuracy: float = 0.0
    tts_usage_count: int = 0
    voice_errors: int = 0

class VoiceAnalytics(BaseModel):
    daily_stats: VoiceUsageStats
    weekly_stats: VoiceUsageStats
    monthly_stats: VoiceUsageStats
    language_distribution: Dict[str, int]
    error_rate: float
    popular_voices: List[Dict[str, Any]]

# ===== ERROR SCHEMAS =====
class VoiceError(BaseModel):
    error_type: str  # "transcription", "tts", "audio_processing", "unsupported_format"
    error_message: str
    error_code: Optional[str] = None
    timestamp: str
    audio_info: Optional[Dict[str, Any]] = None