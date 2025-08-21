# Use AWS Lambda Python 3.11 base image
FROM public.ecr.aws/lambda/python:3.11

# Set working directory
WORKDIR /var/task

# Install system dependencies required by Playwright/Chromium
RUN yum install -y \
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
    curl \
    wget \
    unzip \
    tar \
    gzip \
    xorg-x11-server-Xvfb \
    && yum clean all

# Upgrade pip
RUN pip install --upgrade pip

# Install Playwright globally so the CLI is available for browser installation
RUN pip install playwright

# Install Chromium browser with required dependencies
RUN playwright install --with-deps chromium

# Copy Python dependencies and install into Lambda task root
COPY requirements.txt .
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy Lambda function code
COPY lambda_function.py .

# Set the Lambda handler
CMD ["lambda_function.lambda_handler"]
