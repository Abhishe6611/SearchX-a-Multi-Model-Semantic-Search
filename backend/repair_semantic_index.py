"""
Semantic Index Repair Script

This script repairs the semantic search pipeline by:
1. Finding all media files that need processing
2. Re-extracting text from files with empty text
3. Generating embeddings for files without embeddings
4. Rebuilding the FAISS vector index
5. Marking files with proper status

Run this after installing Tesseract OCR or when the index is corrupted.
"""
import asyncio
import logging
from database import SessionLocal
from models import MediaFile, ProcessingStatus
from services.text_extraction_service import TextExtractionService
from services.embedding_service import EmbeddingService
from services.vector_index_service import VectorIndexService
from utils.path_utils import get_physical_path
import numpy as np
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def repair_semantic_index():
    """Main repair function"""
    print("\n" + "="*70)
    print("SEMANTIC SEARCH INDEX REPAIR")
    print("="*70)
    
    db = SessionLocal()
    text_service = TextExtractionService()
    embedding_service = EmbeddingService()
    vector_service = VectorIndexService()
    
    # Initialize services
    print("\n📦 Initializing services...")
    await embedding_service.initialize()
    await vector_service.initialize()
    print("✅ Services initialized")
    
    # Find files needing repair
    print("\n🔍 Scanning database for files needing repair...")
    all_files = db.query(MediaFile).all()
    
    # Categorize issues
    empty_text_files = []
    missing_embedding_files = []
    
    for f in all_files:
        text_len = len(f.extracted_text) if f.extracted_text else 0
        if text_len == 0:
            empty_text_files.append(f)
        elif f.has_embedding == 0:
            missing_embedding_files.append(f)
    
    print(f"\n📊 REPAIR SUMMARY:")
    print(f"   Total files: {len(all_files)}")
    print(f"   ❌ Empty text (need OCR): {len(empty_text_files)}")
    print(f"   ❌ Missing embeddings: {len(missing_embedding_files)}")
    print(f"   ✅ OK files: {len(all_files) - len(empty_text_files) - len(missing_embedding_files)}")
    
    if len(empty_text_files) == 0 and len(missing_embedding_files) == 0:
        print(f"\n✅ Nothing to repair! All files are properly indexed.")
        db.close()
        return
    
    print(f"\n{'='*70}")
    print("STARTING REPAIR PROCESS")
    print(f"{'='*70}")
    
    # Step 1: Re-extract text from files with empty text
    if empty_text_files:
        print(f"\n\n📝 STEP 1: RE-EXTRACTING TEXT ({len(empty_text_files)} files)")
        print("-" * 70)
        
        for idx, f in enumerate(empty_text_files, 1):
            file_id = f.id
            filename = f.original_filename
            file_type = f.file_type
            
            print(f"\n[{idx}/{len(empty_text_files)}] File {file_id}: {filename}")
            print(f"   Type: {file_type}")
            
            try:
                # Get physical path
                file_path_url = f.file_path
                physical_path = get_physical_path(file_path_url)
                print(f"   Path: {physical_path}")
                
                # Extract text
                print(f"   🔍 Extracting text...")
                extracted_text = await text_service.extract_text(physical_path, file_type)
                
                if len(extracted_text.strip()) > 0:
                    # Update database
                    f.extracted_text = extracted_text
                    db.commit()
                    
                    print(f"   ✅ Extracted {len(extracted_text)} characters")
                    preview = extracted_text[:100].replace('\n', ' ').strip()
                    print(f"   Preview: '{preview}...'")
                    
                    # Add to missing embeddings list
                    if f not in missing_embedding_files:
                        missing_embedding_files.append(f)
                else:
                    print(f"   ⚠️  Text extraction returned EMPTY")
                    f.processing_status = ProcessingStatus.FAILED
                    f.processing_error = "Text extraction returned empty - file may be blank or unsupported"
                    db.commit()
                    
            except Exception as e:
                print(f"   ❌ FAILED: {str(e)}")
                f.processing_status = ProcessingStatus.FAILED
                f.processing_error = str(e)
                db.commit()
    
    # Step 2: Generate embeddings and rebuild index
    if missing_embedding_files:
        print(f"\n\n🧠 STEP 2: GENERATING EMBEDDINGS ({len(missing_embedding_files)} files)")
        print("-" * 70)
        
        # Clear existing index - we'll rebuild from scratch
        print("\n   Clearing existing index...")
        vector_service.index.reset()
        vector_service.id_mapping = {}
        
        # Process files in batches
        batch_size = 16
        successful = 0
        failed = 0
        
        for i in range(0, len(missing_embedding_files), batch_size):
            batch = missing_embedding_files[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(missing_embedding_files) + batch_size - 1) // batch_size
            
            print(f"\n   Batch {batch_num}/{total_batches} ({len(batch)} files)")
            
            # Collect texts for batch
            batch_data = []
            for f in batch:
                text = f.extracted_text
                if text and len(text.strip()) > 0:
                    batch_data.append((f.id, text))
            
            if not batch_data:
                print(f"   ⚠️  Batch has no valid text, skipping...")
                continue
            
            try:
                # Generate embeddings in batch
                texts = [text for _, text in batch_data]
                file_ids = [fid for fid, _ in batch_data]
                
                print(f"   🧠 Generating {len(texts)} embeddings...")
                embeddings = await embedding_service.generate_batch_embeddings(texts)
                print(f"   ✅ Generated embeddings: shape {embeddings.shape}")
                
                # Add to index
                print(f"   📊 Adding to vector index...")
                start_pos = vector_service.index.ntotal
                vector_service.index.add(embeddings.astype(np.float32))
                
                # Update mappings and database
                for j, file_id in enumerate(file_ids):
                    index_pos = start_pos + j
                    vector_service.id_mapping[index_pos] = file_id
                    
                    # Update database
                    file_obj = db.query(MediaFile).filter(MediaFile.id == file_id).first()
                    if file_obj:
                        file_obj.embedding_id = index_pos
                        file_obj.has_embedding = 1
                        file_obj.processing_status = ProcessingStatus.SUCCESS
                        file_obj.processed_date = datetime.now(timezone.utc)
                        successful += 1
                
                db.commit()
                print(f"   ✅ Indexed {len(batch_data)} files (total vectors: {vector_service.index.ntotal})")
                
            except Exception as e:
                print(f"   ❌ Batch failed: {str(e)}")
                failed += len(batch)
                for file_id, _ in batch_data:
                    file_obj = db.query(MediaFile).filter(MediaFile.id == file_id).first()
                    if file_obj:
                        file_obj.processing_status = ProcessingStatus.FAILED
                        file_obj.processing_error = f"Embedding generation failed: {str(e)}"
                db.commit()
        
        print(f"\n   📊 Embedding generation complete:")
        print(f"      ✅ Successful: {successful}")
        print(f"      ❌ Failed: {failed}")
    
    # Step 3: Save index
    print(f"\n\n💾 STEP 3: SAVING INDEX")
    print("-" * 70)
    try:
        await vector_service.save_index()
        print(f"   ✅ Index saved successfully")
        print(f"   📊 Total vectors: {vector_service.index.ntotal}")
        print(f"   📊 ID mappings: {len(vector_service.id_mapping)}")
    except Exception as e:
        print(f"   ❌ Failed to save index: {str(e)}")
    
    # Final summary
    print(f"\n\n{'='*70}")
    print("REPAIR COMPLETE - FINAL STATUS")
    print(f"{'='*70}")
    
    # Re-query database
    all_files = db.query(MediaFile).all()
    success_count = sum(1 for f in all_files if f.processing_status == ProcessingStatus.SUCCESS)
    failed_count = sum(1 for f in all_files if f.processing_status == ProcessingStatus.FAILED)
    with_embeddings = sum(1 for f in all_files if f.has_embedding == 1)
    
    print(f"\n📊 DATABASE STATUS:")
    print(f"   Total files: {len(all_files)}")
    print(f"   ✅ SUCCESS: {success_count}")
    print(f"   ❌ FAILED: {failed_count}")
    print(f"   🧠 With embeddings: {with_embeddings}")
    
    print(f"\n📊 VECTOR INDEX:")
    print(f"   Vectors: {vector_service.index.ntotal}")
    print(f"   Mappings: {len(vector_service.id_mapping)}")
    
    if vector_service.index.ntotal > 0:
        print(f"\n✅ SUCCESS! Semantic search is now operational.")
        print(f"   You can now search for:")
        print(f"   - Exact text matches")
        print(f"   - Semantic queries")
    else:
        print(f"\n⚠️  WARNING: Index is still empty!")
        print(f"   Possible causes:")
        print(f"   - Tesseract OCR not installed")
        print(f"   - All files have no extractable text")
        print(f"   - Embedding generation failed")
    
    db.close()
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("⚙️  SEARCHX SEMANTIC INDEX REPAIR TOOL")
    print("="*70)
    print("\nThis tool will:")
    print("  1. Re-extract text from files with empty text")
    print("  2. Generate embeddings for all files with text")
    print("  3. Rebuild the FAISS vector index")
    print("  4. Update database status for all files")
    print(f"\n{'='*70}")
    
    response = input("\n⚠️  Ready to start repair? (yes/no): ").strip().lower()
    
    if response == 'yes':
        asyncio.run(repair_semantic_index())
    else:
        print("\n❌ Repair cancelled.")
        print(f"{'='*70}\n")
