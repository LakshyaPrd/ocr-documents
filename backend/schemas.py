"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime


class DocumentTypeResponse(BaseModel):
    """Document type information"""
    key: str
    name: str
    fields_count: int


class ExtractedFieldResponse(BaseModel):
    """Extracted field data"""
    field_name: str
    field_value: Optional[str]
    confidence: float
    page_number: int
    
    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Document response with extracted fields"""
    id: int
    document_type: str
    original_filename: str
    file_size: int
    upload_date: datetime
    status: str
    ocr_confidence: float
    error_message: Optional[str]
    extracted_fields: List[ExtractedFieldResponse]
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """List of documents"""
    documents: List[DocumentResponse]
    total: int


class UploadResponse(BaseModel):
    """Upload response"""
    message: str
    document_id: int
    status: str


class ProcessingStatusResponse(BaseModel):
    """Processing status"""
    document_id: int
    status: str
    progress: int
    message: str
