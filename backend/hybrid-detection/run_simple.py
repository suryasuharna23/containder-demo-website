# File: backend/hybrid-detection/run_simple.py
import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Simple check
try:
    from config.settings import settings
    print("✅ Settings imported successfully")
    print(f"Host: {settings.API_HOST}")
    print(f"Port: {settings.API_PORT}")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(f"Current path: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    print(f"Looking for: {src_path}")
    print(f"Src exists: {src_path.exists()}")
    
    # Check what's in src directory
    if src_path.exists():
        print("Files in src:")
        for item in src_path.iterdir():
            print(f"  - {item.name}")