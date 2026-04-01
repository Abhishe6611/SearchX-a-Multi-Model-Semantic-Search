import asyncio
import os
import sys

# Ensure backend modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import MediaFile
from services.text_extraction_service import TextExtractionService

async def main():
    db = SessionLocal()
    file_record = db.query(MediaFile).filter_by(id=3).first()
    
    if not file_record:
        print("File not found")
        return
        
    print(f"Testing OCR on: {file_record.original_filename}")
    physical_path = os.path.join("storage", "files", os.path.basename(file_record.file_path))
    print(f"Path: {physical_path}")
    
    service = TextExtractionService()
    try:
        text, keywords = await service.extract_text(physical_path, file_record.file_type)
        print(f"Success! Extracted {len(text)} chars and keywords: {keywords}")
    except Exception as e:
        print(f"Extraction failed: {str(e)}")
        
if __name__ == "__main__":
    asyncio.run(main())
