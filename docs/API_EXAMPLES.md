# SearchX - API Testing Examples

This document provides example API calls for testing SearchX functionality.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently no authentication required (add for production).

---

## 1. Health Check

### Request
```http
GET http://localhost:8000/
```

### Response
```json
{
  "status": "online",
  "service": "SearchX API",
  "version": "1.0.0",
  "timestamp": "2026-02-14T12:00:00.000Z"
}
```

---

## 2. Upload Files

### Request
```http
POST http://localhost:8000/api/upload
Content-Type: multipart/form-data

files: [file1.jpg, file2.pdf, file3.txt]
```

### cURL Example
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "files=@image1.jpg" \
  -F "files=@document.pdf" \
  -F "files=@notes.txt"
```

### PowerShell Example
```powershell
$files = @(
    @{name='files'; filename='image1.jpg'; value=Get-Content -Path 'image1.jpg' -Raw -AsByteStream}
    @{name='files'; filename='document.pdf'; value=Get-Content -Path 'document.pdf' -Raw -AsByteStream}
)

Invoke-RestMethod -Uri "http://localhost:8000/api/upload" -Method Post -Form $files
```

### Response
```json
{
  "success": true,
  "message": "Successfully processed 3 files",
  "files": [
    {
      "filename": "image1.jpg",
      "success": true,
      "file_id": 1,
      "status": "pending"
    },
    {
      "filename": "document.pdf",
      "success": true,
      "file_id": 2,
      "status": "pending"
    },
    {
      "filename": "notes.txt",
      "success": true,
      "file_id": 3,
      "status": "pending"
    }
  ]
}
```

---

## 3. Get All Files

### Request
```http
GET http://localhost:8000/api/files?skip=0&limit=100
```

### Query Parameters
- `skip` (optional): Pagination offset (default: 0)
- `limit` (optional): Max results (default: 100, max: 500)
- `status` (optional): Filter by status (success/pending/failed)

### cURL Example
```bash
# Get all files
curl http://localhost:8000/api/files

# Get only successful files
curl "http://localhost:8000/api/files?status=success"

# Pagination
curl "http://localhost:8000/api/files?skip=10&limit=20"
```

### Response
```json
{
  "success": true,
  "total": 15,
  "skip": 0,
  "limit": 100,
  "files": [
    {
      "id": 1,
      "original_filename": "sunset.jpg",
      "stored_filename": "uuid-123.jpg",
      "file_path": "/storage/files/uuid-123.jpg",
      "thumbnail_path": "/storage/thumbnails/thumb_uuid-123.jpg",
      "file_type": "image/jpeg",
      "file_size": 2048576,
      "file_hash": "abc123...",
      "extracted_text": "Beautiful sunset over mountains...",
      "processing_status": "success",
      "processing_error": null,
      "upload_date": "2026-02-14T10:30:00.000Z",
      "processed_date": "2026-02-14T10:30:05.000Z",
      "has_embedding": true
    }
  ]
}
```

---

## 4. Get Single File

### Request
```http
GET http://localhost:8000/api/files/{file_id}
```

### cURL Example
```bash
curl http://localhost:8000/api/files/1
```

### Response
```json
{
  "success": true,
  "file": {
    "id": 1,
    "original_filename": "sunset.jpg",
    "file_type": "image/jpeg",
    "file_size": 2048576,
    "extracted_text": "...",
    "processing_status": "success",
    "upload_date": "2026-02-14T10:30:00.000Z"
  }
}
```

---

## 5. Semantic Search

### Request
```http
POST http://localhost:8000/api/search?query=sunset&limit=20
```

### Query Parameters
- `query` (required): Search query text
- `limit` (optional): Max results (default: 20, max: 100)

### cURL Examples
```bash
# Simple search
curl -X POST "http://localhost:8000/api/search?query=sunset+landscape"

# With limit
curl -X POST "http://localhost:8000/api/search?query=financial+report&limit=10"

