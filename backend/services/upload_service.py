"""
Upload service - handles file upload, validation, and processing orchestration
"""
import os
import hashlib
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import UploadFile, BackgroundTasks
import logging
import asyncio
import numpy as np
import requests
import base64
from sqlalchemy.orm import Session

from config import settings
from database import SessionLocal
from models import MediaFile, ProcessingStatus
from services.thumbnail_service import ThumbnailService
from services.text_extraction_service import TextExtractionService
from services.vector_index_service import VectorIndexService
from utils.path_utils import normalize_path_for_url, get_physical_path

logger = logging.getLogger(__name__)


class UploadService:
    """Handles file upload and processing pipeline"""
    
    def __init__(self):
        self.thumbnail_service = ThumbnailService()
        self.text_service = TextExtractionService()
        self.vector_service = VectorIndexService()  # Text index
        self.reprocess_status = {
            "is_running": False,
            "total": 0,
            "completed": 0,
            "failed": 0
        }
    
    def _validate_file(self, file: UploadFile) -> tuple[bool, str]:
        """Validate file type and size"""
        # Check file type
        allowed_types = settings.ALLOWED_IMAGE_TYPES + settings.ALLOWED_DOC_TYPES
        if file.content_type not in allowed_types:
            return False, f"File type {file.content_type} not allowed"
        
        # Check extension
        filename = file.filename or "unknown"
        ext = os.path.splitext(filename)[1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            return False, f"File extension {ext} not allowed"
        
        return True, "Valid"
    
    async def _calculate_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _check_duplicate(self, file_hash: str, db: Session) -> bool:
        """Check if file with same hash already exists"""
        existing = db.query(MediaFile).filter(MediaFile.file_hash == file_hash).first()
        return existing is not None
    
    async def _save_file(self, file: UploadFile) -> tuple[str, str, int]:
        """Save uploaded file to storage"""
        # Generate unique filename
        filename = file.filename or "unknown"
        ext = os.path.splitext(filename)[1].lower()
        stored_filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(settings.STORAGE_DIR, stored_filename)
        
        # Save file
        content = await file.read()
        file_size = len(content)
        
        # Check size
        if file_size > settings.MAX_FILE_SIZE:
            raise ValueError(f"File size {file_size} exceeds maximum {settings.MAX_FILE_SIZE}")
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        return file_path, stored_filename, file_size
    
    async def _process_file(self, media_file: MediaFile, db: Session) -> None:
        """Process file: extract text, generate thumbnail, create embedding"""
        file_id: int = media_file.id  # type: ignore
        original_filename: str = media_file.original_filename  # type: ignore
        
        try:
            logger.info(f"[File {file_id}] Starting processing: {original_filename}")
            
            # Get actual values from SQLAlchemy columns - use type: ignore to suppress type checker
            file_path_url: str = media_file.file_path  # type: ignore
            file_path: str = get_physical_path(file_path_url)  # Convert URL path to physical path
            file_type: str = media_file.file_type  # type: ignore
            stored_filename: str = media_file.stored_filename  # type: ignore
            
            # Generate thumbnail
            try:
                logger.info(f"[File {file_id}] Generating thumbnail...")
                thumbnail_path = await self.thumbnail_service.generate_thumbnail(
                    file_path,
                    file_type,
                    stored_filename
                )
                media_file.thumbnail_path = thumbnail_path  # type: ignore
                db.commit()
                logger.info(f"[File {file_id}] Thumbnail generated: {thumbnail_path}")
            except Exception as e:
                logger.error(f"[File {file_id}] Thumbnail generation failed: {str(e)}")
                # Continue processing even if thumbnail fails
            
            # Extract text
            text_extraction_failed = False
            extracted_text = ""
            keywords = ""
            try:
                logger.info(f"[File {file_id}] 📝 Extracting text...")
                extracted_text, keywords = await self.text_service.extract_text(
                    file_path,
                    file_type
                )
                media_file.extracted_text = extracted_text  # type: ignore
                media_file.keywords = keywords  # type: ignore
                db.commit()
                
                if len(extracted_text.strip()) > 0:
                    logger.info(f"[File {file_id}] ✅ Extracted {len(extracted_text)} characters of text")
                    preview = extracted_text[:100].replace('\n', ' ').strip()
                    logger.info(f"[File {file_id}]    Preview: '{preview}...'")
                else:
                    logger.warning(f"[File {file_id}] ⚠️  Text extraction returned EMPTY result")
                    logger.warning(f"[File {file_id}]    File will be marked FAILED - no searchable content")
                    text_extraction_failed = True
                    
            except Exception as e:
                logger.error(f"[File {file_id}] ❌ Text extraction FAILED: {str(e)}")
                text_extraction_failed = True
                media_file.processing_error = f"Text extraction error: {str(e)}"  # type: ignore
                db.commit()
            

            
            # Generate embedding if we have text
            embedding_generated = False
            
            # --- 1. Text Embeddings ---
            if extracted_text and len(extracted_text.strip()) > 0:
                try:
                    logger.info(f"[File {file_id}] 🧠 Generating text embedding...")
                    # Import here to avoid circular dependency
                    from services.embedding_service import EmbeddingService
                    embedding_service = EmbeddingService()
                    if embedding_service.model is None:
                        await embedding_service.initialize()
                    
                    text_embedding = await embedding_service.generate_embedding(extracted_text)
                    
                    # Add to vector index
                    await self.vector_service.add_vector(file_id, text_embedding)
                    
                    # Update database record
                    if self.vector_service.index is not None:
                        media_file.embedding_id = self.vector_service.index.ntotal - 1  # type: ignore
                    
                    media_file.has_embedding = 1  # type: ignore
                    embedding_generated = True
                    logger.info(f"[File {file_id}] ✅ Text embedding generated and indexed.")
                    
                except Exception as e:
                    logger.error(f"[File {file_id}] ❌ Text embedding generation failed: {str(e)}")
                    if not media_file.processing_error:
                        media_file.processing_error = f"Text embedding error: {str(e)}"  # type: ignore
                    db.commit()
            
            # Mark status based on what succeeded
            if text_extraction_failed:
                media_file.processing_status = ProcessingStatus.FAILED  # type: ignore
                media_file.processed_date = datetime.now(timezone.utc)  # type: ignore
                db.commit()
                logger.error(f"[File {file_id}] ❌ Processing FAILED: {original_filename}")
                logger.error(f"[File {file_id}]    Reason: Text extraction failed or returned empty")
            elif not embedding_generated:
                media_file.processing_status = ProcessingStatus.FAILED  # type: ignore
                media_file.processed_date = datetime.now(timezone.utc)  # type: ignore
                db.commit()
                logger.error(f"[File {file_id}] ❌ Processing FAILED: {original_filename}")
                logger.error(f"[File {file_id}]    Reason: Embedding generation failed")
            else:
                media_file.processing_status = ProcessingStatus.SUCCESS  # type: ignore
                media_file.processed_date = datetime.now(timezone.utc)  # type: ignore
                db.commit()
                logger.info(f"[File {file_id}] ✅ Processing COMPLETE: {original_filename}")
                logger.info(f"[File {file_id}]    Text: {len(extracted_text)} chars, Embedding: ✓, Indexed: ✓")
            
        except Exception as e:
            logger.error(f"[File {file_id}] ✗ Processing failed: {str(e)}", exc_info=True)
            media_file.processing_status = ProcessingStatus.FAILED  # type: ignore
            media_file.processing_error = str(e)  # type: ignore
            media_file.processed_date = datetime.now(timezone.utc)  # type: ignore
            db.commit()
        finally:
            db.close()
    
    def _process_file_sync(self, file_id: int):
        """Synchronous wrapper for background task processing"""
        db = SessionLocal()
        try:
            media_file = db.query(MediaFile).filter(MediaFile.id == file_id).first()
            if media_file:
                # Run async function in new event loop
                import asyncio
                asyncio.run(self._process_file(media_file, db))
        except Exception as e:
            logger.error(f"Background processing error for file {file_id}: {str(e)}", exc_info=True)
        finally:
            if db:
                db.close()
    
    async def process_uploads(self, files: List[UploadFile], background_tasks: Optional[BackgroundTasks] = None) -> List[Dict[str, Any]]:
        """Process multiple file uploads"""
        results: List[Dict[str, Any]] = []
        db = SessionLocal()
        
        try:
            for file in files:
                try:
                    # Validate file
                    is_valid, message = self._validate_file(file)
                    if not is_valid:
                        results.append({
                            "filename": file.filename,
                            "success": False,
                            "error": message
                        })
                        continue
                    
                    # Save file
                    file_path, stored_filename, file_size = await self._save_file(file)
                    
                    # Calculate hash
                    file_hash = await self._calculate_hash(file_path)
                    
                    # Check for duplicates
                    if self._check_duplicate(file_hash, db):
                        os.remove(file_path)  # Delete duplicate
                        results.append({
                            "filename": file.filename,
                            "success": False,
                            "error": "Duplicate file already exists"
                        })
                        continue
                    
                    # Create database record
                    # Normalize paths to URL-friendly format
                    url_file_path = normalize_path_for_url(file_path)
                    
                    media_file = MediaFile(
                        original_filename=file.filename,
                        stored_filename=stored_filename,
                        file_path=url_file_path,  # Store URL-friendly path
                        file_type=file.content_type,
                        file_size=file_size,
                        file_hash=file_hash,
                        processing_status=ProcessingStatus.PENDING,
                        upload_date=datetime.now(timezone.utc)
                    )
                    
                    db.add(media_file)
                    db.commit()
                    db.refresh(media_file)
                    
                    file_id = int(media_file.id)  # type: ignore
                    
                    results.append({
                        "filename": file.filename,
                        "success": True,
                        "file_id": file_id,
                        "status": "pending"
                    })
                    
                    # Use FastAPI BackgroundTasks for proper task management
                    if background_tasks:
                        logger.info(f"Scheduling background processing for file {file_id}")
                        background_tasks.add_task(self._process_file_sync, file_id)
                    else:
                        # Fallback: process immediately (synchronous)
                        logger.warning(f"No BackgroundTasks available, processing file {file_id} synchronously")
                        await self._process_file(media_file, SessionLocal())
                    
                except Exception as e:
                    logger.error(f"Error processing {file.filename}: {str(e)}", exc_info=True)
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": str(e)
                    })
            
            return results
            
        finally:
            db.close()
    
    async def repair_pipeline(self):
        """Repair stuck files and regenerate missing thumbnails"""
        logger.info("="*60)
        logger.info("STARTING MEDIA PIPELINE REPAIR")
        logger.info("="*60)

        db = SessionLocal()
        try:
            # Find all files that need repair
            pending_files = db.query(MediaFile).filter(
                MediaFile.processing_status == ProcessingStatus.PENDING
            ).all()

            failed_files = db.query(MediaFile).filter(
                MediaFile.processing_status == ProcessingStatus.FAILED
            ).all()

            files_without_thumbnails = db.query(MediaFile).filter(
                MediaFile.thumbnail_path == None,
                MediaFile.processing_status == ProcessingStatus.SUCCESS
            ).all()

            total_to_repair = len(pending_files) + len(failed_files) + len(files_without_thumbnails)

            logger.info(f"Found {len(pending_files)} PENDING files")
            logger.info(f"Found {len(failed_files)} FAILED files")
            logger.info(f"Found {len(files_without_thumbnails)} files missing thumbnails")
            logger.info(f"Total files to repair: {total_to_repair}")

            repaired_count = 0

            # Process pending files
            for file in pending_files:
                logger.info(f"Reprocessing PENDING file {file.id}: {file.original_filename}")
                new_db = SessionLocal()
                try:
                    # Get fresh copy in new session
                    file_to_process = new_db.query(MediaFile).filter(MediaFile.id == file.id).first()
                    if file_to_process:
                        await self._process_file(file_to_process, new_db)
                        repaired_count += 1
                finally:
                    new_db.close()

            # Process failed files
            for file in failed_files:
                logger.info(f"Reprocessing FAILED file {file.id}: {file.original_filename}")
                # Reset status to pending
                file.processing_status = ProcessingStatus.PENDING  # type: ignore
                file.processing_error = None  # type: ignore
                db.commit()

                new_db = SessionLocal()
                try:
                    # Get fresh copy in new session
                    file_to_process = new_db.query(MediaFile).filter(MediaFile.id == file.id).first()
                    if file_to_process:
                        await self._process_file(file_to_process, new_db)
                        repaired_count += 1
                finally:
                    new_db.close()

            # Regenerate missing thumbnails for successful files
            for file in files_without_thumbnails:
                logger.info(f"Regenerating thumbnail for file {file.id}: {file.original_filename}")
                try:
                    file_path_url: str = file.file_path  # type: ignore
                    file_path = get_physical_path(file_path_url)
                    file_type: str = file.file_type  # type: ignore
                    stored_filename: str = file.stored_filename  # type: ignore

                    thumbnail_path = await self.thumbnail_service.generate_thumbnail(
                        file_path,
                        file_type,
                        stored_filename
                    )
                    file.thumbnail_path = thumbnail_path  # type: ignore
                    db.commit()
                    logger.info(f"✓ Thumbnail generated for file {file.id}")
                    repaired_count += 1
                except Exception as e:
                    logger.error(f"✗ Failed to generate thumbnail for file {file.id}: {str(e)}")

            logger.info("="*60)
            logger.info(f"REPAIR COMPLETE: {repaired_count}/{total_to_repair} files repaired")
            logger.info("="*60)

        except Exception as e:
            logger.error(f"Repair pipeline error: {str(e)}", exc_info=True)
        finally:
            db.close()

    async def reprocess_all_files(self):
        """Batch reprocess all files: re-extract text and regenerate embeddings for accuracy"""
        logger.info("="*60)
        logger.info("STARTING BATCH REPROCESSING OF ALL FILES")
        logger.info("="*60)

        db = SessionLocal()
        try:
            self.reprocess_status["is_running"] = True
            # Get ALL files to reprocess (including FAILED ones)
            all_files = db.query(MediaFile).all()

            total_files = len(all_files)
            
            self.reprocess_status["total"] = total_files
            self.reprocess_status["completed"] = 0
            self.reprocess_status["failed"] = 0
            
            logger.info(f"Found {total_files} files to reprocess")

            reprocessed_count = 0
            failed_count = 0

            # Reprocess each file
            for idx, file in enumerate(all_files, 1):
                logger.info(f"[{idx}/{total_files}] Reprocessing file {file.id}: {file.original_filename}")
                new_db = SessionLocal()
                try:
                    # Reset to pending
                    file_to_process = new_db.query(MediaFile).filter(MediaFile.id == file.id).first()
                    if file_to_process:
                        # Clear old embedding data
                        file_to_process.extracted_text = None  # type: ignore
                        file_to_process.keywords = None  # type: ignore
                        file_to_process.embedding_id = None  # type: ignore
                        file_to_process.image_embedding_id = None  # type: ignore
                        file_to_process.has_embedding = 0  # type: ignore
                        file_to_process.processing_status = ProcessingStatus.PENDING  # type: ignore
                        file_to_process.processing_error = None  # type: ignore
                        new_db.commit()

                        # Reprocess
                        await self._process_file(file_to_process, new_db)
                        reprocessed_count += 1
                        self.reprocess_status["completed"] = reprocessed_count
                except Exception as e:
                    logger.error(f"Failed to reprocess file {file.id}: {str(e)}")
                    failed_count += 1
                    self.reprocess_status["failed"] = failed_count
                finally:
                    new_db.close()

            logger.info("="*60)
            logger.info(f"BATCH REPROCESSING COMPLETE: {reprocessed_count}/{total_files} files reprocessed")
            if failed_count > 0:
                logger.warning(f"Failed to reprocess {failed_count} files")
            logger.info("="*60)

        except Exception as e:
            logger.error(f"Batch reprocessing error: {str(e)}", exc_info=True)
        finally:
            self.reprocess_status["is_running"] = False
            db.close()

    async def reprocess_single_file(self, file_id: int):
        """Reprocess a single file by ID"""
        logger.info(f"STARTING REPROCESSING OF FILE {file_id}")
        
        db = SessionLocal()
        try:
            file_to_process = db.query(MediaFile).filter(MediaFile.id == file_id).first()
            if not file_to_process:
                raise Exception(f"File {file_id} not found")
                
            # Clear old embedding data
            file_to_process.extracted_text = None  # type: ignore
            file_to_process.keywords = None  # type: ignore
            file_to_process.embedding_id = None  # type: ignore
            file_to_process.image_embedding_id = None  # type: ignore
            file_to_process.has_embedding = 0  # type: ignore
            file_to_process.processing_status = ProcessingStatus.PENDING  # type: ignore
            file_to_process.processing_error = None  # type: ignore
            db.commit()

            # Reprocess
            await self._process_file(file_to_process, db)
            
            logger.info(f"SINGLE REPROCESSING COMPLETE: File {file_id} reprocessed")

        except Exception as e:
            logger.error(f"Single reprocessing error for {file_id}: {str(e)}", exc_info=True)
            raise
        finally:
            db.close()
