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
                    # Removed generic 'passport no' as it appears in Visas too
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
                'keywords': ['aadhaar', 'aadhar', 'uidai'],  # Removed generic 'uid'
                'patterns': [
                    r'aadhaa?r',
                    r'unique\s*identification',
                    r'uidai',
                    r'\d{4}\s*\d{4}\s*\d{4}',  # Aadhaar number format
                ],
                'weight': 1.0
            },
            'VISIT_VISA': {
                'keywords': ['visit visa', 'tourist visa', 'visitor', 'entry permit'],
                'patterns': [
                    r'visit\s*visa',
                    r'tourist\s*visa',
                    r'visitor\s*visa',
                    r'entry\s*type.*visit',
                    r'entry\s*permit',  # Relaxed from 'entry permit no'
                    r'u\.i\.d\s*no',
                ],
                'weight': 1.2  # Increased weight to prioritize over Passport
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
        print(f"📄 CLASSIFIER SAW TEXT START: {text[:200]}...")
        print(f"📄 CLASSIFIER SAW TEXT END: ...{text[-200:]}")
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
        print(f"📊 ALL CLASSIFIER SCORES: {scores}")
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
            logger.info(f"Starting classification for: {file_path}")
            
            # Extract text using OCR service's process_document method
            # We'll use a lightweight approach - just get the raw text
            from pathlib import Path
            import tempfile
            
            # Create temp directory for processing
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Process document to get text (this will handle PDF/images)
                result = ocr_service.process_document(file_path, 'PASSPORT', temp_dir)
                
                # Get the raw text from OCR
                if 'raw_text' in result:
                    text = result['raw_text']
                elif 'extracted_fields' in result:
                    # Fallback: combine all extracted field values
                    text = ' '.join([str(v.get('value', '')) for v in result['extracted_fields'].values()])
                else:
                    logger.warning("No text found in OCR result")
                    return ('UNKNOWN', 0.0)
                
                logger.info(f"Extracted {len(text)} characters for classification")
                
            finally:
                # Cleanup temp directory
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            
            if not text or len(text.strip()) < 10:
                logger.warning(f"Insufficient text extracted from {file_path}")
                return ('UNKNOWN', 0.0)
            
            # Get filename for additional hints
            filename = Path(file_path).name
            
            # Classify based on extracted text
            doc_type, confidence = self.classify(text, filename)
            
            logger.info(f"Classification result: {doc_type} ({confidence:.1f}% confidence)")
            return (doc_type, confidence)
            
        except Exception as e:
            logger.error(f"Error classifying file {file_path}: {str(e)}", exc_info=True)
            return ('UNKNOWN', 0.0)
