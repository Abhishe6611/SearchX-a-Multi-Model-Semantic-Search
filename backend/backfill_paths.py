"""
Backfill script to fix existing file paths in database
Converts Windows backslash paths to URL-friendly forward slash paths
"""
import asyncio
import logging
from database import SessionLocal
from models import MediaFile
from utils.path_utils import normalize_path_for_url

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def backfill_paths():
    """Fix all file and thumbnail paths in database"""
    logger.info("="*70)
    logger.info("STARTING PATH BACKFILL - Converting to URL-friendly format")
    logger.info("="*70)
    
    db = SessionLocal()
    try:
        # Get all files
        all_files = db.query(MediaFile).all()
        logger.info(f"Found {len(all_files)} files to process")
        
        fixed_count = 0
        error_count = 0
        
        for file in all_files:
            try:
                file_id = file.id
                original_file_path = str(file.file_path)
                # Use getattr to avoid SQLAlchemy Column type issues
                thumb_path_value = getattr(file, 'thumbnail_path', None)
                original_thumb_path = str(thumb_path_value) if thumb_path_value is not None else None
                
                # Check if paths need fixing (contain backslashes or don't start with /)
                needs_fix = '\\' in original_file_path or not original_file_path.startswith('/')
                
                if needs_fix:
                    # Normalize file path
                    new_file_path = normalize_path_for_url(original_file_path)
                    file.file_path = new_file_path  # type: ignore
                    
                    # Normalize thumbnail path if exists
                    if original_thumb_path:
                        needs_thumb_fix = '\\' in original_thumb_path or not original_thumb_path.startswith('/')
                        if needs_thumb_fix:
                            new_thumb_path = normalize_path_for_url(original_thumb_path)
                            file.thumbnail_path = new_thumb_path  # type: ignore
                            logger.info(f"  ✓ Fixed thumbnail: {original_thumb_path} -> {new_thumb_path}")
                    
                    db.commit()
                    fixed_count += 1
                    logger.info(f"✅ File {file_id}: {original_file_path} -> {new_file_path}")
                else:
                    logger.info(f"⏭️  File {file_id}: Already in correct format")
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error fixing file {file.id}: {str(e)}")
                db.rollback()
        
        logger.info("="*70)
        logger.info(f"BACKFILL COMPLETE:")
        logger.info(f"  Total Files: {len(all_files)}")
        logger.info(f"  Fixed: {fixed_count}")
        logger.info(f"  Errors: {error_count}")
        logger.info(f"  Already Correct: {len(all_files) - fixed_count - error_count}")
        logger.info("="*70)
        
    except Exception as e:
        logger.error(f"Backfill failed: {str(e)}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(backfill_paths())
