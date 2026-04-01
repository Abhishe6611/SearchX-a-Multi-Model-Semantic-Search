"""
Embedding service - generates and manages semantic embeddings
"""
import logging
import asyncio
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from typing import List
from config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Handles embedding generation using sentence transformers"""
    
    def __init__(self):
        self.model: SentenceTransformer | None = None
        self.device: str | None = None
        self.embedding_counter = 0
        self._init_lock = asyncio.Lock()
        
    def _get_model(self) -> SentenceTransformer:
        """Get the text embedding model, ensuring it's initialized"""
        if self.model is None:
            raise RuntimeError("Text embedding model not initialized. Call initialize() first.")
        return self.model


    async def initialize(self):
        """Initialize both embedding models"""
        async with self._init_lock:
            if self.model is not None:
                return  # Skip if already initialized
                
            try:
                logger.info(f"Loading text embedding model: {settings.EMBEDDING_MODEL}")
            
                # Set device
                self.device = 'cuda' if settings.USE_GPU and torch.cuda.is_available() else 'cpu'
                logger.info(f"Using device: {self.device}")
                
                # Load text model
                self.model = SentenceTransformer(settings.EMBEDDING_MODEL, device=self.device)
                test_embedding: np.ndarray = self.model.encode("test", convert_to_numpy=True)
                logger.info(f"Text model loaded successfully. Dimension: {len(test_embedding)}")
                
            except Exception as e:
                logger.error(f"Failed to initialize embedding models: {str(e)}")
                raise
    
    async def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding vector for text"""
        try:
            # Ensure model is initialized
            model = self._get_model()
            
            # Clean and truncate text if too long
            text = text.strip()
            if len(text) == 0:
                raise ValueError("Cannot generate embedding for empty text")
            
            # Truncate very long text (model has token limits)
            max_chars = 5000
            if len(text) > max_chars:
                text = text[:max_chars]
                logger.warning(f"Text truncated to {max_chars} characters")
            
            import asyncio
            # Offload heavy PyTorch CPU calculations to a secondary thread so the main asyncio loop doesn't hang!
            embedding: np.ndarray = await asyncio.to_thread(
                model.encode,
                text,
                convert_to_numpy=True,
                show_progress_bar=False,
                normalize_embeddings=True
            )
            
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise
    
    async def generate_batch_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts (batch processing)"""
        try:
            # Ensure model is initialized
            model = self._get_model()
            
            # Clean texts
            texts = [t.strip()[:5000] for t in texts if t.strip()]
            
            if len(texts) == 0:
                raise ValueError("No valid texts to embed")
            
            import asyncio
            # Generate embeddings in batch, pushed to isolated thread
            embeddings: np.ndarray = await asyncio.to_thread(
                model.encode,
                texts,
                convert_to_numpy=True,
                show_progress_bar=False,
                batch_size=32,
                normalize_embeddings=True
            )
            
            logger.info(f"Generated {len(embeddings)} text embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {str(e)}")
            raise


