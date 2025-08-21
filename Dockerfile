# Use AWS Lambda Python 3.11 base image
FROM public.ecr.aws/lambda/python:3.11

# Set working directory
WORKDIR /var/task

# Install system dependencies required by Playwright
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

# Copy Python dependencies and install
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy Lambda function code
COPY lambda_function.py .

# Install Playwright browsers
RUN pip install playwright --target "${LAMBDA_TASK_ROOT}" \
    && playwright install --with-deps chromium

# Set the Lambda handler
CMD ["lambda_function.lambda_handler"]



