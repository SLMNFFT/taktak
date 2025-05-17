# Base image with Python 3.11 and slim tools
FROM python:3.11-slim

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-ara \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-deu \
    libtesseract-dev \
    poppler-utils \
    build-essential \
    libgl1 \
    ghostscript \
    ffmpeg \
    libsndfile1 \
    fonts-dejavu \
    fonts-noto \
    fonts-noto-arabic \
    fonts-arabeyes \
    fontconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Update font cache
RUN fc-cache -f -v

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY . .

EXPOSE 8501

# Streamlit environment variables
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ENABLECORS=false

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]