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

# Copy your requirements.txt into the container
COPY requirements.txt /app/requirements.txt

WORKDIR /app

# Install python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy your app code (if any)
COPY . /app

# Your command here (example)
CMD ["streamlit", "run", "your_app.py"]
