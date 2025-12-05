# Use a stable Python version
FROM python:3.11-slim

# Install system libraries needed for Pillow, lxml, WeasyPrint
RUN apt-get update && apt-get install -y \
    libjpeg-dev zlib1g-dev libfreetype6-dev libharfbuzz-dev libfribidi-dev \
    libcairo2 libcairo2-dev libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Start the app
CMD ["gunicorn", "app:app"]
