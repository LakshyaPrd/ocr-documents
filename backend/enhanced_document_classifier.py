"""
Enhanced Document Type Classifier
Automatically detects document type with high accuracy using multi-stage validation.
Includes cross-validation to prevent misclassification.
"""

import re
from typing import Dict, Optional, Tuple, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class EnhancedDocumentClassifier:
    """Classify documents with strict validation and cross-checking."""
    
    def __init__(self):
        """Initialize classifier with enhanced detection patterns."""
        
        # Define strict EXCLUSION patterns - if found, document CANNOT be that type
        self.exclusion_patterns = {
            'PASSPORT': [
                r'residence\s*visa',
                r'visit\s*visa',
                r'labor\s*card',
                r'emirates\s*id',
                r'entry\s*permit\s*no',
                r'visa\s*type',
                r'sponsor',
            ],
            'RESIDENCE_VISA': [
                r'passeport',
                r'P<[A-Z]{3}',  # Passport MRZ
                r'visit\s*visa',
                r'tourist',
            ],
            'VISIT_VISA': [
                r'residence\s*permit',
                r'P<[A-Z]{3}',  # Passport MRZ
                r'labor\s*card',
            ],
            'LABOR_CARD': [
                r'visit\s*visa',
                r'residence\s*visa',
            ],
            'EMIRATES_ID': [
                r'passport',
                r'visa',
                r'labor',
            ],
            'HOME_COUNTRY_ID': [
                r'passport',
                r'visa',
                r'emirates',
            ],
            'INVOICE': [
                r'passport',
                r'visa',
                r'purchase\s*order',
            ],
            'PURCHASE_ORDER': [
                r'passport',
                r'visa',
                r'invoice',
            ],
            'COMPANY_LICENSE': [
                r'passport',
                r'visa',
                r'invoice',
            ]
        }
        
        # Enhanced detection patterns with mandatory and optional indicators
        self.detection_patterns = {
            'PASSPORT': {
                'mandatory': [
                    r'P<[A-Z]{3}',  # MRZ line - MUST have this
                ],
                'strong_indicators': [
                    r'passport',
                    r'passeport',
                    r'passaporte',
                    r'reisepass',
                    r'[A-Z]{1}\d{7,9}',  # Passport number format
                    r'nationality',
                    r'place\s*of\s*birth',
                    r'date\s*of\s*birth',
                    r'sex.*[MF]',
                ],
                'weak_indicators': [
                    r'surname',
                    r'given\s*names?',
                ],
                'weight': 1.0,
                'required_score': 35  # Need mandatory + strong indicators
            },
            
            'VISIT_VISA': {
                'mandatory': [
                    r'(?:visit|tourist|visitor)\s*visa',
                    r'entry\s*permit',
                ],
                'strong_indicators': [
                    r'u\.?i\.?d\s*(?:no|number)',
                    r'visa\s*type',
                    r'entry\s*type',
                    r'sponsor',
                    r'visa\s*number',
                    r'visa\s*status',
                ],
                'weak_indicators': [
                    r'passport\s*(?:no|number)',
                    r'duration',
                    r'valid\s*until',
                ],
                'weight': 1.0,
                'required_score': 30
            },
            
            'RESIDENCE_VISA': {
                'mandatory': [
                    r'residence',
                    r'r\s*e\s*s\s*i\s*d\s*e\s*n\s*c\s*e',
                    r'resident\s*(?:permit|visa)',
                    r'united\s*arab\s*emirates',
                    r'state\s*of\s*united\s*arab\s*emirates',
                ],
                'strong_indicators': [
                    r'permit\s*(?:no|number)',
                    r'file\s*(?:no|number)',
                    r'u\.?i\.?d\s*(?:no|number)',
                    r'sponsor',
                    r'profession',
                    r'place\s*of\s*issue',
                    r'valid\s*until',
                ],
                'weak_indicators': [
                    r'passport\s*(?:no|number)',
                    r'nationality',
                ],
                'weight': 1.0,
                'required_score': 25
            },
            
            'LABOR_CARD': {
                'mandatory': [
                    r'labor\s*card',
                    r'work\s*permit',
                    r'mol',
                ],
                'strong_indicators': [
                    r'ministry\s*of\s*(?:labor|labour)',
                    r'ministry\s*of\s*human\s*resources',
                    r'mohre',
                    r'employer',
                    r'occupation',
                    r'card\s*(?:no|number)',
                ],
                'weak_indicators': [
                    r'validity',
                    r'issue\s*date',
                ],
                'weight': 1.0,
                'required_score': 25
            },
            
            'EMIRATES_ID': {
                'mandatory': [
                    r'emirates\s*id',
                    r'784-\d{4}-\d{7}-\d{1}',  # Emirates ID format
                ],
                'strong_indicators': [
                    r'identity\s*card',
                    r'idn',
                    r'card\s*(?:no|number)',
                    r'united\s*arab\s*emirates',
                ],
                'weak_indicators': [
                    r'nationality',
                    r'expiry',
                ],
                'weight': 1.0,
                'required_score': 30
            },
            
            'HOME_COUNTRY_ID': {
                'mandatory': [
                    r'aadhaa?r',
                    r'uidai',
                ],
                'strong_indicators': [
                    r'\d{4}\s*\d{4}\s*\d{4}',  # Aadhaar number
                    r'unique\s*identification',
                    r'government\s*of\s*india',
                ],
                'weak_indicators': [
                    r'dob',
                    r'address',
                ],
                'weight': 1.0,
                'required_score': 25
            },
            
            'INVOICE': {
                'mandatory': [
                    r'invoice',
                ],
                'strong_indicators': [
                    r'tax\s*invoice',
                    r'invoice\s*(?:no|number|#)',
                    r'bill\s*to',
                    r'(?:sub)?total',
                    r'amount',
                    r'quantity',
                ],
                'weak_indicators': [
                    r'date',
                    r'customer',
                ],
                'weight': 0.9,
                'required_score': 20
            },
            
            'PURCHASE_ORDER': {
                'mandatory': [
                    r'purchase\s*order',
                    r'p\.?o\.?\s*(?:no|number)',
                ],
                'strong_indicators': [
                    r'vendor',
                    r'buyer',
                    r'ship\s*to',
                    r'order\s*date',
                ],
                'weak_indicators': [
                    r'quantity',
                    r'price',
                ],
                'weight': 0.9,
                'required_score': 20
            },
            
            'COMPANY_LICENSE': {
                'mandatory': [
                    r'(?:commercial|business|trade|professional)\s*licen[cs]e',
                    r'license\s*type',
                ],
                'strong_indicators': [
                    r'licen[cs]e\s*(?:no|number)',
                    r'main\s*license\s*(?:no|number)',
                    r'dcci\s*no',
                    r'chamber\s*of\s*commerce',
                    r'legal\s*(?:form|type)',
                ],
                'weak_indicators': [
                    r'issue\s*date',
                    r'expiry\s*date',
                    r'activity',
                ],
                'weight': 1.0,
                'required_score': 25
            },
            
            'VISA_CANCELLATION': {
                'mandatory': [
                    r'(?:visa|residence)\s*cancellation',
                    r'application\s*for\s*cancellation',
                ],
                'strong_indicators': [
                    r'cancellation\s*transaction',
                    r'cancellation\s*date',
                    r'establishment\s*(?:no|number)',
                    r'sponsor',
                    r'application\s*(?:no|number)',
                ],
                'weak_indicators': [
                    r'passport',
                    r'nationality',
                    r'profession',
                ],
                'weight': 1.0,
                'required_score': 25
            },
            
            'COMPANY_VAT_CERTIFICATE': {
                'mandatory': [
                    r'federal\s*tax\s*authority',
                    r'tax\s*registration\s*certificate',
                ],
                'strong_indicators': [
                    r'vat\s*number',
                    r'trn',
                    r'registration\s*number',
                    r'certificate\s*number',
                    r'legal\s*name',
                ],
                'weak_indicators': [
                    r'address',
                    r'issue\s*date',
                    r'tax\s*period',
                ],
                'weight': 1.0,
                'required_score': 30
            },
            
            'ENTRY_PERMIT': {
                'mandatory': [
                    r'entry\s*permit',
                    r'permit\s*no',
                ],
                'strong_indicators': [
                    r'permit\s*number',
                    r'visa\s*number',
                    r'uid\s*number',
                    r'file\s*number',
                    r'application\s*number',
                    r'place\s*of\s*issue',
                ],
                'weak_indicators': [
                    r'nationality',
                    r'passport',
                    r'profession',
                ],
                'weight': 1.0,
                'required_score': 30
            }
        }
    
    def classify(self, text: str, filename: Optional[str] = None) -> Tuple[str, float, List[str]]:
        """
        Classify document with strict validation.
        
        Args:
            text: Extracted text from document
            filename: Optional filename for hints
            
        Returns:
            Tuple of (document_type, confidence_score, validation_messages)
        """
        if not text or len(text.strip()) < 20:
            return ('UNKNOWN', 0.0, ['Insufficient text for classification'])
        
        text_lower = text.lower()
        text_upper = text.upper()
        
        logger.info(f"Classifying document (text length: {len(text)} chars)")
        
        scores = {}
        details = {}
        
        # Calculate scores for each document type
        for doc_type, patterns in self.detection_patterns.items():
            score = 0.0
            found_mandatory = False
            strong_matches = []
            weak_matches = []
            
            # Check mandatory patterns - MUST have at least one
            for pattern in patterns.get('mandatory', []):
                if re.search(pattern, text, re.IGNORECASE):
                    found_mandatory = True
                    score += 25
                    break
            
            # Skip if mandatory not found
            if not found_mandatory:
                scores[doc_type] = 0
                details[doc_type] = {'reason': 'Missing mandatory indicator'}
                continue
            
            # Check for EXCLUSION patterns - if found, this CANNOT be that type
            excluded = False
            exclusion_found = None
            for pattern in self.exclusion_patterns.get(doc_type, []):
                if re.search(pattern, text, re.IGNORECASE):
                    excluded = True
                    exclusion_found = pattern
                    break
            
            if excluded:
                scores[doc_type] = 0
                details[doc_type] = {'reason': f'Excluded by pattern: {exclusion_found}'}
                logger.info(f"{doc_type} excluded due to pattern: {exclusion_found}")
                continue
            
            # Check strong indicators
            for pattern in patterns.get('strong_indicators', []):
                if re.search(pattern, text, re.IGNORECASE):
                    score += 10
                    strong_matches.append(pattern)
            
            # Check weak indicators
            for pattern in patterns.get('weak_indicators', []):
                if re.search(pattern, text, re.IGNORECASE):
                    score += 3
                    weak_matches.append(pattern)
            
            # Apply weight
            score *= patterns['weight']
            
            # Bonus for multiple strong matches
            if len(strong_matches) >= 3:
                score *= 1.3
            
            # Check if meets minimum required score
            required_score = patterns.get('required_score', 20)
            if score < required_score:
                score = 0
                details[doc_type] = {
                    'reason': f'Score too low ({score:.1f} < {required_score})',
                    'strong_matches': len(strong_matches),
                    'weak_matches': len(weak_matches)
                }
            else:
                details[doc_type] = {
                    'score': score,
                    'strong_matches': len(strong_matches),
                    'weak_matches': len(weak_matches),
                    'patterns_found': strong_matches + weak_matches
                }
            
            scores[doc_type] = score
        
        # Log all scores for debugging
        logger.info(f"Classification scores: {scores}")
        logger.debug(f"Classification details: {details}")
        
        # Get best match
        if not scores or max(scores.values()) == 0:
            return ('UNKNOWN', 0.0, ['No document type matched the criteria'])
        
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        # Normalize confidence to 0-100
        confidence = min(100.0, best_score * 2)  # Scale up for better confidence values
        
        # Check for ambiguous results (second best too close)
        sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        validation_messages = []
        
        if len(sorted_types) > 1:
            second_best = sorted_types[1]
            if second_best[1] > 0 and (best_score - second_best[1]) < 15:
                confidence *= 0.6  # Significantly reduce confidence
                validation_messages.append(
                    f"Ambiguous classification: {best_type} vs {second_best[0]}"
                )
                logger.warning(
                    f"Ambiguous: {best_type} ({best_score:.1f}) vs "
                    f"{second_best[0]} ({second_best[1]:.1f})"
                )
        
        # Add validation message with details
        if best_type in details and 'patterns_found' in details[best_type]:
            validation_messages.append(
                f"Identified as {best_type} based on {details[best_type]['strong_matches']} "
                f"strong indicators"
            )
        
        # Final confidence check
        if confidence < 60:
            validation_messages.append(
                f"Low confidence ({confidence:.1f}%). Manual verification recommended."
            )
        
        logger.info(
            f"Final classification: {best_type} with {confidence:.1f}% confidence"
        )
        
        return (best_type, confidence, validation_messages)
    
    def quick_classify_from_file(
        self, 
        file_path: str, 
        ocr_service
    ) -> Tuple[str, float, List[str], Optional[str]]:
        """
        Classify a document file using OCR text extraction.
        Returns: (type, confidence, messages, extracted_text)
        """
        try:
            logger.info(f"Starting file classification: {file_path}")
            
            from pathlib import Path
            import tempfile
            import shutil
            
            # Create temp directory
            temp_dir = tempfile.mkdtemp()
            text = None
            
            try:
                # Extract text using OCR (use a neutral document type for extraction)
                result = ocr_service.process_document(file_path, 'PASSPORT', temp_dir)
                
                # Get raw text
                if 'raw_text' in result:
                    text = result['raw_text']
                elif 'extracted_fields' in result:
                    text = ' '.join([
                        str(v.get('value', '')) 
                        for v in result['extracted_fields'].values()
                    ])
                
                if not text or len(text.strip()) < 20:
                    return ('UNKNOWN', 0.0, ['Insufficient text extracted'], text)
                
                logger.info(f"Extracted {len(text)} characters for classification")
                
            finally:
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass
            
            # Classify
            filename = Path(file_path).name
            doc_type, confidence, messages = self.classify(text, filename)
            
            logger.info(
                f"Classification complete: {doc_type} ({confidence:.1f}%)"
            )
            
            return (doc_type, confidence, messages, text)
            
        except Exception as e:
            logger.error(f"Classification error: {str(e)}", exc_info=True)
            return ('UNKNOWN', 0.0, [f'Classification failed: {str(e)}'], None)
