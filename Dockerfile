# Lambda-ready Playwright Python image with compatible Chromium and GLIBC
FROM ghcr.io/sponsors/playwright/python:1.42-lambda

# Set working directory
WORKDIR /var/task

# Copy Python dependencies and install into Lambda task root
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy your Lambda function code
COPY lambda_function.py .

# Set the Lambda handler
CMD ["lambda_function.lambda_handler"]
