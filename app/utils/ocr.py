"""
OCR utilities for extracting text from medical report images
Supports multiple OCR backends
"""
from typing import Optional
import pytesseract
from PIL import Image
import io
from app.core.config import settings


import os
import logging

logger = logging.getLogger(__name__)

# Explicitly set Tesseract path for Windows
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    logger.info("OCR: Running on non-Windows OS (Linux presumed). Relying on system PATH for Tesseract.")


class OCRService:
    """Service for Optical Character Recognition"""
    
    def __init__(self):
        self.service = settings.OCR_SERVICE
    
    async def extract_text(self, image_data: bytes) -> str:
        """
        Extract text from medical report image
        
        Args:
            image_data: Image file bytes
        
        Returns:
            Extracted text string
        """
        if self.service == "tesseract":
            return await self._tesseract_ocr(image_data)
        elif self.service == "google_vision":
            return await self._google_vision_ocr(image_data)
        else:
            raise ValueError(f"Unsupported OCR service: {self.service}")
    
    async def _tesseract_ocr(self, image_data: bytes) -> str:
        """Extract text using Tesseract OCR (Non-blocking wrapper)"""
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._run_tesseract_sync, image_data)

    def _run_tesseract_sync(self, image_data: bytes) -> str:
        """Synchronous Tesseract execution with image optimization"""
        logger.info(f"OCR: Starting Tesseract execution on {len(image_data)} bytes")
        # Open image
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Image preprocessing
        width, height = image.size
        
        # 1. Resize if too small (upscale for accuracy)
        if width < 300:
            scale = 300 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
        # 2. Resize if too large (downscale for performance/memory)
        # 1800px width is usually sufficient for A4 documents
        elif width > 1800:
            scale = 1800 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Extract text with better configuration
        # Use PSM mode 6 (Assume a single uniform block of text)
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(image, lang='eng', config=custom_config)
        
        # If no text extracted, try with different PSM mode
        if not text.strip():
            custom_config = r'--oem 3 --psm 11'  # Sparse text
            text = pytesseract.image_to_string(image, lang='eng', config=custom_config)
        
        if not text.strip():
            raise Exception("No text could be extracted from the image. Please ensure the image is clear and readable.")
        
        return text
    
    async def _google_vision_ocr(self, image_data: bytes) -> str:
        """Extract text using Google Cloud Vision API"""
        # TODO: Implement Google Vision OCR
        # Requires: google-cloud-vision library
        raise NotImplementedError("Google Vision OCR not yet implemented")
    
    def parse_structured_data(self, text: str) -> dict:
        """
        Parse OCR text into structured data
        Enhanced parser for medical reports
        
        Args:
            text: Raw OCR text
        
        Returns:
            Dictionary with parsed data
        """
        import re
        
        lines = text.split('\n')
        parameters = []
        
        # Common medical test parameters (expanded list)
        medical_keywords = [
            # Blood count
            'hemoglobin', 'hb', 'rbc', 'wbc', 'platelet', 'hematocrit', 'pcv', 'mcv', 'mch', 'mchc', 'rdw',
            # Lipid panel
            'cholesterol', 'hdl', 'ldl', 'triglyceride', 'vldl',
            # Liver function
            'alt', 'ast', 'sgot', 'sgpt', 'bilirubin', 'albumin', 'alkaline', 'phosphatase',
            # Kidney function
            'creatinine', 'urea', 'bun', 'uric acid', 'egfr',
            # Diabetes
            'glucose', 'hba1c', 'fasting', 'random',
            # Thyroid
            'tsh', 't3', 't4', 'ft3', 'ft4',
            # Complete blood count components
            'neutrophil', 'lymphocyte', 'monocyte', 'eosinophil', 'basophil',
            # Other common tests
            'calcium', 'sodium', 'potassium', 'chloride', 'magnesium', 'phosphorus',
            'vitamin d', 'vitamin b12', 'folate', 'ferritin', 'iron'
        ]
        
        # Pattern to match parameter lines: Name Value Unit (Range)
        # Examples: "Hemoglobin 8.5 g/dL (13.0 - 17.0)" or "Total RBC 4.6 million/µL (4.5 - 5.9)"
        parameter_pattern = re.compile(
            r'([A-Za-z\s]+(?:\([^)]+\))?)\s+([\d,\.]+)\s*([a-zA-Z/%µ]+)?\s*(?:\(([^)]+)\))?',
            re.IGNORECASE
        )
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            line_lower = line.lower()
            
            # Check if line contains medical keywords
            has_medical_keyword = any(keyword in line_lower for keyword in medical_keywords)
            
            if has_medical_keyword:
                # Try to extract parameter using regex
                match = parameter_pattern.search(line)
                if match:
                    name = match.group(1).strip()
                    value = match.group(2).strip().replace(',', '')
                    unit = match.group(3).strip() if match.group(3) else ''
                    normal_range = match.group(4).strip() if match.group(4) else ''
                    
                    # Clean up name (remove extra spaces, common prefixes)
                    name = re.sub(r'\s+', ' ', name)
                    name = re.sub(r'^test\s+', '', name, flags=re.IGNORECASE)
                    
                    parameters.append({
                        "name": name,
                        "value": value,
                        "unit": unit,
                        "range": normal_range
                    })
                else:
                    # Fallback: try to extract name and value manually
                    parts = line.split()
                    if len(parts) >= 2:
                        # Find where numbers start
                        value_idx = None
                        for idx, part in enumerate(parts):
                            if re.match(r'^[\d,\.]+$', part.replace(',', '')):
                                value_idx = idx
                                break
                        
                        if value_idx and value_idx > 0:
                            name = ' '.join(parts[:value_idx])
                            value = parts[value_idx].replace(',', '')
                            
                            # Try to extract unit and range from remaining parts
                            unit = ''
                            normal_range = ''
                            if value_idx + 1 < len(parts):
                                # Check if next part is unit
                                if re.match(r'^[a-zA-Z/%µ]+$', parts[value_idx + 1]):
                                    unit = parts[value_idx + 1]
                                
                                # Look for range in parentheses
                                remaining = ' '.join(parts[value_idx + 1:])
                                range_match = re.search(r'\(([^)]+)\)', remaining)
                                if range_match:
                                    normal_range = range_match.group(1)
                            
                            parameters.append({
                                "name": name,
                                "value": value,
                                "unit": unit,
                                "range": normal_range
                            })
        
        # If no parameters found but text exists, try a more lenient approach
        if not parameters and text.strip():
            # Look for any lines with numbers that might be test results
            for line in lines:
                line = line.strip()
                if re.search(r'\d+', line) and len(line.split()) >= 2:
                    parts = line.split()
                    # If line has a number and at least 2 words, it might be a parameter
                    if any(re.match(r'^\d+', p.replace(',', '')) for p in parts):
                        # Try to extract
                        for i, part in enumerate(parts):
                            if re.match(r'^[\d,\.]+$', part.replace(',', '')):
                                if i > 0:
                                    name = ' '.join(parts[:i])
                                    value = part.replace(',', '')
                                    parameters.append({
                                        "name": name,
                                        "value": value,
                                        "unit": "",
                                        "range": ""
                                    })
                                break
        
        return {
            "report_type": self._detect_report_type(text),
            "lab_name": self._extract_lab_name(text),
            "date": self._extract_date(text),
            "parameters": parameters
        }
    
    def _detect_report_type(self, text: str) -> str:
        """Detect report type from text"""
        text_lower = text.lower()
        
        # Check for CBC first (most common)
        if 'cbc' in text_lower or 'complete blood count' in text_lower or 'haematology' in text_lower:
            return "Complete Blood Count"
        elif 'lipid' in text_lower or 'cholesterol' in text_lower:
            return "Lipid Panel"
        elif 'bmp' in text_lower or 'basic metabolic panel' in text_lower:
            return "Basic Metabolic Panel"
        elif 'lft' in text_lower or 'liver function' in text_lower:
            return "Liver Function Test"
        elif 'hba1c' in text_lower or 'hemoglobin a1c' in text_lower:
            return "HbA1c Test"
        elif 'thyroid' in text_lower:
            return "Thyroid Panel"
        elif 'urine' in text_lower:
            return "Urine Analysis"
        elif 'stool' in text_lower:
            return "Stool Analysis"
        else:
            return "Other"
    
    def _extract_lab_name(self, text: str) -> str:
        """Extract lab name from text"""
        # Simple extraction - enhance with NLP
        lines = text.split('\n')[:10]  # Check first 10 lines
        for line in lines:
            if any(keyword in line.lower() for keyword in ['lab', 'diagnostics', 'laboratory', 'clinic']):
                return line.strip()
        return "Unknown Lab"
    
    def _extract_date(self, text: str) -> str:
        """Extract date from text"""
        import re
        from datetime import datetime
        
        # Try to find date patterns
        # Try to find date patterns - Prioritize ISO format (YYYY-MM-DD)
        date_patterns = [
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',  # YYYY-MM-DD
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # DD-MM-YYYY or MM-DD-YYYY
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    date_str = matches[0]
                    # Normalize to ISO format
                    # If it looks like YYYY-MM-DD, try to parse it
                    if re.match(r'^\d{4}', date_str):
                        return date_str # Already ISO-like
                    return date_str
                except:
                    continue
        
        # Default to today
        return datetime.now().strftime("%Y-%m-%d")
