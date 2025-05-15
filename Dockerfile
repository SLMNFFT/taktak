FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libavdevice-dev \
    libavformat-dev \
    libswscale-dev \
    libavcodec-dev \
    libavutil-dev \
    pkg-config \                # <== Needed for PyAV (used by aiortc)
    build-essential \           # <== Ensures langdetect compiles and others install cleanly
    python3-dev \               # <== Required for native extensions
    python3-distutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

