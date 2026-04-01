"""
Analyze current search quality and test different thresholds
Run this to evaluate your search system performance
"""
import asyncio
from database import SessionLocal
from models import MediaFile, ProcessingStatus
from services.embedding_service import EmbeddingService
from services.vector_index_service import VectorIndexService
from config import settings
import numpy as np

async def analyze_search_quality():
    """Comprehensive analysis of search system"""

    print("=" * 70)
    print("SEARCHX - SEARCH QUALITY ANALYSIS")
    print("=" * 70)
    print()

    # Initialize services
    print("[1/5] Initializing services...")
    embedding_service = EmbeddingService()
    vector_service = VectorIndexService()

    await embedding_service.initialize()
    await vector_service.initialize()

    # Get database stats
    print("[2/5] Analyzing database...")
    db = SessionLocal()

    total_files = db.query(MediaFile).count()
    with_embeddings = db.query(MediaFile).filter(MediaFile.has_embedding == 1).count()
    files = db.query(MediaFile).filter(MediaFile.has_embedding == 1).all()

    print(f"   Total files: {total_files}")
    print(f"   With embeddings: {with_embeddings}")
    print(f"   Without embeddings: {total_files - with_embeddings}")
    print()

    if len(files) == 0:
        print("[ERROR] No files with embeddings found!")
        db.close()
        return

    # Analyze text lengths
    print("[3/5] Text extraction analysis...")
    text_lengths = [len(f.extracted_text) if f.extracted_text else 0 for f in files]
    print(f"   Min text length: {min(text_lengths)} chars")
    print(f"   Max text length: {max(text_lengths)} chars")
    print(f"   Average text length: {np.mean(text_lengths):.0f} chars")
    print(f"   Median text length: {np.median(text_lengths):.0f} chars")
    print()

    # Show sample extracted texts
    print("[4/5] Sample extracted texts:")
    for i, file in enumerate(files[:3], 1):
        text_preview = file.extracted_text[:100] if file.extracted_text else "None"
        print(f"   File {i}: {file.original_filename}")
        print(f"      Text: {text_preview}...")
        print(f"      Length: {len(file.extracted_text) if file.extracted_text else 0} chars")
        print()

    # Test queries with different thresholds
    print("[5/5] Testing search with different thresholds...")
    print()

    test_queries = [
        "income tax",
        "election id",
        "government document",
        "certificate",
        "education"
    ]

    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]

    for query in test_queries:
        print(f"Query: '{query}'")
        print("-" * 60)

        # Generate query embedding
        query_emb = await embedding_service.generate_embedding(query)

        # Search
        raw_results = await vector_service.search(query_emb, k=20)

        # Test different thresholds
        for threshold in thresholds:
            filtered = [r for r in raw_results if r[1] >= threshold]
            print(f"   Threshold {threshold:.1f}: {len(filtered)} results", end="")

            if filtered:
                top_score = filtered[0][1]
                print(f" (top score: {top_score:.3f})")

                # Show top 3 with scores
                for i, (file_id, score) in enumerate(filtered[:3], 1):
                    file = db.query(MediaFile).filter(MediaFile.id == file_id).first()
                    if file:
                        print(f"      {i}. {file.original_filename[:30]:<30} [{score:.3f}]")
            else:
                print()

        print()

    db.close()

    # Recommendations
    print("=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    print()

    print("[Threshold Analysis]")
    print("   Current threshold: 0.1 (very permissive)")
    print()
    print("   Recommendations based on your data:")
    print("   • 0.1-0.2: Returns too many irrelevant results (NOT recommended)")
    print("   • 0.3-0.4: Good balance (RECOMMENDED for general use)")
    print("   • 0.5+: Very strict, only highly relevant (for precision)")
    print()

    print("[Model Quality]")
    print(f"   Current model: {settings.EMBEDDING_MODEL}")
    print(f"   Dimension: {settings.EMBEDDING_DIMENSION}")
    print()
    print("   Consider upgrading to:")
    print("   • all-mpnet-base-v2 (768D) - Better accuracy, slower")
    print("   • all-MiniLM-L12-v2 (384D) - Same speed, slightly better")
    print()

    print("[Next Steps]")
    print("   1. Use Admin Dashboard to test queries visually")
    print("   2. Adjust SIMILARITY_THRESHOLD in config.py")
    print("   3. Consider hybrid search for exact match handling")
    print("   4. Read RANKING_IMPROVEMENT_GUIDE.md for detailed options")
    print()

if __name__ == "__main__":
    asyncio.run(analyze_search_quality())
