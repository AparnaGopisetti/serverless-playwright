# Use Ubuntu-based Python 3.11 image for GLIBC >= 2.28
FROM python:3.11-slim

# Install system dependencies for Playwright/Chromium and Lambda RIC
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libx11-xcb1 \
    libxkbcommon0 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libgtk-3-0 \
    libdrm2 \
    libxext6 \
    libxfixes3 \
    libxrender1 \
    libxtst6 \
    ca-certificates \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /var/task

# Copy Python dependencies
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install AWS Lambda Runtime Interface Client
RUN pip install --no-cache-dir awslambdaric

# Install Playwright and Chromium
RUN pip install --no-cache-dir playwright \
    && playwright install chromium

# Copy Lambda function
COPY lambda_function.py .

# Set Lambda entrypoint
CMD ["python3", "-m", "awslambdaric", "lambda_function.lambda_handler"]
