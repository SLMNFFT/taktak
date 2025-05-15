FROM python:3.12-slim

# Install system dependencies for aiortc and PyAV
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libopus-dev \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavfilter-dev \
    libavutil-dev \
    libswscale-dev \
    libavresample-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements.txt before installing
COPY requirements.txt /app/requirements.txt

# Upgrade pip, setuptools, wheel first (wheel is helpful for building wheels)
RUN pip install --upgrade pip setuptools wheel

# Install python dependencies
RUN pip install -r requirements.txt

# Copy your app code
COPY . /app

# Default command (adjust 'your_app.py' to your main script)
CMD ["streamlit", "run", "your_app.py"]
