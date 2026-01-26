"""
Document Type Classifier
Automatically detects document type from uploaded files using keyword matching and pattern recognition.
"""

import re
from typing import Dict, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DocumentClassifier:
    """Classify documents based on text content and patterns."""
    
    def __init__(self):
        """Initialize classifier with detection patterns for each document type."""
        self.detection_patterns = {
            'PASSPORT': {
                'keywords': ['passport', 'passeport', 'passaporte', 'reisepass'],
                'patterns': [
                    r'P<[A-Z]{3}',  # MRZ line starting with P<
                    r'[A-Z0-9]{9}<<',  # Passport number in MRZ format
                    r'passport\s*(?:no|number|#)',
                ],
                'weight': 1.0
            },
            'LABOR_CARD': {
                'keywords': ['labor card', 'work permit', 'عمل', 'بطاقة'],
                'patterns': [
                    r'labor\s*card',
                    r'ministry\s*of\s*(?:labor|labour)',
                    r'mol',
                    r'work\s*permit',
                ],
                'weight': 1.0
            },
            'RESIDENCE_VISA': {
                'keywords': ['residence', 'visa', 'resident', 'إقامة'],
                'patterns': [
                    r'residence\s*visa',
                    r'resident\s*permit',
                    r'visa\s*type',
                    r'entry\s*permit',
                ],
                'weight': 1.0
            },
            'EMIRATES_ID': {
                'keywords': ['emirates id', 'identity card', 'هوية'],
                'patterns': [
                    r'emirates\s*id',
                    r'identity\s*card',
                    r'idn\s*\d{3}-\d{4}-\d{7}-\d{1}',  # Emirates ID format
                    r'784-\d{4}-\d{7}-\d{1}',
                ],
                'weight': 1.0
            },
            'HOME_COUNTRY_ID': {
                'keywords': ['aadhaar', 'aadhar', 'uid', 'uidai'],
                'patterns': [
                    r'aadhaa?r',
                    r'unique\s*identification',
                    r'uidai',
                    r'\d{4}\s*\d{4}\s*\d{4}',  # Aadhaar number format
                ],
                'weight': 1.0
            },
            'VISIT_VISA': {
                'keywords': ['visit visa', 'tourist visa', 'visitor'],
                'patterns': [
                    r'visit\s*visa',
                    r'tourist\s*visa',
                    r'visitor\s*visa',
                    r'entry\s*type.*visit',
                ],
                'weight': 1.0
            },
            'INVOICE': {
                'keywords': ['invoice', 'tax invoice', 'bill', 'فاتورة'],
                'patterns': [
                    r'(?:tax\s*)?invoice',
                    r'invoice\s*(?:no|number|#)',
                    r'bill\s*to',
                    r'subtotal',
                    r'grand\s*total',
                ],
                'weight': 0.9
            },
            'PURCHASE_ORDER': {
                'keywords': ['purchase order', 'po number', 'order'],
                'patterns': [
                    r'purchase\s*order',
                    r'po\s*(?:no|number|#)',
                    r'p\.o\.\s*(?:no|number)',
                    r'vendor',
                    r'buyer',
                ],
                'weight': 0.9
            },
            'COMPANY_LICENSE': {
                'keywords': ['license', 'licence', 'commercial license', 'business license'],
                'patterns': [
                    r'(?:commercial|business|company)\s*licen[cs]e',
                    r'licen[cs]e\s*(?:no|number|#)',
                    r'legal\s*type',
                    r'duns\s*number',
                    r'register\s*no',
                ],
                'weight': 0.9
            }
        }
    
    def classify(self, text: str, filename: Optional[str] = None) -> Tuple[str, float]:
        """
        Classify document based on extracted text.
        
        Args:
            text: Extracted text from document
            filename: Optional filename for additional hints
            
        Returns:
            Tuple of (document_type, confidence_score)
        """
        if not text or len(text.strip()) < 10:
            logger.warning("Text too short for classification")
            return ('UNKNOWN', 0.0)
        
        text_lower = text.lower()
        scores = {}
        
        # Calculate scores for each document type
        for doc_type, patterns in self.detection_patterns.items():
            score = 0.0
            matches = 0
            
            # Check keywords
            for keyword in patterns['keywords']:
                if keyword.lower() in text_lower:
                    score += 10
                    matches += 1
            
            # Check regex patterns
            for pattern in patterns['patterns']:
                if re.search(pattern, text, re.IGNORECASE):
                    score += 15
                    matches += 1
            
            # Apply weight
            score *= patterns['weight']
            
            # Bonus for multiple matches
            if matches > 2:
                score *= 1.2
            
            scores[doc_type] = score
        
        # Get best match
        if not scores or max(scores.values()) == 0:
            return ('UNKNOWN', 0.0)
        
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        # Normalize confidence to 0-100
        confidence = min(100.0, best_score)
        
        # Check if second-best is too close (ambiguous)
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[0] - sorted_scores[1] < 10:
            confidence *= 0.7  # Reduce confidence for ambiguous cases
        
        logger.info(f"Classified as {best_type} with {confidence:.1f}% confidence")
        logger.debug(f"All scores: {scores}")
        
        return (best_type, confidence)
    
    def quick_classify_from_file(self, file_path: str, ocr_service) -> Tuple[str, float]:
        """
        Quickly classify a document file using lightweight OCR.
        
        Args:
            file_path: Path to document file
            ocr_service: OCR service instance for text extraction
            
        Returns:
            Tuple of (document_type, confidence_score)
        """
        try:
            # Extract text from first page only for speed
            text = ocr_service.extract_text_from_image(file_path, page_limit=1)
            
            if not text:
                logger.warning(f"No text extracted from {file_path}")
                return ('UNKNOWN', 0.0)
            
            # Get filename for additional hints
            filename = Path(file_path).name
            
            return self.classify(text, filename)
            
        except Exception as e:
            logger.error(f"Error classifying file {file_path}: {str(e)}")
            return ('UNKNOWN', 0.0)
