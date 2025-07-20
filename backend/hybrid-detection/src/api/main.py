# File: backend/hybrid-detection/src/api/main.py
# Fungsi: Server API utama yang menggabungkan YOLO detection dan OpenCV calculation
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image as PILImage
import sys
from pathlib import Path

# Import module lokal
sys.path.append(str(Path(__file__).parent.parent))
from detection.yolo_detector import YOLOBottleDetector
from image_processing.size_calculator import OpenCVSizeCalculator
from config.settings import settings

# Inisialisasi FastAPI app
app = FastAPI(title='Hybrid Bottle Detection API')

# Setup CORS untuk frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Inisialisasi detector dan calculator
yolo_detector = YOLOBottleDetector(confidence=settings.YOLO_CONFIDENCE)
size_calculator = OpenCVSizeCalculator(settings.REFERENCE_OBJECT_WIDTH_CM)

class ImageRequest(BaseModel):
    """Model untuk request gambar dari frontend"""
    image: str

def decode_base64_image(base64_string: str) -> np.ndarray:
    """Konversi base64 string ke OpenCV image"""
    try:
        if base64_string.startswith('data:image'):
            base64_string = base64_string.split(',')[1]
        
        image_data = base64.b64decode(base64_string)
        pil_image = PILImage.open(BytesIO(image_data))
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        return cv_image
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Invalid image data: {str(e)}')

def encode_image_to_base64(image: np.ndarray) -> str:
    """Konversi OpenCV image ke base64 string"""
    try:
        _, buffer = cv2.imencode('.png', image)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        return f'data:image/png;base64,{image_base64}'
    except Exception as e:
        print(f'Error encoding image: {e}')
        return ''

@app.post('/')
async def analyze_bottle(request: ImageRequest):
    """
    Endpoint utama untuk analisis botol hybrid (YOLO + OpenCV)
    
    Flow:
    1. YOLO mendeteksi area botol
    2. OpenCV mencari reference object (koin)
    3. OpenCV menganalisis detail botol dalam area YOLO
    4. Hitung ukuran real dan klasifikasi
    5. Return hasil dengan gambar annotated
    """
    try:
        # Step 1: Decode gambar dari frontend
        image = decode_base64_image(request.image)
        original_image = image.copy()
        
        # Step 2: YOLO Detection - cari botol
        print('Running YOLO detection...')
        detections = yolo_detector.detect_bottles(image)
        
        if not detections:
            return {'error': 'No bottles detected by YOLO'}
        
        # Ambil deteksi terbaik (confidence tertinggi)
        best_detection = max(detections, key=lambda x: x['confidence'])
        print(f'Best detection: {best_detection}')
        
        # Step 3: Cari reference object (kotak) untuk kalibrasi ukuran
        print('Finding reference object (box)...')
        reference = size_calculator.find_reference_object(image)
        
        if not reference:
            return {'error': 'Reference object (box/square) not found for size calibration'}
        
        ppm = reference['ppm']  # Pixels per metric untuk konversi
        print(f'Pixels per metric: {ppm}')
        
        # Step 4: Ekstrak kontur botol dalam area YOLO
        print('Extracting bottle contour...')
        bottle_data = size_calculator.extract_bottle_contour(image, best_detection['bbox'])
        
        if not bottle_data:
            return {'error': 'Could not extract bottle contour'}
        
        # Step 5: Hitung dimensi real
        print('Calculating dimensions...')
        dimensions = size_calculator.calculate_real_dimensions(bottle_data, ppm)
        
        # Step 6: Klasifikasi botol
        classification = size_calculator.classify_bottle(
            dimensions, 
            settings.KNOWN_BOTTLE_SPECS, 
            settings.CLASSIFICATION_TOLERANCE_PERCENT
        )
        
        # Step 7: Buat gambar hasil dengan annotasi
        result_image = yolo_detector.draw_detections(original_image, [best_detection])
        
        # Gambar reference object (kotak) - UPDATE BAGIAN INI
        result_image = size_calculator.draw_reference_detection(result_image, reference)
        
        # Gambar kontur botol
        cv2.drawContours(result_image, [bottle_data['contour']], -1, (0, 255, 255), 2)
        
        # Siapkan response untuk frontend
        response = {
            'classification': classification['classification'],
            'confidence_percent': classification['confidence_percent'],
            'real_height_cm': dimensions['real_height_cm'],
            'real_diameter_cm': dimensions['real_diameter_cm'],
            'estimated_volume_ml': dimensions['estimated_volume_ml'],
            'detection_method': 'YOLO + OpenCV',
            'yolo_confidence': best_detection['confidence'],
            'processed_image': encode_image_to_base64(result_image)
        }
        
        return response
        
    except Exception as e:
        print(f'Error in analysis: {e}')
        return {'error': str(e)}

@app.get('/health')
async def health_check():
    """Endpoint untuk cek status server"""
    return {
        'status': 'healthy',
        'yolo_available': yolo_detector.model is not None,
        'device': yolo_detector.device if yolo_detector.model else 'none'
    }