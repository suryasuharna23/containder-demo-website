# File: backend/hybrid-detection/src/image_processing/size_calculator.py
# Fungsi: Menghitung ukuran botol berdasarkan pengukuran kontur nyata
import cv2
import numpy as np
import math
from typing import Optional, Dict, Tuple, List

class OpenCVSizeCalculator:
    """Class untuk menghitung ukuran botol dengan pengukuran kontur OpenCV"""
    
    def __init__(self, pixels_per_cm_base: float = 10.0):
        """
        Args:
            pixels_per_cm_base: Base conversion rate (akan dikalibrasi otomatis)
        """
        self.pixels_per_cm_base = pixels_per_cm_base
    
    def extract_bottle_contour(self, image: np.ndarray, yolo_bbox: list) -> Optional[dict]:
        """
        Ekstrak kontur botol dalam area YOLO dengan analisis detail
        Args:
            image: Gambar original
            yolo_bbox: Bounding box dari YOLO [x1, y1, x2, y2]
        Returns:
            Dict berisi data kontur dan pengukuran detail
        """
        try:
            x1, y1, x2, y2 = yolo_bbox
            
            # Potong area ROI dari deteksi YOLO
            roi = image[y1:y2, x1:x2]
            
            if roi.size == 0:
                return None
                
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # Multiple preprocessing untuk deteksi kontur yang lebih akurat
            
            # 1. Gaussian blur untuk noise reduction
            blurred = cv2.GaussianBlur(gray_roi, (5, 5), 0)
            
            # 2. Multiple thresholding approaches
            # Otsu thresholding
            _, thresh_otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Adaptive thresholding
            thresh_adaptive = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                                   cv2.THRESH_BINARY, 11, 2)
            
            # 3. Edge detection dengan multiple parameters
            edges1 = cv2.Canny(blurred, 50, 150)
            edges2 = cv2.Canny(blurred, 30, 100)
            
            # 4. Kombinasi semua metode
            combined = cv2.bitwise_or(thresh_otsu, thresh_adaptive)
            combined = cv2.bitwise_or(combined, edges1)
            combined = cv2.bitwise_or(combined, edges2)
            
            # 5. Morphological operations untuk cleanup
            kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            
            combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel_close)
            combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel_open)
            
            # 6. Cari kontur
            contours, hierarchy = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return None
            
            # 7. Filter dan pilih kontur terbaik
            valid_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)
                
                # Filter berdasarkan area minimum
                if area < 500:
                    continue
                
                # Hitung circularity untuk filter noise
                if perimeter > 0:
                    circularity = 4 * math.pi * area / (perimeter * perimeter)
                    if circularity < 0.1:  # Terlalu tidak beraturan
                        continue
                
                valid_contours.append((contour, area))
            
            if not valid_contours:
                return None
            
            # Ambil kontur terbesar yang valid
            largest_contour = max(valid_contours, key=lambda x: x[1])[0]
            
            # 8. Adjust koordinat kembali ke gambar original
            adjusted_contour = largest_contour + [x1, y1]
            
            return self._analyze_contour_measurements(adjusted_contour, roi.shape)
            
        except Exception as e:
            print(f'Error extracting bottle contour: {e}')
            return None
    
    def _analyze_contour_measurements(self, contour: np.ndarray, roi_shape: tuple) -> dict:
        """
        Analisis pengukuran detail dari kontur
        Args:
            contour: Kontur yang sudah disesuaikan
            roi_shape: Ukuran ROI untuk referensi
        Returns:
            Dict berisi pengukuran detail
        """
        try:
            # Basic measurements
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            
            # Bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Minimum enclosing rectangle (rotated)
            rect = cv2.minAreaRect(contour)
            (center_x, center_y), (rect_w, rect_h), angle = rect
            
            # Minimum enclosing circle
            (circle_x, circle_y), radius = cv2.minEnclosingCircle(contour)
            
            # Fit ellipse jika cukup points
            if len(contour) >= 5:
                ellipse = cv2.fitEllipse(contour)
                (ellipse_center, ellipse_axes, ellipse_angle) = ellipse
                major_axis = max(ellipse_axes)
                minor_axis = min(ellipse_axes)
            else:
                major_axis = max(rect_w, rect_h)
                minor_axis = min(rect_w, rect_h)
                ellipse_angle = angle
            
            # Hull dan solidity
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            solidity = area / hull_area if hull_area > 0 else 0
            
            # Aspect ratios
            aspect_ratio_rect = rect_w / rect_h if rect_h > 0 else 1
            aspect_ratio_ellipse = major_axis / minor_axis if minor_axis > 0 else 1
            
            # Extent (ratio of contour area to bounding rectangle area)
            extent = area / (w * h) if (w * h) > 0 else 0
            
            # Circularity
            circularity = 4 * math.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
            
            # Moments untuk centroid dan orientation
            moments = cv2.moments(contour)
            if moments['m00'] != 0:
                centroid_x = int(moments['m10'] / moments['m00'])
                centroid_y = int(moments['m01'] / moments['m00'])
            else:
                centroid_x, centroid_y = int(center_x), int(center_y)
            
            print(f"Contour measurements:")
            print(f"   Area: {area:.0f} pixels²")
            print(f"   Perimeter: {perimeter:.0f} pixels")
            print(f"   Bounding: {w}x{h} pixels")
            print(f"   Ellipse: {major_axis:.1f}x{minor_axis:.1f} pixels")
            print(f"   Solidity: {solidity:.3f}")
            print(f"   Aspect Ratio: {aspect_ratio_ellipse:.2f}")
            
            return {
                'contour': contour,
                'measurements': {
                    'area_pixels': area,
                    'perimeter_pixels': perimeter,
                    'bounding_width': w,
                    'bounding_height': h,
                    'rect_width': rect_w,
                    'rect_height': rect_h,
                    'major_axis': major_axis,
                    'minor_axis': minor_axis,
                    'radius': radius,
                    'solidity': solidity,
                    'aspect_ratio': aspect_ratio_ellipse,
                    'extent': extent,
                    'circularity': circularity,
                    'angle': ellipse_angle
                },
                'centers': {
                    'bounding': (x + w//2, y + h//2),
                    'centroid': (centroid_x, centroid_y),
                    'circle': (int(circle_x), int(circle_y)),
                    'ellipse': (int(ellipse_center[0]), int(ellipse_center[1]))
                },
                'bbox': (x, y, w, h)
            }
            
        except Exception as e:
            print(f'Error analyzing contour measurements: {e}')
            return {}
    
    def calculate_bottle_dimensions(self, bottle_data: dict) -> dict:
        """
        Hitung dimensi botol berdasarkan pengukuran kontur
        Args:
            bottle_data: Data hasil analyze_contour_measurements
        Returns:
            Dict berisi dimensi dalam pixel dan estimasi real
        """
        try:
            measurements = bottle_data['measurements']
            
            # Ambil dimensi utama
            height_pixels = measurements['major_axis']  # Tinggi berdasarkan major axis ellipse
            diameter_pixels = measurements['minor_axis']  # Diameter berdasarkan minor axis ellipse
            
            # Alternative measurements
            height_alt = measurements['bounding_height']
            width_alt = measurements['bounding_width']
            
            # Pilih yang lebih konsisten berdasarkan aspect ratio
            aspect_ratio = measurements['aspect_ratio']
            
            if aspect_ratio > 1.5:  # Botol tegak
                estimated_height = height_pixels
                estimated_diameter = diameter_pixels
            else:  # Botol miring atau pendek
                estimated_height = max(height_pixels, height_alt)
                estimated_diameter = min(diameter_pixels, width_alt)
            
            # Koreksi berdasarkan solidity (bentuk tidak sempurna)
            solidity = measurements['solidity']
            corrected_diameter = estimated_diameter * math.sqrt(solidity)
            
            # Volume calculation menggunakan rumus silinder dengan koreksi
            radius = corrected_diameter / 2
            volume_cylinder = math.pi * (radius ** 2) * estimated_height
            
            # Koreksi volume berdasarkan bentuk nyata
            # Botol biasanya tidak sempurna silinder (leher mengecil, dll)
            shape_factor = 0.85  # Faktor koreksi untuk bentuk botol yang tidak sempurna
            corrected_volume = volume_cylinder * shape_factor * solidity
            
            print(f"Calculated dimensions (pixels):")
            print(f"   Height: {estimated_height:.1f}")
            print(f"   Diameter: {corrected_diameter:.1f}")
            print(f"   Volume (cylinder): {volume_cylinder:.0f} cubic pixels")
            print(f"   Volume (corrected): {corrected_volume:.0f} cubic pixels")
            
            return {
                'height_pixels': estimated_height,
                'diameter_pixels': corrected_diameter,
                'raw_diameter_pixels': estimated_diameter,
                'volume_cubic_pixels': corrected_volume,
                'raw_volume_cubic_pixels': volume_cylinder,
                'shape_factor': shape_factor,
                'solidity_factor': solidity,
                'aspect_ratio': aspect_ratio,
                'measurement_confidence': self._calculate_measurement_confidence(measurements)
            }
            
        except Exception as e:
            print(f'Error calculating dimensions: {e}')
            return {}
    
    def _calculate_measurement_confidence(self, measurements: dict) -> float:
        """
        Hitung confidence score berdasarkan kualitas pengukuran
        Args:
            measurements: Dict pengukuran kontur
        Returns:
            Confidence score 0.0-1.0
        """
        try:
            # Faktor-faktor yang mempengaruhi confidence
            solidity = measurements.get('solidity', 0)
            circularity = measurements.get('circularity', 0)
            extent = measurements.get('extent', 0)
            aspect_ratio = measurements.get('aspect_ratio', 1)
            
            # Score berdasarkan solidity (0.6-1.0 = good)
            solidity_score = min(solidity / 0.6, 1.0) if solidity >= 0.3 else 0
            
            # Score berdasarkan aspect ratio (botol biasanya 1.5-4.0)
            if 1.5 <= aspect_ratio <= 4.0:
                aspect_score = 1.0
            elif 1.0 <= aspect_ratio < 1.5:
                aspect_score = (aspect_ratio - 1.0) / 0.5
            else:
                aspect_score = max(0, 1.0 - abs(aspect_ratio - 2.5) / 2.5)
            
            # Score berdasarkan extent (seberapa penuh bounding box)
            extent_score = min(extent / 0.5, 1.0) if extent >= 0.2 else 0
            
            # Kombinasi weighted
            total_confidence = (
                solidity_score * 0.4 +
                aspect_score * 0.4 +
                extent_score * 0.2
            )
            
            return min(max(total_confidence, 0.0), 1.0)
            
        except Exception as e:
            print(f'Error calculating confidence: {e}')
            return 0.5
    
    def estimate_real_dimensions_from_context(self, dimensions: dict) -> dict:
        """
        Estimasi ukuran real berdasarkan konteks pengukuran yang lebih akurat
        """
        try:
            height_pixels = dimensions['height_pixels']
            diameter_pixels = dimensions['diameter_pixels']
            volume_pixels = dimensions['volume_cubic_pixels']
            confidence = dimensions['measurement_confidence']
            aspect_ratio = dimensions['aspect_ratio']
            
            # Scale estimation yang lebih konservatif dan realistis
            
            # Untuk botol dengan aspect ratio tinggi (botol tegak)
            if aspect_ratio > 2.0:  # Botol tegak
                # Asumsi tinggi botol normal: 15-25cm
                typical_height_cm = 20.0
                estimated_scale = height_pixels / typical_height_cm
            else:  # Botol miring atau pendek
                # Asumsi diameter botol normal: 6-8cm
                typical_diameter_cm = 7.0
                estimated_scale = diameter_pixels / typical_diameter_cm
            
            # Batas scale yang masuk akal
            # Scale biasanya antara 5-50 pixels per cm
            if estimated_scale < 5:
                estimated_scale = 5
            elif estimated_scale > 50:
                estimated_scale = 50
            
            # Konversi ke real dimensions
            real_height_cm = height_pixels / estimated_scale
            real_diameter_cm = diameter_pixels / estimated_scale
            
            # Volume dengan batas yang realistis
            real_volume_ml = volume_pixels / (estimated_scale ** 3)
            
            # Batasi volume dalam range yang masuk akal (50-2000mL)
            if real_volume_ml < 50:
                real_volume_ml = 50
            elif real_volume_ml > 2000:
                real_volume_ml = 2000
            
            # Diameter juga dibatasi (3-12cm untuk botol normal)
            if real_diameter_cm < 3:
                real_diameter_cm = 3
            elif real_diameter_cm > 12:
                real_diameter_cm = 12
            
            # Height dibatasi (8-35cm untuk botol normal)
            if real_height_cm < 8:
                real_height_cm = 8
            elif real_height_cm > 35:
                real_height_cm = 35
            
            print(f"Improved scale estimation:")
            print(f"   Estimated scale: {estimated_scale:.2f} pixels/cm")
            print(f"   Real height: {real_height_cm:.1f} cm")
            print(f"   Real diameter: {real_diameter_cm:.1f} cm")
            print(f"   Real volume: {real_volume_ml:.0f} mL")
            
            return {
                'real_height_cm': round(real_height_cm, 2),
                'real_diameter_cm': round(real_diameter_cm, 2),
                'estimated_volume_ml': round(real_volume_ml, 0),
                'estimated_scale_ppm': round(estimated_scale, 2),
                'measurement_confidence': round(confidence * 100, 1),
                'scale_confidence': 'improved'
            }
            
        except Exception as e:
            print(f'Error estimating real dimensions: {e}')
            return {}
    
    def classify_bottle(self, dimensions: dict, known_specs: dict, tolerance: float = 25) -> dict:
        """
        Klasifikasi botol berdasarkan volume yang dihitung dari pengukuran
        """
        try:
            estimated_volume = dimensions.get('estimated_volume_ml', 0)
            confidence_factor = dimensions.get('measurement_confidence', 0) / 100
            
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
                volume_confidence = max(0, 100 - (min_difference / known_specs[best_match]['volume']) * 100)
                final_confidence = (volume_confidence * 0.7) + (confidence_factor * 100 * 0.3)
                
                print(f"Classification: {best_match} ({final_confidence:.1f}% confidence)")
                return {
                    'classification': best_match,
                    'confidence_percent': round(final_confidence, 2),
                    'volume_match_percent': round(volume_confidence, 2),
                    'measurement_quality': round(confidence_factor * 100, 2)
                }
            else:
                print(f"No match found for {estimated_volume}mL")
                return {
                    'classification': 'Unknown',
                    'confidence_percent': 0,
                    'measurement_quality': round(confidence_factor * 100, 2)
                }
                
        except Exception as e:
            print(f'Error in classification: {e}')
            return {'classification': 'Error', 'confidence_percent': 0}
    
    def draw_detailed_analysis(self, image: np.ndarray, bottle_data: dict, dimensions: dict, real_dims: dict) -> np.ndarray:
        """
        Gambar analisis detail pada gambar
        """
        result_image = image.copy()
        
        try:
            # Gambar kontur utama
            cv2.drawContours(result_image, [bottle_data['contour']], -1, (0, 255, 255), 2)
            
            # Gambar bounding box
            x, y, w, h = bottle_data['bbox']
            cv2.rectangle(result_image, (x, y), (x + w, y + h), (255, 0, 255), 2)
            
            # Gambar center points
            centers = bottle_data['centers']
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
            names = ['bounding', 'centroid', 'circle', 'ellipse']
            
            for i, (name, center) in enumerate(centers.items()):
                cv2.circle(result_image, center, 3, colors[i], -1)
                cv2.putText(result_image, name[:3], (center[0]+5, center[1]-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, colors[i], 1)
            
            # Info panel dengan pengukuran detail
            info_lines = [
                f"Measured: {real_dims.get('real_height_cm', 0):.1f}cm x {real_dims.get('real_diameter_cm', 0):.1f}cm",
                f"Volume: {real_dims.get('estimated_volume_ml', 0):.0f}mL",
                f"Confidence: {real_dims.get('measurement_confidence', 0):.1f}%",
                f"Solidity: {dimensions.get('solidity_factor', 0):.2f}",
                f"Aspect: {dimensions.get('aspect_ratio', 0):.2f}",
                f"Scale: {real_dims.get('estimated_scale_ppm', 0):.1f} px/cm"
            ]
            
            # Background untuk info panel
            panel_height = len(info_lines) * 20 + 20
            cv2.rectangle(result_image, (x, y - panel_height - 10), (x + 350, y - 5), (0, 0, 0), -1)
            cv2.rectangle(result_image, (x, y - panel_height - 10), (x + 350, y - 5), (255, 255, 255), 2)
            
            # Gambar text info
            for i, line in enumerate(info_lines):
                cv2.putText(result_image, line, (x + 5, y - panel_height + 15 + (i * 20)), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
        except Exception as e:
            print(f'Error drawing detailed analysis: {e}')
        
        return result_image