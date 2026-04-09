import re
import os
from PIL import Image
from django.conf import settings

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None


class VitalSignExtractor:
    """Extract vital signs from medical report images/PDFs using OCR"""
    
    @staticmethod
    def extract_from_file(file_path):
        """
        Extract vital signs from uploaded medical report file
        Supports: JPG, PNG, PDF
        Returns: dict with extracted vital signs
        """
        try:
            print(f"🔍 Processing file: {file_path}")
            
            # Get file extension
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.pdf':
                print("   Converting PDF to images...")
                images = VitalSignExtractor._pdf_to_images(file_path)
                text = ""
                for img in images:
                    text += VitalSignExtractor._ocr_image(img) + "\n"
            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                print("   Reading image file...")
                img = Image.open(file_path)
                text = VitalSignExtractor._ocr_image(img)
            else:
                print(f"   ⚠️  Unsupported file type: {ext}")
                return None
            
            print("   📝 Extracting vital signs from text...")
            vital_signs = VitalSignExtractor._parse_vital_signs(text)
            
            if vital_signs:
                print(f"   ✅ Extracted: {vital_signs}")
                return vital_signs
            else:
                print("   ⚠️  No vital signs found in image")
                return None
        
        except Exception as e:
            print(f"   ❌ Error processing file: {str(e)}")
            return None
    
    @staticmethod
    def _pdf_to_images(pdf_path):
        """Convert PDF to PIL images"""
        if not convert_from_path:
            print("   ⚠️  pdf2image not available")
            return []
        try:
            return convert_from_path(pdf_path)
        except Exception as e:
            print(f"   Error converting PDF: {str(e)}")
            return []
    
    @staticmethod
    def _ocr_image(image):
        """Extract text from image using OCR"""
        if not pytesseract:
            print("   ⚠️  pytesseract not available")
            return ""
        try:
            text = pytesseract.image_to_string(image)
            print(f"   OCR extracted {len(text)} characters")
            return text
        except Exception as e:
            print(f"   Error during OCR: {str(e)}")
            return ""
    
    @staticmethod
    def _parse_vital_signs(text):
        """Parse vital signs from OCR text using regex patterns"""
        vital_signs = {}
        text_upper = text.upper()
        
        # Heart Rate (BPM)
        # Patterns: "HR: 78", "Heart Rate: 78 BPM", "78 bpm", etc.
        hr_patterns = [
            r'(?:HR|HEART\s*RATE)[:\s]+(\d+)\s*(?:BPM)?',
            r'(\d+)\s*BPM',
            r'HR\s*(\d+)',
        ]
        hr_value = VitalSignExtractor._extract_value(text_upper, hr_patterns)
        if hr_value and 40 <= hr_value <= 200:
            vital_signs['heart_rate'] = float(hr_value)
            print(f"   ✓ Heart Rate: {hr_value} bpm")
        
        # Blood Pressure (mmHg)
        # Patterns: "BP: 120/80", "Blood Pressure 120/80 mmHg", "120/80", etc.
        bp_patterns = [
            r'(?:BP|BLOOD\s*PRESSURE)[:\s]+(\d+)\s*[/\-]\s*(\d+)',
            r'(\d{2,3})\s*[/\-]\s*(\d{2,3})\s*mmHg',
            r'(\d{2,3})\s*[/\-]\s*(\d{2,3})\s*(?:MMHG)?',
        ]
        bp_match = VitalSignExtractor._extract_bp(text_upper, bp_patterns)
        if bp_match:
            sys_val, dia_val = bp_match
            if 80 <= sys_val <= 200 and 40 <= dia_val <= 130:
                vital_signs['blood_pressure_sys'] = float(sys_val)
                vital_signs['blood_pressure_dia'] = float(dia_val)
                print(f"   ✓ Blood Pressure: {sys_val}/{dia_val} mmHg")
        
        # SpO2 (Oxygen Saturation %)
        # Patterns: "SpO2: 98%", "O2 Saturation: 98", "98%", etc.
        spo2_patterns = [
            r'(?:SPO2|O2\s*SAT(?:URATION)?)[:\s]+(\d+)\s*%?',
            r'(\d+)\s*%\s*(?:O2|OXYGEN)',
            r'OXYGEN[:\s]+(\d+)',
        ]
        spo2_value = VitalSignExtractor._extract_value(text_upper, spo2_patterns)
        if spo2_value and 70 <= spo2_value <= 100:
            vital_signs['spo2'] = float(spo2_value)
            print(f"   ✓ SpO2: {spo2_value}%")
        
        # Blood Glucose (mg/dL)
        # Patterns: "Glucose: 95", "Blood Glucose: 95 mg/dL", "95 mg/dL", etc.
        glucose_patterns = [
            r'(?:GLUCOSE|BLOOD\s*GLUCOSE)[:\s]+(\d+)\s*(?:MG/DL)?',
            r'(\d+)\s*MG/DL',
            r'FASTING\s*(?:GLUCOSE)?[:\s]+(\d+)',
        ]
        glucose_value = VitalSignExtractor._extract_value(text_upper, glucose_patterns)
        if glucose_value and 50 <= glucose_value <= 500:
            vital_signs['glucose'] = float(glucose_value)
            print(f"   ✓ Glucose: {glucose_value} mg/dL")
        
        # BMI (Body Mass Index)
        # Patterns: "BMI: 22.5", "BMI 22.5 kg/m²", etc.
        bmi_patterns = [
            r'BMI[:\s]+(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*KG/M[²2]',
        ]
        bmi_value = VitalSignExtractor._extract_value(text_upper, bmi_patterns)
        if bmi_value and 10 <= bmi_value <= 60:
            vital_signs['bmi'] = float(bmi_value)
            print(f"   ✓ BMI: {bmi_value}")
        
        # Temperature (°C)
        # Patterns: "Temp: 36.5°C", "Temperature: 36.5", "36.5C", etc.
        temp_patterns = [
            r'(?:TEMP|TEMPERATURE)[:\s]+(\d+\.?\d*)\s*[°C]',
            r'(\d+\.?\d*)\s*[°C]',
            r'BODY\s*TEMP[:\s]+(\d+\.?\d*)',
        ]
        temp_value = VitalSignExtractor._extract_value(text_upper, temp_patterns)
        if temp_value and 35 <= temp_value <= 42:
            vital_signs['temperature'] = float(temp_value)
            print(f"   ✓ Temperature: {temp_value}°C")
        
        return vital_signs if vital_signs else None
    
    @staticmethod
    def _extract_value(text, patterns):
        """Extract single numeric value from text using regex patterns"""
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    try:
                        return float(match.group(1))
                    except (ValueError, IndexError):
                        continue
        return None
    
    @staticmethod
    def _extract_bp(text, patterns):
        """Extract blood pressure (systolic/diastolic) from text"""
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    sys = int(match.group(1))
                    dia = int(match.group(2))
                    return (sys, dia)
                except (ValueError, IndexError):
                    continue
        return None
    
    @staticmethod
    def extract_with_defaults(file_path, defaults=None):
        """
        Extract vital signs from file with fallback to defaults
        
        Args:
            file_path: Path to medical report file
            defaults: Dict with default values for missing fields
        
        Returns:
            Dict with complete vital signs (extracted + defaults)
        """
        defaults = defaults or {}
        extracted = VitalSignExtractor.extract_from_file(file_path)
        
        if extracted:
            # Use extracted values, fallback to defaults
            result = {
                'heart_rate': extracted.get('heart_rate', defaults.get('heart_rate', 75.0)),
                'blood_pressure_sys': extracted.get('blood_pressure_sys', defaults.get('blood_pressure_sys', 120.0)),
                'blood_pressure_dia': extracted.get('blood_pressure_dia', defaults.get('blood_pressure_dia', 80.0)),
                'spo2': extracted.get('spo2', defaults.get('spo2', 98.0)),
                'bmi': extracted.get('bmi', defaults.get('bmi', 22.0)),
                'temperature': extracted.get('temperature', defaults.get('temperature', 36.5)),
                'glucose': extracted.get('glucose', defaults.get('glucose', 95.0)),
            }
            return result
        else:
            # Use all defaults if extraction failed
            return {
                'heart_rate': defaults.get('heart_rate', 75.0),
                'blood_pressure_sys': defaults.get('blood_pressure_sys', 120.0),
                'blood_pressure_dia': defaults.get('blood_pressure_dia', 80.0),
                'spo2': defaults.get('spo2', 98.0),
                'bmi': defaults.get('bmi', 22.0),
                'temperature': defaults.get('temperature', 36.5),
                'glucose': defaults.get('glucose', 95.0),
            }
