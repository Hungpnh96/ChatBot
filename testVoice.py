#!/usr/bin/env python3
# create_audio.py - Tạo file audio test từ nhiều nguồn

import os
import sys
import tempfile
from datetime import datetime

def method_1_microphone():
    """Phương pháp 1: Record từ microphone"""
    print("🎤 PHƯƠNG PHÁP 1: Record từ microphone")
    print("-" * 40)
    
    try:
        import speech_recognition as sr
        
        # Tạo recognizer
        r = sr.Recognizer()
        
        # Liệt kê microphones
        mics = sr.Microphone.list_microphone_names()
        print(f"Tìm thấy {len(mics)} microphones:")
        for i, name in enumerate(mics):
            print(f"  {i}: {name}")
        
        # Chọn microphone
        mic_index = None
        if len(mics) > 1:
            try:
                choice = input(f"\nChọn microphone (0-{len(mics)-1}, Enter=default): ").strip()
                if choice:
                    mic_index = int(choice)
            except:
                mic_index = None
        
        # Setup microphone
        if mic_index is not None:
            mic = sr.Microphone(device_index=mic_index)
        else:
            mic = sr.Microphone()
        
        print(f"\n📱 Chuẩn bị record...")
        print(f"Hãy nói một câu tiếng Việt rõ ràng trong 5 giây")
        print(f"Ví dụ: 'Xin chào, tôi là Bixby'")
        
        with mic as source:
            print("🔧 Đang điều chỉnh noise...")
            r.adjust_for_ambient_noise(source, duration=1)
            print(f"Energy threshold: {r.energy_threshold}")
            
            input("Nhấn Enter để bắt đầu record...")
            print("🔴 ĐANG RECORD - NÓI NGAY BÂY GIỜ!")
            
            # Record
            audio = r.listen(source, timeout=10, phrase_time_limit=5)
            print("✅ Record xong!")
        
        # Lưu file
        filename = f"mic_audio_{datetime.now().strftime('%H%M%S')}.wav"
        with open(filename, "wb") as f:
            f.write(audio.get_wav_data())
        
        print(f"💾 Đã lưu: {filename}")
        
        # Test ngay với Google
        try:
            text = r.recognize_google(audio, language='vi-VN')
            print(f"✅ Google nhận diện: '{text}'")
        except Exception as e:
            print(f"❌ Google không nhận diện được: {e}")
        
        return filename
        
    except ImportError:
        print("❌ Cần cài đặt: pip install SpeechRecognition pyaudio")
        return None
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return None

def method_2_download_sample():
    """Phương pháp 2: Download file audio mẫu"""
    print("\n🌐 PHƯƠNG PHÁP 2: Download file audio mẫu")
    print("-" * 40)
    
    try:
        import urllib.request
        
        # URL file audio tiếng Việt mẫu
        sample_urls = [
            ("vietnamese_sample_1.wav", "https://www2.cs.uic.edu/~i101/SoundFiles/BabyElephantWalk60.wav"),
            # Thực tế bạn cần file tiếng Việt, tôi sẽ tạo bằng TTS
        ]
        
        print("📥 Tạo file audio mẫu bằng TTS...")
        
        # Tạo audio bằng TTS
        try:
            import pyttsx3
            
            engine = pyttsx3.init()
            
            # Thiết lập voice tiếng Việt nếu có
            voices = engine.getProperty('voices')
            for voice in voices:
                if 'vietnamese' in voice.name.lower() or 'vi' in voice.id.lower():
                    engine.setProperty('voice', voice.id)
                    break
            
            # Thiết lập tốc độ
            engine.setProperty('rate', 150)
            
            # Tạo file audio
            texts = [
                "Xin chào, tôi là Bixby",
                "Hôm nay thời tiết đẹp quá",
                "Cảm ơn bạn đã sử dụng dịch vụ",
                "Tôi có thể giúp gì cho bạn"
            ]
            
            filenames = []
            for i, text in enumerate(texts):
                filename = f"tts_sample_{i+1}.wav"
                engine.save_to_file(text, filename)
                engine.runAndWait()
                
                if os.path.exists(filename):
                    print(f"✅ Tạo file: {filename} - '{text}'")
                    filenames.append(filename)
                else:
                    print(f"❌ Không tạo được: {filename}")
            
            return filenames
            
        except ImportError:
            print("❌ Cần cài đặt: pip install pyttsx3")
            return None
        except Exception as e:
            print(f"❌ Lỗi TTS: {e}")
            return None
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return None

