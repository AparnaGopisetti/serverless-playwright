# ===========================
# Stage 1: Build dependencies
# ===========================
# Define custom function directory
ARG FUNCTION_DIR="/function"

FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy as build-image

# Install aws-lambda-cpp build dependencies
RUN apt-get update && \
  apt-get install -y \
  g++ \
  make \
  cmake \
  unzip \
  libcurl4-openssl-dev \
  software-properties-common \
  fonts-liberation \
  libappindicator3-1 \
  libasound2 \
  libatk-bridge2.0-0 \
  libatk1.0-0 \
  libcups2 \
  libdbus-1-3 \
  libgdk-pixbuf2.0-0 \
  libnspr4 \
  libnss3 \
  pciutils \
  xdg-utils

ARG FUNCTION_DIR
RUN mkdir -p ${FUNCTION_DIR}

# Copy function code
COPY . ${FUNCTION_DIR}

# Install Lambda Runtime Interface Client
RUN pip install --target ${FUNCTION_DIR} awslambdaric

# Install Playwright + Chromium
RUN pip install --target ${FUNCTION_DIR} playwright==1.32.0 \
    && playwright install chromium

# Install other dependencies from requirements.txt
COPY requirements.txt .
RUN pip install --target ${FUNCTION_DIR} -r requirements.txt

# ===========================
# Stage 2: Final image
# ===========================
FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

ARG FUNCTION_DIR
WORKDIR ${FUNCTION_DIR}

# Copy built dependencies from build stage
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}

# Lambda runtime
ENTRYPOINT ["python", "-m", "awslambdaric"]
CMD ["lambda_function.handler"]
