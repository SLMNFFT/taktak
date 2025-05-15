FROM python:3.11-slim

# Set UTF-8 locale
RUN apt-get update && apt-get install -y locales \
    && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Python environment
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    poppler-utils \
    build-essential \
    libgl1 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Streamlit environment
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ENABLECORS=false

# Expose Streamlit port
EXPOSE 8501

# Run the app
CMD ["streamlit", "run", "main.py"]
