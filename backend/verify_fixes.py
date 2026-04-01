"""
Quick verification script to test all fixed endpoints
Run after starting the backend server
"""
import asyncio
import sys
from database import SessionLocal
from models import MediaFile

async def verify_system():
    """Verify all critical fixes are working"""
    print("\n" + "="*70)
    print("SEARCHX SYSTEM VERIFICATION")
    print("="*70)
    
    db = SessionLocal()
    try:
        # Test 1: Database Path Format
        print("\n[TEST 1] Database Path Format")
        files = db.query(MediaFile).all()
        
        all_correct = True
        for file in files:
            file_path = str(file.file_path)
            # Use getattr to avoid SQLAlchemy Column type issues
            thumb_path_value = getattr(file, 'thumbnail_path', None)
            thumb_path = str(thumb_path_value) if thumb_path_value is not None else None
            
            # Check file path format
            if not file_path.startswith('/storage/'):
                print(f"  ❌ File {file.id}: Bad path format: {file_path}")
                all_correct = False
            elif '\\' in file_path:
                print(f"  ❌ File {file.id}: Contains backslash: {file_path}")
                all_correct = False
            else:
                print(f"  ✅ File {file.id}: {file.original_filename}")
                print(f"     Path: {file_path}")
                
            # Check thumbnail path format
            if thumb_path:
                if not thumb_path.startswith('/storage/'):
                    print(f"  ❌ Thumbnail: Bad format: {thumb_path}")
                    all_correct = False
                elif '\\' in thumb_path:
                    print(f"  ❌ Thumbnail: Contains backslash: {thumb_path}")
                    all_correct = False
                else:
                    print(f"     Thumbnail: {thumb_path}")
        
        if all_correct:
            print(f"\n  ✅ All {len(files)} files have correct path format")
        else:
            print(f"\n  ❌ Some files have incorrect paths - run backfill_paths.py")
            
        # Test 2: Physical Files Exist
        print("\n[TEST 2] Physical File Existence")
        import os
        from utils.path_utils import get_physical_path
        
        for file in files:
            file_path_url = str(file.file_path)
            # Use getattr to avoid SQLAlchemy Column type issues
            thumb_path_value = getattr(file, 'thumbnail_path', None)
            thumb_path_url = str(thumb_path_value) if thumb_path_value is not None else None
            
            # Check file
            physical_path = get_physical_path(file_path_url)
            if os.path.exists(physical_path):
                size_kb = os.path.getsize(physical_path) // 1024
                print(f"  ✅ File {file.id}: {size_kb} KB")
            else:
                print(f"  ❌ File {file.id}: NOT FOUND at {physical_path}")
            
            # Check thumbnail
            if thumb_path_url:
                thumb_physical = get_physical_path(thumb_path_url)
                if os.path.exists(thumb_physical):
                    thumb_size = os.path.getsize(thumb_physical) // 1024
                    print(f"     Thumbnail: {thumb_size} KB")
                else:
                    print(f"     ❌ Thumbnail NOT FOUND")
        
        # Test 3: Import Check
        print("\n[TEST 3] Module Imports")
        try:
            from utils.path_utils import get_physical_path
            print("  ✅ path_utils imported successfully")
        except ImportError as e:
            print(f"  ❌ Failed to import path_utils: {e}")
        
        # Test 4: Configuration
        print("\n[TEST 4] Configuration Check")
        from config import settings
        print(f"  Storage Dir: {settings.STORAGE_DIR}")
        print(f"  Thumbnail Dir: {settings.THUMBNAILS_DIR}")
        print(f"  Base Dir: {settings.BASE_DIR}")
        
        if os.path.exists(settings.STORAGE_DIR):
            print(f"  ✅ Storage directory exists")
        else:
            print(f"  ❌ Storage directory not found")
        
        if os.path.exists(settings.THUMBNAILS_DIR):
            print(f"  ✅ Thumbnails directory exists")
        else:
            print(f"  ❌ Thumbnails directory not found")
        
        print("\n" + "="*70)
        print("VERIFICATION COMPLETE")
        print("="*70)
        print("\nNext Steps:")
        print("1. Start backend:  cd backend && uvicorn main:app --reload")
        print("2. Start frontend: cd frontend && npm run dev")
        print("3. Open browser:   http://localhost:3000")
        print("4. Test:")
        print("   - View grid shows thumbnails")
        print("   - Click image opens viewer")
        print("   - Click PDF opens in iframe")
        print("   - Search doesn't crash (even with 0 results)")
        print("   - Upload new file works")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    return all_correct


if __name__ == "__main__":
    result = asyncio.run(verify_system())
    sys.exit(0 if result else 1)
