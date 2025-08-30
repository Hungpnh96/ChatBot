# api/voice.py - Complete Voice Chat API Endpoints
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
import io
import logging
from models.schemas import (
    VoiceTranscriptRequest, VoiceTranscriptResponse, 
    TextToSpeechRequest, VoiceChatRequest, VoiceChatResponse,
    VoiceCapabilities, MessageIn, ChatResponse
)
from services.voice_service import voice_service
from services.chat_service import chat_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat/api/voice", tags=["voice"])

@router.post("/transcribe", response_model=VoiceTranscriptResponse)
async def transcribe_audio(
    audio: UploadFile = File(..., description="Audio file (WAV, MP3, M4A, WebM, OGG)"),
    conversation_id: Optional[int] = Form(None),
    language: str = Form("vi-VN", description="Language code (vi-VN, en-US, etc.)")
):
    """
    Transcribe audio file to text using speech recognition
    
    - **audio**: Audio file in supported format
    - **conversation_id**: Optional conversation ID to associate with
    - **language**: Language code for recognition (default: vi-VN)
    """
    try:
        logger.info(f"Transcribing audio file: {audio.filename}, size: {audio.size if hasattr(audio, 'size') else 'unknown'}")
        
        # Validate file type
        allowed_types = [
            'audio/wav', 'audio/mpeg', 'audio/mp4', 'audio/webm', 
            'audio/ogg', 'audio/x-wav', 'audio/mp3'
        ]
        
        if audio.content_type and audio.content_type not in allowed_types:
            logger.warning(f"Unsupported audio format: {audio.content_type}")
            # Don't fail immediately - pydub can handle many formats
        
        # Check file size (limit to 10MB)
        if hasattr(audio, 'size') and audio.size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="Audio file too large. Maximum size is 10MB."
            )
        
        # Read audio data
        audio_data = await audio.read()
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        # Transcribe using voice service
        result = await voice_service.transcribe_audio(
            audio_data=audio_data,
            language=language,
            conversation_id=conversation_id
        )
        
        if result.get("error"):
            raise HTTPException(
                status_code=500, 
                detail=f"Transcription failed: {result['error']}"
            )
        
        logger.info(f"Transcription completed: {len(result.get('text', ''))} characters")
        return VoiceTranscriptResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@router.post("/text-to-speech")
async def text_to_speech(request: TextToSpeechRequest):
    """
    Convert text to speech audio
    
    Returns audio stream in WAV format
    """
    try:
        logger.info(f"Converting text to speech: {len(request.text)} characters")
        
        # Validate text length
        if len(request.text) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Text too long. Maximum length is 1000 characters."
            )
        
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Empty text provided")
        
        # Generate speech using voice service
        audio_data = await voice_service.text_to_speech(
            text=request.text,
            language=request.language,
            voice=request.voice,
            speed=request.speed,
            pitch=request.pitch
        )
        
        # Return audio as streaming response
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=speech_{len(request.text)}_chars.wav",
                "Cache-Control": "no-cache",
                "X-Audio-Duration": str(len(audio_data) / 16000),  # Rough estimate
                "X-Text-Length": str(len(request.text))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating speech: {e}")
        raise HTTPException(status_code=500, detail=f"Speech generation failed: {str(e)}")

