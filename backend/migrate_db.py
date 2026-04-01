import sqlite3
import os
from pathlib import Path

# Connect to database directly to perform ALTER TABLE
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "searchx.db"

def migrate():
    print(f"Connecting to database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(media_files)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "keywords" not in columns:
            print("Adding keywords column...")
            cursor.execute("ALTER TABLE media_files ADD COLUMN keywords TEXT NULL;")
            conn.commit()
            print("Successfully added keywords column.")
        else:
            print("keywords column already exists.")
            
    except Exception as e:
        print(f"Error migrating database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
