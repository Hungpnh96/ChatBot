#!/usr/bin/env python3
"""
Script để cài đặt cả 2 models: gemma3n:e4b và gemma2:2b
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

def check_system_requirements():
    """Kiểm tra yêu cầu hệ thống"""
    print("🔍 Kiểm tra yêu cầu hệ thống...")
    
    # Kiểm tra RAM
    try:
        import psutil
        ram_gb = psutil.virtual_memory().total / (1024**3)
        print(f"   RAM: {ram_gb:.1f} GB")
        
        if ram_gb < 8:
            print("   ⚠️  Cảnh báo: RAM < 8GB có thể gây chậm khi chạy gemma3n:e4b")
        else:
            print("   ✅ RAM đủ để chạy cả 2 models")
    except ImportError:
        print("   ℹ️  Không thể kiểm tra RAM (cần psutil)")
    
    # Kiểm tra disk space
    try:
        disk_usage = psutil.disk_usage('/')
        disk_gb = disk_usage.free / (1024**3)
        print(f"   Disk space: {disk_gb:.1f} GB free")
        
        if disk_gb < 10:
            print("   ⚠️  Cảnh báo: Disk space < 10GB có thể không đủ")
        else:
            print("   ✅ Disk space đủ")
    except:
        print("   ℹ️  Không thể kiểm tra disk space")

def main():
    """Main function"""
    print("🚀 Bixby Chatbot - Setup Dual Models")
    print("=" * 50)
    
    # Kiểm tra yêu cầu hệ thống
    check_system_requirements()
    print()
    
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
    
    # Models cần cài đặt
    target_models = ["gemma3n:e4b", "gemma2:2b"]
    models_to_install = []
    
    for model in target_models:
        if model in installed_models:
            print(f"✅ Model {model} đã được cài đặt!")
        else:
            models_to_install.append(model)
    
    if not models_to_install:
        print("\n🎉 Tất cả models đã được cài đặt!")
        return
    
    # Cài đặt models còn thiếu
    print(f"\n3. Cài đặt {len(models_to_install)} models còn thiếu...")
    
    for i, model in enumerate(models_to_install, 1):
        print(f"\n[{i}/{len(models_to_install)}] Cài đặt {model}...")
        
        if model == "gemma3n:e4b":
            print("   ℹ️  Model này cần nhiều RAM (khuyến nghị 8GB+)")
            print("   ℹ️  Kích thước: ~4GB")
        elif model == "gemma2:2b":
            print("   ℹ️  Model nhẹ, phù hợp với server yếu")
            print("   ℹ️  Kích thước: ~1.5GB")
        
        if install_model(model):
            print(f"   ✅ {model} cài đặt thành công!")
        else:
            print(f"   ❌ {model} cài đặt thất bại!")
            choice = input("   Bạn có muốn tiếp tục với model khác không? (y/n): ")
            if choice.lower() != 'y':
                sys.exit(1)
    
    print("\n🎉 Hoàn thành! Models đã sẵn sàng sử dụng.")
    print("\n📋 Thông tin cấu hình:")
    print("   - Primary model: gemma3n:e4b (mạnh hơn, cần nhiều RAM)")
    print("   - Fallback model: gemma2:2b (nhẹ hơn, phù hợp server yếu)")
    print("   - Hệ thống sẽ tự động chuyển đổi nếu model chính không khả dụng")
    
    print("\n🚀 Để khởi động chatbot:")
    print("  cd ChatBot/backend")
    print("  python main.py")

if __name__ == "__main__":
    main()
