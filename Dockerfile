# Build phase: add awslambdaric and boto3
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy as build

RUN pip install awslambdaric boto3

# Final phase: copy over site-packages, requirements, and code
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /var/task
COPY --from=build /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY lambda_function.py .

CMD [ "lambda_function.lambda_handler" ]
