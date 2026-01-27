# Quick GitHub Setup Commands

## Step 1: Create GitHub Repository
1. Go to https://github.com/new
2. Repository name: `ocr-document-api`
3. Choose Private or Public
4. Click "Create repository"

## Step 2: Push Code to GitHub (Run in PowerShell)

```powershell
# Navigate to project
cd c:\Lakshya\ocr-data

# Initialize git (if needed)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - OCR Document API v2.1"

# Add your GitHub repository
git remote add origin https://github.com/YOUR_USERNAME/ocr-document-api.git

# Push to GitHub
git push -u origin main
```

## Step 3: Deploy to VPS

```bash
# SSH into VPS
ssh project_2@srv1259166

# Navigate to directory
cd /projects/project_2/ocr-documents

# Clone from GitHub
git clone https://github.com/YOUR_USERNAME/ocr-document-api.git .

# Build and start
docker-compose build
docker-compose up -d

# Verify
docker ps | grep ocr-backend
curl http://localhost:8002/
```

## Future Updates

```powershell
# On Windows - after making changes:
git add .
git commit -m "Description of changes"
git push
```

```bash
# On VPS - to update:
cd /projects/project_2/ocr-documents
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

## Troubleshooting

If git asks for credentials:
```bash
# Use personal access token instead of password
# Generate at: https://github.com/settings/tokens
```

If you need to change repository URL:
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/ocr-document-api.git
```
