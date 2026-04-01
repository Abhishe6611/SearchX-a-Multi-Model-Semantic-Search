"""
Simple diagnostic without Unicode emojis for Windows
"""
import asyncio
from database import SessionLocal
from models import MediaFile
from services.vector_index_service import VectorIndexService

async def main():
    print("\n" + "="*60)
    print("SEMANTIC PIPELINE DIAGNOSTIC")
    print("="*60)
    
    db = SessionLocal()
    files = db.query(MediaFile).all()
    
    print(f"\nDATABASE STATUS")
    print(f"   Total files: {len(files)}")
    
    for f in files:
        print(f"\n{'-'*50}")
        print(f"File ID: {f.id}")
        print(f"   Name: {f.original_filename}")
        print(f"   Type: {f.file_type}")
        print(f"   Status: {f.processing_status.name}")
        
        text_len = len(f.extracted_text) if f.extracted_text else 0
        print(f"   Extracted text: {text_len} chars")
        if text_len > 0:
            preview = f.extracted_text[:150].replace('\n', ' ').strip()
            print(f"   Preview: '{preview}...'")
        else:
            print(f"   Preview: (EMPTY)")
        
        print(f"   Has embedding: {f.has_embedding}")
        print(f"   Embedding ID: {f.embedding_id}")
    
    db.close()
    
    # Check FAISS index
    print(f"\n{'='*60}")
    print(f"VECTOR INDEX STATUS")
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
    
    # Summary
    print(f"\n{'='*60}")
    print(f"DIAGNOSTIC SUMMARY")
    print(f"{'='*60}")
    
    db = SessionLocal()
    files = db.query(MediaFile).all()
    
    successful = [f for f in files if f.processing_status.name == 'SUCCESS']
    failed = [f for f in files if f.processing_status.name == 'FAILED']
    empty_text = [f for f in files if not f.extracted_text or len(f.extracted_text.strip()) == 0]
    with_embeddings = [f for f in files if f.has_embedding == 1]
    
    print(f"   Total files: {len(files)}")
    print(f"   SUCCESS: {len(successful)}")
    print(f"   FAILED: {len(failed)}")
    print(f"   With text: {len(files) - len(empty_text)}")
    print(f"   With embeddings: {len(with_embeddings)}")
    print(f"   Index vectors: {vector_service.index.ntotal if vector_service.index else 0}")
    
    if vector_service.index and vector_service.index.ntotal > 0:
        print(f"\nSUCCESS! Semantic search is operational.")
        print(f"   You can now search for:")
        print(f"   - Text from your images")
        print(f"   - Semantic queries")
    else:
        print(f"\nWARNING: Index is empty - search won't work!")
    
    if failed:
        print(f"\nFailed files:")
        for f in failed:
            print(f"   - {f.id}: {f.original_filename}")
            if f.processing_error:
                print(f"     Error: {f.processing_error}")
    
    db.close()
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(main())