def method_3_browser_record():
    """Phương pháp 3: Hướng dẫn record từ browser"""
    print("\n🌐 PHƯƠNG PHÁP 3: Record từ browser")
    print("-" * 40)
    
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Audio Recorder</title>
    <meta charset="utf-8">
</head>
<body>
    <h2>🎤 Audio Recorder for Voice Test</h2>
    <button id="startBtn">Start Recording</button>
    <button id="stopBtn" disabled>Stop Recording</button>
    <button id="downloadBtn" disabled>Download Audio</button>
    
    <div id="status">Ready to record</div>
    <audio id="audio" controls style="display:none;"></audio>
    
    <script>
        let mediaRecorder;
        let audioChunks = [];
        
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const downloadBtn = document.getElementById('downloadBtn');
        const status = document.getElementById('status');
        const audio = document.getElementById('audio');
        
        startBtn.onclick = async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };
                
                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    audio.src = audioUrl;
                    audio.style.display = 'block';
                    
                    // Create download link
                    const a = document.createElement('a');
                    a.href = audioUrl;
                    a.download = 'recorded_audio_' + new Date().getTime() + '.wav';
                    downloadBtn.onclick = () => a.click();
                    downloadBtn.disabled = false;
                    
                    status.textContent = 'Recording complete! Click Download to save.';
                };
                
                mediaRecorder.start();
                startBtn.disabled = true;
                stopBtn.disabled = false;
                status.textContent = '🔴 Recording... Speak now!';
                
            } catch (err) {
                status.textContent = 'Error: ' + err.message;
            }
        };
        
        stopBtn.onclick = () => {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
            startBtn.disabled = false;
            stopBtn.disabled = true;
        };
    </script>
    
    <div style="margin-top: 20px; padding: 10px; background: #f0f0f0;">
        <h3>Hướng dẫn:</h3>
        <ol>
            <li>Nhấn "Start Recording"</li>
            <li>Cho phép truy cập microphone</li>
            <li>Nói một câu tiếng Việt (2-5 giây)</li>
            <li>Nhấn "Stop Recording"</li>
            <li>Nhấn "Download Audio" để tải file</li>
            <li>Đưa file vào thư mục backend để test</li>
        </ol>
    </div>
