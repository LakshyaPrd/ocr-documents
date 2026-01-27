"""
Enhanced Pydantic schemas for API request/response models
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class DocumentTypeResponse(BaseModel):
    """Response model for document type information"""
    key: str = Field(..., description="Document type key/identifier")
    name: str = Field(..., description="Human-readable document name")
    fields_count: int = Field(..., description="Number of fields to extract")

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    """Response model for document upload"""
    message: str = Field(..., description="Status message")
    document_id: int = Field(..., description="Unique document identifier")
    status: str = Field(..., description="Processing status")
    document_type: Optional[str] = Field(None, description="Detected/assigned document type")
    detection_confidence: Optional[float] = Field(None, description="Classification confidence (0-100)")

    class Config:
        from_attributes = True


class ProcessingStatusResponse(BaseModel):
    """Response model for processing status"""
    document_id: int = Field(..., description="Document identifier")
    status: str = Field(..., description="Current processing status")
    progress: int = Field(..., description="Progress percentage (0-100)")
    message: str = Field(..., description="Status message")
    document_type: Optional[str] = Field(None, description="Document type")
    overall_confidence: Optional[float] = Field(None, description="Overall extraction confidence")

    class Config:
        from_attributes = True


class ExtractedFieldResponse(BaseModel):
    """Response model for extracted field"""
    id: int = Field(..., description="Field identifier")
    field_name: str = Field(..., description="Field name/key")
    field_value: Optional[str] = Field(None, description="Extracted value")
    confidence: Optional[float] = Field(None, description="Extraction confidence (0-100)")
    page_number: Optional[int] = Field(None, description="Source page number")

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Response model for document details"""
    id: int = Field(..., description="Document identifier")
    document_type: str = Field(..., description="Document type")
    original_filename: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    status: str = Field(..., description="Processing status")
    ocr_confidence: Optional[float] = Field(None, description="Overall OCR confidence")
    upload_date: datetime = Field(..., description="Upload timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    extracted_fields: List[ExtractedFieldResponse] = Field(
        default_factory=list, 
        description="List of extracted fields"
    )

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Response model for document list"""
    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")

    class Config:
        from_attributes = True


class QualityCheckResponse(BaseModel):
    """Response model for quality check results"""
    passed: bool = Field(..., description="Whether quality check passed")
    quality_score: float = Field(..., description="Overall quality score (0-100)")
    issues: List[str] = Field(default_factory=list, description="List of quality issues")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Quality metrics")

    class Config:
        from_attributes = True


class ClassificationResponse(BaseModel):
    """Response model for document classification"""
    document_type: str = Field(..., description="Detected document type")
    confidence: float = Field(..., description="Classification confidence (0-100)")
    validation_messages: List[str] = Field(
        default_factory=list, 
        description="Validation messages"
    )

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    recommendation: Optional[str] = Field(None, description="Recommended action")

    class Config:
        from_attributes = True


class OCRField(BaseModel):
    """Stateless extracted field"""
    value: Optional[str] = None
    confidence: Optional[float] = None
    source: Optional[str] = None


class OCRResultResponse(BaseModel):
    """Stateless full OCR result"""
    status: str
    document_type: str
    overall_confidence: float
    processing_time: float
    fields: Dict[str, OCRField]
    quality_score: Optional[float] = None
    warnings: Optional[List[str]] = None
    text_preview: Optional[str] = None
