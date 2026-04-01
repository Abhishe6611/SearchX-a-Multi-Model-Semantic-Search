"""
Test the integrated PDF OCR fallback in text_extraction_service.py
Verifies scanned PDFs are automatically handled with OCR
"""
import asyncio
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from database import get_db
from models import MediaFile
from services.text_extraction_service import TextExtractionService
from config import settings

async def test_integrated_ocr():
    """Test the integrated OCR on the scanned PDF"""
    print("\n" + "="*70)
    print("TESTING INTEGRATED PDF OCR FALLBACK")
    print("="*70)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Find the scanned PDF (10.pdf)
        pdf_file = db.query(MediaFile).filter(
            MediaFile.original_filename == "10.pdf"
        ).first()
        
        if not pdf_file:
            print("❌ Error: 10.pdf not found in database")
            return
        
        print(f"\n📄 Found file: {pdf_file.original_filename}")
        print(f"   Stored path (relative): {pdf_file.file_path}")
        
        # Build absolute path
        absolute_path = Path(settings.BASE_DIR) / pdf_file.file_path.lstrip('/')
        print(f"   Absolute path: {absolute_path}")
        print(f"   File exists: {absolute_path.exists()}")
        print(f"   Current status: {pdf_file.processing_status}")
        print(f"   Current text length: {len(pdf_file.extracted_text or '')}")
        
        if not absolute_path.exists():
            print(f"❌ Error: File not found at {absolute_path}")
            return
        
        # Initialize text extraction service
        extractor = TextExtractionService()
        
        # Test extraction with integrated OCR fallback
        print("\n" + "="*70)
        print("RUNNING TEXT EXTRACTION WITH INTEGRATED OCR FALLBACK")
        print("="*70)
        
        extracted_text = await extractor.extract_text(
            str(absolute_path),
            pdf_file.file_type
        )
        
        print("\n" + "="*70)
        print("EXTRACTION RESULTS")
        print("="*70)
        print(f"✅ Extracted {len(extracted_text)} characters")
        
        if len(extracted_text) > 0:
            preview = extracted_text[:300].replace('\n', ' ')
            print(f"\n📝 Preview (first 300 chars):")
            print(f"   {preview}...")
            
            # Check for expected content
            expected_keywords = ["CBSE", "ABHISHEK", "SECONDARY", "EXAMINATION", "2021"]
            found_keywords = [kw for kw in expected_keywords if kw.upper() in extracted_text.upper()]
            
            print(f"\n🔍 Expected keywords found: {len(found_keywords)}/{len(expected_keywords)}")
            for kw in expected_keywords:
                status = "✅" if kw in found_keywords else "❌"
                print(f"   {status} {kw}")
            
            if len(found_keywords) >= 3:
                print(f"\n✅ SUCCESS: OCR fallback is working correctly!")
                print(f"   The scanned PDF is now extractable via the main service.")
            else:
                print(f"\n⚠️  WARNING: OCR worked but expected content not found")
        else:
            print(f"\n❌ FAILED: No text extracted")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_integrated_ocr())
