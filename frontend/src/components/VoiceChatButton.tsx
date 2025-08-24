// components/VoiceChatButton.tsx - Voice Recognition Button Component
import React, { useState, useRef, useEffect } from 'react';
import { AudioRecorder } from '../api.ts';

interface VoiceChatButtonProps {
  onTranscriptComplete: (transcript: string) => void;
  onAudioComplete?: (audio: Blob) => void; // fallback when SpeechRecognition is not supported
  disabled?: boolean;
  autoSpeak?: boolean;
  language?: string;
  size?: 'small' | 'medium' | 'large';
}

export const VoiceChatButton: React.FC<VoiceChatButtonProps> = ({
  onTranscriptComplete,
  onAudioComplete,
  disabled = false,
  autoSpeak = true,
  language = 'vi-VN',
  size = 'medium'
}) => {
  const [isListening, setIsListening] = useState(false);
  const [isRecording, setIsRecording] = useState(false); // fallback recording
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);
  const recorderRef = useRef<AudioRecorder | null>(null);
  const transcriptRef = useRef<string>('');
  const hadSpeechRef = useRef<boolean>(false);

  const sizeStyles = {
    small: { width: '36px', height: '36px', fontSize: '14px' },
    medium: { width: '44px', height: '44px', fontSize: '16px' },
    large: { width: '52px', height: '52px', fontSize: '18px' }
  };

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (error) {
          console.warn('Error stopping recognition on cleanup:', error);
        }
      }
      if (recorderRef.current) {
        // ensure tracks stopped
        // cleanup handled in stopRecording()
      }
    };
  }, []);

  const startListening = async () => {
    if (disabled || isListening || isRecording) return;

    try {
      setError(null);
      setTranscript('');
      transcriptRef.current = '';
      hadSpeechRef.current = false;

      const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

      // Start backup recording in parallel (if possible)
      try {
        recorderRef.current = new AudioRecorder();
        await recorderRef.current.startRecording();
        setIsRecording(true);
        console.log('🎙️ Backup recording started');
      } catch (recErr) {
        console.warn('Backup recording not available:', recErr);
      }

      if (SR) {
        const recognition = new SR();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = language;

        recognition.onstart = () => {
          console.log('🎤 Speech recognition started');
          setIsListening(true);
        };

        recognition.onresult = (event: any) => {
          let finalText = '';
          let interimText = '';
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const res = event.results[i];
            if (res.isFinal) finalText += res[0].transcript;
            else interimText += res[0].transcript;
          }
          if (interimText) {
            hadSpeechRef.current = true;
          }
          if (finalText) {
            transcriptRef.current += finalText;
            setTranscript(prev => (prev + finalText).trim());
          }
        };

        recognition.onerror = async (ev: any) => {
          console.warn('Speech recognition error:', ev?.error);
          setError('Lỗi nhận dạng giọng nói');
          // keep backup recording running
        };

        recognition.onend = async () => {
          console.log('🛑 Speech recognition ended');
          setIsListening(false);
          const text = transcriptRef.current.trim();
          if (text) {
            // stop backup recording and discard
            if (recorderRef.current && isRecording) {
              try { await recorderRef.current.stopRecording(); } catch {}
              setIsRecording(false);
            }
            onTranscriptComplete(text);
          } else {
            // no transcript -> use recorded audio
            if (recorderRef.current && isRecording) {
              try {
                const audioBlob = await recorderRef.current.stopRecording();
                setIsRecording(false);
                if (onAudioComplete) onAudioComplete(audioBlob);
              } catch (e) {
                setError('Không thu được giọng nói');
                setIsRecording(false);
              }
            } else {
              setError('Không thu được giọng nói');
            }
          }
        };

        recognitionRef.current = recognition;
        recognition.start();
        console.log('🎤 Speech recognition started');
      } else {
        // No SpeechRecognition support: rely on recording only
        if (!isRecording) {
          try {
            recorderRef.current = new AudioRecorder();
            await recorderRef.current.startRecording();
            setIsRecording(true);
          } catch (e) {
            setError('Không thể truy cập micro');
          }
        }
      }
    } catch (error) {
      console.error('Error starting voice input:', error);
      setError('Voice input failed to start');
      setIsListening(false);
      setIsRecording(false);
    }
  };

  const stopListening = async () => {
    // Stop speech recognition if in progress
    if (recognitionRef.current && isListening) {
      try {
        recognitionRef.current.stop();
        setIsListening(false);
      } catch (error) {
        console.warn('Error stopping recognition:', error);
        setIsListening(false);
      }
      return;
    }

    // Stop fallback recording if in progress
    if (recorderRef.current && isRecording) {
      try {
        const audioBlob = await recorderRef.current.stopRecording();
        setIsRecording(false);
        if (onAudioComplete) {
          onAudioComplete(audioBlob);
        }
      } catch (error) {
        console.warn('Error stopping recording:', error);
        setIsRecording(false);
      }
    }
  };

  const handleClick = () => {
    if (isListening || isRecording) {
      stopListening();
    } else {
      startListening();
    }
  };

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={handleClick}
        disabled={disabled}
        style={{
          ...sizeStyles[size],
          marginLeft: '6px',
          background: (isListening || isRecording)
            ? 'linear-gradient(45deg, #ff4444, #ff6b6b)'
            : disabled 
            ? '#ccc' 
            : 'linear-gradient(45deg, #42a5f5, #1e88e5)',
          color: 'white',
          border: 'none',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: disabled ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s ease',
          boxShadow: (isListening || isRecording)
            ? '0 0 20px rgba(255, 68, 68, 0.5)' 
            : '0 2px 8px rgba(0,0,0,0.1)',
          transform: (isListening || isRecording) ? 'scale(1.1)' : 'scale(1)',
          animation: (isListening || isRecording) ? 'pulse 1.5s infinite' : 'none'
        }}
        title={isListening ? 'Click to stop listening...' : 'Click to start voice input'}
      >
        {(isListening || isRecording) ? '🔴' : '🎤'}
      </button>

      {/* Listening indicator */}
      {(isListening || isRecording) && (
        <div style={{
          position: 'absolute',
          top: '-8px',
          right: '-8px',
          width: '16px',
          height: '16px',
          background: '#ff4444',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '8px',
          color: 'white',
          animation: 'blink 1s infinite'
        }}>
          ●
        </div>
      )}

      {/* Transcript preview */}
      {transcript && !isListening && !isRecording && (
        <div style={{
          position: 'absolute',
          bottom: '100%',
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'rgba(0,0,0,0.8)',
          color: 'white',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '11px',
          whiteSpace: 'nowrap',
          maxWidth: '200px',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          marginBottom: '4px',
          zIndex: 1000
        }}>
          "{transcript}"
        </div>
      )}

      {/* Error message */}
      {error && (
        <div style={{
          position: 'absolute',
          bottom: '100%',
          left: '50%',
          transform: 'translateX(-50%)',
          background: '#ff4444',
          color: 'white',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '10px',
          whiteSpace: 'nowrap',
          marginBottom: '4px',
          zIndex: 1000
        }}>
          {error}
        </div>
      )}

      {/* CSS animations */}
      <style>{`
        @keyframes pulse {
          0% {
            box-shadow: 0 0 0 0 rgba(255, 68, 68, 0.7);
          }
          70% {
            box-shadow: 0 0 0 10px rgba(255, 68, 68, 0);
          }
          100% {
            box-shadow: 0 0 0 0 rgba(255, 68, 68, 0);
          }
        }
        
        @keyframes blink {
          0%, 50% {
            opacity: 1;
          }
          51%, 100% {
            opacity: 0.3;
          }
        }
      `}</style>
    </div>
  );
};