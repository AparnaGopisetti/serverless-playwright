FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /var/task

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY lambda_function.py .

CMD [ "lambda_function.lambda_handler" ]

