"""
FastAPI application - Enhanced OCR Document Extraction System
Stateless API Version - Single Upload & Process Endpoint
"""
import os
import shutil
import uuid
import logging
import time
from typing import Optional, List, Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from schemas import OCRResultResponse, ErrorResponse
from ocr_service import OCRService
from config import DOCUMENT_TYPES
from enhanced_document_classifier import EnhancedDocumentClassifier
from image_quality_checker import ImageQualityChecker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Global Services
ocr_service: Optional[OCRService] = None
classifier: Optional[EnhancedDocumentClassifier] = None
quality_checker: Optional[ImageQualityChecker] = None
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global ocr_service, classifier, quality_checker
    
    # Startup
    logger.info("🚀 Starting OCR API Server...")
    
    # Initialize Directories
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_DIR, "temp"), exist_ok=True)
    logger.info(f"✅ Upload directory: {UPLOAD_DIR}")
    
    # Initialize Services
    TESSERACT_CMD = os.getenv("TESSERACT_CMD")
    ocr_service = OCRService(tesseract_cmd=TESSERACT_CMD)
    classifier = EnhancedDocumentClassifier()
    quality_checker = ImageQualityChecker()
    
    logger.info("✅ Services initialized successfully")
    yield
    # Shutdown
    logger.info("🛑 Shutting down application")


# Initialize FastAPI app
app = FastAPI(
    title="OCR Document Extraction API",
    description="Stateless Production API for extracting structured data from documents.",
    version="2.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "OCR API is running (Stateless Mode)",
        "version": "2.1.0",
        "supported_documents": list(DOCUMENT_TYPES.keys())
    }


@app.post("/api/upload", response_model=OCRResultResponse, responses={400: {"model": ErrorResponse}})
async def upload_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
    skip_quality_check: bool = Form(False)
):
    """
    Upload and process a document immediately.
    Returns extracted fields in JSON format.
    """
    start_time = time.time()
    file_path = None
    temp_dir = None
    
    try:
        # Validate file extension
        allowed_extensions = {"pdf", "png", "jpg", "jpeg", "tiff", "bmp"}
        file_ext = file.filename.split(".")[-1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_file_type",
                    "message": f"File type '.{file_ext}' not supported",
                    "allowed_types": list(allowed_extensions)
                }
            )
        
        # Save file temporarily
        unique_id = str(uuid.uuid4())
        unique_filename = f"{unique_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        logger.info(f"📂 File received: {file.filename}")
        
        # STEP 1: Quality Check
        quality_score = 0.0
        warnings = []
        
        if not skip_quality_check:
            logger.info("🔍 Running quality check...")
            quality_result = quality_checker.check_quality(file_path)
            quality_score = quality_result['quality_score']
            
            if not quality_result['passed']:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "quality_check_failed",
                        "message": "Document quality insufficient",
                        "metrics": quality_result
                    }
                )
            if quality_result['warnings']:
                warnings = quality_result['warnings']

        # STEP 2: Classification / Validation
        captured_text = None

        if not document_type:
            logger.info("🧠 Auto-detecting document type...")
            # Get text from classifier to reuse it
            detected_type, conf, msgs, captured_text = classifier.quick_classify_from_file(file_path, ocr_service)
            
            if detected_type == 'UNKNOWN' or conf < 40:
                 raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "classification_failed",
                        "message": "Could not identify document type",
                        "detected": detected_type,
                        "confidence": conf,
                        "text_preview": captured_text[:500] if captured_text else "No text extracted"
                    }
                )
            document_type = detected_type
            logger.info(f"✅ Detected: {document_type} ({conf}%)")
        else:
            # Verify provided type
            if document_type not in DOCUMENT_TYPES:
                raise HTTPException(status_code=400, detail=f"Invalid document_type: {document_type}")

        # STEP 3: Extraction (Synchronous)
        logger.info(f"📝 Extracting data for {document_type}...")
        
        # Create unique temp dir for this process
        temp_dir = os.path.join(UPLOAD_DIR, "temp", unique_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Optimization: Pass captured_text to skip re-reading image
        result = ocr_service.process_document(file_path, document_type, temp_dir, pre_extracted_text=captured_text)
        
        # STEP 4: Format Response
        # Map result['extracted_fields'] to OCRField schema
        # result['extracted_fields'] is {key: {value:..., confidence:..., source:...}}
        
        fields_response = {}
        for key, data in result.get('extracted_fields', {}).items():
            fields_response[key] = {
                "value": str(data.get('value')) if data.get('value') is not None else None,
                "confidence": data.get('confidence'),
                "source": data.get('source')
            }
            
        processing_time = time.time() - start_time
        
        return {
            "status": "success",
            "document_type": document_type,
            "overall_confidence": result.get('overall_confidence', 0.0),
            "processing_time": round(processing_time, 2),
            "fields": fields_response,
            "quality_score": round(quality_score, 1) if not skip_quality_check else None,
            "warnings": warnings,
            "text_preview": captured_text[:500] if captured_text else "No text extracted"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup ALL files
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.debug(f"Deleted uploaded file: {file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete file: {cleanup_error}")
        
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.debug(f"Deleted temp dir: {temp_dir}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete temp dir: {cleanup_error}")
