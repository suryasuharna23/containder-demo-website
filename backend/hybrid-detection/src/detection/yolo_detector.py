# File: backend/hybrid-detection/src/detection/yolo_detector.py
# Fungsi: Deteksi botol menggunakan YOLO (You Only Look Once) AI model
import cv2
import numpy as np
from typing import List, Optional

# Import YOLO dan torch
try:
    from ultralytics import YOLO
    import torch  # ← Tambahkan import torch ini!
    YOLO_AVAILABLE = True
    print("✅ YOLO libraries loaded successfully")
except ImportError as e:
    print(f"⚠️ YOLO libraries not available: {e}")
    YOLO_AVAILABLE = False
    YOLO = None
    torch = None

class YOLOBottleDetector:
    """Class untuk mendeteksi botol menggunakan YOLO"""
    
    def __init__(self, model_path: str = 'yolov8n.pt', confidence: float = 0.5):
        """
        Inisialisasi detector YOLO
        Args:
            model_path: Path ke file model YOLO (.pt)
            confidence: Minimum confidence score (0.0-1.0)
        """
        self.confidence = confidence
        
        # Check if YOLO is available
        if not YOLO_AVAILABLE:
            print("YOLO not available. Using fallback mode.")
            self.device = 'none'
            self.model = None
            return
        
        # Determine device only if torch is available
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        try:
            # Load model YOLO pre-trained
            self.model = YOLO(model_path)
            print(f'YOLO model loaded on {self.device}')
        except Exception as e:
            print(f'Error loading YOLO model: {e}')
            self.model = None
    
    def detect_bottles(self, image: np.ndarray) -> List[dict]:
        """
        Deteksi botol dalam gambar
        Args:
            image: Gambar input (OpenCV format)
        Returns:
            List berisi data deteksi botol
        """
        if not YOLO_AVAILABLE or self.model is None:
            print("YOLO model not available, returning empty detections")
            return []
        
        try:
            # Jalankan inference YOLO
            results = self.model(image, conf=self.confidence, device=self.device)
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Ambil koordinat bounding box
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = box.conf[0].cpu().numpy()
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        # Filter khusus class botol (39 = bottle di COCO dataset)
                        if class_id == 39:
                            detection = {
                                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                'confidence': float(confidence),
                                'center': [int((x1 + x2) / 2), int((y1 + y2) / 2)],
                                'width': int(x2 - x1),
                                'height': int(y2 - y1)
                            }
                            detections.append(detection)
            
            return detections
            
        except Exception as e:
            print(f'Error in YOLO detection: {e}')
            return []
    
    def get_best_detection(self, detections: List[dict]) -> Optional[dict]:
        """Get the detection with highest confidence"""
        if not detections:
            return None
        return max(detections, key=lambda x: x['confidence'])
    
    def draw_detections(self, image: np.ndarray, detections: List[dict]) -> np.ndarray:
        """
        Gambar bounding box hasil deteksi pada gambar
        Args:
            image: Gambar original
            detections: List hasil deteksi
        Returns:
            Gambar dengan bounding box
        """
        result_image = image.copy()
        
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            confidence = detection['confidence']
            
            # Gambar kotak hijau di sekitar botol
            cv2.rectangle(result_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Tambah label confidence
            label = f'Bottle: {confidence:.2f}'
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            cv2.rectangle(result_image, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), (0, 255, 0), -1)
            cv2.putText(result_image, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        return result_image