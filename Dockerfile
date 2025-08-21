# Use Ubuntu-based Python 3.11 image for GLIBC >= 2.28
FROM python:3.11-slim

# Set working directory
WORKDIR /var/task

# Install system dependencies required by Playwright/Chromium
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    ca-certificates \
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
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set Playwright browser path to Lambda-accessible directory
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Copy Python dependencies
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install AWS Lambda Runtime Interface Client
RUN pip install --no-cache-dir awslambdaric

# Install Lambda-compatible Playwright and Chromium
RUN pip install --no-cache-dir playwright==1.32.0 \
    && playwright install chromium

# Copy Lambda function code
COPY lambda_function.py .

# Set Lambda entrypoint
CMD ["python3", "-m", "awslambdaric", "lambda_function.lambda_handler"]
