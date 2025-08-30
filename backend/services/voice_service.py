# services/voice_service.py - Fixed Voice Service Implementation
import asyncio
import logging
import io
import tempfile
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import speech_recognition as sr
import pyttsx3
from pydub import AudioSegment
import threading
import queue
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class VoiceService:
    """Complete service for handling voice transcription and text-to-speech"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.tts_engine = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._vosk_model = None  # Cache for Vosk model
        self._initialize_tts()
        self._configure_recognizer()
    
    def _initialize_tts(self):
        """Initialize text-to-speech engine with Vietnamese support"""
        try:
            self.tts_engine = pyttsx3.init()
            
            # Get available voices
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Try to find Vietnamese voice
                vietnamese_voice = None
                for voice in voices:
                    voice_name = voice.name.lower()
                    voice_id = voice.id.lower()
                    if any(keyword in voice_name or keyword in voice_id 
                          for keyword in ['vietnamese', 'vietnam', 'vi-vn', 'linh']):
                        vietnamese_voice = voice
                        break
                
                if vietnamese_voice:
                    self.tts_engine.setProperty('voice', vietnamese_voice.id)
                    logger.info(f"Using Vietnamese voice: {vietnamese_voice.name}")
                else:
                    # Use first available voice
                    self.tts_engine.setProperty('voice', voices[0].id)
                    logger.info(f"Using default voice: {voices[0].name}")
            
            # Configure TTS settings for Vietnamese
            self.tts_engine.setProperty('rate', 150)  # Speaking rate
            self.tts_engine.setProperty('volume', 0.9)  # Volume level
            
            logger.info("TTS engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.tts_engine = None
    
    def _configure_recognizer(self):
        """Configure speech recognizer for better Vietnamese recognition"""
        try:
            # Adjust recognizer settings for Vietnamese
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            self.recognizer.operation_timeout = None
            self.recognizer.phrase_threshold = 0.3
            self.recognizer.non_speaking_duration = 0.8
            
            logger.info("Speech recognizer configured for Vietnamese")
            
        except Exception as e:
            logger.error(f"Error configuring recognizer: {e}")
    
    async def transcribe_audio(
        self, 
        audio_data: bytes, 
        language: str = "vi-VN",
        conversation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio data to text using speech recognition
        """
        try:
            logger.info(f"Transcribing audio: {len(audio_data)} bytes, language: {language}")
            
            # Create temporary file for audio processing
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
                
                try:
                    # Convert audio to proper format
                    await self._convert_audio_format(audio_data, temp_path)
                    
                    # Perform speech recognition
                    text = await self._recognize_speech_from_file(temp_path, language)
                    
                    # Clean up transcript
                    text = self._clean_transcript(text)
                    
                    logger.info(f"Transcription successful: '{text[:100]}{'...' if len(text) > 100 else ''}'")
                    
                    result = {
                        "text": text,
                        "language": language,
                        "confidence": 0.9,  # Placeholder - could be improved with confidence scoring
                        "timestamp": datetime.now().isoformat(),
                        "conversation_id": conversation_id,
                        "word_count": len(text.split()) if text else 0,
                        "duration_estimate": len(audio_data) / 16000  # Rough estimate
                    }
                    
                    return result
                    
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                        
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {
                "text": "",
                "language": language,
                "confidence": 0.0,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "conversation_id": conversation_id,
                "word_count": 0,
                "duration_estimate": 0
            }
    
    async def _convert_audio_format(self, audio_data: bytes, output_path: str):
        """Convert audio to WAV format suitable for speech recognition"""
        def convert_sync():
            try:
                # Load audio from bytes with robust format fallback
                audio_segment = None
                load_errors = []
                
                # Try different formats in order of likelihood
                formats_to_try = [None, 'webm', 'ogg', 'mp3', 'm4a', 'wav', 'flac']
                
                for fmt in formats_to_try:
                    try:
                        if fmt:
                            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format=fmt)
                        else:
                            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
                        logger.info(f"Successfully loaded audio as {fmt or 'auto-detected'} format")
                        break
                    except Exception as e:
                        load_errors.append(f"{fmt or 'auto'}: {str(e)[:100]}")
                        continue
                
                if audio_segment is None:
                    logger.error(f"Audio conversion failed. Tried formats: {load_errors}")
                    raise Exception("Unsupported audio format. Ensure ffmpeg is installed and audio is valid.")
                
                # Log original audio info
                logger.info(f"Original audio: {len(audio_segment)}ms, {audio_segment.frame_rate}Hz, {audio_segment.channels} channels, {audio_segment.dBFS:.1f}dBFS")
                
                # Check if audio has any content (not just silence)
                if audio_segment.dBFS < -50:
                    logger.warning(f"Audio very quiet ({audio_segment.dBFS:.1f}dBFS), may be mostly silence")
                
                # Apply preprocessing for better speech recognition
                if len(audio_segment) > 200:  # Only for audio > 0.2 seconds
                    try:
                        # Remove silence from beginning and end
                        audio_segment = audio_segment.strip_silence(
                            silence_thresh=audio_segment.dBFS - 20,  # 20dB below average
                            silence_len=300,  # 300ms of silence
                            padding=100       # Keep 100ms padding
                        )
                        logger.info(f"After silence removal: {len(audio_segment)}ms")
                        
                        # Normalize audio levels (important for recognition)
                        audio_segment = audio_segment.normalize()
                        
                        # Apply gentle compression to even out volume levels
                        # This helps with varying speech volumes
                        audio_segment = audio_segment.compress_dynamic_range(
                            threshold=-20.0,  # dBFS
                            ratio=2.0,        # 2:1 compression
                            attack=5.0,       # 5ms attack
                            release=50.0      # 50ms release
                        )
                        
                    except Exception as process_err:
                        logger.warning(f"Audio preprocessing failed, using raw audio: {process_err}")
                
                # Convert to format suitable for speech recognition
                # CRITICAL: Ensure exactly 16kHz, mono, 16-bit PCM
                original_channels = audio_segment.channels
                audio_segment = (audio_segment
                               .set_frame_rate(16000)
                               .set_channels(1)      # FORCE mono
                               .set_sample_width(2)) # FORCE 16-bit
                
                logger.info(f"Format conversion: {original_channels} channels → 1 channel, final: {len(audio_segment)}ms")
                
                # Ensure minimum duration for speech recognition
                if len(audio_segment) < 300:  # Less than 0.3 seconds
                    logger.warning(f"Audio very short ({len(audio_segment)}ms), padding to 500ms")
                    # Pad with silence to minimum duration
                    silence_pad = AudioSegment.silent(duration=500 - len(audio_segment))
                    audio_segment = audio_segment + silence_pad
                
                # Final quality check
                if len(audio_segment) == 0:
                    raise Exception("Audio segment is empty after processing")
                
                # Export to WAV file with specific parameters for speech recognition
                audio_segment.export(
                    output_path, 
                    format="wav",
                    parameters=[
                        "-acodec", "pcm_s16le",  # 16-bit PCM
                        "-ar", "16000",          # 16kHz sample rate
                        "-ac", "1"               # Mono
                    ]
                )
                
                # Verify the exported file
                import wave
                with wave.open(output_path, 'rb') as wf:
                    logger.info(f"Final WAV: {wf.getnframes()} frames, {wf.getframerate()}Hz, {wf.getnchannels()} channels, {wf.getsampwidth()*8}-bit")
                
                logger.info(f"✅ Audio converted successfully for STT: {len(audio_segment)}ms")
                
            except Exception as e:
                logger.error(f"Audio conversion failed: {e}")
                raise
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, convert_sync)
    
    async def _recognize_speech_from_file(self, file_path: str, language: str) -> str:
        """Recognize speech from audio file using multiple providers with better error handling"""
        def recognize_sync():
            try:
                # Load audio file
                with sr.AudioFile(file_path) as source:
                    # Adjust for ambient noise with shorter duration for responsiveness
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                    # Record the audio
                    audio = self.recognizer.record(source)

                # Validate audio duration
                try:
                    import wave
                    with wave.open(file_path, "rb") as wf:
                        frames = wf.getnframes()
                        rate = wf.getframerate() or 16000
                        duration_sec = frames / float(rate)
                        logger.info(f"Audio duration for STT: {duration_sec:.3f}s @ {rate}Hz")
                        
                        if duration_sec < 0.3:
                            logger.warning("Audio very short, but proceeding with recognition")
                        elif duration_sec > 30:
                            logger.warning("Audio very long, may timeout")
                            
                except Exception as dur_err:
                    logger.warning(f"Could not validate audio duration: {dur_err}")
                
                recognition_results = []
                
                # 1. Try Google Speech Recognition first (best for Vietnamese)
                try:
                    # Increase timeout for Google API
                    text = self.recognizer.recognize_google(
                        audio, 
                        language=language,
                        show_all=False  # Get best result only
                    )
                    if text and text.strip():
                        logger.info("✅ Google Speech Recognition succeeded")
                        return text.strip()
                    else:
                        logger.warning("Google returned empty transcript")
                        
                except sr.UnknownValueError:
                    logger.warning("❌ Google Speech Recognition could not understand audio")
                    recognition_results.append("Google: Could not understand audio")
                    
                except sr.RequestError as e:
                    logger.warning(f"❌ Google Speech Recognition request failed: {e}")
                    recognition_results.append(f"Google: Request error - {e}")
                    
                except Exception as e:
                    logger.warning(f"❌ Google Speech Recognition unexpected error: {e}")
                    recognition_results.append(f"Google: Unexpected error - {e}")
                
                # 2. Try Vosk (offline) if available
                try:
                    vosk_result = self._try_vosk_recognition(file_path, language)
                    if vosk_result and vosk_result.strip():
                        logger.info("✅ Vosk Speech Recognition succeeded")
                        return vosk_result.strip()
                    else:
                        logger.warning("Vosk returned empty transcript")
                        recognition_results.append("Vosk: Empty transcript")
                        
                except Exception as e:
                    logger.warning(f"❌ Vosk Speech Recognition failed: {e}")
                    recognition_results.append(f"Vosk: {str(e)[:100]}")
                
                # 3. Try Sphinx as last resort (English only)
                try:
                    if language.startswith('en'):
                        text = self.recognizer.recognize_sphinx(audio)
                        if text and text.strip():
                            logger.info("✅ Sphinx Speech Recognition succeeded")
                            return text.strip()
                        else:
                            logger.warning("Sphinx returned empty transcript")
                            recognition_results.append("Sphinx: Empty transcript")
                    else:
                        recognition_results.append("Sphinx: Not available for non-English")
                        
                except sr.UnknownValueError:
                    logger.warning("❌ Sphinx could not understand audio")
                    recognition_results.append("Sphinx: Could not understand audio")
                    
                except sr.RequestError as e:
                    logger.warning(f"❌ Sphinx request failed: {e}")
                    recognition_results.append(f"Sphinx: Request error - {e}")
                    
                except Exception as e:
                    logger.warning(f"❌ Sphinx unexpected error: {e}")
                    recognition_results.append(f"Sphinx: Unexpected error - {e}")
                
                # 4. If all failed, provide detailed error
                error_summary = " | ".join(recognition_results)
                logger.error(f"All speech recognition methods failed: {error_summary}")
                
                # Try to give helpful error message
                if "Could not understand audio" in error_summary:
                    raise Exception("Audio không thể nhận diện được. Hãy thử nói rõ hơn hoặc ghi âm lại.")
                elif "Request error" in error_summary:
                    raise Exception("Lỗi kết nối dịch vụ nhận diện giọng nói. Kiểm tra kết nối internet.")
                else:
                    raise Exception(f"Tất cả dịch vụ nhận diện giọng nói đều thất bại: {error_summary}")
                
            except Exception as e:
                logger.error(f"Speech recognition error: {e}")
                raise
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, recognize_sync)
    
    def _try_vosk_recognition(self, file_path: str, language: str) -> str:
        """Try Vosk recognition with better error handling"""
        try:
            import json
            import wave
            
            # Try to import Vosk
            try:
                from vosk import Model, KaldiRecognizer
            except ImportError:
                raise Exception("Vosk not installed. Install with: pip install vosk")
            
            # Determine model path based on language
            model_paths = {
                "vi-VN": ["/app/data/models/vosk-vi", "./data/models/vosk-vi", "./models/vosk-model-vi", "vosk-model-vi-0.4"],
                "en-US": ["/app/data/models/vosk-en", "./data/models/vosk-en", "./models/vosk-model-en-us", "vosk-model-en-us-0.22"],
                "en-GB": ["/app/data/models/vosk-en", "./data/models/vosk-en", "./models/vosk-model-en-us", "vosk-model-en-us-0.22"]
            }
            
            # Get model paths for the language (default to Vietnamese)
            lang_key = language if language in model_paths else "vi-VN"
            paths_to_try = model_paths.get(lang_key, model_paths["vi-VN"])
            
            # Add environment variable path
            env_path = os.environ.get("VOSK_MODEL_PATH")
            if env_path:
                paths_to_try.insert(0, env_path)
            
            # Find available model
            model_path = None
            for path in paths_to_try:
                if os.path.isdir(path):
                    model_path = path
                    break
            
            if not model_path:
                raise Exception(f"Vosk model not found. Tried paths: {paths_to_try}")
            
            # Load model (cache it to avoid reload cost)
            if not hasattr(self, '_vosk_model') or self._vosk_model is None:
                logger.info(f"Loading Vosk model from: {model_path}")
                self._vosk_model = Model(model_path)
                logger.info("Vosk model loaded successfully")

            # Validate and process audio file
            with wave.open(file_path, "rb") as wf:
                # Get audio parameters
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                frame_rate = wf.getframerate()
                frames = wf.getnframes()
                duration = frames / frame_rate
                
                logger.info(f"Vosk input audio: {duration:.2f}s, {frame_rate}Hz, {channels}ch, {sample_width*8}bit")
                
                # Vosk requirements validation
                if channels != 1:
                    raise Exception(f"Vosk requires mono audio (1 channel), got {channels} channels. Audio conversion failed.")
                if sample_width != 2:
                    logger.warning(f"Vosk expects 16-bit audio, got {sample_width * 8}-bit")
                if frame_rate not in [8000, 16000, 44100, 48000]:
                    logger.warning(f"Vosk may not work optimally with {frame_rate}Hz sample rate")
                
                # Create recognizer with appropriate settings
                rec = KaldiRecognizer(self._vosk_model, frame_rate)
                rec.SetWords(True)  # Enable word-level info
                rec.SetPartialWords(True)  # Enable partial word results
                
                # Store all recognition results
                final_results = []
                partial_results = []
                word_results = []
                
                # Process audio in smaller chunks for better responsiveness
                chunk_size = int(frame_rate * 0.1)  # 100ms chunks
                total_processed = 0
                
                logger.info(f"Processing audio in {chunk_size} frame chunks...")
                
                while True:
                    data = wf.readframes(chunk_size)
                    if len(data) == 0:
                        break
                    
                    total_processed += len(data) // (channels * sample_width)
                    
                    if rec.AcceptWaveform(data):
                        # Final result for this chunk
                        result = json.loads(rec.Result())
                        if result.get("text"):
                            final_results.append(result["text"])
                            logger.debug(f"Vosk final chunk: '{result['text']}'")
                            
                        # Extract word-level results if available
                        if result.get("result"):
                            for word_info in result["result"]:
                                if word_info.get("word"):
                                    word_results.append(word_info["word"])
                    else:
                        # Collect partial results
                        partial = json.loads(rec.PartialResult())
                        if partial.get("partial"):
                            partial_results.append(partial["partial"])
                            logger.debug(f"Vosk partial: '{partial['partial']}'")
                
                # Get final result from remaining audio
                final_result = json.loads(rec.FinalResult())
                if final_result.get("text"):
                    final_results.append(final_result["text"])
                    logger.debug(f"Vosk final end: '{final_result['text']}'")
                
                # Compile results with priority: final > words > partial
                result_text = ""
                
                if final_results:
                    # Use final results (highest confidence)
                    result_text = " ".join(final_results).strip()
                    logger.info(f"✅ Using Vosk final results: '{result_text}'")
                    
                elif word_results:
                    # Use word-level results
                    result_text = " ".join(word_results).strip()
                    logger.info(f"✅ Using Vosk word results: '{result_text}'")
                    
                elif partial_results:
                    # Use partial results as last resort
                    # Take the longest partial result
                    longest_partial = max(partial_results, key=len) if partial_results else ""
                    result_text = longest_partial.strip()
                    logger.info(f"⚠️ Using Vosk partial result: '{result_text}'")
                
                # Log processing stats
                processed_duration = total_processed / frame_rate
                logger.info(f"Vosk processed {processed_duration:.2f}s of {duration:.2f}s audio")
                logger.info(f"Vosk results: {len(final_results)} final, {len(word_results)} words, {len(partial_results)} partial")
                
                # Validate result
                if not result_text or len(result_text.strip()) == 0:
                    raise Exception("Vosk produced empty transcript - audio may not contain recognizable speech")
                
                return result_text
                
        except Exception as e:
            logger.error(f"Vosk recognition failed: {e}")
            raise
    
    def _clean_transcript(self, text: str) -> str:
        """Clean and format transcribed text"""
        if not text:
            return ""
        
        # Basic cleaning
        text = text.strip()
        
        # Remove multiple spaces
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # Vietnamese-specific cleaning
        vietnamese_corrections = {
            # Common transcription errors for Vietnamese
            "chào bạn": "chào bạn",
            "xin chào": "xin chào", 
            "cảm ơn": "cảm ơn",
            "tạm biệt": "tạm biệt",
            "làm ơn": "làm ơn",
            "xin lỗi": "xin lỗi"
        }
        
        # Apply corrections (case-insensitive)
        text_lower = text.lower()
        for wrong, correct in vietnamese_corrections.items():
            if wrong in text_lower:
                # Preserve original case pattern
                text = re.sub(re.escape(wrong), correct, text, flags=re.IGNORECASE)
        
        return text
    
    async def text_to_speech(
        self,
        text: str,
        language: str = "vi-VN",
        voice: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 1.0
    ) -> bytes:
        """
        Convert text to speech audio
        """
        try:
            if not self.tts_engine:
                raise Exception("TTS engine not available")
            
            logger.info(f"Converting text to speech: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            
            def generate_speech():
                try:
                    # Configure voice settings
                    if voice:
                        try:
                            self.tts_engine.setProperty('voice', voice)
                        except Exception as ve:
                            logger.warning(f"Voice {voice} not available: {ve}, using default")
                    
                    # Adjust speed (rate)
                    base_rate = 150
                    new_rate = int(base_rate * speed)
                    new_rate = max(50, min(300, new_rate))  # Clamp to valid range
                    self.tts_engine.setProperty('rate', new_rate)
                    
                    # Create temporary file for audio output
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                        temp_path = temp_file.name
                    
                    try:
                        # Generate speech
                        self.tts_engine.save_to_file(text, temp_path)
                        self.tts_engine.runAndWait()
                        
                        # Verify file was created
                        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                            raise Exception("TTS engine failed to generate audio file")
                        
                        # Read generated audio
                        with open(temp_path, 'rb') as f:
                            audio_data = f.read()
                        
                        if len(audio_data) == 0:
                            raise Exception("Generated audio file is empty")
                        
                        return audio_data
                        
                    finally:
                        # Clean up temporary file
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                            
                except Exception as e:
                    logger.error(f"TTS generation failed: {e}")
                    raise
            
            # Run in thread pool
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(self.executor, generate_speech)
            
            logger.info(f"TTS completed: {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            logger.error(f"Text-to-speech failed: {e}")
            raise Exception(f"TTS generation failed: {str(e)}")
    
    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available TTS voices"""
        try:
            if not self.tts_engine:
                return []
            
            def get_voices_sync():
                voices = self.tts_engine.getProperty('voices')
                voice_list = []
                
                for voice in voices:
                    voice_info = {
                        "id": voice.id,
                        "name": voice.name,
                        "languages": getattr(voice, 'languages', []),
                        "gender": getattr(voice, 'gender', 'unknown'),
                        "age": getattr(voice, 'age', 'unknown'),
                        "is_vietnamese": any(keyword in voice.name.lower() 
                                           for keyword in ['vietnamese', 'vietnam', 'vi-vn', 'linh'])
                    }
                    voice_list.append(voice_info)
                
                return voice_list
            
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.executor, get_voices_sync)
            
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if voice service is available"""
        try:
            # Check if basic speech recognition is available
            if not self.recognizer:
                return False
            
            # Check if at least one recognition method is available
            has_google_sr = True  # Google Speech Recognition is usually available
            
            # Check Vosk availability
            has_vosk = False
            try:
                import vosk
                model_paths = ["/app/data/models/vosk-vi", "./data/models/vosk-vi"]
                env_path = os.environ.get("VOSK_MODEL_PATH")
                if env_path:
                    model_paths.insert(0, env_path)
                has_vosk = any(os.path.isdir(path) for path in model_paths)
            except ImportError:
                has_vosk = False
            
            # Service is available if we have at least one recognition method
            return has_google_sr or has_vosk
            
        except Exception as e:
            logger.error(f"Error checking voice service availability: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get voice service status"""
        try:
            # Check Vosk availability
            vosk_available = False
            vosk_model_path = None
            try:
                import vosk
                model_paths = ["/app/data/models/vosk-vi", "./data/models/vosk-vi"]
                env_path = os.environ.get("VOSK_MODEL_PATH")
                if env_path:
                    model_paths.insert(0, env_path)
                
                for path in model_paths:
                    if os.path.isdir(path):
                        vosk_available = True
                        vosk_model_path = path
                        break
            except ImportError:
                vosk_available = False
            
            return {
                "vosk_available": vosk_available,
                "vosk_model_path": vosk_model_path,
                "tts_available": self.tts_engine is not None,
                "speech_recognition_available": self.recognizer is not None,
                "google_sr_available": True,
                "fallback_mode": not self.is_available(),
                "message": "Voice features available" if self.is_available() else "Voice features not available - text chat only"
            }
        except Exception as e:
            logger.error(f"Error getting voice status: {e}")
            return {
                "vosk_available": False,
                "fallback_mode": True,
                "error": str(e),
                "message": "Voice features not available - text chat only"
            }
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages"""
        return [
            {"code": "vi-VN", "name": "Tiếng Việt", "country": "Vietnam"},
            {"code": "en-US", "name": "English", "country": "United States"},
            {"code": "en-GB", "name": "English", "country": "United Kingdom"},
            {"code": "ja-JP", "name": "日本語", "country": "Japan"},
            {"code": "ko-KR", "name": "한국어", "country": "South Korea"},
            {"code": "zh-CN", "name": "中文 (简体)", "country": "China"},
            {"code": "zh-TW", "name": "中文 (繁體)", "country": "Taiwan"},
            {"code": "th-TH", "name": "ไทย", "country": "Thailand"},
            {"code": "id-ID", "name": "Bahasa Indonesia", "country": "Indonesia"},
            {"code": "ms-MY", "name": "Bahasa Melayu", "country": "Malaysia"}
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check voice service health"""
        health_status = {
            "status": "healthy",
            "tts_available": self.tts_engine is not None,
            "speech_recognition_available": True,
            "supported_languages": len(self.get_supported_languages()),
            "available_voices": len(await self.get_available_voices()),
            "timestamp": datetime.now().isoformat(),
            "vosk_available": False,
            "google_sr_available": True
        }
        
        # Test Vosk availability
        try:
            import vosk
            # Try to find a model
            model_paths = ["./data/models/vosk-vi", "./models/vosk-model-vi"]
            env_path = os.environ.get("VOSK_MODEL_PATH")
            if env_path:
                model_paths.insert(0, env_path)
            
            vosk_model_found = any(os.path.isdir(path) for path in model_paths)
            health_status["vosk_available"] = vosk_model_found
            health_status["vosk_model_paths"] = model_paths
            
        except ImportError:
            health_status["vosk_available"] = False
            health_status["vosk_error"] = "Vosk not installed"
        
        # Test TTS
        try:
            if self.tts_engine:
                test_audio = await self.text_to_speech("Test", speed=2.0)
                health_status["tts_test"] = "passed"
                health_status["tts_test_size"] = len(test_audio)
            else:
                health_status["tts_test"] = "failed - engine not available"
        except Exception as e:
            health_status["tts_test"] = f"failed: {str(e)}"
        
        # Test Speech Recognition availability
        try:
            health_status["sr_test"] = "available" if self.recognizer else "unavailable"
        except Exception as e:
            health_status["sr_test"] = f"failed: {str(e)}"
        
        # Overall status
        if not health_status["tts_available"] and not health_status["speech_recognition_available"]:
            health_status["status"] = "unhealthy"
        elif not health_status["tts_available"] or not health_status["speech_recognition_available"]:
            health_status["status"] = "degraded"
        
        return health_status
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.tts_engine:
                self.tts_engine.stop()
            if hasattr(self, '_vosk_model'):
                self._vosk_model = None
            self.executor.shutdown(wait=True)
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Global voice service instance
voice_service = VoiceService()