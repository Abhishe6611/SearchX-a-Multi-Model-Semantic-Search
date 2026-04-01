"""
Database models for SearchX
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
from typing import Dict, Any
import enum

Base = declarative_base()


class ProcessingStatus(str, enum.Enum):
    """File processing status enum"""
    PENDING = "pending"    # Orange - In queue
    SUCCESS = "success"    # Green - Processed successfully
    FAILED = "failed"      # Red - Processing failed


class MediaFile(Base):
    """Media file model"""
    __tablename__ = "media_files"
    
    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True)
    file_path = Column(String(512), nullable=False)
    thumbnail_path = Column(String(512), nullable=True)
    
    file_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)  # In bytes
    file_hash = Column(String(64), nullable=False, unique=True, index=True)
    
    extracted_text = Column(Text, nullable=True)
    keywords = Column(Text, nullable=True)
    processing_status = Column(
        Enum(ProcessingStatus),
        default=ProcessingStatus.PENDING,
        nullable=False,
        index=True
    )
    processing_error = Column(Text, nullable=True)
    
    upload_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    processed_date = Column(DateTime, nullable=True)
    
    # Vector embedding metadata
    embedding_id = Column(Integer, nullable=True, index=True)  # Index in FAISS for text
    image_embedding_id = Column(Integer, nullable=True, index=True)  # Index in FAISS for images
    has_embedding = Column(Integer, default=0)  # 0=False, 1=True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        # Access actual values (not Column objects) - suppress type checker
        extracted_text_val: str | None = self.extracted_text  # type: ignore
        keywords_val: str | None = self.keywords  # type: ignore
        processing_status_val: ProcessingStatus | None = self.processing_status  # type: ignore  
        upload_date_val: datetime | None = self.upload_date  # type: ignore
        processed_date_val: datetime | None = self.processed_date  # type: ignore
        
        return {
            "id": self.id,
            "original_filename": self.original_filename,
            "stored_filename": self.stored_filename,
            "file_path": self.file_path,
            "thumbnail_path": self.thumbnail_path,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "file_hash": self.file_hash,
            "extracted_text": extracted_text_val[:500] if extracted_text_val else None,  # Truncate for API
            "keywords": [k.strip() for k in keywords_val.split(',')] if keywords_val else [],
            "processing_status": processing_status_val.value if processing_status_val else "pending",
            "processing_error": self.processing_error,
            "upload_date": upload_date_val.isoformat() if upload_date_val else None,
            "processed_date": processed_date_val.isoformat() if processed_date_val else None,
            "has_embedding": bool(self.has_embedding)
        }
    
    def __repr__(self):
        return f"<MediaFile(id={self.id}, filename='{self.original_filename}', status='{self.processing_status}')>"
