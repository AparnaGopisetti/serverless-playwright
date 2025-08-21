# Use AWS Lambda Python 3.11 base image
FROM public.ecr.aws/lambda/python:3.11

# Set working directory
WORKDIR /var/task

# Install system dependencies for Chromium
RUN yum -y install \
    libX11 \
    glib2 \
    gtk3 \
    atk \
    pango \
    cups-libs \
    libXcomposite \
    libXcursor \
    libXdamage \
    libXext \
    libXi \
    libXtst \
    alsa-lib \
    libdrm \
    libgbm \
    nss \
    ffmpeg \
    ca-certificates \
    && yum clean all

# Copy Python dependencies
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright (Lambda-compatible version) and Chromium
RUN pip install --no-cache-dir playwright==1.32.0 \
    && playwright install chromium

# Copy Lambda function
COPY lambda_function.py .

# Set Lambda entrypoint
CMD ["lambda_function.lambda_handler"]
