"""
Experimental: OCR for Scanned PDFs
Tests extracting text from image-based PDFs using OCR
"""
import asyncio
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
from pathlib import Path
from config import settings

# Configure Tesseract
if settings.TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH


async def extract_text_from_pdf_with_ocr(pdf_path: str, use_ocr_fallback: bool = True) -> str:
    """
    Extract text from PDF with OCR fallback for scanned PDFs
    
    Strategy:
    1. Try PyMuPDF text extraction first (fast)
    2. If empty/minimal text and use_ocr_fallback=True, use OCR (slower)
    """
    print(f"\n{'='*70}")
    print(f"Processing: {Path(pdf_path).name}")
    print(f"{'='*70}")
    
    # Step 1: Try normal text extraction
    print(f"\n[Step 1] Attempting PyMuPDF text extraction...")
    doc = fitz.open(pdf_path)
    text_parts = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = page.get_text()
        if isinstance(page_text, str):
            text_parts.append(page_text)
        print(f"   Page {page_num + 1}: {len(page_text)} chars")
    
    # Combine text
    full_text = '\n'.join(text_parts)
    full_text = ' '.join(full_text.split())  # Clean whitespace
    
    print(f"\n   PyMuPDF extracted: {len(full_text)} characters total")
    
    # If we got decent text, return it
    if len(full_text.strip()) > 50:  # Threshold: at least 50 chars
        print(f"   ✅ Sufficient text found via PyMuPDF")
        doc.close()
        return full_text
    
    # Step 2: Text is empty/minimal - try OCR fallback
    if not use_ocr_fallback:
        print(f"   ⚠️  Minimal text, but OCR fallback disabled")
        doc.close()
        return full_text
    
    print(f"\n[Step 2] Text extraction yielded minimal results")
    print(f"   Falling back to OCR (treating as scanned PDF)...")
    
    ocr_text_parts = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        print(f"\n   Processing page {page_num + 1}/{len(doc)} with OCR...")
        
        # Convert PDF page to image
        # Use higher resolution for better OCR accuracy
        zoom = 2.0  # 2x zoom = 144 DPI (default is 72 DPI)
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert pixmap to PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        print(f"      Image size: {img.size[0]}x{img.size[1]} pixels")
        
        # Convert to RGB if needed (better OCR results)
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
            print(f"      Converted to RGB mode")
        
        # Perform OCR
        print(f"      Running Tesseract OCR...")
        try:
            ocr_result = pytesseract.image_to_string(
                img,
                lang=settings.OCR_LANGUAGES,
                config='--psm 1'  # PSM 1: Automatic page segmentation with OSD
            )
            
            ocr_text = str(ocr_result) if ocr_result else ""
            ocr_text = ' '.join(ocr_text.split())  # Clean whitespace
            
            print(f"      ✅ OCR extracted: {len(ocr_text)} characters")
            if len(ocr_text) > 0:
                preview = ocr_text[:80].replace('\n', ' ')
                print(f"      Preview: '{preview}...'")
            
            ocr_text_parts.append(ocr_text)
            
        except Exception as e:
            print(f"      ❌ OCR failed: {str(e)}")
            ocr_text_parts.append("")
    
    doc.close()
    
    # Combine OCR results
    final_text = ' '.join(ocr_text_parts)
    final_text = ' '.join(final_text.split())
    
    print(f"\n{'='*70}")
    print(f"FINAL RESULT:")
    print(f"   Total extracted: {len(final_text)} characters")
    if len(final_text) > 0:
        preview = final_text[:200].replace('\n', ' ')
        print(f"   Preview: '{preview}...'")
    else:
        print(f"   ⚠️  No text extracted (PDF may be blank or unreadable)")
    print(f"{'='*70}")
    
    return final_text


