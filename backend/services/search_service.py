"""
Search service - orchestrates hybrid semantic + keyword search
"""
import logging
from typing import List, Dict, Any
from database import SessionLocal
from models import MediaFile, ProcessingStatus
from services.embedding_service import EmbeddingService
from services.vector_index_service import VectorIndexService
from services.hybrid_search_service import HybridSearchService
from config import settings

logger = logging.getLogger(__name__)


class SearchService:
    """Handles semantic and hybrid search operations"""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_index = VectorIndexService()
        self.hybrid_search = HybridSearchService()

    async def initialize(self):
        """Initialize search components"""
        try:
            logger.info("Initializing search service...")

            # Initialize embedding model
            await self.embedding_service.initialize()

            # Initialize FAISS index
            await self.vector_index.initialize()

            # Initialize hybrid search (includes BM25)
            await self.hybrid_search.initialize()

            # Check if we need to rebuild index due to model change
            db = SessionLocal()
            files_with_text = db.query(MediaFile).filter(
                MediaFile.processing_status == ProcessingStatus.SUCCESS,
                MediaFile.extracted_text.isnot(None),
                MediaFile.has_embedding == 0  # Files that need indexing
            ).count()

            db.close()

            if files_with_text > 0:
                logger.info(f"Found {files_with_text} files needing indexing")
                # We'll index them as they come through the normal upload pipeline

            logger.info("Search service initialized successfully")

        except Exception as e:
            logger.error(f"Search service initialization failed: {str(e)}")
            raise

    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Save index one final time
            if self.vector_index.index is not None:
                await self.vector_index.save_index()

            # Cleanup hybrid search
            await self.hybrid_search.cleanup()

            logger.info("Search service cleanup complete")
        except Exception as e:
            logger.error(f"Search service cleanup failed: {str(e)}")

    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Perform intelligent search (hybrid or semantic based on configuration)
        Returns list of matching files with relevance scores
        """
        try:
            logger.info(f"Search for: '{query}' (hybrid: {settings.HYBRID_SEARCH_ENABLED})")

            if settings.HYBRID_SEARCH_ENABLED:
                # Use hybrid search (semantic + keyword)
                results = await self.hybrid_search.hybrid_search(query, limit)
                logger.info(f"Hybrid search returned {len(results)} results")
                return results
            else:
                # Fallback to semantic-only search
                results = await self._semantic_only_search(query, limit)
                logger.info(f"Semantic search returned {len(results)} results")
                return results

        except Exception as e:
            logger.error(f"Search failed: {str(e)}", exc_info=True)
            # Return empty results instead of 500 to prevent blank page
            return []

    async def _semantic_only_search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Original semantic search implementation (fallback)
        """
        try:
            logger.info(f"Semantic-only search for: '{query}'")

            # Generate query embedding
            query_embedding = await self.embedding_service.generate_embedding(query)

            # Search vector index
            search_results = await self.vector_index.search(query_embedding, k=limit)

            if not search_results:
                logger.info("No results found")
                return []

            # Get file details from database
            db = SessionLocal()
            results = []

            for file_id, similarity_score in search_results:
                # Filter by similarity threshold
                if similarity_score < settings.SIMILARITY_THRESHOLD:
                    continue

                file = db.query(MediaFile).filter(MediaFile.id == file_id).first()

                if file:
                    file_dict = file.to_dict()
                    file_dict['relevance_score'] = round(float(similarity_score), 4)
                    results.append(file_dict)

            db.close()

            # Sort by relevance score (highest first)
            results.sort(key=lambda x: x['relevance_score'], reverse=True)

            logger.info(f"Returning {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Semantic search failed: {str(e)}", exc_info=True)
            return []

    async def add_to_index(self, file_id: int, text: str):
        """Add a file's embedding to the search index"""
        try:
            if settings.HYBRID_SEARCH_ENABLED:
                # Add to hybrid index (semantic + keyword)
                await self.hybrid_search.add_document_to_index(file_id, text)
            else:
                # Add to semantic index only
                embedding = await self.embedding_service.generate_embedding(text)
                await self.vector_index.add_vector(file_id, embedding)

            logger.info(f"Added file {file_id} to search index")

        except Exception as e:
            logger.error(f"Failed to add file {file_id} to index: {str(e)}")
            raise

    async def remove_from_index(self, file_id: int):
        """Remove a file from the search index"""
        try:
            if settings.HYBRID_SEARCH_ENABLED:
                await self.hybrid_search.remove_document_from_index(file_id)
            else:
                await self.vector_index.remove_vector(file_id)

            logger.info(f"Removed file {file_id} from search index")
        except Exception as e:
            logger.error(f"Failed to remove file {file_id} from index: {str(e)}")
            raise

    async def rebuild_index(self):
        """Rebuild the entire search index from database"""
        try:
            logger.info("Starting full index rebuild...")

            if settings.HYBRID_SEARCH_ENABLED:
                await self.hybrid_search.rebuild_indices()
            else:
                await self.vector_index.rebuild_from_database()

            logger.info("Index rebuild complete")
        except Exception as e:
            logger.error(f"Index rebuild failed: {str(e)}")
            raise
