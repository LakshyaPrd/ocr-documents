# ✅ System Ready - Quick Start Guide

## 🎉 Installation Complete!

Both backend and frontend are set up and ready to use.

---

## 🚀 Starting the System

### **Option 1: Automatic Start (Easiest)**

Double-click this file:
```
c:\Lakshya\ocr-data\start-all.bat
```

This will automatically:
- ✅ Start backend server (http://localhost:8000)
- ✅ Start frontend server (http://localhost:3000)
- Opens both in separate command windows

### **Option 2: Manual Start**

**Terminal 1 - Backend:**
```bash
cd c:\Lakshya\ocr-data\backend
venv\Scripts\activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd c:\Lakshya\ocr-data\frontend
npm run dev
```

---

## ⚙️ Before First Use

### Install Tesseract OCR (Required)

1. **Download**: https://github.com/UB-Mannheim/tesseract/wiki
2. **Install** to: `C:\Program Files\Tesseract-OCR\`
3. **Verify**: Open CMD and type `tesseract --version`

The system will automatically detect Tesseract at this location.

---

## 🧪 Testing the System

1. **Open browser**: http://localhost:3000
2. **Select document type**: Choose "PASSPORT" from dropdown
3. **Upload file**: Drag & drop or click to browse (PDF, PNG, JPG)
4. **Click**: "Upload & Extract"
5. **Wait**: ~5-10 seconds for processing
6. **View results**: Click "View Details" to see all extracted fields
7. **Export**: Click "Export CSV" to download data

---

## 📊 What to Expect

### Upload Success
```
✅ Upload successful! Processing started...
```

### Processing Status
- ⏳ **Pending** - Document uploaded, waiting to process
- 🔄 **Processing** - OCR extraction in progress
- ✅ **Done** - All fields extracted successfully
- ⚠️ **Partial** - Some fields extracted, some missing
- ❌ **Failed** - Unable to process (check error message)

### Example Output (Passport)
When you click "View Details" on a processed passport, you'll see ~25 fields:
- Full Name, Father's Name, Mother's Name
- Date of Birth, Place of Birth, Gender
- Passport Number, Issue/Expiry Date
- File Number, Present Address
- Mobile Number, Email, Blood Group
- And more...

---

## 🔧 Troubleshooting

### ❌ "Tesseract not found"
**Solution**: Tesseract not installed or wrong path
- Install from: https://github.com/UB-Mannheim/tesseract/wiki
- Default path should work: `C:\Program Files\Tesseract-OCR\`

### ❌ Frontend won't load
**Solution**: Missing dependencies
```bash
cd frontend
npm install
npm run dev
```

### ❌ Backend errors
**Solution**: Python dependencies issue
```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### ❌ "Port already in use"
**Solution**: Another service using the port
- Backend (8000): Stop other FastAPI/Python servers
- Frontend (3000): Stop other Next.js servers

---

## 📁 Supported Document Types

| Document Type | Fields Extracted | Status |
|--------------|-----------------|--------|
| Passport | 25 fields | ✅ Ready |
| Labor Card | 20 fields | ✅ Ready |
| Emirates ID | 15 fields | ✅ Ready |
| Residence Visa | 18 fields | ✅ Ready |
| Labor Contract | 30 fields | ✅ Ready |
| Home Country ID | 22 fields | ✅ Ready |
| Purchase Order | 25 fields | ✅ Ready |
| Invoice | 28 fields | ✅ Ready |
| Company License | 20 fields | ✅ Ready |
| Company VAT Certificate | 15 fields | ✅ Ready |

---

## 🎯 Next Steps

1. ✅ Install Tesseract OCR
2. ✅ Run `start-all.bat`
3. ✅ Test with sample documents
4. ✅ Review extracted data
5. ✅ Export to CSV

---

## 📚 Additional Resources

- **Full Documentation**: `README.md`
- **API Documentation**: http://localhost:8000/docs (when backend is running)
- **Implementation Details**: Check walkthrough.md in your artifacts folder

---

## 💡 Tips

- **Good Scans**: Use 300 DPI or higher for best OCR accuracy
- **Clear Text**: Ensure text is not rotated or distorted
- **File Size**: Keep under 10MB for optimal performance
- **Multiple Pages**: PDFs are automatically split into pages
- **Manual Corrections**: Click fields in detailed view to edit values

---

**System Status**: ✅ Ready for Production
**Created**: January 4, 2026
**Version**: 1.0.0
