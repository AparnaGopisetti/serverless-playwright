# Use AWS Lambda Python 3.11 base image
FROM public.ecr.aws/lambda/python:3.11

# Set working directory
WORKDIR /var/task

# Copy Python dependencies file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and required browsers
RUN pip install --no-cache-dir playwright \
    && playwright install --with-deps chromium

# Copy Lambda function code
COPY lambda_function.py .

# Lambda entrypoint (handler)
CMD ["lambda_function.lambda_handler"]

