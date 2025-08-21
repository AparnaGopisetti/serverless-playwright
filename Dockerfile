FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy
WORKDIR /var/task
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY lambda_function.py .
CMD ["python3", "-m", "awslambdaric", "lambda_function.lambda_handler"]
