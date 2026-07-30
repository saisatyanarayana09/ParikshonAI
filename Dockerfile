# Use an official lightweight Python image
FROM python:3.10-slim

# Prevent Python from writing pyc files and keep stdout/stderr unbuffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for OCR, PDF processing, and Postgres
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
# Using --no-cache-dir helps keep the image size small
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the Django project code
COPY . .

# Collect static files for Whitenoise
RUN python manage.py collectstatic --noinput

# Expose the port Render expects
EXPOSE 8000

# Run migrations and start the Gunicorn server simultaneously 
CMD bash -c "python manage.py migrate && gunicorn parikshon_ai.wsgi:application --bind 0.0.0.0:${PORT:-8000} --timeout 120"
