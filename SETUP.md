# Quick Setup Guide

## Step-by-Step Installation

### 1. Install Tesseract OCR

**Windows:**
- Download: https://github.com/UB-Mannheim/tesseract/wiki
- Run installer (default location: `C:\Program Files\Tesseract-OCR\`)
- Verify: Open CMD and type `tesseract --version`

**macOS:**
```bash
brew install tesseract
tesseract --version
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
tesseract --version
```

### 2. Setup Backend

```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create .env file from template
copy .env.example .env  # Windows
# OR
cp .env.example .env    # Mac/Linux

# Edit .env file and configure Tesseract path
# Windows: TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
# Mac/Linux: TESSERACT_CMD=/usr/local/bin/tesseract
```

### 3. Setup Frontend

```bash
# Open NEW terminal/command prompt
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install
```

### 4. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate  # or: source venv/bin/activate
python main.py
```
✅ Backend running at: http://localhost:8000

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```
✅ Frontend running at: http://localhost:3000

### 5. Access the Application

Open your browser and navigate to:
**http://localhost:3000**

---

## Quick Test

1. Select "PASSPORT" from document type dropdown
2. Upload a sample passport image/PDF
3. Click "Upload & Extract"
4. Wait 5-10 seconds for processing
5. Click "View Details" to see extracted fields
6. Export to CSV if needed

---

## Common Issues

### ❌ "Tesseract not found"
**Solution:** Edit `backend/.env` and set correct path:
- Windows: `TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe`
- Mac: `TESSERACT_CMD=/usr/local/bin/tesseract`
- Linux: `TESSERACT_CMD=/usr/bin/tesseract`

### ❌ "Port 8000 already in use"
**Solution:** Kill the process using port 8000 or change port in `backend/main.py`

### ❌ Frontend won't start
**Solution:**
```bash
cd frontend
rm -rf node_modules .next
npm install
npm run dev
```

### ❌ Database errors
**Solution:**
```bash
cd backend
rm ocr_data.db  # Delete old database
python main.py  # Will recreate fresh database
```

---

## File Structure

```
ocr-data/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── config.py            # Document type configurations
│   ├── models.py            # Database models
│   ├── database.py          # Database setup
│   ├── ocr_service.py       # OCR processing logic
│   ├── schemas.py           # API schemas
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # Environment config (create from .env.example)
│   ├── .env.example         # Example environment file
│   └── uploads/             # Uploaded files directory
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Main page
│   │   ├── layout.tsx       # Root layout
│   │   ├── globals.css      # Global styles
│   │   └── components/
│   │       ├── DocumentUpload.tsx   # Upload component
│   │       └── ResultsTable.tsx     # Results display
│   ├── package.json         # Node dependencies
│   ├── next.config.js       # Next.js config
│   ├── tailwind.config.ts   # Tailwind config
│   └── tsconfig.json        # TypeScript config
│
└── README.md                # Main documentation
```

---

## Next Steps

1. ✅ Install dependencies
2. ✅ Configure .env file
3. ✅ Start both servers
4. ✅ Test with sample documents
5. 🚀 Ready for production!

---

## Need Help?

- Check main README.md for detailed documentation
- API docs: http://localhost:8000/docs
- Test API: http://localhost:8000
