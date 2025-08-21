FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y ... 

WORKDIR /var/task

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Lambda RIC
RUN pip install --no-cache-dir awslambdaric

# Install Playwright AND Chromium binary
RUN pip install --no-cache-dir playwright==1.41.0 \
    && playwright install chromium

COPY lambda_function.py .
CMD ["python3", "-m", "awslambdaric", "lambda_function.lambda_handler"]
