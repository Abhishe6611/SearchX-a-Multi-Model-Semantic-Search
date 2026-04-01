"""
Hybrid search service - combines semantic search with BM25 keyword matching
for optimal accuracy across different query types
"""
import logging
import re
import pickle
import os
from typing import List, Dict, Any, Tuple
from collections import defaultdict
import numpy as np
from rank_bm25 import BM25Okapi

from database import SessionLocal
from models import MediaFile, ProcessingStatus
from services.embedding_service import EmbeddingService
from services.vector_index_service import VectorIndexService
from config import settings

logger = logging.getLogger(__name__)


class HybridSearchService:
    """
    Combines semantic search (transformer embeddings + FAISS)
    with keyword search (BM25) for best accuracy
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_index = VectorIndexService()  # Text embeddings
        self.bm25_index = None
        self.file_id_mapping: List[int] = []  # Maps BM25 doc index to MediaFile ID
        self.bm25_index_path = str(settings.BASE_DIR / "storage" / "bm25_index.pkl")
        self.mapping_path = str(settings.BASE_DIR / "storage" / "bm25_mapping.pkl")

    async def initialize(self):
        """Initialize both semantic and keyword search components"""
        try:
            logger.info("Initializing hybrid search service...")

            # Initialize semantic search
            await self.embedding_service.initialize()
            await self.vector_index.initialize()

            # Load or build BM25 index
            await self._load_or_build_bm25_index()

            logger.info("Hybrid search service initialized successfully")

        except Exception as e:
            logger.error(f"Hybrid search initialization failed: {str(e)}")
            raise

    async def _load_or_build_bm25_index(self):
        """Load existing BM25 index or build from database"""
        try:
            if os.path.exists(self.bm25_index_path) and os.path.exists(self.mapping_path):
                # Load existing index
                logger.info("Loading existing BM25 index...")
                with open(self.bm25_index_path, 'rb') as f:
                    self.bm25_index = pickle.load(f)
                with open(self.mapping_path, 'rb') as f:
                    self.file_id_mapping = pickle.load(f)
                logger.info(f"Loaded BM25 index with {len(self.file_id_mapping)} documents")
            else:
                # Build new index
                await self._build_bm25_index()

        except Exception as e:
            logger.error(f"Failed to load BM25 index: {str(e)}")
            # Fallback: build new index
            await self._build_bm25_index()

    async def _build_bm25_index(self):
        """Build BM25 index from database documents"""
        try:
            logger.info("Building BM25 index from database...")

            db = SessionLocal()
            files = db.query(MediaFile).filter(
                MediaFile.processing_status == ProcessingStatus.SUCCESS,
                MediaFile.extracted_text.isnot(None)
            ).all()

            if not files:
                logger.warning("No processed files found for BM25 indexing")
                self.bm25_index = BM25Okapi([])  # Empty index
                self.file_id_mapping = []
                db.close()
                return

            # Prepare documents for BM25
            documents = []
            self.file_id_mapping = []

            for file in files:
                text = str(file.extracted_text) if file.extracted_text else ""
                if text.strip():
                    # Preprocess text for BM25
                    processed_text = self._preprocess_text_for_bm25(text)
                    documents.append(processed_text)
                    self.file_id_mapping.append(file.id)

            # Build BM25 index
            self.bm25_index = BM25Okapi(documents)

            # Save index
            await self._save_bm25_index()

            db.close()
            logger.info(f"Built BM25 index with {len(documents)} documents")

        except Exception as e:
            logger.error(f"Failed to build BM25 index: {str(e)}")
            # Graceful fallback
            self.bm25_index = BM25Okapi([])
            self.file_id_mapping = []

    def _preprocess_text_for_bm25(self, text: str) -> List[str]:
        """Preprocess text for BM25: tokenize, lowercase, remove noise"""
        try:
            # Lowercase
            text = text.lower()

            # Remove special characters but keep alphanumeric and spaces
            text = re.sub(r'[^\w\s]', ' ', text)

            # Split into tokens
            tokens = text.split()

            # Remove very short tokens and common stop words
            stop_words = {
                'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
                'by', 'from', 'this', 'that', 'these', 'those', 'is', 'are', 'was',
                'were', 'be', 'been', 'have', 'has', 'had', 'will', 'would', 'could',
                'should', 'may', 'might', 'can', 'do', 'does', 'did', 'a', 'an'
            }

            filtered_tokens = [
                token for token in tokens
                if len(token) >= 2 and token not in stop_words
            ]

            return filtered_tokens

        except Exception as e:
            logger.warning(f"Text preprocessing failed: {str(e)}")
            return text.lower().split()

    async def _save_bm25_index(self):
        """Save BM25 index and mapping to disk"""
        try:
            os.makedirs(os.path.dirname(self.bm25_index_path), exist_ok=True)

            with open(self.bm25_index_path, 'wb') as f:
                pickle.dump(self.bm25_index, f)
            with open(self.mapping_path, 'wb') as f:
                pickle.dump(self.file_id_mapping, f)

            logger.debug("BM25 index saved successfully")

        except Exception as e:
            logger.error(f"Failed to save BM25 index: {str(e)}")

    async def hybrid_search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining semantic and keyword matching
        Returns ranked results with combined scores
        """
        try:
            logger.info(f"Hybrid search for: '{query}' (limit: {limit})")

            if not settings.HYBRID_SEARCH_ENABLED:
                # Fallback to semantic only
                return await self._semantic_search_only(query, limit)

            import asyncio
            # Execute both search mechanisms asynchronously at the same time!
            semantic_results, keyword_results = await asyncio.gather(
                self._get_semantic_results(query, limit * 2),
                self._get_keyword_results(query, limit * 2)
            )

            # Combine and rank results
            combined_results = self._combine_results(
                semantic_results,
                keyword_results,
                query
            )

            # Get file details from database
            final_results = await self._enrich_with_file_details(combined_results[:limit])

            logger.info(f"Hybrid search returned {len(final_results)} results")
            return final_results

        except Exception as e:
            logger.error(f"Hybrid search failed: {str(e)}", exc_info=True)
            # Graceful fallback to semantic search
            return await self._semantic_search_only(query, limit)

    async def _get_semantic_results(self, query: str, limit: int) -> Dict[int, float]:
        """Get semantic similarity scores for all documents"""
        try:
            query_embedding = await self.embedding_service.generate_embedding(query)
            search_results = await self.vector_index.search(query_embedding, k=limit)

            # Convert to dict {file_id: score}
            semantic_scores = {}
            for file_id, score in search_results:
                semantic_scores[file_id] = float(score)

            logger.debug(f"Semantic search found {len(semantic_scores)} results")
            return semantic_scores

        except Exception as e:
            logger.error(f"Semantic search failed: {str(e)}")
            return {}


    async def _get_keyword_results(self, query: str, limit: int) -> Dict[int, float]:
        """Get BM25 keyword matching scores for all documents"""
        try:
            keyword_scores = {}

            # 1. Get BM25 scores (exact word matching)
            if self.bm25_index and self.file_id_mapping:
                query_tokens = self._preprocess_text_for_bm25(query)

                if query_tokens:
                    bm25_scores = self.bm25_index.get_scores(query_tokens)
                    max_score = max(bm25_scores) if bm25_scores.max() > 0 else 1.0

                    for i, score in enumerate(bm25_scores):
                        if i < len(self.file_id_mapping):
                            file_id = self.file_id_mapping[i]
                            normalized_score = float(score / max_score)
                            if normalized_score > 0.01:
                                keyword_scores[file_id] = normalized_score

            # 2. Add partial/prefix matching for short queries or proper nouns
            partial_scores = await self._get_partial_match_results(query)

            # Combine scores - take the max of BM25 and partial match
            for file_id, partial_score in partial_scores.items():
                if file_id in keyword_scores:
                    keyword_scores[file_id] = max(keyword_scores[file_id], partial_score)
                else:
                    keyword_scores[file_id] = partial_score

            logger.debug(f"Keyword search found {len(keyword_scores)} results (BM25 + partial)")
            return keyword_scores

        except Exception as e:
            logger.error(f"Keyword search failed: {str(e)}")
            return {}

    async def _get_partial_match_results(self, query: str) -> Dict[int, float]:
        """Get partial/substring match scores from database"""
        try:
            db = SessionLocal()
            partial_scores = {}

            # Clean query for matching
            query_lower = query.lower().strip()
            query_tokens = query_lower.split()

            if not query_tokens:
                db.close()
                return {}

            # Get all documents with extracted text
            files = db.query(MediaFile).filter(
                MediaFile.processing_status == ProcessingStatus.SUCCESS,
                MediaFile.extracted_text.isnot(None)
            ).all()

            for file in files:
                text = str(file.extracted_text).lower() if file.extracted_text else ""
                if not text:
                    continue

                # Calculate partial match score
                match_score = 0.0
                total_tokens = len(query_tokens)

                for token in query_tokens:
                    if len(token) < 2:
                        continue

                    # Check for substring match (partial/prefix matching)
                    if token in text:
                        # Full token found as substring
                        match_score += 1.0
                    else:
                        # Check if any word in text starts with this token (prefix match)
                        text_words = text.split()
                        for word in text_words:
                            if word.startswith(token):
                                match_score += 0.8  # Slightly lower score for prefix match
                                break

                if match_score > 0 and total_tokens > 0:
                    # Normalize score to 0-1 range
                    normalized_score = match_score / total_tokens
                    partial_scores[file.id] = min(normalized_score, 1.0)

            db.close()
            logger.debug(f"Partial match found {len(partial_scores)} results")
            return partial_scores

        except Exception as e:
            logger.error(f"Partial match search failed: {str(e)}")
            return {}

    def _combine_results(self, semantic_scores: Dict[int, float],
                        keyword_scores: Dict[int, float],
                        query: str) -> List[Tuple[int, float, Dict[str, float]]]:
        """
        Combine semantic and keyword scores with intelligent weighting
        Returns: [(file_id, combined_score, score_breakdown)]
        """
        try:
            # Get all file IDs from both searches
            all_file_ids = set(semantic_scores.keys()) | set(keyword_scores.keys())

            combined_results = []

            for file_id in all_file_ids:
                semantic_score = semantic_scores.get(file_id, 0.0)
                keyword_score = keyword_scores.get(file_id, 0.0)

                # Adaptive weighting based on query characteristics
                semantic_weight, keyword_weight = self._get_adaptive_weights(query, semantic_score, keyword_score)

                # Combined score
                combined_score = (semantic_weight * semantic_score) + (keyword_weight * keyword_score)

                # Boost for documents that match both approaches
                if semantic_score > 0 and keyword_score > 0:
                    combined_score = combined_score * 1.1  # 10% boost for dual matches

                score_breakdown = {
                    'semantic': semantic_score,
                    'keyword': keyword_score,
                    'semantic_weight': semantic_weight,
                    'keyword_weight': keyword_weight,
                    'combined': combined_score
                }

                combined_results.append((file_id, combined_score, score_breakdown))

            # Sort by combined score (descending)
            combined_results.sort(key=lambda x: x[1], reverse=True)

            logger.debug(f"Combined {len(semantic_scores)} semantic + {len(keyword_scores)} keyword = {len(combined_results)} total")
            return combined_results

        except Exception as e:
            logger.error(f"Result combination failed: {str(e)}")
            # Fallback: semantic only
            return [(fid, score, {'semantic': score, 'keyword': 0, 'combined': score})
                   for fid, score in semantic_scores.items()]

    def _get_adaptive_weights(self, query: str, semantic_score: float, keyword_score: float) -> Tuple[float, float]:
        """
        Determine weights based on query characteristics and available scores
        Returns: (semantic_weight, keyword_weight)
        """
        try:
            # Base weights from config
            base_semantic = settings.SEMANTIC_WEIGHT
            base_keyword = settings.KEYWORD_WEIGHT

            # Adapt based on query length and characteristics
            query_tokens = query.lower().split()

            # Short queries (1-2 words) often benefit more from keyword matching
            if len(query_tokens) <= 2:
                keyword_boost = 0.1
                semantic_weight = max(0.3, base_semantic - keyword_boost)
                keyword_weight = min(0.7, base_keyword + keyword_boost)

            # Long queries (5+ words) often benefit more from semantic understanding
            elif len(query_tokens) >= 5:
                semantic_boost = 0.1
                semantic_weight = min(0.8, base_semantic + semantic_boost)
                keyword_weight = max(0.2, base_keyword - semantic_boost)

            # Medium queries: use base weights
            else:
                semantic_weight = base_semantic
                keyword_weight = base_keyword

            # Check for exact keyword matches (boost keyword weight)
            if keyword_score > 0.5:  # High BM25 score suggests good keyword match
                keyword_weight = min(0.6, keyword_weight + 0.15)
                semantic_weight = 1.0 - keyword_weight

            # Ensure weights sum to 1.0
            total = semantic_weight + keyword_weight
            semantic_weight = semantic_weight / total
            keyword_weight = keyword_weight / total

            return semantic_weight, keyword_weight

        except Exception as e:
            logger.warning(f"Adaptive weighting failed: {str(e)}")
            return settings.SEMANTIC_WEIGHT, settings.KEYWORD_WEIGHT

    async def _enrich_with_file_details(self, results: List[Tuple[int, float, Dict[str, float]]]) -> List[Dict[str, Any]]:
        """Get file details from database and enrich results"""
        try:
            db = SessionLocal()

            enriched_results = []

            for file_id, combined_score, score_breakdown in results:
                # Apply threshold filter
                if combined_score < settings.SIMILARITY_THRESHOLD:
                    continue

                file = db.query(MediaFile).filter(MediaFile.id == file_id).first()

                if file:
                    file_dict = file.to_dict()
                    file_dict['relevance_score'] = round(combined_score, 4)
                    file_dict['score_breakdown'] = {
                        'semantic_score': round(score_breakdown['semantic'], 4),
                        'keyword_score': round(score_breakdown['keyword'], 4),
                        'semantic_weight': round(score_breakdown['semantic_weight'], 3),
                        'keyword_weight': round(score_breakdown['keyword_weight'], 3),
                        'search_type': self._get_search_type(score_breakdown)
                    }
                    enriched_results.append(file_dict)

            db.close()
            return enriched_results

        except Exception as e:
            logger.error(f"Result enrichment failed: {str(e)}")
            return []

    def _get_search_type(self, score_breakdown: Dict[str, float]) -> str:
        """Determine the primary search type for this result"""
        semantic_score = score_breakdown.get('semantic', 0)
        keyword_score = score_breakdown.get('keyword', 0)

        if semantic_score > 0.1 and keyword_score > 0.1:
            return 'hybrid'
        elif semantic_score > keyword_score:
            return 'semantic'
        elif keyword_score > semantic_score:
            return 'keyword'
        else:
            return 'semantic'

    async def _semantic_search_only(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback to semantic search only using both text and image models"""
        try:
            logger.info("Falling back to semantic search only")

            semantic_scores = await self._get_semantic_results(query, limit * 2)

            if not semantic_scores:
                return []

            # Get file details from database
            db = SessionLocal()
            results = []

            for file_id, similarity_score in semantic_scores.items():
                if similarity_score < settings.SIMILARITY_THRESHOLD:
                    continue

                file = db.query(MediaFile).filter(MediaFile.id == file_id).first()

                if file:
                    file_dict = file.to_dict()
                    file_dict['relevance_score'] = round(float(similarity_score), 4)
                    file_dict['score_breakdown'] = {
                        'semantic_score': round(float(similarity_score), 4),
                        'keyword_score': 0.0,
                        'semantic_weight': 1.0,
                        'keyword_weight': 0.0,
                        'search_type': 'semantic'
                    }
                    results.append(file_dict)

            db.close()
            results.sort(key=lambda x: x['relevance_score'], reverse=True)

            return results

        except Exception as e:
            logger.error(f"Semantic search fallback failed: {str(e)}")
            return []

    async def add_document_to_index(self, file_id: int, text: str):
        """Add new document to both semantic and keyword indices"""
        try:
            # Add to semantic index (handled by existing services)
            embedding = await self.embedding_service.generate_embedding(text)
            await self.vector_index.add_vector(file_id, embedding)

            # Add to BM25 index
            if self.bm25_index is not None:
                processed_text = self._preprocess_text_for_bm25(text)

                # Rebuild BM25 index (BM25 doesn't support incremental updates easily)
                await self._build_bm25_index()

                logger.info(f"Added document {file_id} to hybrid index")

        except Exception as e:
            logger.error(f"Failed to add document {file_id} to hybrid index: {str(e)}")

    async def remove_document_from_index(self, file_id: int):
        """Remove document from both indices"""
        try:
            # Remove from semantic index
            await self.vector_index.remove_vector(file_id)

            # Rebuild BM25 index (simpler than selective removal)
            await self._build_bm25_index()

            logger.info(f"Removed document {file_id} from hybrid index")

        except Exception as e:
            logger.error(f"Failed to remove document {file_id} from hybrid index: {str(e)}")

    async def rebuild_indices(self):
        """Rebuild both semantic and keyword indices"""
        try:
            logger.info("Rebuilding hybrid search indices...")

            # Rebuild semantic index
            await self.vector_index.rebuild_from_database()

            # Rebuild BM25 index
            await self._build_bm25_index()

            logger.info("Hybrid indices rebuilt successfully")

        except Exception as e:
            logger.error(f"Failed to rebuild hybrid indices: {str(e)}")
            raise

    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Save BM25 index
            if self.bm25_index is not None:
                await self._save_bm25_index()

            logger.info("Hybrid search service cleanup complete")

        except Exception as e:
            logger.error(f"Hybrid search cleanup failed: {str(e)}")