</body>
</html>'''
    
    filename = "audio_recorder.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ Đã tạo file: {filename}")
    print(f"📝 Hướng dẫn:")
    print(f"   1. Mở file {filename} bằng browser")
    print(f"   2. Nhấn 'Start Recording'")
    print(f"   3. Cho phép truy cập microphone")
    print(f"   4. Nói tiếng Việt 2-5 giây")
    print(f"   5. Nhấn 'Stop Recording'")
    print(f"   6. Download file audio")
    print(f"   7. Đưa file vào thư mục backend")
    
    return filename

def method_4_manual_creation():
    """Phương pháp 4: Tạo file audio manual"""
    print("\n⚙️ PHƯƠNG PHÁP 4: Tạo file audio từ text")
    print("-" * 40)
    
    try:
        from pydub import AudioSegment
        from pydub.generators import Sine, Square
        
        # Tạo các tone khác nhau để test
        print("🎵 Tạo file audio test...")
        
        # Test 1: Sine wave
        tone = Sine(440).to_audio_segment(duration=2000)
        tone.export("test_sine_440hz.wav", format="wav")
        print("✅ Tạo: test_sine_440hz.wav")
        
        # Test 2: Mixed frequencies (giống speech hơn)
        freq1 = Sine(300).to_audio_segment(duration=500)
        freq2 = Sine(600).to_audio_segment(duration=500) 
        freq3 = Sine(400).to_audio_segment(duration=500)
        freq4 = Sine(800).to_audio_segment(duration=500)
        
        speech_like = freq1 + freq2 + freq3 + freq4
        speech_like.export("test_speech_like.wav", format="wav")
        print("✅ Tạo: test_speech_like.wav")
        
        # Test 3: White noise (để test noise handling)
        import random
        import array
        
        # Tạo white noise
        duration_ms = 2000
        sample_rate = 44100
        samples = int(duration_ms * sample_rate / 1000)
        
        noise_data = array.array('h', [int(random.uniform(-32768, 32767)) for _ in range(samples)])
        noise_segment = AudioSegment(
            noise_data.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,
            channels=1
        )
        
        # Reduce volume để không quá ồn
        noise_segment = noise_segment - 20  # -20dB
        noise_segment.export("test_noise.wav", format="wav")
        print("✅ Tạo: test_noise.wav")
        
        return ["test_sine_440hz.wav", "test_speech_like.wav", "test_noise.wav"]
        
    except ImportError:
        print("❌ Cần cài đặt: pip install pydub")
        return None
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return None

def test_audio_file(filename):
    """Test file audio với voice service"""
    print(f"\n🧪 TEST FILE: {filename}")
    print("-" * 30)
    
    if not os.path.exists(filename):
        print(f"❌ File không tồn tại: {filename}")
        return
    
    try:
        # Check file size
        size = os.path.getsize(filename)
        print(f"📁 File size: {size} bytes")
        
        # Analyze với pydub
        from pydub import AudioSegment
        audio = AudioSegment.from_file(filename)
        print(f"📊 Audio info:")
        print(f"   Duration: {len(audio)}ms")
        print(f"   Sample rate: {audio.frame_rate}Hz")
        print(f"   Channels: {audio.channels}")
        print(f"   dBFS: {audio.dBFS:.1f}")
        
        # Test với API
        print(f"🚀 Testing với API...")
        
        import subprocess
        import json
        
        # Test transcribe endpoint
        cmd = [
            'curl', '-X', 'POST',
            '-F', f'audio=@{filename}',
            '-F', 'language=vi-VN',
            'http://localhost:8000/chat/api/voice/transcribe'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                response = json.loads(result.stdout)
                print(f"✅ API Response:")
                print(f"   Text: '{response.get('text', '')}'")
                print(f"   Confidence: {response.get('confidence', 0)}")
                print(f"   Error: {response.get('error', 'None')}")
            else:
                print(f"❌ API Error: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"❌ API Timeout")
        except Exception as e:
            print(f"❌ API Test Error: {e}")
        
    except Exception as e:
        print(f"❌ Test error: {e}")

def main():
    print("🎤 TẠO FILE AUDIO TEST CHO VOICE RECOGNITION")
    print("=" * 60)
    
    print("Chọn phương pháp tạo audio:")
    print("1. Record từ microphone (tốt nhất)")
    print("2. Tạo bằng TTS")
    print("3. Record từ browser")
    print("4. Tạo audio test manual")
    print("5. Test file có sẵn")
    
    choice = input("\nChọn (1-5): ").strip()
    
    files_created = []
    
    if choice == "1":
        file = method_1_microphone()
        if file:
            files_created.append(file)
    
    elif choice == "2":
        files = method_2_download_sample()
        if files:
            files_created.extend(files)
    
    elif choice == "3":
        file = method_3_browser_record()
        print(f"\n⏳ Sau khi tạo xong file từ browser, chạy lại script này với option 5")
    
    elif choice == "4":
        files = method_4_manual_creation()
        if files:
            files_created.extend(files)
    
    elif choice == "5":
        filename = input("Nhập tên file audio: ").strip()
        test_audio_file(filename)
        return
    
    else:
        print("❌ Lựa chọn không hợp lệ")
        return
    
    # Test các file đã tạo
    for file in files_created:
        test_audio_file(file)
    
    if files_created:
        print(f"\n✅ Đã tạo {len(files_created)} file(s):")
        for file in files_created:
            print(f"   - {file}")
        
        print(f"\n💡 Để test thêm, chạy:")
        print(f"   python create_audio.py")
        print(f"   hoặc curl -X POST -F 'audio=@{files_created[0]}' -F 'language=vi-VN' http://localhost:8000/chat/api/voice/transcribe")

if __name__ == "__main__":
    main()