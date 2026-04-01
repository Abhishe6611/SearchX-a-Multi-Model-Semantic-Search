"""
Diagnostic script to trace the semantic search pipeline
"""
import asyncio
from database import SessionLocal
from models import MediaFile
from services.vector_index_service import VectorIndexService
from config import settings
import os

async def main():
    print("\n" + "="*60)
    print("SEMANTIC PIPELINE DIAGNOSTIC")
    print("="*60)
    
    db = SessionLocal()
    files = db.query(MediaFile).all()
    
    print(f"\n📊 DATABASE STATUS")
    print(f"   Total files: {len(files)}")
    
    for f in files:
        print(f"\n{'='*50}")
        print(f"📄 File ID: {f.id}")
        print(f"   Name: {f.original_filename}")
        print(f"   Type: {f.file_type}")
        print(f"   Status: {f.processing_status.name}")
        print(f"   Thumbnail: {'✓' if f.thumbnail_path else '✗'}")
        
        # Check extracted text
        text_len = len(f.extracted_text) if f.extracted_text else 0
        print(f"   Extracted text: {text_len} chars")
        if text_len > 0:
            preview = f.extracted_text[:150].replace('\n', ' ').strip()
            print(f"   Text preview: '{preview}...'")
        else:
            print(f"   Text preview: (EMPTY - THIS IS THE PROBLEM!)")
        
        # Check embedding status
        print(f"   Has embedding: {f.has_embedding}")
        print(f"   Embedding ID: {f.embedding_id}")
    
    db.close()
    
    # Check FAISS index
    print(f"\n{'='*60}")
    print(f"🔍 VECTOR INDEX STATUS")
    print(f"{'='*60}")
    
    vector_service = VectorIndexService()
    await vector_service.initialize()
    
    if vector_service.index:
        print(f"   Index vectors: {vector_service.index.ntotal}")
        print(f"   ID mappings: {len(vector_service.id_mapping)}")
        print(f"   Dimension: {vector_service.dimension}")
        print(f"   Mappings: {vector_service.id_mapping}")
    else:
        print(f"   Index: NOT INITIALIZED")
    
    # Check index files
    print(f"\n{'='*60}")
    print(f"📁 INDEX FILES STATUS")
    print(f"{'='*60}")
    
    index_file = f"{settings.VECTOR_INDEX_PATH}.index"
    mapping_file = f"{settings.VECTOR_INDEX_PATH}_mapping.pkl"
    
    print(f"   Index file: {index_file}")
    print(f"   Exists: {os.path.exists(index_file)}")
    if os.path.exists(index_file):
        print(f"   Size: {os.path.getsize(index_file)} bytes")
    
    print(f"\n   Mapping file: {mapping_file}")
    print(f"   Exists: {os.path.exists(mapping_file)}")
    if os.path.exists(mapping_file):
        print(f"   Size: {os.path.getsize(mapping_file)} bytes")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"🔧 DIAGNOSTIC SUMMARY")
    print(f"{'='*60}")
    
    db = SessionLocal()
    files = db.query(MediaFile).all()
    
    empty_text = [f for f in files if not f.extracted_text or len(f.extracted_text.strip()) == 0]
    missing_embeddings = [f for f in files if f.has_embedding == 0]
    
    print(f"   ❌ Files with EMPTY text: {len(empty_text)}")
    if empty_text:
        for f in empty_text:
            print(f"      - {f.id}: {f.original_filename} (Type: {f.file_type})")
    
    print(f"   ❌ Files missing embeddings: {len(missing_embeddings)}")
    if missing_embeddings:
        for f in missing_embeddings:
            print(f"      - {f.id}: {f.original_filename}")
    
    print(f"   ⚠️  Index size: {vector_service.index.ntotal if vector_service.index else 0}")
    
    if vector_service.index and vector_service.index.ntotal == 0:
        print(f"\n   🚨 CRITICAL: Index is EMPTY - no vectors for search!")
    
    if empty_text:
        print(f"\n   🚨 CRITICAL: Text extraction FAILED for {len(empty_text)} files")
        print(f"      → OCR/PDF extraction is broken")
    
    if missing_embeddings:
        print(f"\n   🚨 CRITICAL: {len(missing_embeddings)} files missing embeddings")
        print(f"      → Embedding generation or indexing is broken")
    
    db.close()
    
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(main())
