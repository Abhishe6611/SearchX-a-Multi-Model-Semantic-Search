"""
Configuration management using environment variables
"""
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings"""
    
    # Base paths
    BASE_DIR: Path = Path(__file__).parent
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", str(BASE_DIR / "storage" / "files"))
    UPLOAD_DIR: str = os.getenv("STORAGE_DIR", str(BASE_DIR / "storage" / "files"))  # Alias for STORAGE_DIR
    THUMBNAILS_DIR: str = os.getenv("THUMBNAILS_DIR", str(BASE_DIR / "storage" / "thumbnails"))
    THUMBNAIL_DIR: str = os.getenv("THUMBNAILS_DIR", str(BASE_DIR / "storage" / "thumbnails"))  # Alias for THUMBNAILS_DIR
    EMBEDDINGS_DIR: str = os.getenv("EMBEDDINGS_DIR", str(BASE_DIR / "storage" / "embeddings"))
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'searchx.db'}"
    )
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    RELOAD: bool = False  # Disable reload to fix route registration issues
    
    # CORS
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173"
    ).split(",")
    ALLOWED_ORIGINS: List[str] = CORS_ORIGINS  # Alias for CORS_ORIGINS
    
    # File upload settings
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", str(50 * 1024 * 1024)))  # 50MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]
    ALLOWED_DOC_TYPES: List[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ]
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".webp", ".pdf", ".docx", ".txt"]
    
    # Thumbnail settings
    THUMBNAIL_SIZE: tuple[int, int] = (300, 300)
    THUMBNAIL_QUALITY: int = 85
    
    # Embedding model settings (Text / Documents)
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2")
    EMBEDDING_DIMENSION: int = 768  # Changed from 384 for all-mpnet-base-v2

    # VLM Integration
    NVIDIA_API_KEY: str = os.getenv(
        "NVIDIA_API_KEY", 
        "Enter Your API Here"
    )
    VLM_MODEL: str = os.getenv("VLM_MODEL", "moonshotai/kimi-k2.5")
    
    # Document Intelligence (Nemotron)
    NEMOTRON_API_KEY: str = os.getenv(
        "NEMOTRON_API_KEY", 
        "Enter Your API Here"
    )
    NEMOTRON_MODEL: str = "nvidia/nemotron-ocr-v1"

    # Vector search settings
    VECTOR_INDEX_PATH: str = os.getenv(
        "VECTOR_INDEX_PATH",
        str(BASE_DIR / "storage" / "faiss_index")
    )

    USE_GPU: bool = os.getenv("USE_GPU", "False").lower() == "true"

    # Search settings
    DEFAULT_SEARCH_LIMIT: int = 20
    MAX_SEARCH_LIMIT: int = 100
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.25"))  # Lowered from 0.35 to include more relevant results

    # Hybrid search settings
    HYBRID_SEARCH_ENABLED: bool = True
    SEMANTIC_WEIGHT: float = float(os.getenv("SEMANTIC_WEIGHT", "0.4"))  # Weight for semantic similarity
    KEYWORD_WEIGHT: float = float(os.getenv("KEYWORD_WEIGHT", "0.6"))   # Weight for BM25 keyword matching (prioritize exact matches)
    
    def __init__(self):
        """Create necessary directories"""
        os.makedirs(self.STORAGE_DIR, exist_ok=True)
        os.makedirs(self.THUMBNAILS_DIR, exist_ok=True)
        os.makedirs(self.EMBEDDINGS_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(self.VECTOR_INDEX_PATH), exist_ok=True)



# Global settings instance
settings = Settings()
