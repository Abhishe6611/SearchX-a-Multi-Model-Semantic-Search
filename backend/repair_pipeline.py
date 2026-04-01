"""
SearchX Media Pipeline Repair CLI
Run this to repair stuck files and regenerate missing thumbnails
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.upload_service import UploadService
from database import init_db
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Run media pipeline repair"""
    print("\n" + "="*60)
    print("SearchX Media Pipeline Repair Utility")
    print("="*60 + "\n")
    
    # Initialize database
    init_db()
    
    # Create upload service and run repair
    upload_service = UploadService()
    await upload_service.repair_pipeline()
    
    print("\n✓ Repair process completed!\n")


if __name__ == "__main__":
    asyncio.run(main())
