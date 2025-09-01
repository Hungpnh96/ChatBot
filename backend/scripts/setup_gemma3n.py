#!/usr/bin/env python3
"""
Script để cài đặt model gemma3n:e4b cho Ollama
"""

import requests
import json
import time
import sys
import os

def check_ollama_server():
    """Kiểm tra Ollama server có chạy không"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_installed_models():
    """Lấy danh sách models đã cài đặt"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        return []
    except:
        return []

def install_model(model_name):
    """Cài đặt model"""
    print(f"Đang cài đặt model {model_name}...")
    
    try:
        # Gọi API để pull model
        response = requests.post(
            "http://localhost:11434/api/pull",
            json={"name": model_name},
            stream=True
        )
        
        if response.status_code == 200:
            print("Đang tải model (có thể mất vài phút)...")
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if 'status' in data:
                            print(f"Status: {data['status']}")
                        if 'completed_at' in data:
                            print(f"Hoàn thành: {data['completed_at']}")
                            break
                    except json.JSONDecodeError:
                        continue
            
            print(f"✅ Model {model_name} đã được cài đặt thành công!")
            return True
        else:
            print(f"❌ Lỗi khi cài đặt model: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Bixby Chatbot - Setup Gemma3n:e4b Model")
    print("=" * 50)
    
    # Kiểm tra Ollama server
    print("1. Kiểm tra Ollama server...")
    if not check_ollama_server():
        print("❌ Ollama server không chạy!")
        print("Hãy khởi động Ollama trước:")
        print("  - macOS: brew install ollama && ollama serve")
        print("  - Linux: curl -fsSL https://ollama.ai/install.sh | sh && ollama serve")
        print("  - Windows: Tải từ https://ollama.ai/download")
        sys.exit(1)
    
    print("✅ Ollama server đang chạy")
    
    # Kiểm tra models đã cài đặt
    print("\n2. Kiểm tra models đã cài đặt...")
    installed_models = get_installed_models()
    print(f"Models hiện tại: {', '.join(installed_models) if installed_models else 'Không có'}")
    
    # Kiểm tra gemma3n:e4b
    target_model = "gemma3n:e4b"
    if target_model in installed_models:
        print(f"✅ Model {target_model} đã được cài đặt!")
        return
    
    # Cài đặt model
    print(f"\n3. Cài đặt model {target_model}...")
    if install_model(target_model):
        print("\n🎉 Hoàn thành! Model đã sẵn sàng sử dụng.")
        print("\nĐể khởi động chatbot:")
        print("  cd ChatBot/backend")
        print("  python main.py")
    else:
        print("\n❌ Cài đặt thất bại!")
        sys.exit(1)

if __name__ == "__main__":
    main()
