# SearchX Setup Guide

Complete step-by-step setup instructions for SearchX Semantic Media Search System.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Prerequisites Installation](#prerequisites-installation)
3. [Backend Setup](#backend-setup)
4. [Frontend Setup](#frontend-setup)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM**: 4GB (8GB recommended)
- **Disk**: 2GB free space (more for media storage)
- **CPU**: Dual-core processor (quad-core recommended)

### Software Requirements
- **Python**: 3.9, 3.10, or 3.11
- **Node.js**: 16.x or higher
- **npm**: 8.x or higher
- **Tesseract OCR**: 5.x

---

## Prerequisites Installation

### 1. Install Python

**Windows:**
1. Download from https://www.python.org/downloads/
2. Run installer
3. ✅ Check "Add Python to PATH"
4. Click "Install Now"
5. Verify:
   ```powershell
   python --version
   ```

**macOS:**
```bash
brew install python@3.11
```

**Linux:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

### 2. Install Node.js

**Windows:**
1. Download from https://nodejs.org/
2. Run installer (choose LTS version)
3. Verify:
   ```powershell
   node --version
   npm --version
   ```

**macOS:**
```bash
brew install node
```

**Linux:**
```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 3. Install Tesseract OCR

**Windows (Chocolatey):**
```powershell
choco install tesseract
```

**Windows (Manual):**
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run installer
3. Note installation path (e.g., `C:\Program Files\Tesseract-OCR`)
4. Add to PATH or configure in `.env`

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-eng
```

**Verify Installation:**
```powershell
tesseract --version
```

Should output: `tesseract 5.x.x`

---

## Backend Setup

### Step 1: Navigate to Backend Directory

```powershell
cd "c:\Users\Avvi\D drive\New- SX\backend"
```

### Step 2: Create Virtual Environment

```powershell
python -m venv venv
```

### Step 3: Activate Virtual Environment

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows CMD:**
```cmd
.\venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` in your prompt.

### Step 4: Upgrade pip

```powershell
python -m pip install --upgrade pip
```

### Step 5: Install Dependencies

```powershell
pip install -r requirements.txt
```

This will install:
- FastAPI & Uvicorn (API server)
- SQLAlchemy (Database ORM)
- Pillow & PyMuPDF (Image/PDF processing)
- pytesseract (OCR)
- python-docx (Document parsing)
- sentence-transformers & torch (AI embeddings)
- faiss-cpu (Vector search)

**Note:** First installation may take 5-10 minutes (downloading models).

### Step 6: Configure Environment

```powershell
Copy-Item .env.example .env
```

**Edit `.env` if needed:**
```env
# If Tesseract not in PATH:
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe

# For GPU support (requires CUDA):
USE_GPU=True

# Adjust language support:
OCR_LANGUAGES=eng+fra+deu
```

### Step 7: Initialize Database

The database will be created automatically on first run.

### Step 8: Start Backend Server

```powershell
python main.py
```

**Expected Output:**
```
INFO: Starting SearchX API...
INFO: Loading embedding model: sentence-transformers/all-MiniLM-L6-v2
INFO: Using device: cpu
INFO: Model loaded successfully. Embedding dimension: 384
INFO: Database initialized successfully
INFO: SearchX API started successfully
INFO: Uvicorn running on http://0.0.0.0:8000
```

✅ Backend is running at: **http://localhost:8000**

Keep this terminal open!

---

## Frontend Setup

### Step 1: Open New Terminal

Open a **new** terminal window (keep backend running).

### Step 2: Navigate to Frontend Directory

```powershell
cd "c:\Users\Avvi\D drive\New- SX\frontend"
```

### Step 3: Install Dependencies

```powershell
npm install
```

This will install:
- React & React DOM
- Vite (dev server & build tool)
- Tailwind CSS (styling)
- Axios (API client)
- React Dropzone (file upload)
- Lucide React (icons)

**Note:** Installation takes 2-5 minutes.

### Step 4: Configure Environment

```powershell
Copy-Item .env.example .env
```

**Edit `.env` if backend is on different port:**
```env
VITE_API_URL=http://localhost:8000
```

### Step 5: Start Frontend Server

```powershell
npm run dev
```

**Expected Output:**
```
VITE v5.0.11  ready in XXX ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
```

✅ Frontend is running at: **http://localhost:3000**

---

## Verification

### 1. Check Backend API

Open browser: http://localhost:8000

Should see:
```json
{
  "status": "online",
  "service": "SearchX API",
  "version": "1.0.0",
  "timestamp": "2026-02-14T..."
}
```

**API Documentation:**
http://localhost:8000/docs

### 2. Check Frontend

Open browser: http://localhost:3000

You should see:
- ✅ SearchX header with logo
- ✅ Statistics bar (all zeros initially)
- ✅ Upload zone
- ✅ Search bar

### 3. Test Upload

1. Drag & drop an image or document into upload zone
2. Wait for upload to complete
3. Check status indicator:
   - 🟠 Orange = Processing
   - 🟢 Green = Success (after a few seconds)
   - 🔴 Red = Failed

### 4. Test Search

1. Wait for file status to turn green
2. Enter search query related to file content
3. Results should appear with relevance scores

### 5. Test Media Viewer

1. Click on any file card
2. Verify viewer opens with:
   - ✅ Image zoom & pan (for images)
   - ✅ PDF viewer (for PDFs)
   - ✅ Delete button
   - ✅ Download button

---

## Troubleshooting

### Backend Issues

#### Error: `ModuleNotFoundError: No module named 'fastapi'`

**Solution:** Virtual environment not activated or dependencies not installed.
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### Error: `TesseractNotFoundError`

**Solution:** Tesseract not found.

1. Verify installation:
   ```powershell
   tesseract --version
   ```

2. If not found, add to PATH or set in `.env`:
   ```env
   TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
   ```

#### Error: `Address already in use (port 8000)`

**Solution:** Port is occupied.

```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F
```

#### Error: Model download fails

**Solution:** Check internet connection. Model is ~80MB.

Alternatively, pre-download:
```powershell
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### Frontend Issues

#### Error: `Cannot connect to backend`

**Solution:** Ensure backend is running on port 8000.

Check `.env`:
```env
VITE_API_URL=http://localhost:8000
```

#### Error: `npm ERR! code ENOENT`

**Solution:** Node.js not installed or not in PATH.

Verify:
```powershell
node --version
npm --version
```

#### Port 3000 already in use

**Solution:** Change port in `vite.config.js`:
```javascript
export default defineConfig({
  server: {
    port: 3001  // Change to 3001 or any free port
  }
})
```

### Processing Issues

#### Files stuck in "Processing" (orange) status

**Possible causes:**
1. OCR taking long time (large images)
2. Model downloading on first run
3. Error occurred but not caught

**Solution:**
- Check backend terminal for errors
- Wait 30-60 seconds for first file
- Subsequent files process faster
- Check `searchx.db` for error messages

#### Search returns no results

**Possible causes:**
1. Files still processing
2. No text extracted
3. Query too specific

**Solution:**
- Wait for green status
- Try broader queries
- Check if files have extracted text (view file details)

### Database Issues

#### Corrupted database

**Solution:** Delete and recreate:
```powershell
cd backend
Remove-Item searchx.db
python main.py  # Will recreate database
```

**Note:** This deletes all file records (but not physical files).

---

## Advanced Configuration

### GPU Acceleration

If you have NVIDIA GPU with CUDA:

1. Install PyTorch with CUDA:
   ```powershell
   pip uninstall torch
   pip install torch --index-url https://download.pytorch.org/whl/cu118
   ```

2. Enable in `.env`:
   ```env
   USE_GPU=True
   ```

3. Verify:
   ```powershell
   python -c "import torch; print(torch.cuda.is_available())"
   ```

### Multiple Language OCR

Install additional language packs:

**Windows:**
Download from: https://github.com/tesseract-ocr/tessdata

Place in: `C:\Program Files\Tesseract-OCR\tessdata`

**Linux:**
```bash
sudo apt install tesseract-ocr-fra tesseract-ocr-deu
```

**Configure:**
```env
OCR_LANGUAGES=eng+fra+deu+spa
```

### Production Deployment

See `README.md` section on deployment for cloud setup.

---

## Next Steps

1. ✅ Upload sample files
2. ✅ Test semantic search
3. ✅ Try different file types
4. ✅ Explore media viewer features
5. 📖 Read API documentation
6. 🚀 Deploy to production (optional)

---

## Support

For issues not covered here:

1. Check backend terminal for error logs
2. Check browser console (F12) for frontend errors
3. Verify all dependencies installed correctly
4. Ensure Tesseract is accessible
5. Review README.md for additional information

---

**Setup Complete! 🎉**

You now have a fully functional semantic media search system.
