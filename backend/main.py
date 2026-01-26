"""
FastAPI application - OCR Document Extraction System
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from contextlib import asynccontextmanager
import os
import shutil
from datetime import datetime
import uuid

from database import get_db, init_db
from models import Document, ExtractedField
from schemas import (
    DocumentResponse, DocumentListResponse, UploadResponse,
    ProcessingStatusResponse, DocumentTypeResponse, ExtractedFieldResponse
)
from ocr_service import OCRService
from config import DOCUMENT_TYPES
from document_classifier import DocumentClassifier
from dotenv import load_dotenv

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    init_db()
    print("✅ Database initialized")
    print("✅ OCR Service ready")
    print(f"✅ Upload directory: {UPLOAD_DIR}")
    yield
    # Shutdown (if needed)
    pass


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="OCR Document Extraction API",
    description="API for extracting structured data from documents using OCR",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - Allow frontend from different ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now - tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OCR service
TESSERACT_CMD = os.getenv("TESSERACT_CMD")
ocr_service = OCRService(tesseract_cmd=TESSERACT_CMD)

# Initialize document classifier
classifier = DocumentClassifier()

# Upload directory
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "temp"), exist_ok=True)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "OCR Document Extraction API is running",
        "version": "1.0.0"
    }


@app.get("/api/document-types", response_model=List[DocumentTypeResponse])
async def get_document_types():
    """Get all available document types that are supported"""
    #Only show the main supported document types
    supported_types = [
        "PASSPORT",
        "LABOR_CARD", 
        "RESIDENCE_VISA",
        "EMIRATES_ID",
        "HOME_COUNTRY_ID",
        "VISIT_VISA",
        "INVOICE",
        "PURCHASE_ORDER",
        "COMPANY_LICENSE"
    ]
    
    types = []
    for key, config in DOCUMENT_TYPES.items():
        # Only include supported types
        if key in supported_types:
            types.append(DocumentTypeResponse(
                key=key,
                name=config["name"],
                fields_count=len(config["fields"])
            ))
    
    return types


def process_document_ocr(document_id: int, file_path: str, document_type: str, db: Session):
    """
    Background task to process document OCR
    """
    try:
        # Update status to processing
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return
        
        document.status = "processing"
        db.commit()
        
        # Create temp directory for this document
        temp_dir = os.path.join(UPLOAD_DIR, "temp", str(document_id))
        os.makedirs(temp_dir, exist_ok=True)
        
        # Process document with OCR
        result = ocr_service.process_document(file_path, document_type, temp_dir)
        
        # Update document with results
        document.status = result['status']
        document.ocr_confidence = result['overall_confidence']
        
        # Save extracted fields to database
        for field_name, field_data in result['extracted_fields'].items():
            extracted_field = ExtractedField(
                document_id=document_id,
                field_name=field_name,
                field_value=field_data['value'],
                confidence=field_data['confidence'],
                page_number=field_data.get('page', 1)
            )
            db.add(extracted_field)
        
        db.commit()
        
        # Cleanup temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    except Exception as e:
        print(f"Error processing document {document_id}: {str(e)}")
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = "failed"
            document.error_message = str(e)
            db.commit()


@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None),  # Now optional for auto-detection
    db: Session = Depends(get_db)
):
    """
    Upload a document for OCR processing.
    If document_type is not provided, it will be auto-detected.
    """
    # Validate file extension first
    allowed_extensions = {"pdf", "png", "jpg", "jpeg"}
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Generate unique filename and save file
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_size = os.path.getsize(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Auto-detect document type if not provided
    detected_type = None
    confidence = 0.0
    
    if not document_type:
        try:
            detected_type, confidence = classifier.quick_classify_from_file(file_path, ocr_service)
            
            if detected_type == 'UNKNOWN' or confidence < 50:
                # Clean up file if detection failed
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise HTTPException(
                    status_code=400,
                    detail="Could not auto-detect document type. Please specify document_type parameter."
                )
            
            document_type = detected_type
            print(f"✓ Auto-detected document type: {document_type} ({confidence:.1f}% confidence)")
            
        except HTTPException:
            raise
        except Exception as e:
            # Clean up file on error
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Auto-detection failed: {str(e)}")
    
    # Validate document type (whether provided or detected)
    if document_type not in DOCUMENT_TYPES:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Invalid document type: {document_type}")

    # Create database record
    document = Document(
        document_type=document_type,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        status="pending"
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Start background OCR processing
    background_tasks.add_task(process_document_ocr, document.id, file_path, document_type, db)
    
    return UploadResponse(
        message="Document uploaded successfully. Processing started.",
        document_id=document.id,
        status="pending"
    )


@app.get("/api/documents", response_model=DocumentListResponse)
async def get_documents(
    skip: int = 0,
    limit: int = 100,
    document_type: str = None,
    db: Session = Depends(get_db)
):
    """
    Get all documents with optional filtering
    """
    query = db.query(Document)
    
    if document_type:
        query = query.filter(Document.document_type == document_type)
    
    total = query.count()
    documents = query.order_by(Document.upload_date.desc()).offset(skip).limit(limit).all()
    
    return DocumentListResponse(
        documents=documents,
        total=total
    )


@app.get("/api/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """
    Get a specific document with all extracted fields
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@app.get("/api/documents/{document_id}/status", response_model=ProcessingStatusResponse)
async def get_processing_status(document_id: int, db: Session = Depends(get_db)):
    """
    Get processing status of a document
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Calculate progress
    progress_map = {
        "pending": 10,
        "processing": 50,
        "completed": 100,
        "failed": 0,
        "partial": 75
    }
    
    progress = progress_map.get(document.status, 0)
    
    messages = {
        "pending": "Document uploaded. Waiting to start processing...",
        "processing": "Extracting text and fields from document...",
        "completed": "Document processed successfully!",
        "failed": f"Processing failed: {document.error_message or 'Unknown error'}",
        "partial": "Partial extraction completed. Some fields may be missing."
    }
    
    return ProcessingStatusResponse(
        document_id=document_id,
        status=document.status,
        progress=progress,
        message=messages.get(document.status, "Unknown status")
    )


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """
    Delete a document and its extracted fields
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Delete from database (cascade will delete extracted fields)
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}


@app.put("/api/documents/{document_id}/fields/{field_id}")
async def update_field(
    document_id: int,
    field_id: int,
    field_value: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Update an extracted field value (manual correction)
    """
    field = db.query(ExtractedField).filter(
        ExtractedField.id == field_id,
        ExtractedField.document_id == document_id
    ).first()
    
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    
    field.field_value = field_value
    db.commit()
    
    return {"message": "Field updated successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
