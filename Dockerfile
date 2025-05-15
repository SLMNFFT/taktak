FROM python:3.12-slim

# Install system dependencies needed for aiortc and other libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    libffi-dev \
    libssl-dev \
    libsrtp2-dev \
    libopus-dev \
    libvpx-dev \
    && rm -rf /var/lib/apt/lists/*

# Set workdir and copy files
WORKDIR /app

COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copy rest of your app
COPY . .

# Command to run your app (example)
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
