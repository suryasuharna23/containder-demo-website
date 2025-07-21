# File: backend/hybrid-detection/run.py
import sys
import uvicorn
from pathlib import Path

# Perbaiki path - tambahkan src directory ke Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

if __name__ == '__main__':
    from config.settings import settings
    
    print(f'Starting Hybrid Bottle Detection API...')
    print(f'Host: {settings.API_HOST}')
    print(f'Port: {settings.API_PORT}')
    print(f'YOLO Device: {settings.YOLO_DEVICE}')
    
    uvicorn.run(
        'src.api.main:app',
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
    )