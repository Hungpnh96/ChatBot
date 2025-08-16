// hooks/useVoiceChat.ts - Complete Voice Chat Hook
import { useState, useRef, useCallback, useEffect } from 'react';
import 'styled-jsx';

// --- Declare SpeechRecognition interfaces trực tiếp (không dùng declare global) ---

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  start(): void;
  stop(): void;
  abort(): void;
  onstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => any) | null;
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
  onspeechstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onspeechend: ((this: SpeechRecognition, ev: Event) => any) | null;
}

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message: string;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

// --- Hook interfaces ---

interface VoiceConfig {
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
  maxDuration?: number; // Maximum recording duration in seconds
  autoStop?: boolean; // Auto stop on silence
}

interface VoiceState {
  isListening: boolean;
  isSupported: boolean;
  transcript: string;
  interimTranscript: string;
  error: string | null;
  confidence: number;
  isProcessing: boolean;
}

interface SpeechSynthesisOptions {
  rate?: number;
  pitch?: number;
  volume?: number;
  voice?: SpeechSynthesisVoice;
}

export const useVoiceChat = (config: VoiceConfig = {}) => {
  const {
    language = 'vi-VN',
    continuous = false,
    interimResults = true,
    maxDuration = 30,
    autoStop = true
  } = config;

  const [voiceState, setVoiceState] = useState<VoiceState>({
    isListening: false,
    isSupported: false,
    transcript: '',
    interimTranscript: '',
    error: null,
    confidence: 0,
    isProcessing: false
  });

  const [isSpeaking, setIsSpeaking] = useState(false);
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const synthesisRef = useRef<SpeechSynthesis | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const silenceTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognitionConstructor = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

      if (SpeechRecognitionConstructor) {
        const recognition = new SpeechRecognitionConstructor() as SpeechRecognition;
        recognition.continuous = continuous;
        recognition.interimResults = interimResults;
        recognition.lang = language;
        recognition.maxAlternatives = 1;

        recognition.onstart = () => {
          console.log('🎤 Speech recognition started');
          setVoiceState(prev => ({
            ...prev,
            isListening: true,
            error: null,
            isProcessing: false
          }));

          if (maxDuration > 0) {
            timeoutRef.current = setTimeout(() => {
              console.log('⏰ Maximum duration reached, stopping recognition');
              recognition.stop();
            }, maxDuration * 1000);
          }
        };

        recognition.onresult = (event) => {
          let finalTranscript = '';
          let interimTranscript = '';
          let confidence = 0;

          for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            const transcript = result[0].transcript;
            confidence = Math.max(confidence, result[0].confidence);

            if (result.isFinal) {
              finalTranscript += transcript;
              console.log('✅ Final transcript:', transcript);
            } else {
              interimTranscript += transcript;
            }
          }

          setVoiceState(prev => ({
            ...prev,
            transcript: prev.transcript + finalTranscript,
            interimTranscript,
            confidence: confidence || prev.confidence
          }));

          if (autoStop && finalTranscript && !continuous) {
            if (silenceTimeoutRef.current) {
              clearTimeout(silenceTimeoutRef.current);
            }
            silenceTimeoutRef.current = setTimeout(() => {
              console.log('🔇 Silence detected, stopping recognition');
              recognition.stop();
            }, 2000);
          }
        };

        recognition.onend = () => {
          console.log('🛑 Speech recognition ended');
          setVoiceState(prev => ({ ...prev, isListening: false }));

          if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
            timeoutRef.current = null;
          }
          if (silenceTimeoutRef.current) {
            clearTimeout(silenceTimeoutRef.current);
            silenceTimeoutRef.current = null;
          }
        };

        recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
          console.error('❌ Speech recognition error:', event.error);
          let errorMessage = 'Speech recognition error';

          switch (event.error) {
            case 'no-speech':
              errorMessage = 'Không phát hiện giọng nói. Hãy thử lại.';
              break;
            case 'audio-capture':
              errorMessage = 'Không thể truy cập microphone. Kiểm tra quyền truy cập.';
              break;
            case 'not-allowed':
              errorMessage = 'Quyền truy cập microphone bị từ chối.';
              break;
            case 'network':
              errorMessage = 'Lỗi mạng. Kiểm tra kết nối internet.';
              break;
            case 'service-not-allowed':
              errorMessage = 'Dịch vụ nhận dạng giọng nói không khả dụng.';
              break;
            default:
              errorMessage = `Lỗi nhận dạng giọng nói: ${event.error}`;
          }

          setVoiceState(prev => ({
            ...prev,
            isListening: false,
            error: errorMessage,
            isProcessing: false
          }));
        };

        recognition.onspeechstart = () => {
          console.log('🗣️ Speech detected');
          if (silenceTimeoutRef.current) {
            clearTimeout(silenceTimeoutRef.current);
            silenceTimeoutRef.current = null;
          }
        };

        recognition.onspeechend = () => {
          console.log('🤫 Speech ended');
        };

        recognitionRef.current = recognition;
        setVoiceState(prev => ({ ...prev, isSupported: true }));
      } else {
        console.warn('⚠️ Speech Recognition not supported');
        setVoiceState(prev => ({ ...prev, isSupported: false }));
      }

      if ('speechSynthesis' in window) {
        synthesisRef.current = window.speechSynthesis;

        const loadVoices = () => {
          const voices = speechSynthesis.getVoices();
          setAvailableVoices(voices);
          console.log('🎭 Available voices:', voices.length);
        };

        loadVoices();
        speechSynthesis.onvoiceschanged = loadVoices;
      }
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
      }
    };
  }, [language, continuous, interimResults, maxDuration, autoStop]);

  const startListening = useCallback(() => {
    if (recognitionRef.current && !voiceState.isListening) {
      console.log('🎙️ Starting speech recognition...');
      setVoiceState(prev => ({
        ...prev,
        transcript: '',
        interimTranscript: '',
        error: null,
        confidence: 0,
        isProcessing: true
      }));

      try {
        recognitionRef.current.start();
      } catch (error) {
        console.error('Failed to start recognition:', error);
        setVoiceState(prev => ({
          ...prev,
          error: 'Không thể khởi động nhận dạng giọng nói',
          isProcessing: false
        }));
      }
    }
  }, [voiceState.isListening]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current && voiceState.isListening) {
      console.log('⏹️ Stopping speech recognition...');
      recognitionRef.current.stop();
    }
  }, [voiceState.isListening]);

  const speak = useCallback((text: string, options: SpeechSynthesisOptions = {}) => {
    if (synthesisRef.current) {
      console.log('🔊 Speaking:', text.substring(0, 50) + (text.length > 50 ? '...' : ''));

      synthesisRef.current.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = language;
      utterance.rate = options.rate || 0.9;
      utterance.pitch = options.pitch || 1;
      utterance.volume = options.volume || 1;

      if (options.voice) {
        utterance.voice = options.voice;
      } else {
        const vietnameseVoice = availableVoices.find(voice =>
          voice.lang.includes('vi') ||
          voice.name.toLowerCase().includes('vietnamese') ||
          voice.name.toLowerCase().includes('vietnam')
        );
        if (vietnameseVoice) {
          utterance.voice = vietnameseVoice;
        }
      }

      utterance.onstart = () => {
        console.log('🎵 Speech synthesis started');
        setIsSpeaking(true);
      };

      utterance.onend = () => {
        console.log('✅ Speech synthesis completed');
        setIsSpeaking(false);
      };

      utterance.onerror = (error) => {
        console.error('❌ Speech synthesis error:', error);
        setIsSpeaking(false);
      };

      synthesisRef.current.speak(utterance);
    }
  }, [language, availableVoices]);

  const resetTranscript = useCallback(() => {
    console.log('🔄 Resetting transcript');
    setVoiceState(prev => ({
      ...prev,
      transcript: '',
      interimTranscript: '',
      confidence: 0,
      error: null
    }));
  }, []);

  const getVietnameseVoices = useCallback(() => {
    return availableVoices.filter(voice =>
      voice.lang.includes('vi') ||
      voice.name.toLowerCase().includes('vietnamese') ||
      voice.name.toLowerCase().includes('vietnam')
    );
  }, [availableVoices]);

  const getBestVoiceForLanguage = useCallback((lang: string) => {
    const langPrefix = lang.split('-')[0];
    return availableVoices.find(voice =>
      voice.lang.toLowerCase().startsWith(langPrefix)
    );
  }, [availableVoices]);

  const speakWithLanguageDetection = useCallback((text: string, options: SpeechSynthesisOptions = {}) => {
    const isVietnamese = /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/i.test(text);

    let targetLang = language;
    if (isVietnamese) {
      targetLang = 'vi-VN';
    } else if (/^[a-zA-Z\s.,!?]+$/.test(text)) {
      targetLang = 'en-US';
    }

    const bestVoice = getBestVoiceForLanguage(targetLang);
    speak(text, { ...options, voice: bestVoice });
  }, [language, speak, getBestVoiceForLanguage]);

  const stopSpeaking = useCallback(() => {
    if (synthesisRef.current && synthesisRef.current.speaking) {
      console.log('🔇 Stopping speech synthesis');
      synthesisRef.current.cancel();
      setIsSpeaking(false);
    }
  }, []);

  const getStatus = useCallback(() => {
    return {
      canListen: voiceState.isSupported && !voiceState.isListening,
      canSpeak: !!synthesisRef.current && !isSpeaking,
      isActive: voiceState.isListening || isSpeaking,
      hasTranscript: !!voiceState.transcript.trim(),
      errorStatus: voiceState.error,
      confidence: voiceState.confidence
    };
  }, [voiceState, isSpeaking]);

  return {
    ...voiceState,
    isSpeaking,
    availableVoices,
    startListening,
    stopListening,
    speak,
    speakWithLanguageDetection,
    stopSpeaking,
    resetTranscript,
    getVietnameseVoices,
    getBestVoiceForLanguage,
    getStatus,
    maxDuration,
    language,
    continuous,
    interimResults
  };
};

export default useVoiceChat;
