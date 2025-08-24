#!/usr/bin/env python3
"""
Quick script to check if Vosk model exists and is valid
"""

import os
import sys
from pathlib import Path

def check_vosk_model(model_path: str) -> bool:
    """Check if Vosk model exists and has essential files"""
    model_dir = Path(model_path)
    
    if not model_dir.exists():
        print(f"❌ Model directory not found: {model_path}")
        return False
    
    if not any(model_dir.iterdir()):
        print(f"❌ Model directory is empty: {model_path}")
        return False
    
    # Check for essential Vosk model files
    essential_files = [
        "am/final.mdl",
        "graph/HCLG.fst",
        "graph/words.txt"
    ]
    
    missing_files = []
    for file_path in essential_files:
        full_path = model_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"⚠️  Model exists but missing essential files: {missing_files}")
        return False
    
    # Get model size
    total_size = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
    size_mb = total_size / (1024 * 1024)
    
    print(f"✅ Valid Vosk model found: {model_path}")
    print(f"   Size: {size_mb:.1f}MB")
    print(f"   Files: {len(list(model_dir.rglob('*')))} total")
    
    return True

def main():
    """Main function"""
    # Default paths to check
    model_paths = [
        "/app/data/models/vosk-vi",
        "./data/models/vosk-vi",
        "./backend_vosk_vi"
    ]
    
    # Check command line argument
    if len(sys.argv) > 1:
        model_paths = [sys.argv[1]]
    
    print("🔍 Checking Vosk model availability...")
    
    for model_path in model_paths:
        print(f"\nChecking: {model_path}")
        if check_vosk_model(model_path):
            print(f"✅ Model ready at: {model_path}")
            sys.exit(0)
    
    print("\n❌ No valid Vosk model found in any of the checked paths")
    print("💡 Run download script: python /app/scripts/download_vosk_model.py vi")
    sys.exit(1)

if __name__ == "__main__":
    main()