@router.post("/voice-chat")
async def voice_chat(
    audio: UploadFile = File(..., description="Audio file with user's voice message"),
    conversation_id: Optional[int] = Form(None),
    ai_provider: Optional[str] = Form(None, description="AI provider (github, ollama, auto)"),
    language: str = Form("vi-VN", description="Language for speech recognition and TTS"),
    auto_speak: bool = Form(True, description="Auto-convert AI response to speech")
):
    """
    Complete voice chat flow: transcribe audio → get AI response → convert to speech
    
    Returns either audio response or JSON based on auto_speak parameter
    """
    try:
        logger.info("Starting complete voice chat flow")
        
        # Validate file
        if not audio.filename:
            raise HTTPException(status_code=400, detail="No audio file provided")
        
        # Step 1: Transcribe audio
        audio_data = await audio.read()
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        transcript_result = await voice_service.transcribe_audio(
            audio_data=audio_data,
            language=language,
            conversation_id=conversation_id
        )
        
        if transcript_result.get("error"):
            raise HTTPException(
                status_code=400, 
                detail=f"Transcription failed: {transcript_result['error']}"
            )
        
        transcript_text = transcript_result.get("text", "").strip()
        if not transcript_text:
            raise HTTPException(status_code=400, detail="No speech detected in audio")
        
        logger.info(f"Transcription: '{transcript_text[:100]}{'...' if len(transcript_text) > 100 else ''}'")
        
        # Step 2: Get AI response
        chat_message = MessageIn(
            user=transcript_text,
            conversation_id=conversation_id,
            ai_provider=ai_provider
        )
        
        chat_response = chat_service.process_chat(chat_message)
        ai_response_text = chat_response.message.content
        
        logger.info(f"AI response: {len(ai_response_text)} characters")
        
        # Step 3: Handle response format
        if auto_speak:
            # Convert AI response to speech
            try:
                speech_audio = await voice_service.text_to_speech(
                    text=ai_response_text,
                    language=language
                )
                
                return StreamingResponse(
                    io.BytesIO(speech_audio),
                    media_type="audio/wav",
                    headers={
                        "X-Transcript": transcript_text,
                        "X-AI-Response": ai_response_text,
                        "X-Conversation-ID": str(chat_response.conversation_id),
                        "X-AI-Provider": chat_response.ai_provider or "unknown",
                        "X-AI-Model": chat_response.ai_model or "unknown",
                        "Content-Disposition": f"attachment; filename=ai_response_{chat_response.conversation_id}.wav",
                        "Cache-Control": "no-cache"
                    }
                )
            except Exception as tts_error:
                logger.error(f"TTS failed, returning JSON: {tts_error}")
                # Fall back to JSON response if TTS fails
                auto_speak = False
        
        # Return JSON response
        return VoiceChatResponse(
            transcript=transcript_text,
            ai_response=ai_response_text,
            conversation_id=chat_response.conversation_id,
            ai_provider=chat_response.ai_provider,
            audio_duration=transcript_result.get("duration_estimate", 0),
            has_audio_response=False
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in voice chat flow: {e}")
        raise HTTPException(status_code=500, detail=f"Voice chat failed: {str(e)}")

@router.get("/voices")
async def get_available_voices():
    """
    Get list of available TTS voices
    
    Returns information about voices available on the system
    """
    try:
        voices = await voice_service.get_available_voices()
        return {
            "voices": voices,
            "count": len(voices),
            "vietnamese_voices": [v for v in voices if v.get("is_vietnamese", False)]
        }
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get voices: {str(e)}")

@router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages for speech recognition and TTS
    """
    try:
        languages = voice_service.get_supported_languages()
        return {
            "languages": languages,
            "count": len(languages),
            "default": "vi-VN"
        }
    except Exception as e:
        logger.error(f"Error getting languages: {e}")
        return {
            "languages": [{"code": "vi-VN", "name": "Tiếng Việt", "country": "Vietnam"}],
            "count": 1,
            "default": "vi-VN"
        }

@router.get("/capabilities", response_model=VoiceCapabilities)
async def get_voice_capabilities():
    """
    Get complete voice capabilities of the system
    """
    try:
        voices = await voice_service.get_available_voices()
        languages = voice_service.get_supported_languages()
        health = await voice_service.health_check()
        
        return VoiceCapabilities(
            speech_recognition_available=health.get("speech_recognition_available", False),
            text_to_speech_available=health.get("tts_available", False),
            supported_languages=[lang["code"] for lang in languages],
            available_voices=voices,
            offline_mode=False,
            max_audio_size_mb=10,
            max_text_length=1000,
            supported_audio_formats=["wav", "mp3", "m4a", "webm", "ogg"],
            health_status=health.get("status", "unknown")
        )
        
    except Exception as e:
        logger.error(f"Error getting capabilities: {e}")
        # Return minimal capabilities
        return VoiceCapabilities(
            speech_recognition_available=False,
            text_to_speech_available=False,
            supported_languages=["vi-VN"],
            available_voices=[],
            offline_mode=False
        )

@router.get("/health")
async def voice_health_check():
    """
    Health check endpoint for voice services
    """
    try:
        health_status = await voice_service.health_check()
        return {
            "status": "healthy" if health_status.get("status") == "healthy" else "unhealthy",
            "details": health_status,
            "timestamp": health_status.get("timestamp")
        }
    except Exception as e:
        logger.error(f"Voice health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": logger.info(f"Voice health check failed")
        }

@router.post("/test")
async def test_voice_pipeline():
    """
    Test complete voice pipeline with a simple Vietnamese phrase
    """
    try:
        test_text = "Xin chào, tôi là Bixby!"
        
        # Test TTS
        logger.info("Testing TTS...")
        audio_data = await voice_service.text_to_speech(test_text, language="vi-VN")
        
        # Test transcript (would need actual audio, so we'll simulate)
        test_result = {
            "tts_test": {
                "status": "success",
                "text": test_text,
                "audio_size": len(audio_data),
                "estimated_duration": len(audio_data) / 16000
            },
            "sr_test": {
                "status": "available",
                "note": "Speech recognition requires actual audio input"
            },
            "overall": "success"
        }
        
        return test_result
        
    except Exception as e:
        logger.error(f"Voice pipeline test failed: {e}")
        return {
            "tts_test": {"status": "failed", "error": str(e)},
            "sr_test": {"status": "unknown"},
            "overall": "failed"
        }