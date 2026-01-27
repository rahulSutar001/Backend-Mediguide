"""
Image Processing Utilities
Uses OpenCV to detect blur and enhance image quality for OCR/AI processing.
"""
import cv2
import numpy as np
import io
from PIL import Image

def check_blur(image_bytes: bytes, threshold: float = 100.0) -> bool:
    """
    Detects if an image is blurry using the variance of the Laplacian.
    Args:
        image_bytes: Raw image data
        threshold: Variance threshold (default 100). Below this = blurry.
                   Higher threshold = Stricter check (requires more sharpness).
    Returns:
        True if blurry, False otherwise.
    """
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        
        if image is None:
            return False # Can't determine, assume not blurry to avoid blocking valid files
            
        # Calculate Variance of Laplacian
        variance = cv2.Laplacian(image, cv2.CV_64F).var()
        print(f"[DEBUG] Image Sharpness Score (Variance): {variance}")
        
        return variance < threshold
    except Exception as e:
        print(f"[WARNING] Blur check failed: {e}")
        return False

def enhance_image(image_bytes: bytes) -> bytes:
    """
    Enhances image clarity using CLAHE and sharpening.
    Args:
        image_bytes: Raw image data
    Returns:
        Enhanced image bytes (JPEG format)
    """
    try:
        # Decode
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return image_bytes
            
        # 1. Convert to LAB color space
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # 2. Apply CLAHE to L-channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        
        # 3. Merge and convert back to BGR
        limg = cv2.merge((cl, a, b))
        enhanced_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        
        # 4. Apply Sharpening Kernel
        kernel = np.array([[-1,-1,-1], 
                           [-1, 9,-1], 
                           [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced_img, -1, kernel)
        
        # Encode back to bytes
        success, encoded_img = cv2.imencode('.jpg', sharpened)
        if success:
            return encoded_img.tobytes()
            
        return image_bytes
        
    except Exception as e:
        print(f"[WARNING] Image enhancement failed: {e}")
        return image_bytes
