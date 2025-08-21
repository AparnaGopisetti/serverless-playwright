FROM public.ecr.aws/lambda/python:3.11

WORKDIR /var/task

# System dependencies for Chromium
RUN yum install -y \
    libX11 glib2 gtk3 atk pango cups-libs \
    libXcomposite libXcursor libXdamage libXext libXi \
    libXtst alsa-lib libdrm libgbm nss \
    xorg-x11-server-Xvfb \
    && yum clean all

# Upgrade pip and install Python deps
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --target "${LAMBDA_TASK_ROOT}" -r requirements.txt

# Copy Lambda function
COPY lambda_function.py .

# Set Lambda handler
CMD ["lambda_function.lambda_handler"]
