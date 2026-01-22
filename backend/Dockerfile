# Backend Dockerfile - Optimized for VPS deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (including Poppler for PDF processing)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download EasyOCR models to avoid download on first run
RUN python -c "import easyocr; reader = easyocr.Reader(['en', 'ar'], gpu=False)"

# Copy application code
COPY . .

# Create directories for uploads and temp files
RUN mkdir -p uploads temp_images

# Expose port 8001 (to avoid conflict with CRM on 8000)
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health')" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
