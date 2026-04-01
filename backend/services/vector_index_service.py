"""
Vector index service - manages FAISS index for semantic search
"""
import os
import logging
import numpy as np
import faiss
import pickle
from typing import List, Tuple
from config import settings
from database import SessionLocal
from models import MediaFile

logger = logging.getLogger(__name__)


class VectorIndexService:
    """Manages FAISS vector index for similarity search"""
    
    def __init__(self, index_path: str = None, dimension: int = None):
        self.index = None
        self.id_mapping: dict[int, int] = {}  # Maps FAISS index position to MediaFile ID
        self.index_path = index_path or settings.VECTOR_INDEX_PATH
        self.mapping_path = f"{self.index_path}_mapping.pkl"
        self.dimension = dimension if dimension is not None else settings.EMBEDDING_DIMENSION
    
    async def initialize(self):
        """Initialize or load existing FAISS index"""
        try:
            if os.path.exists(f"{self.index_path}.index") and os.path.exists(self.mapping_path):
                # Load existing index
                logger.info("Loading existing FAISS index...")
                self.index = faiss.read_index(f"{self.index_path}.index")
                
                with open(self.mapping_path, 'rb') as f:
                    self.id_mapping = pickle.load(f)
                
                logger.info(f"Loaded index with {self.index.ntotal} vectors")
            else:
                # Create new index
                logger.info("Creating new FAISS index...")
                # Use IndexFlatIP for cosine similarity (with normalized vectors)
                self.index = faiss.IndexFlatIP(self.dimension)
                self.id_mapping = {}
                logger.info("Created new FAISS index")
            
        except Exception as e:
            logger.error(f"Failed to initialize FAISS index: {str(e)}")
            # Create new index on failure
            self.index = faiss.IndexFlatIP(self.dimension)
            self.id_mapping = {}
    
    async def add_vector(self, file_id: int, embedding: np.ndarray):
        """Add a vector to the index"""
        try:
            if self.index is None:
                await self.initialize()
            
            # Ensure embedding is normalized and correct shape
            embedding = np.array([embedding], dtype=np.float32)
            if embedding.shape[1] != self.dimension:
                raise ValueError(f"Embedding dimension mismatch: {embedding.shape[1]} vs {self.dimension}")
            
            # Add to index
            index_position = self.index.ntotal
            self.index.add(embedding)
            
            # Store mapping
            self.id_mapping[index_position] = file_id
            
            logger.info(f"Added vector for file {file_id} at position {index_position}")
            
            # Save index
            await self.save_index()
            
        except Exception as e:
            logger.error(f"Failed to add vector: {str(e)}")
            raise
    
    async def search(self, query_embedding: np.ndarray, k: int = 20) -> List[Tuple[int, float]]:
        """
        Search for k most similar vectors
        Returns list of (file_id, similarity_score) tuples
        """
        try:
            if self.index is None or self.index.ntotal == 0:
                logger.warning("Index is empty")
                return []
            
            # Ensure query is normalized and correct shape
            query_embedding = np.array([query_embedding], dtype=np.float32)
            
            # Search
            k = min(k, self.index.ntotal)  # Don't search for more than available
            distances, indices = self.index.search(query_embedding, k)
            
            # Convert to file IDs with scores
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx == -1:  # FAISS returns -1 for empty slots
                    continue
                
                file_id = self.id_mapping.get(int(idx))
                if file_id is not None:
                    # Distance is cosine similarity (with IndexFlatIP)
                    similarity_score = float(distance)
                    results.append((file_id, similarity_score))
            
            logger.info(f"Search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise
    
    async def remove_vector(self, file_id: int):
        """
        Remove a vector from the index
        Note: FAISS doesn't support deletion, so we rebuild the index
        """
        try:
            if self.index is None or self.index.ntotal == 0:
                return
            
            logger.info(f"Removing vector for file {file_id}")
            
            # Find index position
            index_position = None
            for pos, fid in self.id_mapping.items():
                if fid == file_id:
                    index_position = pos
                    break
            
            if index_position is None:
                logger.warning(f"File {file_id} not found in index")
                return
            
            # Rebuild index without this vector
            await self._rebuild_index_without(index_position)
            
            logger.info(f"Removed vector for file {file_id}")
            
        except Exception as e:
            logger.error(f"Failed to remove vector: {str(e)}")
            raise
    
    async def _rebuild_index_without(self, skip_position: int):
        """Rebuild index excluding one position"""
        try:
            # Get all vectors except the one to remove
            all_vectors = []
            new_mapping = {}
            
            for i in range(self.index.ntotal):
                if i == skip_position:
                    continue
                
                vector = self.index.reconstruct(int(i))
                all_vectors.append(vector)
                new_mapping[len(all_vectors) - 1] = self.id_mapping[i]
            
            # Create new index
            new_index = faiss.IndexFlatIP(self.dimension)
            
            if all_vectors:
                vectors_array = np.array(all_vectors, dtype=np.float32)
                new_index.add(vectors_array)
            
            # Replace old index
            self.index = new_index
            self.id_mapping = new_mapping
            
            # Save
            await self.save_index()
            
            logger.info(f"Index rebuilt with {self.index.ntotal} vectors")
            
        except Exception as e:
            logger.error(f"Index rebuild failed: {str(e)}")
            raise
    
    async def save_index(self):
        """Save index and mapping to disk"""
        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.index, f"{self.index_path}.index")
            
            # Save ID mapping
            with open(self.mapping_path, 'wb') as f:
                pickle.dump(self.id_mapping, f)
            
            logger.debug("Index saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save index: {str(e)}")
            raise
    
    async def rebuild_from_database(self):
        """Rebuild entire index from database (for maintenance/recovery)"""
        try:
            from services.embedding_service import EmbeddingService
            
            logger.info("Rebuilding index from database...")
            
            # Create new index
            self.index = faiss.IndexFlatIP(self.dimension)
            self.id_mapping = {}
            
            # Get all successfully processed files with text
            db = SessionLocal()
            files = db.query(MediaFile).filter(
                MediaFile.processing_status == "success",
                MediaFile.extracted_text.isnot(None)
            ).all()
            
            logger.info(f"Found {len(files)} files to index")
            
            embedding_service = EmbeddingService()
            await embedding_service.initialize()
            
            # Generate embeddings in batches
            batch_size = 32
            for i in range(0, len(files), batch_size):
                batch = files[i:i+batch_size]
                # Convert Column[str] to str for embedding generation
                texts: list[str] = [str(f.extracted_text) for f in batch]
                
                embeddings = await embedding_service.generate_batch_embeddings(texts)
                
                # Add to index
                start_pos = self.index.ntotal
                self.index.add(embeddings.astype(np.float32))
                
                # Update mapping
                for j, file in enumerate(batch):
                    self.id_mapping[start_pos + j] = file.id
                    
                    # Update database - use setattr to avoid Column type issues
                    file.embedding_id = start_pos + j
                    setattr(file, 'has_embedding', 1)
                
                db.commit()
                logger.info(f"Indexed {i + len(batch)}/{len(files)} files")
            
            # Save index
            await self.save_index()
            
            db.close()
            logger.info("Index rebuild complete")
            
        except Exception as e:
            logger.error(f"Index rebuild failed: {str(e)}")
            raise
