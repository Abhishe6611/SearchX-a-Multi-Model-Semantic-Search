"""
Test text extraction directly on uploaded files
"""
import asyncio
from services.text_extraction_service import TextExtractionService
from database import SessionLocal
from models import MediaFile
from utils.path_utils import get_physical_path

async def test_extraction():
    print("\n" + "="*60)
    print("TESTING TEXT EXTRACTION DIRECTLY")
    print("="*60)
    
    text_service = TextExtractionService()
    db = SessionLocal()
    files = db.query(MediaFile).all()
    
    for f in files:
        print(f"\n{'='*50}")
        print(f"Testing file: {f.original_filename}")
        print(f"File ID: {f.id}")
        print(f"Type: {f.file_type}")
        print(f"DB path: {f.file_path}")
        
        # Get physical path
        physical_path = get_physical_path(f.file_path)
        print(f"Physical path: {physical_path}")
        
        try:
            # Attempt extraction
            print(f"\n🔍 Attempting text extraction...")
            text = await text_service.extract_text(physical_path, f.file_type)
            
            print(f"✅ SUCCESS!")
            print(f"   Extracted: {len(text)} chars")
            if len(text) > 0:
                preview = text[:200].replace('\n', ' ').strip()
                print(f"   Preview: '{preview}...'")
            else:
                print(f"   ⚠️  Text is EMPTY")
                
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
    
    db.close()
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(test_extraction())