# Complex query
curl -X POST "http://localhost:8000/api/search?query=person+wearing+glasses"
```

### PowerShell Example
```powershell
$uri = "http://localhost:8000/api/search?query=sunset&limit=20"
Invoke-RestMethod -Uri $uri -Method Post
```

### Response
```json
{
  "success": true,
  "query": "sunset landscape",
  "count": 5,
  "results": [
    {
      "id": 1,
      "original_filename": "sunset.jpg",
      "file_type": "image/jpeg",
      "file_size": 2048576,
      "upload_date": "2026-02-14T10:30:00.000Z",
      "relevance_score": 0.8542,
      "thumbnail_path": "/storage/thumbnails/thumb_uuid-123.jpg"
    },
    {
      "id": 5,
      "original_filename": "mountain_view.jpg",
      "relevance_score": 0.7234
    }
  ]
}
```

**Note:** Results are sorted by relevance_score (highest first).

---

## 6. Delete File

### Request
```http
DELETE http://localhost:8000/api/files/{file_id}
```

### cURL Example
```bash
curl -X DELETE http://localhost:8000/api/files/1
```

### PowerShell Example
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/files/1" -Method Delete
```

### Response
```json
{
  "success": true,
  "message": "File deleted successfully"
}
```

**Note:** This deletes:
- Database record
- Physical file
- Thumbnail
- Vector embedding

---

## 7. Download File

### Request
```http
GET http://localhost:8000/api/download/{file_id}
```

### Browser
```
http://localhost:8000/api/download/1
```

### cURL Example
```bash
# Download and save
curl -o downloaded_file.jpg http://localhost:8000/api/download/1
```

### PowerShell Example
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/download/1" -OutFile "downloaded.jpg"
```

### Response
Binary file content with appropriate headers:
```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="original_filename.jpg"
```

---

## 8. Get Statistics

### Request
```http
GET http://localhost:8000/api/stats
```

### cURL Example
```bash
curl http://localhost:8000/api/stats
```

### Response
```json
{
  "success": true,
  "stats": {
    "total_files": 150,
    "processed": 145,
    "failed": 2,
    "pending": 3,
    "images": 90,
    "documents": 60
  }
}
```

---

## Error Responses

### 404 Not Found
```json
{
  "detail": "File not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Upload failed: Invalid file type"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["query", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Testing Tips

### 1. Test Upload with Various File Types

```bash
# Image
curl -X POST http://localhost:8000/api/upload -F "files=@test.jpg"

# PDF
curl -X POST http://localhost:8000/api/upload -F "files=@document.pdf"

# Text
curl -X POST http://localhost:8000/api/upload -F "files=@notes.txt"

# Multiple files
curl -X POST http://localhost:8000/api/upload \
  -F "files=@image1.jpg" \
  -F "files=@image2.png" \
  -F "files=@doc.pdf"
```

### 2. Test Semantic Search

Try various query types:

```bash
# Object recognition
curl -X POST "http://localhost:8000/api/search?query=dog"

# Scene description
curl -X POST "http://localhost:8000/api/search?query=beach+sunset"

# Document content
curl -X POST "http://localhost:8000/api/search?query=invoice"

# Abstract concepts
curl -X POST "http://localhost:8000/api/search?query=happy+celebration"
```

### 3. Test Processing Pipeline

1. Upload file
2. Check status (should be "pending")
3. Wait 5-10 seconds
4. Check status again (should be "success")
5. Perform search to verify embedding

```bash
# Upload
RESPONSE=$(curl -X POST http://localhost:8000/api/upload -F "files=@test.jpg")
FILE_ID=$(echo $RESPONSE | jq -r '.files[0].file_id')

# Check status
curl "http://localhost:8000/api/files/$FILE_ID"

# Wait
sleep 10

# Check again
curl "http://localhost:8000/api/files/$FILE_ID"
```

### 4. Test Error Handling

```bash
# Invalid file type
curl -X POST http://localhost:8000/api/upload -F "files=@test.exe"

# Non-existent file
curl http://localhost:8000/api/files/99999

# Empty search query
curl -X POST "http://localhost:8000/api/search?query="
```

---

## Interactive API Documentation

Visit: **http://localhost:8000/docs**

FastAPI provides interactive Swagger UI where you can:
- View all endpoints
- See request/response schemas
- Test APIs directly in browser
- Download OpenAPI specification

---

## Postman Collection

Coming soon: Import ready-to-use Postman collection for all endpoints.

---

## Rate Limiting

Currently no rate limiting (add for production).

Recommended limits:
- Upload: 10 requests/minute
- Search: 60 requests/minute
- Downloads: 30 requests/minute

---

## Best Practices

1. **Always check processing_status** before searching uploaded files
2. **Use pagination** for large result sets
3. **Keep queries specific** for better relevance
4. **Handle errors gracefully** in your client
5. **Implement retries** for failed uploads

---

**Happy Testing! 🧪**
