# Base image with Python 3.11 and slim tools
FROM python:3.11-slim

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies including Tesseract with Arabic support
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-ara \  # Added Arabic OCR support
    tesseract-ocr-fra \  # Optional: Other languages you might want
    tesseract-ocr-spa \
    tesseract-ocr-deu \
    libtesseract-dev \
    poppler-utils \
    build-essential \
    libgl1 \
    curl \
    ghostscript \
    ffmpeg \
    libsndfile1 \
    fonts-dejavu \        # Base fonts
    fonts-noto \          # Additional Unicode fonts
    fonts-arabeyes \      # Arabic-specific fonts
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add Poppler to PATH (usually not needed, but safe)
ENV PATH="/usr/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Streamlit environment variables
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ENABLECORS=false

# Run the Streamlit app
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]