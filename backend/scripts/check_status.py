#!/usr/bin/env python3
"""
Script kiểm tra trạng thái hệ thống Bixby Chatbot
"""

import requests
import json
import sys
import os

def check_ollama_status():
    """Kiểm tra trạng thái Ollama"""
    print("🔍 Kiểm tra Ollama...")
    
    try:
        # Kiểm tra server
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            print(f"   ✅ Ollama server đang chạy")
            print(f"   📦 Models đã cài đặt: {', '.join(models) if models else 'Không có'}")
            
            # Kiểm tra models cần thiết
            required_models = ["gemma3n:e4b", "gemma2:2b"]
            missing_models = [model for model in required_models if model not in models]
            
            if missing_models:
                print(f"   ⚠️  Models thiếu: {', '.join(missing_models)}")
                print(f"   💡 Chạy: python setup_models.py")
            else:
                print(f"   ✅ Tất cả models đã sẵn sàng")
            
            return True
        else:
            print(f"   ❌ Ollama server lỗi: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Không thể kết nối Ollama: {e}")
        return False

def check_backend_status():
    """Kiểm tra trạng thái Backend"""
    print("\n🔍 Kiểm tra Backend...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Backend đang chạy")
            print(f"   🏥 Health: {data.get('status', 'unknown')}")
            
            # Kiểm tra AI providers
            if 'ollama_gemma3n_configured' in data:
                print(f"   🤖 Gemma3n: {'✅' if data['ollama_gemma3n_configured'] else '❌'}")
            if 'ollama_gemma2_configured' in data:
                print(f"   🤖 Gemma2: {'✅' if data['ollama_gemma2_configured'] else '❌'}")
            
            # Kiểm tra API services
            if 'weather_service_available' in data:
                print(f"   🌤️  Weather API: {'✅' if data['weather_service_available'] else '❌'}")
            if 'news_service_available' in data:
                print(f"   📰 News API: {'✅' if data['news_service_available'] else '❌'}")
            
            return True
        else:
            print(f"   ❌ Backend lỗi: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Không thể kết nối Backend: {e}")
        print(f"   💡 Chạy: python main.py")
        return False

def check_frontend_status():
    """Kiểm tra trạng thái Frontend"""
    print("\n🔍 Kiểm tra Frontend...")
    
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ Frontend đang chạy")
            return True
        else:
            print(f"   ❌ Frontend lỗi: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Không thể kết nối Frontend: {e}")
        print(f"   💡 Chạy: npm start")
        return False

def check_api_keys():
    """Kiểm tra API keys"""
    print("\n🔍 Kiểm tra API Keys...")
    
    # Kiểm tra từ environment
    weather_key = os.getenv('OPENWEATHER_API_KEY')
    news_key = os.getenv('NEWS_API_KEY')
    
    print(f"   🌤️  Weather API Key: {'✅' if weather_key else '❌'}")
    print(f"   📰 News API Key: {'✅' if news_key else '❌'}")
    
    if not weather_key and not news_key:
        print(f"   💡 Thêm API keys vào .env hoặc config.json")
        print(f"   💡 Xem hướng dẫn trong env.example")

def main():
    """Main function"""
    print("🚀 Bixby Chatbot - System Status Check")
    print("=" * 50)
    
    # Kiểm tra các thành phần
    ollama_ok = check_ollama_status()
    backend_ok = check_backend_status()
    frontend_ok = check_frontend_status()
    check_api_keys()
    
    # Tóm tắt
    print("\n" + "=" * 50)
    print("📊 TÓM TẮT TRẠNG THÁI:")
    print(f"   Ollama: {'✅' if ollama_ok else '❌'}")
    print(f"   Backend: {'✅' if backend_ok else '❌'}")
    print(f"   Frontend: {'✅' if frontend_ok else '❌'}")
    
    if ollama_ok and backend_ok and frontend_ok:
        print("\n🎉 Hệ thống hoạt động bình thường!")
        print("🌐 Truy cập: http://localhost:3000")
    else:
        print("\n⚠️  Có vấn đề với hệ thống!")
        print("🔧 Hướng dẫn khắc phục:")
        
        if not ollama_ok:
            print("   - Khởi động Ollama: ollama serve")
            print("   - Cài đặt models: python setup_models.py")
        
        if not backend_ok:
            print("   - Khởi động Backend: python main.py")
        
        if not frontend_ok:
            print("   - Khởi động Frontend: npm start")

if __name__ == "__main__":
    main()
