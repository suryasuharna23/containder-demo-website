# File: backend/hybrid-detection/src/image_processing/size_calculator.py
# Fungsi: Menghitung ukuran botol menggunakan reference object (kotak hitam)
import cv2
import numpy as np
import math
from typing import Optional, Dict, Tuple

class OpenCVSizeCalculator:
    """Class untuk menghitung ukuran botol dengan OpenCV menggunakan kotak hitam referensi"""
    
    def __init__(self, reference_width_cm: float = 5.0):
        """
        Args:
            reference_width_cm: Ukuran real reference object (kotak hitam) dalam cm
        """
        self.reference_width_cm = reference_width_cm
    
    def find_reference_object(self, image: np.ndarray) -> Optional[dict]:
        """
        Cari reference object (kotak hitam) dalam gambar untuk kalibrasi
        Args:
            image: Gambar input
        Returns:
            Dict berisi data reference object dan pixels-per-metric
        """
        try:
            # Convert ke grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Untuk objek hitam, kita pakai pendekatan berbeda
            # 1. Coba dengan thresholding untuk isolasi objek gelap
            _, thresh1 = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)  # Objek gelap jadi putih
            
            # 2. Morphological operations untuk cleanup
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            thresh1 = cv2.morphologyEx(thresh1, cv2.MORPH_CLOSE, kernel)
            thresh1 = cv2.morphologyEx(thresh1, cv2.MORPH_OPEN, kernel)
            
            # 3. Coba juga dengan edge detection yang lebih sensitif
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 30, 100)  # Lower threshold untuk objek gelap
            
            # 4. Kombinasi kedua metode
            combined = cv2.bitwise_or(thresh1, edges)
            
            # 5. Morphological operations lagi untuk memperbaiki hasil
            kernel2 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel2)
            
            print("🔍 Searching for black reference box...")
            
            # 6. Cari kontur dari hasil kombinasi
            contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                print("⚠️ No contours found")
                return None
            
            # 7. Filter kontur untuk mencari kotak hitam
            valid_boxes = []
            
            for contour in contours:
                # Hitung area kontur
                area = cv2.contourArea(contour)
                
                # Filter berdasarkan area (kotak tidak terlalu kecil/besar)
                if area < 800 or area > 50000:  # Adjust range untuk kotak hitam
                    continue
                
                # Approximate kontur ke polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Cek apakah bentuknya mendekati persegi (4 sudut)
                if len(approx) >= 4 and len(approx) <= 8:  # Lebih toleran untuk kotak hitam
                    # Hitung bounding rectangle
                    x, y, w, h = cv2.boundingRect(approx)
                    
                    # Cek aspect ratio (mendekati persegi)
                    aspect_ratio = float(w) / h
                    
                    # Toleransi untuk persegi: ratio antara 0.6 - 1.6 (lebih toleran)
                    if 0.6 <= aspect_ratio <= 1.6:
                        # Cek apakah area cukup solid (untuk objek hitam)
                        contour_area = cv2.contourArea(contour)
                        bbox_area = w * h
                        solidity = contour_area / bbox_area
                        
                        # Filter objek yang cukup solid
                        if solidity >= 0.6:  # Minimal 60% solid
                            valid_boxes.append({
                                'contour': approx,
                                'bbox': (x, y, w, h),
                                'area': contour_area,
                                'aspect_ratio': aspect_ratio,
                                'solidity': solidity,
                                'center': (x + w//2, y + h//2)
                            })
            
            if not valid_boxes:
                print("⚠️ No valid black boxes found")
                return None
            
            # 8. Pilih kotak terbaik (berdasarkan aspek ratio mendekati 1 dan area sedang)
            best_box = None
            best_score = 0
            
            for box in valid_boxes:
                # Score berdasarkan seberapa mendekati persegi + area yang reasonable
                aspect_score = 1 - abs(1 - box['aspect_ratio'])  # Semakin mendekati 1, semakin baik
                area_score = min(box['area'] / 5000, 1)  # Normalize area score
                solidity_score = box['solidity']
                
                total_score = (aspect_score * 0.4) + (area_score * 0.3) + (solidity_score * 0.3)
                
                if total_score > best_score:
                    best_score = total_score
                    best_box = box
            
            if best_box:
                x, y, w, h = best_box['bbox']
                ppm = w / self.reference_width_cm
                
                print(f"📦 Black reference box found: {w}x{h} pixels")
                print(f"📏 Aspect ratio: {best_box['aspect_ratio']:.2f}, Solidity: {best_box['solidity']:.2f}")
                print(f"📐 PPM: {ppm:.2f}")
                
                return {
                    'center': best_box['center'],
                    'bbox': best_box['bbox'],
                    'width_pixels': w,
                    'height_pixels': h,
                    'ppm': ppm,
                    'contour': best_box['contour'],
                    'area': best_box['area'],
                    'aspect_ratio': best_box['aspect_ratio'],
                    'solidity': best_box['solidity']
                }
            
            print("⚠️ No suitable black reference box found")
            return None
            
        except Exception as e:
            print(f'❌ Error finding black reference object: {e}')
            return None
    
    def extract_bottle_contour(self, image: np.ndarray, yolo_bbox: list) -> Optional[dict]:
        """
        Ekstrak kontur botol dalam area yang sudah dideteksi YOLO
        Args:
            image: Gambar original
            yolo_bbox: Bounding box dari YOLO [x1, y1, x2, y2]
        Returns:
            Dict berisi data kontur botol
        """
        try:
            x1, y1, x2, y2 = yolo_bbox
            
            # Potong area ROI dari deteksi YOLO
            roi = image[y1:y2, x1:x2]
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # Preprocessing untuk edge detection
            blurred = cv2.GaussianBlur(gray_roi, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)
            
            # Morphological operations untuk memperbaiki edge
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
            
            # Cari kontur
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Ambil kontur terbesar
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Adjust koordinat kembali ke gambar original
                adjusted_contour = largest_contour + [x1, y1]
                
                # Hitung bounding rectangle
                x, y, w, h = cv2.boundingRect(adjusted_contour)
                
                return {
                    'contour': adjusted_contour,
                    'bbox': (x, y, w, h),
                    'area': cv2.contourArea(largest_contour),
                    'center': (x + w//2, y + h//2),
                    'height_pixels': h,
                    'width_pixels': w
                }
            
            return None
            
        except Exception as e:
            print(f'❌ Error extracting bottle contour: {e}')
            return None
    
    def calculate_real_dimensions(self, bottle_data: dict, ppm: float) -> dict:
        """
        Konversi ukuran pixel ke ukuran real (cm)
        Args:
            bottle_data: Data botol dari extract_bottle_contour
            ppm: Pixels per metric dari reference object
        Returns:
            Dict berisi ukuran real dalam cm dan estimasi volume
        """
        try:
            # Konversi pixel ke cm menggunakan PPM
            height_cm = bottle_data['height_pixels'] / ppm
            width_cm = bottle_data['width_pixels'] / ppm
            diameter_cm = width_cm  # Asumsi width = diameter
            
            # Estimasi volume menggunakan rumus silinder
            radius_cm = diameter_cm / 2
            estimated_volume_ml = math.pi * (radius_cm ** 2) * height_cm
            
            print(f"📏 Calculated dimensions: {height_cm:.1f}cm H x {diameter_cm:.1f}cm D = {estimated_volume_ml:.0f}mL")
            
            return {
                'real_height_cm': round(height_cm, 2),
                'real_diameter_cm': round(diameter_cm, 2),
                'estimated_volume_ml': round(estimated_volume_ml, 0)
            }
            
        except Exception as e:
            print(f'❌ Error calculating dimensions: {e}')
            return {}
    
    def classify_bottle(self, dimensions: dict, known_specs: dict, tolerance: float = 15) -> dict:
        """
        Klasifikasi botol berdasarkan volume yang dihitung
        Args:
            dimensions: Hasil calculate_real_dimensions
            known_specs: Database spesifikasi botol
            tolerance: Toleransi perbedaan dalam persen
        Returns:
            Dict berisi klasifikasi dan confidence
        """
        try:
            estimated_volume = dimensions.get('estimated_volume_ml', 0)
            
            best_match = None
            min_difference = float('inf')
            
            # Cari match terbaik berdasarkan volume
            for bottle_type, specs in known_specs.items():
                volume_diff = abs(estimated_volume - specs['volume'])
                volume_diff_percent = (volume_diff / specs['volume']) * 100
                
                if volume_diff_percent <= tolerance and volume_diff < min_difference:
                    min_difference = volume_diff
                    best_match = bottle_type
            
            if best_match:
                confidence = max(0, 100 - (min_difference / known_specs[best_match]['volume']) * 100)
                print(f"🎯 Classification: {best_match} ({confidence:.1f}% confidence)")
                return {
                    'classification': best_match,
                    'confidence_percent': round(confidence, 2)
                }
            else:
                print(f"❓ No match found for {estimated_volume}mL")
                return {
                    'classification': 'Unknown',
                    'confidence_percent': 0
                }
                
        except Exception as e:
            print(f'❌ Error in classification: {e}')
            return {'classification': 'Error', 'confidence_percent': 0}
    
    def draw_reference_detection(self, image: np.ndarray, reference_data: dict) -> np.ndarray:
        """
        Gambar deteksi reference object (kotak hitam) pada gambar
        Args:
            image: Gambar original
            reference_data: Data reference object
        Returns:
            Gambar dengan annotasi reference object
        """
        result_image = image.copy()
        
        try:
            # Gambar bounding box kotak referensi dengan warna yang kontras (kuning)
            x, y, w, h = reference_data['bbox']
            cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 255, 255), 3)  # Kuning, lebih tebal
            
            # Gambar kontur jika ada
            if 'contour' in reference_data:
                cv2.drawContours(result_image, [reference_data['contour']], -1, (0, 255, 255), 2)
            
            # Tambah label dengan background untuk kontras
            label = f'Black Box: {self.reference_width_cm}cm'
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            # Background putih untuk text
            cv2.rectangle(result_image, (x, y - 30), (x + label_size[0] + 10, y - 5), (255, 255, 255), -1)
            cv2.putText(result_image, label, (x + 5, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            
            # Info PPM dan akurasi
            info_labels = [
                f'PPM: {reference_data["ppm"]:.1f}',
                f'Ratio: {reference_data["aspect_ratio"]:.2f}',
                f'Solid: {reference_data["solidity"]:.2f}'
            ]
            
            for i, info_label in enumerate(info_labels):
                info_size = cv2.getTextSize(info_label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
                info_y = y + h + 15 + (i * 15)
                cv2.rectangle(result_image, (x, info_y - 10), (x + info_size[0] + 5, info_y + 5), (255, 255, 255), -1)
                cv2.putText(result_image, info_label, (x + 2, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
            
        except Exception as e:
            print(f'Error drawing reference detection: {e}')
        
        return result_image
    
    def extract_bottle_contour(self, image: np.ndarray, yolo_bbox: list) -> Optional[dict]:
        """
        Ekstrak kontur botol dalam area yang sudah dideteksi YOLO
        Args:
            image: Gambar original
            yolo_bbox: Bounding box dari YOLO [x1, y1, x2, y2]
        Returns:
            Dict berisi data kontur botol
        """
        try:
            x1, y1, x2, y2 = yolo_bbox
            
            # Potong area ROI dari deteksi YOLO
            roi = image[y1:y2, x1:x2]
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # Preprocessing untuk edge detection
            blurred = cv2.GaussianBlur(gray_roi, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)
            
            # Morphological operations untuk memperbaiki edge
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
            
            # Cari kontur
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Ambil kontur terbesar
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Adjust koordinat kembali ke gambar original
                adjusted_contour = largest_contour + [x1, y1]
                
                # Hitung bounding rectangle
                x, y, w, h = cv2.boundingRect(adjusted_contour)
                
                return {
                    'contour': adjusted_contour,
                    'bbox': (x, y, w, h),
                    'area': cv2.contourArea(largest_contour),
                    'center': (x + w//2, y + h//2),
                    'height_pixels': h,
                    'width_pixels': w
                }
            
            return None
            
        except Exception as e:
            print(f'❌ Error extracting bottle contour: {e}')
            return None
    
    def calculate_real_dimensions(self, bottle_data: dict, ppm: float) -> dict:
        """
        Konversi ukuran pixel ke ukuran real (cm)
        Args:
            bottle_data: Data botol dari extract_bottle_contour
            ppm: Pixels per metric dari reference object
        Returns:
            Dict berisi ukuran real dalam cm dan estimasi volume
        """
        try:
            # Konversi pixel ke cm menggunakan PPM
            height_cm = bottle_data['height_pixels'] / ppm
            width_cm = bottle_data['width_pixels'] / ppm
            diameter_cm = width_cm  # Asumsi width = diameter
            
            # Estimasi volume menggunakan rumus silinder
            radius_cm = diameter_cm / 2
            estimated_volume_ml = math.pi * (radius_cm ** 2) * height_cm
            
            print(f"📏 Calculated dimensions: {height_cm:.1f}cm H x {diameter_cm:.1f}cm D = {estimated_volume_ml:.0f}mL")
            
            return {
                'real_height_cm': round(height_cm, 2),
                'real_diameter_cm': round(diameter_cm, 2),
                'estimated_volume_ml': round(estimated_volume_ml, 0)
            }
            
        except Exception as e:
            print(f'❌ Error calculating dimensions: {e}')
            return {}
    
    def classify_bottle(self, dimensions: dict, known_specs: dict, tolerance: float = 15) -> dict:
        """
        Klasifikasi botol berdasarkan volume yang dihitung
        Args:
            dimensions: Hasil calculate_real_dimensions
            known_specs: Database spesifikasi botol
            tolerance: Toleransi perbedaan dalam persen
        Returns:
            Dict berisi klasifikasi dan confidence
        """
        try:
            estimated_volume = dimensions.get('estimated_volume_ml', 0)
            
            best_match = None
            min_difference = float('inf')
            
            # Cari match terbaik berdasarkan volume
            for bottle_type, specs in known_specs.items():
                volume_diff = abs(estimated_volume - specs['volume'])
                volume_diff_percent = (volume_diff / specs['volume']) * 100
                
                if volume_diff_percent <= tolerance and volume_diff < min_difference:
                    min_difference = volume_diff
                    best_match = bottle_type
            
            if best_match:
                confidence = max(0, 100 - (min_difference / known_specs[best_match]['volume']) * 100)
                print(f"🎯 Classification: {best_match} ({confidence:.1f}% confidence)")
                return {
                    'classification': best_match,
                    'confidence_percent': round(confidence, 2)
                }
            else:
                print(f"❓ No match found for {estimated_volume}mL")
                return {
                    'classification': 'Unknown',
                    'confidence_percent': 0
                }
                
        except Exception as e:
            print(f'❌ Error in classification: {e}')
            return {'classification': 'Error', 'confidence_percent': 0}
    
    def draw_reference_detection(self, image: np.ndarray, reference_data: dict) -> np.ndarray:
        """
        Gambar deteksi reference object (kotak hitam) pada gambar
        Args:
            image: Gambar original
            reference_data: Data reference object
        Returns:
            Gambar dengan annotasi reference object
        """
        result_image = image.copy()
        
        try:
            # Gambar bounding box kotak referensi dengan warna yang kontras (kuning)
            x, y, w, h = reference_data['bbox']
            cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 255, 255), 3)  # Kuning, lebih tebal
            
            # Gambar kontur jika ada
            if 'contour' in reference_data:
                cv2.drawContours(result_image, [reference_data['contour']], -1, (0, 255, 255), 2)
            
            # Tambah label dengan background untuk kontras
            label = f'Black Box: {self.reference_width_cm}cm'
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            # Background putih untuk text
            cv2.rectangle(result_image, (x, y - 30), (x + label_size[0] + 10, y - 5), (255, 255, 255), -1)
            cv2.putText(result_image, label, (x + 5, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            
            # Info PPM dan akurasi
            info_labels = [
                f'PPM: {reference_data["ppm"]:.1f}',
                f'Ratio: {reference_data["aspect_ratio"]:.2f}',
                f'Solid: {reference_data["solidity"]:.2f}'
            ]
            
            for i, info_label in enumerate(info_labels):
                info_size = cv2.getTextSize(info_label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
                info_y = y + h + 15 + (i * 15)
                cv2.rectangle(result_image, (x, info_y - 10), (x + info_size[0] + 5, info_y + 5), (255, 255, 255), -1)
                cv2.putText(result_image, info_label, (x + 2, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
            
        except Exception as e:
            print(f'Error drawing reference detection: {e}')
        
        return result_image