FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies with pinned versions
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-ara \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-deu \
    poppler-utils \
    libprotobuf-dev=3.21.12-1 \
    protobuf-compiler=3.21.12-1 \
    build-essential \
    libgl1 \
    fonts-dejavu \
    fonts-noto \
    fonts-noto-arabic \
    fonts-arabeyes \
    fontconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python build dependencies first
RUN pip install --upgrade pip==24.0 wheel setuptools==69.0.3

WORKDIR /app

# Copy requirements before source code for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]