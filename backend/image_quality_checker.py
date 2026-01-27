"""
Image Quality Checker
Validates document image quality before OCR processing to ensure reliable extraction.
"""

import cv2
import numpy as np
from typing import Dict, Tuple, Optional
import logging
from pathlib import Path
from pdf2image import convert_from_path
import os

logger = logging.getLogger(__name__)


class ImageQualityChecker:
    """Check image quality metrics for OCR reliability."""
    
    def __init__(self):
        """Initialize quality checker with thresholds."""
        self.thresholds = {
            'blur_threshold': 50.0,   # Lowered to be more forgiving (was 100.0)
            'brightness_min': 40,     # Minimum average brightness
            'brightness_max': 240,    # Maximum average brightness
            'contrast_min': 30,       # Minimum contrast (std deviation)
            'resolution_min': 300,    # Minimum DPI equivalent
            'min_width': 600,         # Minimum image width in pixels
            'min_height': 400,        # Minimum image height in pixels
        }
    
    def check_quality(self, file_path: str) -> Dict[str, any]:
        """
        Perform comprehensive quality check on document image.
        
        Args:
            file_path: Path to the image or PDF file
            
        Returns:
            Dictionary containing quality metrics and pass/fail status
        """
        try:
            # Convert PDF to image if needed
            if file_path.lower().endswith('.pdf'):
                images = self._pdf_to_images(file_path)
                if not images:
                    return self._failed_result("Failed to convert PDF to image")
                image = images[0]  # Check first page
            else:
                image = cv2.imread(file_path)
            
            if image is None:
                return self._failed_result("Failed to load image")
            
            # Run all quality checks
            results = {
                'passed': True,
                'quality_score': 0.0,
                'issues': [],
                'warnings': [],
                'metrics': {}
            }
            
            # Check resolution
            height, width = image.shape[:2]
            results['metrics']['width'] = int(width)
            results['metrics']['height'] = int(height)
            
            if width < self.thresholds['min_width'] or height < self.thresholds['min_height']:
                results['passed'] = False
                results['issues'].append(
                    f"Image resolution too low ({width}x{height}). Minimum required: "
                    f"{self.thresholds['min_width']}x{self.thresholds['min_height']}"
                )
            
            # Convert to grayscale for analysis
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Check blur (sharpness)
            blur_score = float(self._check_blur(gray))
            results['metrics']['blur_score'] = blur_score
            
            if blur_score < self.thresholds['blur_threshold']:
                results['passed'] = False
                results['issues'].append(
                    f"Image is blurry (score: {blur_score:.1f}). "
                    f"Minimum required: {self.thresholds['blur_threshold']}"
                )
            elif blur_score < self.thresholds['blur_threshold'] * 1.5:
                results['warnings'].append("Image sharpness is borderline. Results may vary.")
            
            # Check brightness
            brightness = float(self._check_brightness(gray))
            results['metrics']['brightness'] = brightness
            
            if brightness < self.thresholds['brightness_min']:
                results['passed'] = False
                results['issues'].append(
                    f"Image too dark (brightness: {brightness:.1f}). "
                    f"Minimum required: {self.thresholds['brightness_min']}"
                )
            elif brightness > self.thresholds['brightness_max']:
                results['passed'] = False
                results['issues'].append(
                    f"Image too bright/overexposed (brightness: {brightness:.1f}). "
                    f"Maximum allowed: {self.thresholds['brightness_max']}"
                )
            
            # Check contrast
            contrast = float(self._check_contrast(gray))
            results['metrics']['contrast'] = contrast
            
            if contrast < self.thresholds['contrast_min']:
                results['passed'] = False
                results['issues'].append(
                    f"Image has low contrast (score: {contrast:.1f}). "
                    f"Minimum required: {self.thresholds['contrast_min']}"
                )
            
            # Check for skew/rotation
            skew_angle = float(self._check_skew(gray))
            results['metrics']['skew_angle'] = skew_angle
            
            if abs(skew_angle) > 5:
                results['warnings'].append(
                    f"Document appears rotated by {skew_angle:.1f}°. "
                    "This may affect extraction accuracy."
                )
            
            # Calculate overall quality score (0-100)
            results['quality_score'] = float(self._calculate_quality_score(results['metrics']))
            
            # Overall quality assessment
            if results['quality_score'] < 50:
                results['passed'] = False
                if not results['issues']:
                    results['issues'].append("Overall image quality is poor")
            elif results['quality_score'] < 70:
                results['warnings'].append("Image quality is acceptable but not optimal")
            
            logger.info(
                f"Quality check: {'PASSED' if results['passed'] else 'FAILED'} "
                f"(score: {results['quality_score']:.1f})"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error during quality check: {str(e)}", exc_info=True)
            return self._failed_result(f"Quality check failed: {str(e)}")
    
    def _check_blur(self, gray_image: np.ndarray) -> float:
        """
        Check image sharpness using Laplacian variance.
        Higher values = sharper image.
        """
        laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
        variance = laplacian.var()
        return variance
    
    def _check_brightness(self, gray_image: np.ndarray) -> float:
        """Check average brightness of image."""
        return np.mean(gray_image)
    
    def _check_contrast(self, gray_image: np.ndarray) -> float:
        """Check contrast using standard deviation."""
        return np.std(gray_image)
    
    def _check_skew(self, gray_image: np.ndarray) -> float:
        """
        Detect document skew/rotation angle.
        Returns angle in degrees.
        """
        try:
            # Edge detection
            edges = cv2.Canny(gray_image, 50, 150, apertureSize=3)
            
            # Hough line detection
            lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
            
            if lines is None:
                return 0.0
            
            # Calculate angles
            angles = []
            for rho, theta in lines[:, 0]:
                angle = np.degrees(theta) - 90
                if -45 < angle < 45:  # Only consider roughly horizontal/vertical lines
                    angles.append(angle)
            
            if not angles:
                return 0.0
            
            # Return median angle
            return np.median(angles)
            
        except Exception as e:
            logger.warning(f"Skew detection failed: {str(e)}")
            return 0.0
    
    def _calculate_quality_score(self, metrics: Dict) -> float:
        """
        Calculate overall quality score (0-100) based on all metrics.
        """
        score = 100.0
        
        # Blur component (0-30 points)
        blur_score = metrics.get('blur_score', 0)
        if blur_score >= self.thresholds['blur_threshold'] * 2:
            score -= 0
        elif blur_score >= self.thresholds['blur_threshold']:
            score -= 15
        else:
            score -= 30
        
        # Brightness component (0-25 points)
        brightness = metrics.get('brightness', 0)
        brightness_optimal = (self.thresholds['brightness_min'] + self.thresholds['brightness_max']) / 2
        brightness_deviation = abs(brightness - brightness_optimal) / brightness_optimal
        score -= min(25, brightness_deviation * 50)
        
        # Contrast component (0-25 points)
        contrast = metrics.get('contrast', 0)
        if contrast < self.thresholds['contrast_min']:
            score -= 25
        elif contrast < self.thresholds['contrast_min'] * 1.5:
            score -= 15
        
        # Resolution component (0-20 points)
        width = metrics.get('width', 0)
        height = metrics.get('height', 0)
        if width < self.thresholds['min_width'] or height < self.thresholds['min_height']:
            score -= 20
        elif width < self.thresholds['min_width'] * 1.5 or height < self.thresholds['min_height'] * 1.5:
            score -= 10
        
        return max(0.0, min(100.0, score))
    
    def _pdf_to_images(self, pdf_path: str) -> Optional[list]:
        """Convert PDF first page to image."""
        try:
            images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=200)
            if images:
                # Convert PIL to OpenCV format
                import numpy as np
                pil_image = images[0]
                return [cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)]
            return None
        except Exception as e:
            logger.error(f"Failed to convert PDF: {str(e)}")
            return None
    
    def _failed_result(self, error_message: str) -> Dict:
        """Return a failed quality check result."""
        return {
            'passed': False,
            'quality_score': 0.0,
            'issues': [error_message],
            'warnings': [],
            'metrics': {}
        }
