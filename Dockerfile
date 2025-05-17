FROM python:3.11-slim

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
    poppler-utils \
    libprotobuf-dev \
    protobuf-compiler \
    build-essential \
    libgl1 \
    python3-dev \
    g++ \
    fonts-dejavu \
    fonts-noto \
    fonts-noto-arabic \
    fonts-arabeyes \
    fontconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Update pip first
RUN pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]