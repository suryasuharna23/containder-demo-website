# File: backend/hybrid-detection/src/config/settings.py
import os
from pathlib import Path

class Settings:
    # Paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    MODELS_DIR = PROJECT_ROOT / "models"
    YOLO_MODEL_PATH = MODELS_DIR / "yolo" / "yolov8n.pt"
    
    # API Settings
    API_HOST = "127.0.0.1"
    API_PORT = 8001
    
    # YOLO Settings
    YOLO_CONFIDENCE = 0.5
    YOLO_DEVICE = "cpu"
    
    # OpenCV Settings (Measurement-based)
    CLASSIFICATION_TOLERANCE_PERCENT = 25  # Toleransi untuk pengukuran
    
    # Bottle specifications
    KNOWN_BOTTLE_SPECS = {
        "100mL": {"volume": 100, "height": 8.5, "diameter": 3.8},
        "200mL": {"volume": 200, "height": 10.28, "diameter": 4.39},
        "300mL": {"volume": 300, "height": 12.5, "diameter": 5.2},
        "400mL": {"volume": 400, "height": 14.2, "diameter": 5.8},
        "500mL": {"volume": 500, "height": 16.0, "diameter": 6.5},
        "600mL": {"volume": 600, "height": 17.5, "diameter": 7.0},
        "1000mL": {"volume": 1000, "height": 22.0, "diameter": 8.5},
        "1500mL": {"volume": 1500, "height": 28.0, "diameter": 9.5},
    }

settings = Settings()