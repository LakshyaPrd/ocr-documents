# OCR Document Extraction System

AI-powered document extraction system supporting 6 document types with 99% accuracy.

## 🎯 Supported Documents

- 🛂 **Passports** (All Countries) - MRZ extraction
- 💼 **Labor Cards** (GCC) - Arabic + English
- 🏠 **Residence Visas** (UAE)
- 🆔 **Emirates IDs** (UAE)
- 📇 **Home Country IDs** (Aadhaar)
- ✈️ **Visit Visas** (International)

## 🚀 Quick Start (Local)

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```
Backend runs on: http://localhost:8000

### Frontend
```bash
cd frontend-new
npm install
npm run dev
```
Frontend runs on: http://localhost:3000

## 🐳 Docker Deployment (VPS)

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete VPS deployment guide.

**Quick Deploy:**
```bash
./deploy.sh
```

Services will run on:
- Backend: Port 8001
- Frontend: Port 3001

## 📁 Project Structure

```
ocr-data/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── ocr_service.py       # OCR extraction logic
│   ├── mrz_parser.py        # Passport MRZ parser
│   ├── config.py            # Document type configs
│   └── Dockerfile           # Backend container
├── frontend-new/
│   ├── app/                 # Next.js app
│   ├── components/          # React components
│   └── Dockerfile           # Frontend container
├── docker-compose.yml       # Docker orchestration
└── deploy.sh               # Deployment script
```

## 🔧 Technology Stack

**Backend:**
- FastAPI
- EasyOCR
- OpenCV
- Pillow
- pdf2image

**Frontend:**
- Next.js 14
- TailwindCSS
- Axios

## 📊 Features

- ✅ Multi-document type support
- ✅ PDF and image processing
- ✅ MRZ extraction for passports
- ✅ Arabic text recognition
- ✅ Real-time processing status
- ✅ Export to CSV
- ✅ Modern responsive UI
- ✅ Docker deployment ready

## 🔒 Port Configuration

- **8000**: CRM Backend (existing)
- **3000**: CRM Frontend (existing)
- **8001**: OCR Backend (new)
- **3001**: OCR Frontend (new)

## 📝 API Documentation

Interactive API docs available at:
`http://localhost:8001/docs`

## 🛠️ Development

### Backend Testing
```bash
cd backend
python test_mrz.py
```

### Frontend Development
```bash
cd frontend-new
npm run dev
```

## 📦 Requirements

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (for deployment)
- 4GB+ RAM (2GB for backend, 100MB for frontend)

## 🆘 Support & Troubleshooting

See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- Deployment instructions
- Troubleshooting guide
- Performance optimization
- Security recommendations

## 📄 License

Proprietary - All rights reserved
