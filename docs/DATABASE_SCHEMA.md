# SearchX Database Schema

## Overview

SearchX uses SQLite with SQLAlchemy ORM for data persistence. The schema is designed to track media files, their processing status, and vector embedding relationships.

## Tables

### media_files

Primary table storing all uploaded media information.

```sql
CREATE TABLE media_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL UNIQUE,
    file_path VARCHAR(512) NOT NULL,
    thumbnail_path VARCHAR(512),
    
    file_type VARCHAR(100) NOT NULL,
    file_size INTEGER NOT NULL,
    file_hash VARCHAR(64) NOT NULL UNIQUE,
    
    extracted_text TEXT,
    processing_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    processing_error TEXT,
    
    upload_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_date DATETIME,
    
    embedding_id INTEGER,
    has_embedding INTEGER DEFAULT 0,
    
    INDEX idx_file_hash (file_hash),
    INDEX idx_processing_status (processing_status),
    INDEX idx_upload_date (upload_date),
    INDEX idx_embedding_id (embedding_id)
);
```

## Field Descriptions

### Identity Fields

- **id**: Auto-incrementing primary key
- **original_filename**: Original name of uploaded file
- **stored_filename**: Unique filename in storage system

### File Metadata

- **file_path**: Absolute path to stored file
- **thumbnail_path**: Path to generated thumbnail
- **file_type**: MIME type (e.g., 'image/jpeg', 'application/pdf')
- **file_size**: Size in bytes
- **file_hash**: SHA256 hash for duplicate detection

### Processing Fields

- **extracted_text**: Text content from OCR or document parsing
- **processing_status**: Enum value - 'pending', 'success', or 'failed'
- **processing_error**: Error message if processing failed

### Timestamps

- **upload_date**: When file was uploaded (UTC)
- **processed_date**: When processing completed (UTC)

### Vector Search Fields

- **embedding_id**: Position/ID in FAISS vector index
- **has_embedding**: Boolean flag (0 or 1) indicating if embedded

## Processing Status Enum

```python
class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"    # Orange - in queue
    SUCCESS = "success"    # Green - processed successfully
    FAILED = "failed"      # Red - processing failed
```

## Indexes

Performance optimization indexes:

1. **idx_file_hash**: Fast duplicate detection
2. **idx_processing_status**: Filter by status
3. **idx_upload_date**: Chronological sorting
4. **idx_embedding_id**: Vector index lookups

## Relationships

### FAISS Vector Index

The `embedding_id` field creates an implicit relationship with the FAISS vector index:

- Each successfully processed file with text gets an embedding
- `embedding_id` maps to position in FAISS index
- Separate pickle file stores bidirectional mapping

**Mapping File Structure:**
```python
{
    0: 1,    # FAISS index position 0 → media_files.id 1
    1: 3,    # FAISS index position 1 → media_files.id 3
    2: 5,    # etc...
}
```

## Constraints

1. **Unique Constraints:**
   - `stored_filename`: Prevents filename collisions
   - `file_hash`: Prevents duplicate uploads

2. **Not Null Constraints:**
   - All core metadata fields must be populated
   - Processing can proceed without extracted_text

3. **Foreign Keys:**
   - None (intentionally denormalized for simplicity)

## Queries

### Common Queries

**Get all processed files:**
```sql
SELECT * FROM media_files 
WHERE processing_status = 'success' 
ORDER BY upload_date DESC;
```

**Check for duplicate:**
```sql
SELECT id FROM media_files 
WHERE file_hash = ?;
```

**Get files pending processing:**
```sql
SELECT * FROM media_files 
WHERE processing_status = 'pending';
```

**Get files with embeddings:**
```sql
SELECT * FROM media_files 
WHERE has_embedding = 1;
```

**Statistics:**
```sql
SELECT 
    processing_status, 
    COUNT(*) as count 
FROM media_files 
GROUP BY processing_status;
```

## Migration Strategy

### Initial Creation

Database and tables are created automatically on first run via SQLAlchemy:

```python
from database import init_db
init_db()  # Creates all tables
```

### Future Migrations

For schema changes, recommended approach:

1. Use Alembic for migrations
2. Create migration scripts
3. Version control schema changes

Example Alembic setup:
```bash
pip install alembic
alembic init migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Backup Strategy

### SQLite Backup

```bash
# Full backup
sqlite3 searchx.db ".backup searchx_backup.db"

# Export to SQL
sqlite3 searchx.db ".dump" > searchx_backup.sql
```

### Automated Backups

Recommended schedule:
- Daily: Full database backup
- Before schema changes: Manual backup
- Keep 7 daily, 4 weekly, 12 monthly

## Data Retention

### Cleanup Policies

**Failed uploads (optional):**
```sql
-- Delete failed uploads older than 30 days
DELETE FROM media_files 
WHERE processing_status = 'failed' 
AND upload_date < datetime('now', '-30 days');
```

**Orphaned records:**
```sql
-- Find records missing physical files
SELECT * FROM media_files 
WHERE file_path NOT IN (
    -- List of actual files in storage
);
```

## Performance Tuning

### Statistics

```sql
ANALYZE media_files;
```

### Vacuum

```sql
VACUUM;
```

### Index Usage Analysis

```sql
EXPLAIN QUERY PLAN
SELECT * FROM media_files 
WHERE processing_status = 'success';
```

## Testing Data

### Sample Data Insert

```sql
INSERT INTO media_files (
    original_filename, stored_filename, file_path,
    file_type, file_size, file_hash,
    processing_status, upload_date
) VALUES (
    'test.jpg', 'uuid-test.jpg', '/storage/files/uuid-test.jpg',
    'image/jpeg', 1024000, 'hash123...',
    'pending', datetime('now')
);
```

## Schema Version

**Current Version:** 1.0.0
**Last Updated:** 2026-02-14
**Compatible With:** SearchX 1.0.0

---

## Notes

- All timestamps are stored in UTC
- File paths are absolute paths on server
- Thumbnail paths can be NULL if generation fails
- Vector index is stored separately from database
- Schema is optimized for read-heavy workloads
