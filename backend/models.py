"""
Database models for OCR document extraction system
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Document(Base):
    """Uploaded document metadata"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    document_type = Column(String(50), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    ocr_confidence = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    
    # Relationship to extracted fields
    extracted_fields = relationship("ExtractedField", back_populates="document", cascade="all, delete-orphan")
    

class ExtractedField(Base):
    """Extracted fields from OCR processing"""
    __tablename__ = "extracted_fields"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    field_name = Column(String(100), nullable=False, index=True)
    field_value = Column(Text)
    confidence = Column(Float, default=0.0)
    page_number = Column(Integer, default=1)
    extracted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    document = relationship("Document", back_populates="extracted_fields")
