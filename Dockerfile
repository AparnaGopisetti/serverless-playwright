# Use Ubuntu-based Python 3.11 image (Lambda-compatible)
FROM python:3.11-slim

# Set environment variables for Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright-browsers \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget curl gnupg ca-certificates \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libxcomposite1 libxdamage1 libxrandr2 libx11-xcb1 \
    libxkbcommon0 libgbm1 libasound2 libpangocairo-1.0-0 \
    libpango-1.0-0 libgtk-3-0 libdrm2 libxext6 libxfixes3 \
    libxrender1 libxtst6 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create directory for Playwright browsers
RUN mkdir -p $PLAYWRIGHT_BROWSERS_PATH

# Set working directory
WORKDIR /var/task

# Copy Python dependencies
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Install AWS Lambda Runtime Interface Client
RUN pip install awslambdaric

# Install Playwright (version compatible with Lambda GLIBC)
RUN pip install playwright==1.32.0 \
    && playwright install --with-deps chromium

# Copy Lambda function
COPY lambda_function.py .

# Add non-root user for Lambda execution
RUN useradd -m lambdauser
USER lambdauser

# Lambda entrypoint
CMD ["python3", "-m", "awslambdaric", "lambda_function.lambda_handler"]
