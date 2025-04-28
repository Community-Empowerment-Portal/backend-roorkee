FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set the working directory
WORKDIR /app

# Install system dependencies (e.g., PostgreSQL development tools, curl, etc.)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    postgresql-server-dev-all \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Pass build arguments
ARG ENV=production
ARG DATABASE_NAME
ARG DATABASE_USER
ARG DATABASE_PASSWORD
ARG DATABASE_HOST
ARG DATABASE_PORT
ARG SECRET_KEY
ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_MEDIA_STORAGE_BUCKET_NAME
ARG AWS_PDF_STORAGE_BUCKET_NAME
ARG AWS_S3_REGION_NAME
ARG EMAIL_HOST_USER
ARG EMAIL_HOST_PASSWORD
ARG EMAIL_FROM
ARG DJANGO_ALLOWED_HOSTS
ARG DJANGO_CSRF_TRUSTED_ORIGINS
ARG SITE_URL
ARG FRONTEND_URL

# Set environment variables for the application
ENV ENV=${ENV} \
    DATABASE_NAME=${DATABASE_NAME} \
    DATABASE_USER=${DATABASE_USER} \
    DATABASE_PASSWORD=${DATABASE_PASSWORD} \
    DATABASE_HOST=${DATABASE_HOST} \
    DATABASE_PORT=${DATABASE_PORT} \
    SECRET_KEY=${SECRET_KEY} \
    AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
    AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
    AWS_MEDIA_STORAGE_BUCKET_NAME=${AWS_MEDIA_STORAGE_BUCKET_NAME} \
    AWS_PDF_STORAGE_BUCKET_NAME=${AWS_PDF_STORAGE_BUCKET_NAME} \
    AWS_S3_REGION_NAME=${AWS_S3_REGION_NAME} \
    EMAIL_HOST_USER=${EMAIL_HOST_USER} \
    EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD} \
    EMAIL_FROM=${EMAIL_FROM} \
    DJANGO_ALLOWED_HOSTS=${DJANGO_ALLOWED_HOSTS} \
    DJANGO_CSRF_TRUSTED_ORIGINS=${DJANGO_CSRF_TRUSTED_ORIGINS} \
    SITE_URL=${SITE_URL} \
    FRONTEND_URL=${FRONTEND_URL}

# Copy the rest of the application code
COPY . .

# Expose the application port
EXPOSE 8000

# Define the default command to run the application
CMD ["gunicorn", "-c", "gunicorn.conf.py"]

# Add a health check for the application
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/health || exit 1
