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

# Inisialisasi detector dan calculator dengan error handling
try:
    print("Initializing YOLO detector...")
    yolo_detector = YOLOBottleDetector(confidence=settings.YOLO_CONFIDENCE)
    
    print("Initializing size calculator...")
    size_calculator = OpenCVSizeCalculator()
    
    print("All components initialized successfully")
except Exception as e:
    print(f"Error initializing components: {e}")
    yolo_detector = None
    size_calculator = None

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
    Endpoint untuk analisis botol dengan pengukuran kontur detail
    
    Flow:
    1. YOLO mendeteksi area botol
    2. OpenCV ekstrak kontur detail dalam area YOLO
    3. Pengukuran dimensi berdasarkan analisis kontur
    4. Estimasi ukuran real dari konteks pengukuran
    5. Klasifikasi berdasarkan volume terukur
    """
    try:
        # Step 1: Decode gambar
        image = decode_base64_image(request.image)
        original_image = image.copy()
        
        # Step 2: YOLO Detection
        print('Running YOLO detection...')
        detections = yolo_detector.detect_bottles(image)
        
        if not detections:
            return {'error': 'No bottles detected by YOLO'}
        
        best_detection = max(detections, key=lambda x: x['confidence'])
        print(f'Best detection: confidence {best_detection["confidence"]:.2f}')
        
        # Step 3: Ekstrak dan analisis kontur detail
        print('Extracting detailed bottle contour...')
        bottle_data = size_calculator.extract_bottle_contour(image, best_detection['bbox'])
        
        if not bottle_data:
            return {'error': 'Could not extract bottle contour for measurement'}
        
        # Step 4: Hitung dimensi berdasarkan pengukuran kontur
        print('Calculating dimensions from contour measurements...')
        dimensions = size_calculator.calculate_bottle_dimensions(bottle_data)
        
        if not dimensions:
            return {'error': 'Could not calculate bottle dimensions'}
        
        # Step 5: Estimasi ukuran real dari konteks
        print('Estimating real dimensions from measurement context...')
        real_dimensions = size_calculator.estimate_real_dimensions_from_context(dimensions)
        
        # Step 6: Klasifikasi botol
        print('Classifying bottle from measurements...')
        classification = size_calculator.classify_bottle(
            real_dimensions, 
            settings.KNOWN_BOTTLE_SPECS, 
            settings.CLASSIFICATION_TOLERANCE_PERCENT
        )
        
        # Step 7: Buat gambar hasil dengan analisis detail
        result_image = yolo_detector.draw_detections(original_image, [best_detection])
        result_image = size_calculator.draw_detailed_analysis(
            result_image, bottle_data, dimensions, real_dimensions
        )
        
        # Response dengan data pengukuran lengkap
        response = {
            'classification': classification['classification'],
            'confidence_percent': classification['confidence_percent'],
            'real_height_cm': real_dimensions['real_height_cm'],
            'real_diameter_cm': real_dimensions['real_diameter_cm'],
            'estimated_volume_ml': real_dimensions['estimated_volume_ml'],
            'detection_method': 'YOLO + OpenCV Contour Measurement',
            'yolo_confidence': best_detection['confidence'],
            'measurement_details': {
                'height_pixels': dimensions['height_pixels'],
                'diameter_pixels': dimensions['diameter_pixels'],
                'measurement_confidence': real_dimensions['measurement_confidence'],
                'estimated_scale': real_dimensions['estimated_scale_ppm'],
                'solidity': dimensions['solidity_factor'],
                'aspect_ratio': dimensions['aspect_ratio']
            },
            'processed_image': encode_image_to_base64(result_image)
        }
        
        print(f"Measurement complete: {classification['classification']} ({real_dimensions['estimated_volume_ml']}mL)")
        return response
        
    except Exception as e:
        print(f'Error in bottle measurement: {e}')
        return {'error': str(e)}

@app.get('/health')
async def health_check():
    """Endpoint untuk cek status server"""
    return {
        'status': 'healthy',
        'yolo_available': yolo_detector.model is not None,
        'device': yolo_detector.device if yolo_detector.model else 'none'
    }