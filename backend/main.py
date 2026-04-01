"""
SearchX - Semantic Media Search System
Main FastAPI Application
"""
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from database import init_db, get_db
from models import MediaFile, ProcessingStatus
from services.upload_service import UploadService
from services.search_service import SearchService
from services.thumbnail_service import ThumbnailService
from config import settings
from utils.path_utils import get_physical_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize services
upload_service = UploadService()
search_service = SearchService()
thumbnail_service = ThumbnailService()

# Global state for background model loading
class AppState:
    models_loading: bool = True
    models_ready: bool = False
    model_load_error: str | None = None

app_state = AppState()

async def background_initialize_models():
    """Background task to load AI models without blocking the UI/Database endpoints"""
    try:
        logger.info("⏳ Background Task: Initializing heavy AI Models (CLIP + MPNet)...")
        await search_service.initialize()
        app_state.models_loading = False
        app_state.models_ready = True
        logger.info("✅ Background Task: AI Models successfully loaded into RAM!")
    except Exception as e:
        logger.error(f"❌ Background Task: Failed to load models: {str(e)}")
        app_state.models_loading = False
        app_state.model_load_error = str(e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Starting SearchX API...")
    init_db()
    
    # Start AI model initialization silently in background
    asyncio.create_task(background_initialize_models())
    logger.info("SearchX API fully started (Models downloading/loading asynchronously)")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SearchX API...")
    await search_service.cleanup()
    logger.info("SearchX API shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="SearchX API",
    description="Semantic media search system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.THUMBNAIL_DIR, exist_ok=True)

# Mount static file directories for media serving
# These serve files from storage/files and storage/thumbnails directories
app.mount("/storage", StaticFiles(directory=str(settings.BASE_DIR / "storage")), name="storage")


@app.get("/")
async def root() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "SearchX API",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy" if app_state.models_ready else "loading",
        "models_ready": app_state.models_ready,
        "models_loading": app_state.models_loading,
        "error": app_state.model_load_error,
        "service": "SearchX API",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/api/upload", response_model=dict)
async def upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
) -> Dict[str, Any]:
    """
    Upload multiple media files (images/documents)
    Returns list of uploaded files with their processing status
    """
    try:
        logger.info(f"🔼 Upload: Received {len(files)} files")
        results = await upload_service.process_uploads(files, background_tasks)
        
        return {
            "success": True,
            "message": f"Successfully processed {len(results)} files",
            "files": results
        }
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/api/files")
async def get_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get list of all uploaded files with optional status filter
    """
    try:
        db_gen = get_db()
        db: Session = next(db_gen)
        try:
            query = db.query(MediaFile)
            
            if status:
                query = query.filter(MediaFile.processing_status == status)
            
            total: int = query.count()
            files: List[MediaFile] = query.order_by(MediaFile.upload_date.desc()).offset(skip).limit(limit).all()
            
            return {
                "success": True,
                "total": total,
                "skip": skip,
                "limit": limit,
                "files": [file.to_dict() for file in files]
            }
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error fetching files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/files/{file_id}")
async def get_file(file_id: int) -> Dict[str, Any]:
    """Get details of a specific file"""
    try:
        db_gen = get_db()
        db: Session = next(db_gen)
        try:
            file: Optional[MediaFile] = db.query(MediaFile).filter(MediaFile.id == file_id).first()
            
            if not file:
                raise HTTPException(status_code=404, detail="File not found")
            
            return {
                "success": True,
                "file": file.to_dict()
            }
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching file {file_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/files/{file_id}")
async def delete_file(file_id: int) -> Dict[str, Any]:
    """Delete a file and all associated data"""
    db_gen = get_db()
    db: Session = next(db_gen)
    try:
        file: Optional[MediaFile] = db.query(MediaFile).filter(MediaFile.id == file_id).first()
        
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Cast Column types to actual types and convert URL paths to physical paths
        file_path_url = str(file.file_path)
        file_path = get_physical_path(file_path_url)
        # Use getattr for nullable columns to avoid SQLAlchemy Column type issues
        thumbnail_path_db = getattr(file, 'thumbnail_path', None)
        thumbnail_path_url = str(thumbnail_path_db) if thumbnail_path_db is not None else None
        thumbnail_path = get_physical_path(thumbnail_path_url) if thumbnail_path_url else None
        
        # Delete physical files
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"🗑️ Deleted file: {file_path}")
        
        if thumbnail_path and os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
            logger.info(f"🗑️ Deleted thumbnail: {thumbnail_path}")
        
        # Remove from vector index
        await search_service.remove_from_index(file_id)
        
        # Delete from database
        db.delete(file)
        db.commit()
        
        logger.info(f"Successfully deleted file {file_id}")
        return {
            "success": True,
            "message": "File deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.post("/api/search", response_model=dict)
async def search(query: str = Query(..., min_length=1), limit: int = Query(20, ge=1, le=100)) -> Dict[str, Any]:
    """
    Semantic search across all media files
    Returns ranked results by relevance
    """
    if not app_state.models_ready:
        raise HTTPException(
            status_code=503, 
            detail="AI Models are still initializing. Please wait a few moments and try again."
        )

    try:
        logger.info(f"🔍 Search: '{query}' (limit: {limit})")
        results: List[Dict[str, Any]] = await search_service.search(query, limit)
        logger.info(f"✅ Search: Found {len(results)} results")
        
        return {
            "success": True,
            "query": query,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"❌ Search error: {str(e)}", exc_info=True)
        # Return empty results instead of 500 to prevent blank page
        return {
            "success": False,
            "query": query,
            "count": 0,
            "results": [],
            "error": str(e)
        }


@app.get("/api/files/{file_id}/download")
@app.get("/api/download/{file_id}")
async def download_file(file_id: int) -> FileResponse:
    """Download original file (supports both endpoint patterns)"""
    try:
        db_gen = get_db()
        db: Session = next(db_gen)
        try:
            file: Optional[MediaFile] = db.query(MediaFile).filter(MediaFile.id == file_id).first()
            
            if not file:
                raise HTTPException(status_code=404, detail="File not found")
            
            # Cast Column types to actual types
            file_path_url = str(file.file_path)
            file_path = get_physical_path(file_path_url)  # Convert URL path to physical path
            original_filename = str(file.original_filename)
            file_type = str(file.file_type)
            
            if not os.path.exists(file_path):
                logger.error(f"❌ Download: File not found on disk: {file_path}")
                raise HTTPException(status_code=404, detail="File not found")
            
            logger.info(f"📥 Download: Serving {original_filename} ({file_type})")
            return FileResponse(
                path=file_path,
                filename=original_filename,
                media_type=file_type,
                headers={"Content-Disposition": f'attachment; filename="{original_filename}"'}
            )
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/media/{file_id}")
async def get_media(file_id: int) -> FileResponse:
    """Get media file for viewing (not download)"""
    try:
        db_gen = get_db()
        db: Session = next(db_gen)
        try:
            file: Optional[MediaFile] = db.query(MediaFile).filter(MediaFile.id == file_id).first()
            
            if not file:
                raise HTTPException(status_code=404, detail="File not found")
            
            file_path_url = str(file.file_path)
            file_path = get_physical_path(file_path_url)  # Convert URL path to physical path
            file_type = str(file.file_type)
            
            if not os.path.exists(file_path):
                logger.error(f"❌ Media: File not found on disk: {file_path}")
                raise HTTPException(status_code=404, detail="File not found")
            
            logger.info(f"📺 Media: Serving {file.original_filename} ({file_type})")
            return FileResponse(
                path=file_path,
                media_type=file_type
            )
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Media serve error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/repair")
async def repair_media_pipeline(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Repair stuck files and regenerate missing thumbnails"""
    try:
        logger.info("Starting media pipeline repair...")
        background_tasks.add_task(upload_service.repair_pipeline)

        return {
            "success": True,
            "message": "Repair process started in background"
        }
    except Exception as e:
        logger.error(f"Repair error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/reprocess-all")
async def reprocess_all_files(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Batch reprocess all files: re-extract text and regenerate embeddings for accuracy
    This re-processes all successfully indexed files with improved OCR/parsing
    """
    try:
        logger.info("Starting batch reprocessing of all files...")
        
        # Explicitly lock synchronously so frontend polling doesn't abort early
        upload_service.reprocess_status["is_running"] = True
        upload_service.reprocess_status["completed"] = 0
        upload_service.reprocess_status["failed"] = 0
        
        background_tasks.add_task(upload_service.reprocess_all_files)

        return {
            "success": True,
            "message": "Batch reprocessing started in background. This may take a while depending on file count."
        }
    except Exception as e:
        logger.error(f"Batch reprocessing error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/reprocess/{file_id}")
async def reprocess_single_file(file_id: int, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Reprocess a single file by ID
    """
    try:
        logger.info(f"Starting single reprocessing of file {file_id}...")
        
        background_tasks.add_task(upload_service.reprocess_single_file, file_id)

        return {
            "success": True,
            "message": f"Single reprocessing started for file {file_id}. This may take a minute."
        }
    except Exception as e:
        logger.error(f"Single reprocessing error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/reprocess-status")
async def get_reprocess_status() -> Dict[str, Any]:
    """Get real-time tracking of global reprocessing pipeline"""
    return upload_service.reprocess_status


@app.get("/api/stats")
async def get_stats() -> Dict[str, Any]:
    """Get system statistics"""
    try:
        db_gen = get_db()
        db: Session = next(db_gen)
        try:
            total_files: int = db.query(MediaFile).count()
            success_count: int = db.query(MediaFile).filter(
                MediaFile.processing_status == ProcessingStatus.SUCCESS
            ).count()
            failed_count: int = db.query(MediaFile).filter(
                MediaFile.processing_status == ProcessingStatus.FAILED
            ).count()
            pending_count: int = db.query(MediaFile).filter(
                MediaFile.processing_status == ProcessingStatus.PENDING
            ).count()

            images_count: int = db.query(MediaFile).filter(
                MediaFile.file_type.in_(['image/jpeg', 'image/png', 'image/webp'])
            ).count()

            docs_count: int = db.query(MediaFile).filter(
                MediaFile.file_type.in_(['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'])
            ).count()

            return {
                "success": True,
                "stats": {
                    "total_files": total_files,
                    "processed": success_count,
                    "failed": failed_count,
                    "pending": pending_count,
                    "images": images_count,
                    "documents": docs_count
                }
            }
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Stats error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/embeddings")
async def get_all_embeddings() -> Dict[str, Any]:
    """
    Admin endpoint: Get all files with their extracted text and embedding info
    Shows complete extracted content for analysis
    """
    try:
        db_gen = get_db()
        db: Session = next(db_gen)
        try:
            files: List[MediaFile] = db.query(MediaFile).order_by(MediaFile.upload_date.desc()).all()

            detailed_files = []
            for file in files:
                file_info = {
                    "id": file.id,
                    "original_filename": file.original_filename,
                    "file_type": file.file_type,
                    "file_size": file.file_size,
                    "processing_status": file.processing_status.value if file.processing_status else "unknown",
                    "has_embedding": bool(file.has_embedding),
                    "embedding_id": file.embedding_id,
                    "upload_date": file.upload_date.isoformat() if file.upload_date else None,
                    "processed_date": file.processed_date.isoformat() if file.processed_date else None,
                    "extracted_text": file.extracted_text,  # Full text, not truncated
                    "extracted_text_length": len(file.extracted_text) if file.extracted_text else 0,
                    "processing_error": file.processing_error,
                    "file_path": file.file_path,
                    "thumbnail_path": file.thumbnail_path
                }
                detailed_files.append(file_info)

            return {
                "success": True,
                "total": len(detailed_files),
                "files": detailed_files
            }
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Admin embeddings error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/embedding/{file_id}")
async def get_embedding_details(file_id: int) -> Dict[str, Any]:
    """
    Admin endpoint: Get detailed embedding information for a specific file
    Includes the actual embedding vector
    """
    try:
        db_gen = get_db()
        db: Session = next(db_gen)
        try:
            file: Optional[MediaFile] = db.query(MediaFile).filter(MediaFile.id == file_id).first()

            if not file:
                raise HTTPException(status_code=404, detail="File not found")

            # Get embedding vector from FAISS index
            embedding_vector = None
            embedding_stats = None

            if file.has_embedding and file.embedding_id is not None:
                try:
                    # Reconstruct vector from FAISS
                    vector = search_service.vector_index.index.reconstruct(int(file.embedding_id))
                    embedding_vector = vector.tolist()  # Convert numpy array to list

                    # Calculate statistics
                    import numpy as np
                    embedding_stats = {
                        "dimension": len(vector),
                        "norm": float(np.linalg.norm(vector)),
                        "mean": float(np.mean(vector)),
                        "std": float(np.std(vector)),
                        "min": float(np.min(vector)),
                        "max": float(np.max(vector)),
                        "non_zero_count": int(np.count_nonzero(vector))
                    }
                except Exception as e:
                    logger.warning(f"Could not retrieve embedding vector: {str(e)}")

            # Serve genuine computed lexicon stored directly in db
            keywords = []
            if getattr(file, 'keywords', None):
                for k in file.keywords.split(','):
                    k_clean = k.strip()
                    if k_clean:
                        keywords.append({"word": k_clean, "count": 1})

            return {
                "success": True,
                "file": {
                    "id": file.id,
                    "original_filename": file.original_filename,
                    "file_type": file.file_type,
                    "processing_status": file.processing_status.value if file.processing_status else "unknown",
                    "extracted_text": file.extracted_text,
                    "extracted_text_length": len(file.extracted_text) if file.extracted_text else 0,
                    "has_embedding": bool(file.has_embedding),
                    "embedding_id": file.embedding_id,
                    "embedding_vector": embedding_vector,
                    "embedding_stats": embedding_stats,
                    "keywords": keywords,
                    "upload_date": file.upload_date.isoformat() if file.upload_date else None
                }
            }
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Embedding details error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/test-search")
async def test_search_ranking(
    query: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100)
) -> Dict[str, Any]:
    """
    Admin endpoint: Test search with detailed ranking information
    Returns results with similarity scores and extracted text for analysis
    """
    try:
        logger.info(f"Admin test search: '{query}' (limit: {limit})")

        # Generate query embedding
        query_embedding = await search_service.embedding_service.generate_embedding(query)

        # Search vector index
        search_results = await search_service.vector_index.search(query_embedding, k=limit)

        if not search_results:
            return {
                "success": True,
                "query": query,
                "count": 0,
                "results": []
            }

        # Get detailed file information
        db_gen = get_db()
        db: Session = next(db_gen)
        results = []

        try:
            for file_id, similarity_score in search_results:
                file = db.query(MediaFile).filter(MediaFile.id == file_id).first()

                if file:
                    # Pull direct Kimi keywords instead of recomputing simple frequency
                    keywords = []
                    if getattr(file, 'keywords', None):
                        keywords = [k.strip() for k in file.keywords.split(',') if k.strip()][:10]

                    file_dict = {
                        "id": file.id,
                        "original_filename": file.original_filename,
                        "file_type": file.file_type,
                        "relevance_score": round(float(similarity_score), 4),
                        "relevance_percentage": round(float(similarity_score) * 100, 2),
                        "extracted_text": file.extracted_text,
                        "extracted_text_length": len(file.extracted_text) if file.extracted_text else 0,
                        "keywords": keywords,
                        "has_embedding": bool(file.has_embedding),
                        "embedding_id": file.embedding_id,
                        "file_path": file.file_path,
                        "thumbnail_path": file.thumbnail_path
                    }
                    results.append(file_dict)

            # Sort by relevance
            results.sort(key=lambda x: x['relevance_score'], reverse=True)

            return {
                "success": True,
                "query": query,
                "query_length": len(query),
                "count": len(results),
                "results": results,
                "index_info": {
                    "total_vectors": search_service.vector_index.index.ntotal if search_service.vector_index.index else 0,
                    "dimension": settings.EMBEDDING_DIMENSION,
                    "model": settings.EMBEDDING_MODEL
                }
            }
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Admin test search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD
    )