async def test_pdf_ocr():
    """Test OCR extraction on the failed PDF file"""
    print("\n" + "="*70)
    print("TESTING: OCR FOR SCANNED PDFs")
    print("="*70)
    
    # Get the failed PDF from database
    from database import SessionLocal
    from models import MediaFile, ProcessingStatus
    from utils.path_utils import get_physical_path
    
    db = SessionLocal()
    
    # Find failed PDF
    failed_pdf = db.query(MediaFile).filter(
        MediaFile.file_type == "application/pdf",
        MediaFile.processing_status == ProcessingStatus.FAILED
    ).first()
    
    if not failed_pdf:
        print("\n⚠️  No failed PDF found in database")
        print("   All PDFs were successfully processed")
        db.close()
        return
    
    print(f"\nFound failed PDF:")
    print(f"   ID: {failed_pdf.id}")
    print(f"   Name: {failed_pdf.original_filename}")
    print(f"   Error: {failed_pdf.processing_error}")
    
    # Get physical path
    pdf_path = get_physical_path(failed_pdf.file_path)
    print(f"   Path: {pdf_path}")
    
    # Test OCR extraction
    print(f"\n{'='*70}")
    print("STARTING OCR EXTRACTION TEST")
    print(f"{'='*70}")
    
    extracted_text = await extract_text_from_pdf_with_ocr(pdf_path, use_ocr_fallback=True)
    
    # Show results
    print(f"\n{'='*70}")
    print("TEST RESULTS")
    print(f"{'='*70}")
    
    if len(extracted_text.strip()) > 0:
        print(f"\n✅ SUCCESS! OCR extracted text from scanned PDF")
        print(f"   Extracted: {len(extracted_text)} characters")
        print(f"\n   Full text preview:")
        print(f"   {'-'*70}")
        print(f"   {extracted_text[:500]}")
        if len(extracted_text) > 500:
            print(f"   ... ({len(extracted_text) - 500} more characters)")
        print(f"   {'-'*70}")
        
        # Ask if we should update the database
        print(f"\n{'='*70}")
        print("UPDATE DATABASE?")
        print(f"{'='*70}")
        print(f"\nWould you like to update the database with this extracted text?")
        print(f"This will:")
        print(f"  1. Store the extracted text")
        print(f"  2. Generate embedding")
        print(f"  3. Add to search index")
        print(f"  4. Mark file as SUCCESS")
        
        response = input(f"\nUpdate database? (yes/no): ").strip().lower()
        
        if response == 'yes':
            # Import services
            from services.embedding_service import EmbeddingService
            from services.vector_index_service import VectorIndexService
            
            print(f"\nUpdating database...")
            
            # Store text
            failed_pdf.extracted_text = extracted_text
            db.commit()
            print(f"   ✅ Text stored in database")
            
            # Generate embedding
            embedding_service = EmbeddingService()
            await embedding_service.initialize()
            
            print(f"   Generating embedding...")
            embedding = await embedding_service.generate_embedding(extracted_text)
            print(f"   ✅ Embedding generated: shape {embedding.shape}")
            
            # Add to index
            vector_service = VectorIndexService()
            await vector_service.initialize()
            
            print(f"   Adding to vector index...")
            await vector_service.add_vector(failed_pdf.id, embedding)
            print(f"   ✅ Added to index (total vectors: {vector_service.index.ntotal})")
            
            # Update status
            failed_pdf.processing_status = ProcessingStatus.SUCCESS
            failed_pdf.has_embedding = 1
            failed_pdf.embedding_id = vector_service.index.ntotal - 1
            failed_pdf.processing_error = None
            db.commit()
            
            print(f"\n✅ Database updated successfully!")
            print(f"   File is now searchable!")
        else:
            print(f"\n⚠️  Database not updated (test only)")
    else:
        print(f"\n❌ FAILED: OCR could not extract text")
        print(f"   PDF may be:")
        print(f"   - Completely blank")
        print(f"   - Encrypted/protected")
        print(f"   - Very low quality scan")
        print(f"   - Non-text content only")
    
    db.close()
    
    print(f"\n{'='*70}")
    print("TEST COMPLETE")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PDF OCR EXTRACTION EXPERIMENT")
    print("="*70)
    print("\nThis script tests OCR extraction on scanned PDFs")
    print("Strategy:")
    print("  1. Try normal PyMuPDF extraction (fast)")
    print("  2. If empty, convert pages to images")
    print("  3. Run Tesseract OCR on images (slower but works on scans)")
    print(f"\n{'='*70}\n")
    
    asyncio.run(test_pdf_ocr())
