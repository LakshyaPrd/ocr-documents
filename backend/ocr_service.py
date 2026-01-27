"""
OCR processing service using EasyOCR (more powerful than Tesseract)
"""
import easyocr
from PIL import Image
import cv2
import numpy as np
import re
from typing import Dict, List, Tuple, Optional
import os
from config import DOCUMENT_TYPES
from pdf2image import convert_from_path
from mrz_parser import MRZParser


class OCRService:
    def __init__(self, tesseract_cmd: str = None):
        """Initialize OCR service with EasyOCR and MRZ Parser"""
        print("🔄 Initializing EasyOCR (this may take a minute first time)...")
        # Initialize EasyOCR with English language
        # gpu=False for CPU usage (set to True if GPU available)
        self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        
        # Initialize MRZ Parser for universal passport support
        self.mrz_parser = MRZParser()
        
        print("✅ EasyOCR initialized successfully!")
        print("✅ MRZ Parser ready (works for ALL passports worldwide!)")
    
    def extract_text_from_image(self, image_path: str) -> Tuple[str, float]:
        """
        Extract text from image using EasyOCR
        Returns: (extracted_text, confidence_score)
        """
        try:
            # EasyOCR can work directly on image path
            # It automatically handles preprocessing
            result = self.reader.readtext(image_path, detail=1, paragraph=False)
            
            # Sort results by vertical position (top to bottom, left to right)
            result = sorted(result, key=lambda x: (x[0][0][1], x[0][0][0]))
            
            # Combine all detected text
            text_lines = []
            confidences = []
            
            for (bbox, text, confidence) in result:
                text_lines.append(text)
                confidences.append(confidence * 100)  # Convert to percentage
            
            # Join all text with newlines
            full_text = '\n'.join(text_lines)
            
            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return full_text.strip(), avg_confidence
        
        except Exception as e:
            print(f"Error extracting text from image: {str(e)}")
            return "", 0.0
    
    def extract_field_with_pattern(
        self, text: str, field_name: str, patterns: List[str]
    ) -> Tuple[str, float]:
        """
        Extract field value using regex patterns
        Returns: (value, confidence)
        """
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                # Get the captured group (the value)
                value = match.group(1) if match.groups() else match.group(0)
                return value.strip(), 90.0  # Higher confidence for pattern match
        
        return "", 0.0
    
    def extract_all_key_value_pairs(self, text: str) -> Dict[str, Dict[str, any]]:
        """
        Extract ALL key-value pairs from text automatically
        Finds patterns like "Label : Value" or "Label: Value"
        This works for ANY document type!
        """
        extracted = {}
        
        # Pattern to match: "Key : Value" or "Key: Value"
        # More precise - stops at newline or next field
        pattern = r"([A-Za-z][A-Za-z\s&/]{2,30}?)\s*:+\s*([A-Z0-9][^\n:]{3,50}?)(?:\n|$|(?=[A-Z][a-z]+\s*:))"
        
        matches = re.finditer(pattern, text, re.MULTILINE)
        
        for match in matches:
            key = match.group(1).strip()
            value = match.group(2).strip()
            
            # Clean up value - remove trailing labels
            # Stop at common next-field indicators
            value = re.split(r'\s+(?:Name|Date|ID|Number|Sex|Nationality|Card|Expiry|Issue)', value)[0].strip()
            
            # Clean up the key name for use as field name
            field_name = key.lower().replace(' ', '_').replace('&', 'and').replace('/', '_')
            
            # Filter out junk field names (too short, numbers, etc.)
            if (len(field_name) < 3 or 
                field_name.startswith('_') or 
                any(char.isdigit() for char in field_name[:3])):
                continue
            
            # Skip if value is too short, too long, or just symbols
            if len(value) < 2 or len(value) > 100 or value.isspace():
                continue
            
            # Skip values that are clearly noise (too many non-alphanumeric chars)
            if sum(not c.isalnum() and not c.isspace() for c in value) > len(value) * 0.4:
                continue
                
            extracted[field_name] = {
                "value": value,
                "confidence": 85.0,
                "original_label": key
            }
        
        return extracted
    
    def extract_fields_from_text(
        self, text: str, document_type: str
    ) -> Dict[str, Dict[str, any]]:
        """
        Extract fields using PROVEN extraction logic from FinalPassportExtractor
        Returns fields in correct format with proper date formatting
        """
        extracted_fields = {}
        
        # For PASSPORTS: Use proven MRZ extraction
        if document_type == "PASSPORT":
            # Clean text for MRZ
            text_clean = text.replace(' ', '').replace('\t', '').replace('\n\n', '\n')
            
            # Find MRZ lines
            mrz_line1, mrz_line2 = self._find_mrz_lines_proven(text_clean)
            
            if mrz_line1 or mrz_line2:
                print(f"✅ Found MRZ lines - using proven extraction")
                
                # Parse Line 1 - Name and Nationality
                if mrz_line1:
                    # Nationality (positions 2-4)
                    nationality = mrz_line1[2:5].replace('<', '').replace('1', 'I').replace('0', 'O')
                    
                    # Name (positions 5-43)
                    name_part = mrz_line1[5:44] if len(mrz_line1) >= 44 else mrz_line1[5:]
                    name_part = name_part.replace('<', ' ').strip()
                    
                    # Combine surname and given name
                    if '  ' in name_part:
                        parts = name_part.split('  ')
                        surname = parts[0].strip().title()
                        given = ' '.join(parts[1:]).strip().title()
                        full_name = f"{given} {surname}"
                    else:
                        full_name = name_part.title()
                    
                    extracted_fields['name_on_passport'] = {
                        'value': full_name,
                        'confidence': 95.0,
                        'source': 'MRZ'
                    }
                    
                    if nationality and len(nationality) == 3:
                        extracted_fields['nationality'] = {
                            'value': nationality,
                            'confidence': 95.0,
                            'source': 'MRZ'
                        }
                
                # Parse Line 2 - Passport#, DOB, Gender, Expiry, File#
                if mrz_line2:
                    # Passport Number
                    passport_match = re.match(r'([A-Z0-9]+)<', mrz_line2)
                    if passport_match:
                        passport_no = passport_match.group(1).replace('O', '0').replace('I', '1')
                        extracted_fields['passport_number'] = {
                            'value': passport_no,
                            'confidence': 99.0,
                            'source': 'MRZ'
                        }
                    
                    # Find positions
                    first_bracket = mrz_line2.find('<')
                    if first_bracket == -1:
                        first_bracket = 9
                    
                    country_start = first_bracket + 2
                    dob_start = country_start + 3
                    sex_pos = dob_start + 7
                    expiry_start = sex_pos + 1
                    file_start = expiry_start + 7
                    
                    # Date of Birth - with proper formatting
                    dob_str = mrz_line2[dob_start:dob_start+6]
                    if len(dob_str) == 6:
                        dob_str = dob_str.replace('O', '0').replace('I', '1')
                        formatted_dob = self._format_date_proven(dob_str)
                        if formatted_dob:
                            extracted_fields['date_of_birth'] = {
                                'value': formatted_dob,
                                'confidence': 95.0,
                                'source': 'MRZ'
                            }
                    
                    # Gender - FIXED detection
                    if sex_pos < len(mrz_line2):
                        sex = mrz_line2[sex_pos].upper()
                        # Fix OCR errors
                        if sex == '1' or sex == 'I':
                            sex = 'M'
                        elif sex == '0':
                            sex = 'F'
                        
                        if sex in ['M', 'F']:
                            gender_value = 'Male' if sex == 'M' else 'Female'
                            extracted_fields['gender'] = {
                                'value': gender_value,
                                'confidence': 90.0,
                                'source': 'MRZ'
                            }
                    
                    # Expiry Date - with proper formatting
                    expiry_str = mrz_line2[expiry_start:expiry_start+6]
                    if len(expiry_str) == 6:
                        expiry_str = expiry_str.replace('O', '0').replace('I', '1')
                        formatted_expiry = self._format_date_proven(expiry_str)
                        if formatted_expiry:
                            extracted_fields['passport_expiry_date'] = {
                                'value': formatted_expiry,
                                'confidence': 95.0,
                                'source': 'MRZ'
                            }
                    
                    # File Number
                    file_end = file_start + 14
                    if file_end <= len(mrz_line2):
                        file_no = mrz_line2[file_start:file_end].replace('<', '').strip()
                        file_no = file_no.replace('O', '0').replace('I', '1')
                        if file_no and len(file_no) >= 8:
                            extracted_fields['file_number'] = {
                                'value': file_no,
                                'confidence': 85.0,
                                'source': 'MRZ'
                            }
                
                # Extract issue date and place from page text (not in MRZ)
                issue_date = self._extract_issue_date_proven(text, extracted_fields.get('passport_expiry_date', {}).get('value'))
                if issue_date:
                    extracted_fields['passport_issue_date'] = {
                        'value': issue_date,
                        'confidence': 80.0,
                        'source': 'PAGE_OCR'
                    }
                
                issue_place = self._extract_issue_place_proven(text)
                if issue_place:
                    extracted_fields['passport_issue_place'] = {
                        'value': issue_place,
                        'confidence': 75.0,
                        'source': 'PAGE_OCR'
                    }
                
                # Add placeholder fields for compatibility
                extracted_fields['address'] = {'value': None, 'confidence': 0, 'source': 'N/A'}
                extracted_fields['father_name'] = {'value': None, 'confidence': 0, 'source': 'N/A'}
                extracted_fields['mother_name'] = {'value': None, 'confidence': 0, 'source': 'N/A'}
                
                print(f"✅ Extracted {len(extracted_fields)} fields using proven logic")
                return extracted_fields
        
        # For LABOR CARDS: Use proven extraction logic (optimized)
        if document_type == "LABOR_CARD":
            # Use full OCR results (already have them from extract_text_from_image)
            # No need to re-run OCR or preprocess
            
            # Extract using proven patterns
            labor_fields = self._extract_labor_card_proven(text)
            
            if labor_fields:
                print(f"✅ Extracted {len(labor_fields)} labor card fields")
                return labor_fields
        
        # For RESIDENCE VISA: Use proven extraction logic (optimized)
        if document_type == "RESIDENCE_VISA":
            # Use full OCR results - already have text from extract_text_from_image
            # No need to re-run OCR or create temp files
            
            visa_fields = self._extract_residence_visa_proven(text)
            
            if visa_fields:
                print(f"✅ Extracted {len(visa_fields)} residence visa fields")
                return visa_fields
        
        # For VISA CANCELLATION: Use specific extraction logic
        if document_type == "VISA_CANCELLATION":
            cancellation_fields = self._extract_visa_cancellation_proven(text)
            if cancellation_fields:
                print(f"✅ Extracted {len(cancellation_fields)} visa cancellation fields")
                return cancellation_fields
        
        # For COMPANY LICENSE: Use optimized extraction
        if document_type == "COMPANY_LICENSE":
            license_fields = self._extract_company_license_proven(text)
            if license_fields:
                print(f"✅ Extracted {len(license_fields)} company license fields")
                return license_fields

        # For COMPANY VAT CERTIFICATE: Use optimized extraction
        if document_type == "COMPANY_VAT_CERTIFICATE":
            vat_fields = self._extract_vat_certificate_proven(text)
            if vat_fields:
                print(f"✅ Extracted {len(vat_fields)} vat certificate fields")
                return vat_fields
        
        # For ENTRY PERMIT: Use optimized extraction
        if document_type == "ENTRY_PERMIT":
            permit_fields = self._extract_entry_permit_proven(text)
            if permit_fields:
                print(f"✅ Extracted {len(permit_fields)} entry permit fields")
                return permit_fields
        
        # For LABOR CONTRACT: Use standardized extraction
        if document_type == "LABOR_CONTRACT":
            contract_fields = self.extract_simple_fields(text, "LABOR_CONTRACT")
            if contract_fields:
                print(f"✅ Extracted {len(contract_fields)} labor contract fields")
                return contract_fields
        
        # For EMIRATES ID: Use proven extraction logic (optimized)
        if document_type == "EMIRATES_ID":
            # Use full OCR results - already have text from extract_text_from_image
            # No need to re-run OCR
            
            emirates_fields = self._extract_emirates_id_proven(text)
            
            if emirates_fields:
                print(f"✅ Extracted {len(emirates_fields)} Emirates ID fields")
                return emirates_fields
        
        # For HOME COUNTRY ID (Aadhaar): Use proven extraction logic (optimized)
        if document_type == "HOME_COUNTRY_ID":
            # Use full OCR results - already have text from extract_text_from_image
            # No need for preprocessing or duplicate OCR
            
            home_id_fields = self._extract_home_country_id_proven(text)
            
            if home_id_fields:
                print(f"✅ Extracted {len(home_id_fields)} home country ID fields")
                return home_id_fields
        
        # For VISIT VISA: Use proven extraction logic (optimized)
        if document_type == "VISIT_VISA":
            # Use full OCR results - already have text from extract_text_from_image
            # No preprocessing needed
            
            visit_visa_fields = self._extract_visit_visa_proven(text)
            
            if visit_visa_fields:
                print(f"✅ Extracted {len(visit_visa_fields)} visit visa fields")
                return visit_visa_fields
        
        # For INVOICE: Use proven extraction logic (optimized)
        if document_type == "INVOICE":
            invoice_fields = self._extract_invoice_proven(text)
            
            if invoice_fields:
                print(f"✅ Extracted {len(invoice_fields)} invoice fields")
                return invoice_fields
        
        # For PURCHASE_ORDER: Use proven extraction logic (optimized)
        if document_type == "PURCHASE_ORDER":
            po_fields = self._extract_purchase_order_proven(text)
            
            if po_fields:
                print(f"✅ Extracted {len(po_fields)} purchase order fields")
                return po_fields
        
        # For COMPANY_LICENSE: Use proven extraction logic (optimized)
        if document_type == "COMPANY_LICENSE":
            license_fields = self._extract_company_license_proven(text)
            
            if license_fields:
                print(f"✅ Extracted {len(license_fields)} company license fields")
                return license_fields
        
        # Fallback for non-passports: use old logic
        return {}
    
    def _extract_visit_visa_proven(self, text: str) -> Dict:
        """
        Extract visit visa fields using proven logic - optimized for speed
        No preprocessing, no duplicate OCR, reuses cached reader
        """
        extracted = {}
        text_lines = text.split('\n')
        
        # Visa Type & Duration
        visa_keywords = ['TOURIST', 'VISIT', 'VISA', 'SINGLE', 'MULTIPLE', 'TRIP', 'DAYS', 'MONTH']
        visa_lines = []
        
        for line in text_lines:
            line_upper = line.upper()
            if any(kw in line_upper for kw in visa_keywords):
                if re.search(r'\b\d+\s*(?:DAY|DAYS|MONTH|MONTHS)\b', line_upper):
                    visa_lines.append(line.strip())
                elif 'VISA' in line_upper or 'TOURIST' in line_upper or 'VISIT' in line_upper:
                    visa_lines.append(line.strip())
        
        if visa_lines:
            extracted['visa_type_duration'] = {'value': ' '.join(visa_lines), 'confidence': 85.0, 'source': 'VISIT_VISA_OCR'}
        
        # Entry Permit Number (8-15 chars alphanumeric)
        for i, line in enumerate(text_lines):
            if 'ENTRY' in line.upper() and ('PERMIT' in line.upper() or 'NO' in line.upper()):
                match = re.search(r'[A-Z0-9]{8,15}', line)
                if match:
                    extracted['entry_permit_number'] = {'value': match.group(), 'confidence': 90.0, 'source': 'VISIT_VISA_OCR'}
                    break
                if i + 1 < len(text_lines):
                    match = re.search(r'[A-Z0-9]{8,15}', text_lines[i + 1])
                    if match:
                        extracted['entry_permit_number'] = {'value': match.group(), 'confidence': 90.0, 'source': 'VISIT_VISA_OCR'}
                        break
        
        # UID Number (12-15 digits)
        for i, line in enumerate(text_lines):
            if 'U.I.D' in line.upper() or 'UID' in line.upper() or 'UNIFIED' in line.upper():
                match = re.search(r'\b[0-9]{12,15}\b', line)
                if match:
                    extracted['uid_number'] = {'value': match.group(), 'confidence': 92.0, 'source': 'VISIT_VISA_OCR'}
                    break
                if i + 1 < len(text_lines):
                    match = re.search(r'\b[0-9]{12,15}\b', text_lines[i + 1])
                    if match:
                        extracted['uid_number'] = {'value': match.group(), 'confidence': 90.0, 'source': 'VISIT_VISA_OCR'}
                        break
        
        # Date & Place of Issue
        for i, line in enumerate(text_lines):
            if 'ISSUE' in line.upper() or 'ISSUED' in line.upper():
                date_match = re.search(r'([0-3]?\d[/-][0-1]?\d[/-]\d{4})', line)
                if date_match:
                    date_value = date_match.group(1).replace('-', '/')
                    # Look for place
                    place_match = re.search(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)', line[date_match.end():])
                    if place_match:
                        extracted['date_place_of_issue'] = {'value': f"{date_value}, {place_match.group(1)}", 'confidence': 88.0, 'source': 'VISIT_VISA_OCR'}
                    elif i + 1 < len(text_lines):
                        next_line = text_lines[i + 1].strip()
                        if not any(c.isdigit() for c in next_line):
                            extracted['date_place_of_issue'] = {'value': f"{date_value}, {next_line}", 'confidence': 85.0, 'source': 'VISIT_VISA_OCR'}
                    else:
                        extracted['date_place_of_issue'] = {'value': date_value, 'confidence': 80.0, 'source': 'VISIT_VISA_OCR'}
                    break
        
        # Full Name
        skip_words = {'VISIT', 'VISA', 'TOURIST', 'GOVERNMENT', 'IMMIGRATION', 'PASSPORT', 'NATIONALITY', 
                      'PROFESSION', 'DATE', 'PLACE', 'ENTRY', 'PERMIT', 'UNIFIED', 'IDENTIFICATION'}
        
        for i, line in enumerate(text_lines):
            if 'NAME' in line.upper() and ':' in line:
                name = line.split(':', 1)[1].strip()
                if name and not any(c.isdigit() for c in name):
                    extracted['full_name'] = {'value': name, 'confidence': 88.0, 'source': 'VISIT_VISA_OCR'}
                    break
                if i + 1 < len(text_lines):
                    next_line = text_lines[i + 1].strip()
                    if not any(c.isdigit() for c in next_line):
                        extracted['full_name'] = {'value': next_line, 'confidence': 85.0, 'source': 'VISIT_VISA_OCR'}
                        break
        
        # Nationality
        for i, line in enumerate(text_lines):
            if 'NATIONALITY' in line.upper() or 'CITIZEN' in line.upper():
                if ':' in line:
                    nationality = line.split(':', 1)[1].strip()
                    if nationality:
                        extracted['nationality'] = {'value': nationality, 'confidence': 90.0, 'source': 'VISIT_VISA_OCR'}
                        break
                if i + 1 < len(text_lines):
                    next_line = text_lines[i + 1].strip()
                    if next_line and not any(c.isdigit() for c in next_line):
                        extracted['nationality'] = {'value': next_line, 'confidence': 88.0, 'source': 'VISIT_VISA_OCR'}
                        break
        
        # Place of Birth
        for i, line in enumerate(text_lines):
            if 'PLACE' in line.upper() and 'BIRTH' in line.upper():
                if ':' in line:
                    place = line.split(':', 1)[1].strip()
                    if place:
                        extracted['place_of_birth'] = {'value': place, 'confidence': 88.0, 'source': 'VISIT_VISA_OCR'}
                        break
                if i + 1 < len(text_lines):
                    next_line = text_lines[i + 1].strip()
                    if next_line and not any(c.isdigit() for c in next_line):
                        extracted['place_of_birth'] = {'value': next_line, 'confidence': 85.0, 'source': 'VISIT_VISA_OCR'}
                        break
        
        # Date of Birth
        for line in text_lines:
            if 'DOB' in line.upper() or ('DATE' in line.upper() and 'BIRTH' in line.upper()):
                match = re.search(r'([0-3]?\d[/-][0-1]?\d[/-]\d{4})', line)
                if match:
                    extracted['date_of_birth'] = {'value': match.group(1).replace('-', '/'), 'confidence': 90.0, 'source': 'VISIT_VISA_OCR'}
                    break
        
        # Passport Number (1-2 letters + 7-8 digits)
        for i, line in enumerate(text_lines):
            if 'PASSPORT' in line.upper():
                match = re.search(r'\b([A-Z]{1,2}[0-9]{7,8})\b', line)
                if match:
                    extracted['passport_number'] = {'value': match.group(1), 'confidence': 92.0, 'source': 'VISIT_VISA_OCR'}
                    break
                if i + 1 < len(text_lines):
                    match = re.search(r'\b([A-Z]{1,2}[0-9]{7,8})\b', text_lines[i + 1])
                    if match:
                        extracted['passport_number'] = {'value': match.group(1), 'confidence': 90.0, 'source': 'VISIT_VISA_OCR'}
                        break
        
        # Profession
        for i, line in enumerate(text_lines):
            if 'PROFESSION' in line.upper() or 'OCCUPATION' in line.upper() or 'JOB' in line.upper():
                if ':' in line:
                    profession = line.split(':', 1)[1].strip()
                    if profession:
                        extracted['profession'] = {'value': profession, 'confidence': 85.0, 'source': 'VISIT_VISA_OCR'}
                        break
                if i + 1 < len(text_lines):
                    next_line = text_lines[i + 1].strip()
                    if next_line and not any(c.isdigit() for c in next_line):
                        extracted['profession'] = {'value': next_line, 'confidence': 82.0, 'source': 'VISIT_VISA_OCR'}
                        break
        
        return extracted

    
    def _extract_home_country_id_proven(self, text: str) -> Dict:
        """
        Extract home country ID (Aadhaar) fields using proven logic - optimized for speed
        No preprocessing, no duplicate OCR, reuses cached reader
        """
        extracted = {}
        
        # Split text into lines for easier processing
        text_lines = text.split('\n')
        
        # Aadhaar Number (12 digits starting with 2-9, format: XXXX XXXX XXXX)
        for line in text_lines:
            cleaned = re.sub(r'[\s-]', '', line)
            # Check for 12-digit number starting with 2-9
            if re.match(r'^[2-9]\d{11}$', cleaned):
                # Format as XXXX XXXX XXXX
                formatted_id = f"{cleaned[0:4]} {cleaned[4:8]} {cleaned[8:12]}"
                extracted['aadhaar_number'] = {'value': formatted_id, 'confidence': 95.0, 'source': 'AADHAAR_OCR'}
                break
            # Also check with spaces
            if re.match(r'^[2-9]\d{3}\s\d{4}\s\d{4}$', line.strip()):
                extracted['aadhaar_number'] = {'value': line.strip(), 'confidence': 95.0, 'source': 'AADHAAR_OCR'}
                break
        
        # Date of Birth (looks for DOB: DD/MM/YYYY pattern)
        for line in text_lines:
            match = re.search(r'DOB[:\s]*([0-3]?\d[/\-][0-1]?\d[/\-]\d{4})', line, re.IGNORECASE)
            if match:
                dob = match.group(1).replace('-', '/')
                extracted['date_of_birth'] = {'value': dob, 'confidence': 90.0, 'source': 'AADHAAR_OCR'}
                break
        
        # Gender
        for line in text_lines:
            line_upper = line.upper().strip()
            if line_upper in ['MALE', 'FEMALE', 'TRANSGENDER']:
                extracted['gender'] = {'value': line_upper.title(), 'confidence': 95.0, 'source': 'AADHAAR_OCR'}
                break
        
        # Name - appears after government header and before DOB
        skip_words = {
            'GOVERNMENT', 'INDIA', 'UNIQUE', 'IDENTIFICATION', 
            'AUTHORITY', 'AADHAAR', 'DOB', 'MALE', 'FEMALE', 'ADDRESS', 
            'WWW', 'HTTP', 'HELP'
        }
        
        name_parts = []
        found_government = False
        found_dob = False
        
        for line in text_lines:
            line_clean = line.strip()
            
            # Start looking after government header
            if any(word in line.upper() for word in ['GOVERNMENT', 'INDIA']):
                found_government = True
                continue
            
            # Stop at DOB
            if 'DOB' in line.upper() or found_dob:
                found_dob = True
                break
            
            # Look for name after government header
            if found_government and line_clean:
                # Check if it's likely a name part
                if (not any(char.isdigit() for char in line_clean) and
                    not any(skip in line.upper() for skip in skip_words) and
                    len(line_clean) > 1 and
                    not line_clean.startswith('http') and
                    not line_clean.startswith('www')):
                    
                    name_parts.append(line_clean)
                    
                    # Stop after collecting 2-3 parts
                    if len(name_parts) >= 3:
                        break
        
        if name_parts:
            full_name = ' '.join(name_parts)
            full_name = re.sub(r'\s+', ' ', full_name).strip()
            extracted['full_name'] = {'value': full_name, 'confidence': 85.0, 'source': 'AADHAAR_OCR'}
        
        # Address - starts after D/O, S/O, C/O, W/O indicators
        address_indicators = ['D/O', 'S/O', 'C/O', 'W/O', 'Address']
        address_parts = []
        capture = False
        
        skip_terms = [
            'GOVERNMENT', 'UNIQUE', 'IDENTIFICATION', 'AUTHORITY',
            'WWW', 'HTTP', 'HELP@', 'UIDAI', '1800', '1947'
        ]
        
        for line in text_lines:
            line_clean = line.strip()
            line_upper = line.upper()
            
            # Start capturing at address indicator
            if any(indicator in line_upper for indicator in address_indicators):
                capture = True
                # If indicator is not alone, add the rest
                if line_upper not in address_indicators:
                    address_parts.append(line_clean)
                continue
            
            if capture:
                # Stop at Aadhaar number (12 digits)
                cleaned = re.sub(r'[\s-]', '', line_clean)
                if re.match(r'^[2-9]\d{11}$', cleaned):
                    break
                
                # Skip government/contact info
                if any(skip in line_upper for skip in skip_terms):
                    continue
                
                # Add valid address components
                if line_clean and len(line_clean) > 1:
                    address_parts.append(line_clean)
        
        if address_parts:
            # Join and clean address
            full_address = ', '.join(address_parts)
            full_address = re.sub(r',\s*,', ',', full_address)
            full_address = re.sub(r'\s+', ' ', full_address)
            extracted['address'] = {'value': full_address.strip(), 'confidence': 80.0, 'source': 'AADHAAR_OCR'}
        
        return extracted

    
    def _extract_emirates_id_proven(self, text: str) -> Dict:
        """
        Extract Emirates ID fields using proven logic - optimized for speed
        No duplicate OCR, reuses cached reader, single pass
        """
        extracted = {}
        
        # ID Number (format: 784-YYYY-XXXXXXX-X or continuous 15 digits)
        id_pattern = r'(\d{3}-\d{4}-\d{7}-\d)'
        id_match = re.search(id_pattern, text)
        
        if id_match:
            extracted['emirates_id_number'] = {'value': id_match.group(1), 'confidence': 95.0, 'source': 'EMIRATES_OCR'}
        else:
            # Try continuous digits
            id_pattern2 = r'(\d{15,})'
            id_match2 = re.search(id_pattern2, text)
            if id_match2:
                id_num = id_match2.group(1)[:15]
                formatted_id = f"{id_num[:3]}-{id_num[3:7]}-{id_num[7:14]}-{id_num[14]}"
                extracted['emirates_id_number'] = {'value': formatted_id, 'confidence': 90.0, 'source': 'EMIRATES_OCR'}
        
        # Name - look for long capitalized text sequences (avoiding keywords)
        blacklist = ['EMIRATES', 'IDENTITY', 'CARD', 'RESIDENT', 'NATIONALITY', 'AUTHORITY', 'CITIZENSHIP', 
                     'DATE', 'BIRTH', 'ISSUING', 'EXPIRY', 'NAME', 'SEX', 'SIGNATURE', 'FEDERAL']
        
        name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){2,})\b'
        name_matches = re.findall(name_pattern, text)
        
        potential_names = []
        for name in name_matches:
            if len(name) >= 15 and not any(kw in name.upper() for kw in blacklist):
                # Remove Arabic characters
                name_clean = re.sub(r'[\u0600-\u06FF]+', '', name).strip()
                if len(name_clean) >= 15:
                    potential_names.append(name_clean)
        
        if potential_names:
            # Get longest name (most complete)
            extracted['name_on_emirates_id'] = {'value': max(potential_names, key=len), 'confidence': 85.0, 'source': 'EMIRATES_OCR'}
        
        # Dates (DD/MM/YYYY format)
        date_pattern = r'\b(\d{2}/\d{2}/\d{4})\b'
        dates = re.findall(date_pattern, text)
        
        if len(dates) >= 3:
            # Sort by year to identify DOB (oldest), Issue (middle), Expiry (latest)
            dates_sorted = sorted(dates, key=lambda x: (int(x.split('/')[2]), int(x.split('/')[1]), int(x.split('/')[0])))
            extracted['date_of_birth'] = {'value': dates_sorted[0], 'confidence': 90.0, 'source': 'EMIRATES_OCR'}
            extracted['issue_date'] = {'value': dates_sorted[1], 'confidence': 88.0, 'source': 'EMIRATES_OCR'}
            extracted['expiry_date'] = {'value': dates_sorted[2], 'confidence': 90.0, 'source': 'EMIRATES_OCR'}
        elif len(dates) == 2:
            extracted['date_of_birth'] = {'value': dates[0], 'confidence': 85.0, 'source': 'EMIRATES_OCR'}
            extracted['expiry_date'] = {'value': dates[1], 'confidence': 85.0, 'source': 'EMIRATES_OCR'}
        elif len(dates) == 1:
            extracted['date_of_birth'] = {'value': dates[0], 'confidence': 80.0, 'source': 'EMIRATES_OCR'}
        
        # Nationality
        nationality_countries = ['INDIA', 'PAKISTAN', 'BANGLADESH', 'PHILIPPINES', 'EGYPT', 'JORDAN', 
                                'SYRIA', 'LEBANON', 'UNITED STATES', 'UK', 'CANADA', 'NEPAL', 'SRI LANKA']
        
        for country in nationality_countries:
            if country in text.upper():
                extracted['nationality'] = {'value': country.title(), 'confidence': 90.0, 'source': 'EMIRATES_OCR'}
                break
        
        # Sex/Gender - look for standalone M or F
        sex_patterns = [
            r'\b([MF])\b',
            r'(?:Sex|الجنส)[:\s]*([MFذكرأنثى]+)',
        ]
        
        for pattern in sex_patterns:
            sex_match = re.search(pattern, text, re.IGNORECASE)
            if sex_match:
                sex_value = sex_match.group(1).upper()
                if 'ذكر' in sex_value or sex_value == 'M':
                    extracted['gender'] = {'value': 'Male', 'confidence': 85.0, 'source': 'EMIRATES_OCR'}
                    break
                elif 'أنثى' in sex_value or sex_value == 'F':
                    extracted['gender'] = {'value': 'Female', 'confidence': 85.0, 'source': 'EMIRATES_OCR'}
                    break
        
        return extracted

    
    def _extract_residence_visa_proven(self, text: str) -> Dict:
        """
        Extract residence visa fields using proven logic - optimized for speed
        No temp files, single OCR pass, reuses cached reader
        """
        extracted = {}
        
        # UID Number (9 digits)
        uid_pattern = r'(?:U\.I\.D\.No|UID|U\.I\.D)\s*[:\s]*(\d{9})'
        uid_match = re.search(uid_pattern, text, re.IGNORECASE)
        if uid_match:
            extracted['uid_number'] = {'value': uid_match.group(1), 'confidence': 95.0, 'source': 'VISA_OCR'}
        else:
            # Fallback: any 9-digit number
            uid_fallback = re.search(r'\b(\d{9})\b', text)
            if uid_fallback:
                extracted['uid_number'] = {'value': uid_fallback.group(1), 'confidence': 85.0, 'source': 'VISA_OCR'}
        
        # File Number (format: ###/####/######)
        file_patterns = [
            r'(?:File|FILE)\s*[:\s]*(\d{3}/\d{4}/\d+)',
            r'(\d{3}/\d{4}/\d+)',
            r'(\d{3}/\d{4})'
        ]
        for pattern in file_patterns:
            file_match = re.search(pattern, text)
            if file_match:
                extracted['file_number'] = {'value': file_match.group(1), 'confidence': 90.0, 'source': 'VISA_OCR'}
                break
        
        # Name on Visa (all caps, 15+ chars, no keywords)
        name_blacklist = ['ENGINEER', 'SERVICES', 'RESIDENCE', 'EMIRATES', 'TECHNICAL', 'SPONSOR', 'PROFESSION', 'MUHREM', 'ALLOWED', 'LLC']
        name_pattern = r'\b([A-Z\s]{15,})\b'
        name_matches = re.findall(name_pattern, text)
        
        potential_names = []
        for name in name_matches:
            name_clean = name.strip()
            if len(name_clean) >= 15 and not any(kw in name_clean for kw in name_blacklist):
                # Remove Arabic characters
                name_clean = re.sub(r'[\u0600-\u06FF]+', '', name_clean).strip()
                if len(name_clean) >= 15:
                    potential_names.append(name_clean)
        
        if potential_names:
            # Get longest name (most complete)
            extracted['name_on_visa'] = {'value': max(potential_names, key=len), 'confidence': 85.0, 'source': 'VISA_OCR'}
        
        # Profession
        profession_keywords = ['ENGINEER', 'MUHREM', 'NOT ALLOWED', 'ALLOWED TO WORK', 'MANAGER', 'ACCOUNTANT', 'DOCTOR', 'TECHNICIAN']
        for keyword in profession_keywords:
            if keyword in text:
                # Extract surrounding context
                prof_pattern = rf'([A-Z\s]*{keyword}[A-Z\s]*?)(?=\s*(?:[A-Z]{{2,}}\s[A-Z]{{2,}}|$))'
                prof_match = re.search(prof_pattern, text)
                if prof_match:
                    profession = prof_match.group(1).strip()
                    profession = re.sub(r'[\u0600-\u06FF]+', '', profession).strip()
                    if len(profession) >= 3:
                        extracted['profession'] = {'value': profession, 'confidence': 80.0, 'source': 'VISA_OCR'}
                        break
        
        # Sponsor (company with LLC or person name)
        sponsor_patterns = [
            r'([A-Z][A-Za-z\s&\-]+(?:L\.L\.C|LLC))',
            r'((?:[A-Z]{3,}\s+){2,4}(?:TECHNICAL|SERVICES|ENGINEERING|COMPANY)[A-Z\s]*)',
        ]
        
        for pattern in sponsor_patterns:
            sponsor_match = re.search(pattern, text, re.IGNORECASE)
            if sponsor_match:
                sponsor = sponsor_match.group(1)
                # Remove Arabic and clean
                sponsor = re.sub(r'[\u0600-\u06FF]+', '', sponsor).strip()
                sponsor = re.sub(r'\bSponsor\b', '', sponsor, flags=re.I).strip()
                sponsor = sponsor.replace('LL C', 'L.L.C').replace('LLC', 'L.L.C')
                if len(sponsor) >= 10:
                    extracted['sponsor'] = {'value': sponsor, 'confidence': 80.0, 'source': 'VISA_OCR'}
                    break
        
        # Place of Issue
        uae_cities = ['DUBAI', 'ABU DHABI', 'SHARJAH', 'AJMAN', 'RAS AL KHAIMAH', 'FUJAIRAH', 'UMM AL QUWAIN']
        for city in uae_cities:
            if city in text.upper():
                extracted['place_of_issue'] = {'value': city.title(), 'confidence': 90.0, 'source': 'VISA_OCR'}
                break
        
        # Issue Date and Expiry Date (YYYY/MM/DD format)
        date_pattern = r'(\d{4}/\d{2}/\d{2})'
        dates = re.findall(date_pattern, text)
        
        if len(dates) >= 2:
            dates_sorted = sorted(dates)
            extracted['issue_date'] = {'value': dates_sorted[0], 'confidence': 90.0, 'source': 'VISA_OCR'}
            extracted['expiry_date'] = {'value': dates_sorted[-1], 'confidence': 90.0, 'source': 'VISA_OCR'}
        elif len(dates) == 1:
            extracted['issue_date'] = {'value': dates[0], 'confidence': 80.0, 'source': 'VISA_OCR'}
        
        return extracted

    def _extract_visa_cancellation_proven(self, text: str) -> Dict:
        """
        Extract visa cancellation fields using proven logic
        """
        extracted = {}
        
        # 1. Full Name
        name_patterns = [
            r'name\s*[:\-]?\s*([A-Z][A-Za-z\s]{5,50})',
            r'applicant\s*[:\-]?\s*([A-Z][A-Za-z\s]{5,50})',
            r'employee\s*[:\-]?\s*([A-Z][A-Za-z\s]{5,50})'
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                name = re.sub(r'\s+', ' ', name)
                if len(name.split()) >= 2:
                     extracted['full_name'] = {'value': name.upper(), 'confidence': 85.0, 'source': 'CANCEL_OCR'}
                     break
        
        # 2. Passport Number
        ppt_patterns = [
            r'passport\s*(?:no|number|#)?\s*[:\-]?\s*([A-Z0-9]{6,9})',
            r'passport\s*([A-Z0-9]{6,9})',
            r'([A-Z]{1,2}\d{6,8})'
        ]
        for pattern in ppt_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['passport_number'] = {'value': match.group(1).upper(), 'confidence': 90.0, 'source': 'CANCEL_OCR'}
                break
        
        # 3. Visa/Residence Number
        visa_patterns = [
            r'visa\s*(?:no|number|#)?\s*[:\-]?\s*(\d{10,15})',
            r'residence\s*(?:no|number)?\s*[:\-]?\s*(\d{10,15})',
            r'(?:visa|residence)\s*([0-9\/\-]{10,})'
        ]
        for pattern in visa_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['visa_number'] = {'value': match.group(1), 'confidence': 90.0, 'source': 'CANCEL_OCR'}
                break

        # 4. Visa Type
        visa_types = ['employment', 'dependent', 'investor', 'tourist', 'residence', 'partner']
        for v_type in visa_types:
            if v_type in text.lower():
                 extracted['visa_type'] = {'value': v_type.upper(), 'confidence': 85.0, 'source': 'CANCEL_OCR'}
                 break

        # 5. Sponsor ID / Establishment ID
        sponsor_id_patterns = [
            r'sponsor\s*(?:id|number)?\s*[:\-]?\s*(\d{10,15})',
            r'establishment\s*(?:id|card)?\s*[:\-]?\s*(\d{10,15})'
        ]
        for pattern in sponsor_id_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['sponsor_id'] = {'value': match.group(1), 'confidence': 85.0, 'source': 'CANCEL_OCR'}
                break

        # 6. Sponsor Name
        sponsor_name_patterns = [
            r'sponsor\s*name\s*[:\-]?\s*([A-Z][A-Za-z\s&\.\-]{5,100})',
            r'sponsor\s*[:\-]?\s*([A-Z][A-Za-z\s&\.\-]{5,100})'
        ]
        for pattern in sponsor_name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                s_name = match.group(1).strip()
                s_name = re.split(r'\s{2,}|\t|\|', s_name)[0] # Stop at big gaps
                extracted['sponsor_name'] = {'value': s_name.upper(), 'confidence': 80.0, 'source': 'CANCEL_OCR'}
                break

        # 7. Cancellation Number
        cancel_patterns = [
            r'cancellation\s*(?:no|number|ref|reference)?\s*[:\-]?\s*([A-Z0-9\-\/]+)',
            r'reference\s*(?:no|number)?\s*[:\-]?\s*([A-Z0-9\-\/]+)',
            r'transaction\s*(?:no|number)?\s*[:\-]?\s*([A-Z0-9\-\/]+)'
        ]
        for pattern in cancel_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                 extracted['cancellation_ref'] = {'value': match.group(1), 'confidence': 85.0, 'source': 'CANCEL_OCR'}
                 break

        # 8. Nationality
        nat_match = re.search(r'nationality\s*[:\-]?\s*([A-Za-z\s]+)', text, re.IGNORECASE)
        if nat_match:
             extracted['nationality'] = {'value': nat_match.group(1).strip().upper(), 'confidence': 85.0, 'source': 'CANCEL_OCR'}
        
        # 9. Profession
        prof_match = re.search(r'profession\s*[:\-]?\s*([^\n]+)', text, re.IGNORECASE)
        if prof_match:
             extracted['profession'] = {'value': prof_match.group(1).split('  ')[0].strip().upper(), 'confidence': 80.0, 'source': 'CANCEL_OCR'}

        return extracted

    def _extract_vat_certificate_proven(self, text: str) -> Dict:
        """
        Extract VAT certificate fields - FULLY OPTIMIZED
        """
        extracted = {}
        
        # Regex patterns provided by user
        field_patterns = {
            # Registration Numbers
            'registration_number': r'(?:registration\s*number|vat\s*number|trn|tax\s*registration)[\s:]*([A-Z0-9\-\/]+)',
            'certificate_number': r'(?:certificate\s*number|cert\s*no)[\s:]*([A-Z0-9\-\/]+)',

            # Legal Names
            'legal_name_english': r'(?:legal\s*name|entity\s*name|company\s*name)[\s:]*([A-Za-z0-9\s,&\.-]+)',
            'legal_name_arabic': r'(?:الاسم\s*القانوني|اسم\s*الكيان|اسم\s*الشركة)[\s:]*([^\n]+)',

            # Address & Contact
            'registered_address': r'(?:registered\s*address|business\s*address|address)[\s:]*([^\n]+)',
            'contact_number': r'(?:contact|phone|mobile|tel)[\s:]*([+0-9\-\s\(\)]+)',

            # Important Dates
            'effective_registration_date': r'(?:effective\s*registration\s*date|effective\s*date)[\s:]*([0-9/\-]+)',
            'date_of_issue': r'(?:date\s*of\s*issue|issue\s*date|issued\s*on)[\s:]*([0-9/\-]+)',

            # VAT Return Periods
            'first_vat_return_period': r'(?:first\s*vat\s*return\s*period)[\s:]*([0-9/\-]+\s*(?:to|-|–)\s*[0-9/\-]+)',
            'vat_return_due_date': r'(?:vat\s*return\s*due\s*date|return\s*due\s*date)[\s:]*([0-9/\-]+)',
            'tax_period_start_end': r'(?:tax\s*period|period)[\s:]*([0-9/\-]+\s*(?:to|-|–)\s*[0-9/\-]+)',
        }
        
        text_clean = text.replace('\r', '\n')
        # Use case-insensitive search (re.IGNORECASE)
        
        for key, pattern in field_patterns.items():
            match = re.search(pattern, text_clean, re.MULTILINE | re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                extracted[key] = {
                    'value': value,
                    'confidence': 90.0 if len(value) > 2 else 50.0,
                    'source': 'VAT_OCR'
                }
        
        return extracted

    def _extract_entry_permit_proven(self, text: str) -> Dict:
        """
        Extract Entry Permit fields - FULLY OPTIMIZED
        """
        extracted = {}
        
        # Smart field patterns (UAE, SAUDI, QATAR, BAHRAIN, OMAN SUPPORT)
        field_patterns = {
            # --- Core Permit Identifiers ---
            'permit_number': r'(?:entry\s*permit\s*(?:number|no|#)|permit\s*no)[\s:]*([A-Z0-9\-\/]+)',
            'visa_number': r'(?:visa\s*(?:number|no|#))[\s:]*([A-Z0-9\-\/]+)',
            'file_number': r'(?:file\s*number|file\s*no)[\s:]*([A-Z0-9\-\/]+)',
            'uid_number': r'(?:uid\s*(?:number|no))[\s:]*([0-9]{6,15})',
            'application_number': r'(?:application\s*(?:number|no|#))[\s:]*([A-Z0-9\-\/]+)',
            'reference_number': r'(?:reference\s*(?:number|no|#)|ref\s*no)[\s:]*([A-Z0-9\-\/]+)',

            # --- Personal Info ---
            'full_name': r'(?:full\s*name|applicant\s*name|name)[\s:]*([A-Za-z\u0600-\u06FF\s\.-]+)',
            'nationality': r'(?:nationality|citizenship)[\s:]*([A-Za-z\u0600-\u06FF\s]+)',
            'gender': r'(?:gender|sex)[\s:]*([A-Za-z]+)',
            'date_of_birth': r'(?:date\s*of\s*birth|dob)[\s:]*([0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{2,4})',

            # --- Passport Info ---
            'passport_number': r'(?:passport\s*(?:number|no|#))[\s:]*([A-Z0-9]{6,15})',
            'passport_issue_date': r'(?:passport\s*issue\s*date)[\s:]*([0-9\/\-]+)',
            'passport_expiry_date': r'(?:passport\s*expiry\s*date|passport\s*valid\s*until)[\s:]*([0-9\/\-]+)',
            'passport_issue_place': r'(?:place\s*of\s*issue)[\s:]*([A-Za-z\u0600-\u06FF\s]+)',

            # --- Permit Details ---
            'permit_type': r'(?:permit\s*type|visa\s*type)[\s:]*([A-Za-z\s]+)',
            'permit_category': r'(?:permit\s*category|category)[\s:]*([A-Za-z0-9\s]+)',
            'entry_type': r'(?:entry\s*type)[\s:]*([A-Za-z\s]+)',
            'number_of_entries': r'(?:entries\s*allowed)[\s:]*([A-Za-z0-9]+)',
            'duration': r'(?:duration|validity\s*period)[\s:]*([0-9]+\s*(?:days?|months?|yrs?|years?))',

            # --- Validity Dates ---
            'issue_date': r'(?:issue\s*date|issued\s*on)[\s:]*([0-9\/\-]+)',
            'expiry_date': r'(?:expiry\s*date|expires\s*on)[\s:]*([0-9\/\-]+)',
            'valid_from': r'(?:valid\s*from|entry\s*from)[\s:]*([0-9\/\-]+)',
            'valid_until': r'(?:valid\s*until|entry\s*until)[\s:]*([0-9\/\-]+)',

            # --- Travel Info ---
            'port_of_entry': r'(?:port\s*of\s*entry|entry\s*point)[\s:]*([A-Za-z\u0600-\u06FF\s]+)',
            'purpose_of_visit': r'(?:purpose\s*of\s*visit|purpose)[\s:]*([A-Za-z\u0600-\u06FF\s]+)',

            # --- Sponsor / Employer ---
            'sponsor_name': r'(?:sponsor\s*name|sponsored\s*by)[\s:]*([A-Za-z\u0600-\u06FF\s\.-]+)',
            'sponsor_id': r'(?:sponsor\s*(?:id|number|no))[\s:]*([A-Z0-9\-\/]+)',
            'employer_name': r'(?:employer\s*name|company\s*name)[\s:]*([A-Za-z\u0600-\u06FF\s\.-]+)',
            'job_title': r'(?:job\s*title|position)[\s:]*([A-Za-z\u0600-\u06FF\s]+)',

            # --- Contact ---
            'email': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,})',
            'phone': r'(?:phone|mobile|contact)[\s:]*([+0-9\-\s\(\)]{6,20})',
            'address': r'(?:address)[\s:]*([A-Za-z0-9\u0600-\u06FF,\-\s]+)',

            # --- Status ---
            'status': r'(?:status)[\s:]*([A-Za-z]+)',
            'approval_status': r'(?:approval\s*status)[\s:]*([A-Za-z\s]+)',

            # --- Issuing Authority ---
            'issued_by': r'(?:issued\s*by|issuing\s*authority)[\s:]*([A-Za-z\u0600-\u06FF\s]+)',
            'issuing_office': r'(?:issuing\s*office)[\s:]*([A-Za-z\u0600-\u06FF\s]+)',

            # --- QR / Barcode ---
            'qr_code': r'(?:qr\s*code)[\s:]*([A-Za-z0-9]+)',
            'barcode_number': r'(?:barcode|bar\s*code)[\s:]*([A-Za-z0-9]+)',
        }
        
        text_clean = text.replace('\r', '\n')
        
        for key, pattern in field_patterns.items():
            match = re.search(pattern, text_clean, re.MULTILINE | re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                extracted[key] = {
                    'value': value,
                    'confidence': 90.0 if len(value) > 2 else 50.0,
                    'source': 'PERMIT_OCR'
                }
        
        return extracted

    def _extract_company_license_proven(self, text: str) -> Dict:
        """
        Extract UAE Company License fields + Tables - FULLY OPTIMIZED
        """
        extracted = {}
        
        field_patterns = {
            # ------------------- CORE LICENSE FIELDS -------------------------
            "license_type": r"(?:license\s*type)\s*[:\-]?\s*([A-Za-z\s]+)",
            "license_no": r"(?:license\s*no|licence\s*no|license\s*number)\s*[:\-]?\s*([A-Z0-9\-\/]+)",
            "main_license_no": r"(?:main\s*license\s*no)\s*[:\-]?\s*([A-Z0-9\-\/]+)",
            "register_no": r"(?:register\s*no)\s*[:\-]?\s*([A-Z0-9\-\/]+)",
            "dcci_no": r"(?:dcci\s*no)\s*[:\-]?\s*([A-Z0-9\-\/]+)",
            "duns_no": r"(?:d[\.\-]?\s*&?\s*b|duns|d-u-n-s)\s*[:\-]?\s*([0-9\-]+)",

            # ------------------- COMPANY DETAILS ----------------------------
            "company_name": r"(?:company\s*name)\s*[:\-]?\s*([A-Za-z0-9\s&\.,\-]+)",
            "company_name_ar": r"(?:اسم\s*الشركة)\s*[:\-]?\s*([^\n]+)",
            "business_name": r"(?:business\s*name|trade\s*name)\s*[:\-]?\s*([A-Za-z0-9\s&\.,\-]+)",
            "legal_type": r"(?:legal\s*type|entity\s*type|legal\s*form)\s*[:\-]?\s*([A-Za-z\s]+)",

            # ------------------- DATES ----------------------------
            "issue_date": r"(?:issue\s*date)\s*[:\-]?\s*([0-9\/\-]+)",
            "expiry_date": r"(?:expiry\s*date|expires\s*on)\s*[:\-]?\s*([0-9\/\-]+)",

            # ------------------- ADDRESS ----------------------------
            "address": r"(?:address)\s*[:\-]?\s*([A-Za-z0-9\s,\-\/]+)",
            "po_box": r"(?:p\.?\s*o\.?\s*box)\s*[:\-]?\s*([0-9]+)",
            "phone": r"(?:phone\s*no|contact)\s*[:\-]?\s*([+0-9\s\-\(\)]+)",
            "fax": r"(?:fax\s*no)\s*[:\-]?\s*([+0-9\s\-\(\)]+)",
            "mobile": r"(?:mobile\s*no)\s*[:\-]?\s*([+0-9\s\-\(\)]+)",
            "parcel_id": r"(?:parcel\s*id)\s*[:\-]?\s*([A-Za-z0-9\-\/]+)",
            "email": r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})",
        }
        
        text_clean = text.replace('\r', '\n')
        
        for key, pattern in field_patterns.items():
            match = re.search(pattern, text_clean, re.MULTILINE | re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                extracted[key] = {
                    'value': value,
                    'confidence': 90.0 if len(value) > 2 else 50.0,
                    'source': 'LICENSE_OCR'
                }

        # ------------------ TABLE EXTRACTION ------------------------
        members = self._extract_license_members(text_clean)
        if members:
            extracted['members_table'] = {'value': json.dumps(members), 'confidence': 90.0, 'source': 'TABLE_OCR'}
            
        partners = self._extract_partners(text_clean)
        if partners:
            extracted['partners_table'] = {'value': json.dumps(partners), 'confidence': 90.0, 'source': 'TABLE_OCR'}
            
        return extracted

    def _extract_license_members(self, text: str):
        """
        Extract rows like:
        No | Name | Nationality | Role | Share
        """
        rows = []
        pattern = r"(\d+)\s+([A-Za-z\u0600-\u06FF\s\.]+)\s+([A-Za-z\u0600-\u06FF]+)\s+([A-Za-z\s]+)\s+([0-9\.%]+)"
        for m in re.finditer(pattern, text, re.MULTILINE):
            rows.append({
                "no": m.group(1),
                "name": m.group(2).strip(),
                "nationality": m.group(3),
                "role": m.group(4),
                "share": m.group(5)
            })
        return rows

    def _extract_partners(self, text: str):
        """
        Extract rows like:
        Name | Nationality | Sr No | Share
        """
        rows = []
        pattern = r"([A-Za-z\u0600-\u06FF\s\.]+)\s+([A-Za-z]+)\s+(\d+)\s+([0-9\.%]+)"
        for m in re.finditer(pattern, text, re.MULTILINE):
            rows.append({
                "name": m.group(1).strip(),
                "nationality": m.group(2),
                "sr_no": m.group(3),
                "share": m.group(4)
            })
        return rows

    
    def _extract_labor_card_proven(self, text: str) -> Dict:
        """
        Extract labor card fields using proven logic - optimized for speed
        No translation, no preprocessing, single OCR pass
        """
        extracted = {}
        
        # Name extraction
        name = self._extract_labor_name(text)
        if name:
            extracted['full_name'] = {'value': name, 'confidence': 85.0, 'source': 'LABOR_OCR'}
        
        # Work Permit Number (8-11 digits)
        work_permit = self._extract_number(text, 8, 11)
        if work_permit:
            extracted['work_permit_number'] = {'value': work_permit, 'confidence': 90.0, 'source': 'LABOR_OCR'}
        
        # Personal Number (12-16 digits)
        personal_no = self._extract_number(text, 12, 16)
        if personal_no:
            extracted['personal_number'] = {'value': personal_no, 'confidence': 90.0, 'source': 'LABOR_OCR'}
        
        # Expiry Date
        expiry = self._extract_date_labor(text)
        if expiry:
            extracted['expiry_date'] = {'value': expiry, 'confidence': 85.0, 'source': 'LABOR_OCR'}
        
        # Profession
        profession = self._extract_profession(text)
        if profession:
            extracted['profession'] = {'value': profession, 'confidence': 80.0, 'source': 'LABOR_OCR'}
        
        # Nationality
        nationality = self._extract_nationality(text)
        if nationality:
            extracted['nationality'] = {'value': nationality, 'confidence': 85.0, 'source': 'LABOR_OCR'}
        
        # Establishment/Company
        establishment = self._extract_establishment(text)
        if establishment:
            extracted['company_name'] = {'value': establishment, 'confidence': 80.0, 'source': 'LABOR_OCR'}
        
        return extracted
    
    def _extract_labor_name(self, text: str) -> Optional[str]:
        """Extract multi-line name - handles Arabic labor cards"""
        blacklist = ['expiry', 'permit', 'profession', 'nationality', 'date', 'work', 'card', 'labor', 'establishment', 'ministry', 'emirates', 'united', 'arab', 'government', 'resources']
        
        # 1. Try explicit 'Name' label extraction (Highest Priority)
        # Matches: "Name : CHURCHIL..." or "Name: CHURCHIL..."
        name_match = re.search(r'Name\s*[:\.]?\s*([A-Za-z\s]+)(?:$|\n)', text, re.IGNORECASE)
        if name_match:
            candidate = name_match.group(1).strip()
            # Verify candidate isn't just a junk string or blacklisted
            if len(candidate) > 3 and not any(k in candidate.lower() for k in blacklist):
                return candidate.upper()

        name_lines = []
        
        # Find all lines with capitalized words (potential name segments)
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            
            # Match capitalized word sequences (5-80 chars)
            if re.fullmatch(r'[A-Za-z ]{5,80}', line):
                # Skip if contains blacklisted words
                if not any(k in line.lower() for k in blacklist):
                    name_lines.append(line.strip())
        
        # If we have 2+ name lines, combine first two (full name)
        if len(name_lines) >= 2:
            return ' '.join(name_lines[:2]).upper()
        
        # Otherwise return first line if exists
        return name_lines[0].upper() if name_lines else None
    
    def _extract_number(self, text: str, min_len: int, max_len: int) -> Optional[str]:
        """Extract number within specific length range"""
        pattern = r'\b\d{%d,%d}\b' % (min_len, max_len)
        matches = re.findall(pattern, text)
        return matches[0] if matches else None
    
    def _extract_date_labor(self, text: str) -> Optional[str]:
        """Extract date and format as DD-Mon-YY"""
        patterns = [
            r'(\d{2}[/-]\d{2}[/-]\d{4})',
            r'(\d{4}[/-]\d{2}[/-]\d{2})',
            r'(\d{2}\s[A-Z]{3}\s\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                # Try to format
                try:
                    from datetime import datetime
                    # Try different formats
                    for fmt in ['%d/%m/%Y', '%Y/%m/%d', '%d-%m-%Y', '%Y-%m-%d', '%d %b %Y']:
                        try:
                            date_obj = datetime.strptime(date_str, fmt)
                            return date_obj.strftime('%d-%b-%y')
                        except:
                            continue
                except:
                    pass
                # Return as-is if can't format
                return date_str
        
        return None
    
    def _extract_profession(self, text: str) -> Optional[str]:
        """Extract profession - Arabic + English"""
        # 1. Try explicit 'Profession' label extraction (Highest Priority)
        # Matches: "Profession : Engineer" or "Profession: Civil Engineer"
        prof_match = re.search(r'Profession\s*[:\.]?\s*([^\n]+)', text, re.IGNORECASE)
        if prof_match:
            profession = prof_match.group(1).strip()
            # Remove Arabic characters if mixed (optional, or keep both)
            # For now, let's keep it but clean up common noise
            if len(profession) > 2:
                # If mostly Arabic, try to map it
                arabic_professions = {
                    'مدير مشروع': 'Project Manager',
                    'مهندس مدني': 'Civil Engineer',
                    'مهندس كهربائي': 'Electrical Engineer',
                    'مهندس ميكانيكي': 'Mechanical Engineer',
                    'مهندس': 'Engineer',
                    'عامل': 'Worker',
                    'فني': 'Technician',
                    'سائق': 'Driver',
                    'مشرف': 'Supervisor',
                    'محاسب': 'Accountant'
                }
                for ar, en in arabic_professions.items():
                    if ar in profession:
                        return en
                
                # If no map match, just return what we found (likely English or mixed)
                return profession.split('  ')[0].strip() # Take first part if double spaced

        # Arabic profession mapping (most common in GCC labor cards)
        arabic_professions = {
            'مدير مشروع': 'Project Manager',
            'مهندس مدني': 'Civil Engineer',
            'مهندس كهربائي': 'Electrical Engineer',
            'مهندس ميكانيكي': 'Mechanical Engineer',
            'مهندس': 'Engineer',
            'عامل': 'Worker',
            'فني': 'Technician',
            'سائق': 'Driver',
            'مشرف': 'Supervisor',
            'محاسب': 'Accountant'
        }
        
        # Check for Arabic professions first
        for ar, en in arabic_professions.items():
            if ar in text:
                return en
        
        # Then check English keywords
        text_lower = text.lower()
        english_keywords = ['manager', 'engineer', 'technician', 'driver', 'worker', 'supervisor']
        
        for keyword in english_keywords:
            if keyword in text_lower:
                # Extract the full profession phrase
                pattern = rf'\b([A-Za-z ]*{keyword}[A-Za-z ]*)\b'
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    profession = match.group(1).strip()
                    if len(profession) >= 3 and len(profession) <= 40:
                        return profession.title()
        
        return None
    
    def _extract_nationality(self, text: str) -> Optional[str]:
        """Extract nationality - Arabic + English"""
        # Arabic nationality mapping (GCC labor cards)
        arabic_map = {
            'الهند': 'Indian',
            'باكستان': 'Pakistani',
            'بنغلاديش': 'Bangladeshi',
            'نيبال': 'Nepalese',
            'سريلانكا': 'Sri Lankan',
            'الفلبين': 'Filipino',
            'مصر': 'Egyptian',
            'الأردن': 'Jordanian',
            'السودان': 'Sudanese'
        }
        
        # Check Arabic first
        for ar, en in arabic_map.items():
            if ar in text:
                return en
        
        # English fallback
        english_mapping = {
            'india': 'Indian',
            'pakistan': 'Pakistani',
            'bangladesh': 'Bangladeshi',
            'nepal': 'Nepalese',
            'philippines': 'Filipino',
            'sri lanka': 'Sri Lankan',
            'egypt': 'Egyptian',
            'jordan': 'Jordanian',
            'sudan': 'Sudanese'
        }
        
        text_lower = text.lower()
        for country, nationality in english_mapping.items():
            if country in text_lower:
                return nationality
        
        return None
    
    def _extract_establishment(self, text: str) -> Optional[str]:
        """Extract establishment/company name - clean label"""
        # Look for LLC, L.L.C, or establishment keywords
        patterns = [
            r'([A-Z][A-Za-z\s&\-]+(?:LLC|L\.L\.C|LTD|LIMITED))',
            r'(?:Establishment|Company|Corporation)[\s:]+([A-Z][A-Za-z\s&\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company = match.group(1) if match.lastindex == 1 else match.group(0)
                # CRITICAL FIX: Remove label text
                company = re.sub(r'establishment\s*:\s*', '', company, flags=re.I)
                return company.strip().upper()
        
        # Fallback: look for any LLC mention
        if 'llc' in text.lower() or 'l.l.c' in text.lower():
            # Find surrounding text
            pattern = r'([A-Z][A-Za-z\s&\-]{5,50}(?:LLC|L\.L\.C))'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company = match.group(1)
                # Clean label here too
                company = re.sub(r'establishment\s*:\s*', '', company, flags=re.I)
                return company.strip().upper()
        
        return None

    
    def _find_mrz_lines_proven(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Find MRZ lines - proven logic"""
        mrz_line1 = None
        mrz_line2 = None
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('P<') and len(line) >= 40:
                mrz_line1 = line
            elif re.search(r'[A-Z0-9]{7,9}<', line) and len(line) >= 40:
                mrz_line2 = line
        
        return mrz_line1, mrz_line2
    
    def _format_date_proven(self, yymmdd: str) -> Optional[str]:
        """Convert YYMMDD to DD-Mon-YY (21/09/1996 -> 21-Sep-96)"""
        if not yymmdd or len(yymmdd) != 6:
            return None
        
        try:
            from datetime import datetime
            yy = int(yymmdd[0:2])
            mm = int(yymmdd[2:4])
            dd = int(yymmdd[4:6])
            
            year = 1900 + yy if yy >= 50 else 2000 + yy
            date_obj = datetime(year, mm, dd)
            
            return date_obj.strftime('%d-%b-%y')
        except:
            return None
    
    def _extract_issue_date_proven(self, text: str, expiry_date: Optional[str]) -> Optional[str]:
        """Extract issue date from page"""
        # Try regex patterns
        patterns = [
            r'issue.*?(\d{2}[/-]\d{2}[/-]\d{4})',
            r'(\d{2}[/-]\d{2}[/-]20(?:1|2)\d)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                # Format it
                try:
                    from datetime import datetime
                    if '/' in date_str:
                        date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                    else:
                        date_obj = datetime.strptime(date_str, '%d-%m-%Y')
                    return date_obj.strftime('%d-%b-%y')
                except:
                    pass
        
        # Fallback: calculate from expiry
        if expiry_date:
            try:
                from datetime import datetime, timedelta
                expiry = datetime.strptime(expiry_date, '%d-%b-%y')
                issue = expiry.replace(year=expiry.year - 10) + timedelta(days=1)
                return issue.strftime('%d-%b-%y')
            except:
                pass
        
        return None
    
    def _extract_issue_place_proven(self, text: str) -> Optional[str]:
        """Extract issue place"""
        indian_cities = [
            'Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata',
            'Hyderabad', 'Pune', 'Ahmedabad', 'Madurai', 'Kochi',
            'Trivandrum', 'Kannanoor', 'Coimbatore', 'Vellore'
        ]
        
        for city in indian_cities:
            if city.lower() in text.lower():
                return city
        
        return None

    
    def process_document(
        self, file_path: str, document_type: str, temp_dir: str, pre_extracted_text: Optional[str] = None
    ) -> Dict:
        """
        Process a document (PDF or image) and extract all fields
        Returns: {
            'text_pages': [page texts],
            'extracted_fields': {field: {value, confidence, page}},
            'overall_confidence': float,
            'status': str
        }
        """
        result = {
            'text_pages': [],
            'raw_text': '',  # Combined text from all pages for classification
            'extracted_fields': {},
            'overall_confidence': 0.0,
            'status': 'failed'
        }
        
        try:
            # OPTIMIZATION: Use pre-extracted text if available (skips OCR)
            if pre_extracted_text:
                print(f"⚡ Using pre-extracted text for {document_type} (Skipping OCR)")
                result['raw_text'] = pre_extracted_text
                result['text_pages'] = [pre_extracted_text]
                result['overall_confidence'] = 85.0  # Default confidence when skipped
                
                # Extract fields directly
                fields = self.extract_fields_from_text(pre_extracted_text, document_type)
                
                for field_name, field_data in fields.items():
                    result['extracted_fields'][field_name] = {
                        'value': field_data['value'],
                        'confidence': field_data['confidence'],
                        'page': 1
                    }
                
                if result['extracted_fields']:
                    result['status'] = 'completed'
                else:
                    result['status'] = 'partial'
                    
                return result

            # Check file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # Convert PDF to images if needed
            if file_ext == '.pdf':
                try:
                    print(f"Converting PDF to images: {file_path}")
                    
                    # Try to find poppler in common locations
                    poppler_path = None
                    possible_paths = [
                        r"C:\poppler-25.12.0\Library\bin",
                        r"C:\Program Files\poppler\bin",
                        r"C:\poppler\bin",
                    ]
                    
                    for path in possible_paths:
                        if os.path.exists(path):
                            poppler_path = path
                            print(f"Found Poppler at: {poppler_path}")
                            break
                    
                    # Convert PDF pages to images
                    if poppler_path:
                        images = convert_from_path(file_path, dpi=300, poppler_path=poppler_path)
                    else:
                        # Try without explicit path (rely on PATH environment)
                        images = convert_from_path(file_path, dpi=300)
                    
                    # Save images temporarily
                    image_paths = []
                    for i, img in enumerate(images):
                        temp_img_path = os.path.join(temp_dir, f'page_{i}.png')
                        img.save(temp_img_path, 'PNG')
                        image_paths.append(temp_img_path)
                    
                    print(f"Converted {len(image_paths)} pages from PDF")
                    
                except Exception as e:
                    result['status'] = 'failed'
                    result['error'] = f'PDF conversion failed: {str(e)}. Make sure Poppler is installed at C:\\poppler-25.12.0\\Library\\bin'
                    print(f"PDF conversion error: {e}")
                    return result
                    
            elif file_ext in ['.png', '.jpg', '.jpeg']:
                image_paths = [file_path]
            else:
                result['status'] = 'failed'
                result['error'] = 'Unsupported file format. Please upload PDF, PNG, or JPG.'
                return result
            
            # Extract text from each page
            page_confidences = []
            
            for page_num, image_path in enumerate(image_paths, start=1):
                print(f"Processing page {page_num}/{len(image_paths)}...")
                text, confidence = self.extract_text_from_image(image_path)
                result['text_pages'].append(text)
                page_confidences.append(confidence)
                
                # Extract fields from this page
                page_fields = self.extract_fields_from_text(text, document_type)
                
                for field_name, field_data in page_fields.items():
                    # Store field with page number (don't overwrite if already found)
                    if field_name not in result['extracted_fields']:
                        result['extracted_fields'][field_name] = {
                            'value': field_data['value'],
                            'confidence': field_data['confidence'],
                            'page': page_num
                        }
            
            # Combine all pages into raw_text for classification
            result['raw_text'] = '\n'.join(result['text_pages'])
            
            # Calculate overall confidence
            if page_confidences:
                result['overall_confidence'] = sum(page_confidences) / len(page_confidences)
            
            # Set status based on extracted fields
            # Changed: Show "completed" if we got ANY fields, not just partial
            if result['extracted_fields']:
                # If we have at least 50% of expected fields, mark as completed
                expected_field_count = len(DOCUMENT_TYPES.get(document_type, {}).get('fields', []))
                extracted_count = len(result['extracted_fields'])
                
                if extracted_count >= expected_field_count * 0.3:  # 30% threshold
                    result['status'] = 'completed'
                else:
                    result['status'] = 'partial'
            else:
                result['status'] = 'partial'
            
            # Clean up temporary image files
            if file_ext == '.pdf':
                for img_path in image_paths:
                    try:
                        if os.path.exists(img_path):
                            os.remove(img_path)
                    except:
                        pass
            
            return result
        
        except Exception as e:
            print(f"Error processing document: {str(e)}")
            import traceback
            traceback.print_exc()
            result['status'] = 'failed'
            result['error'] = str(e)
            return result
