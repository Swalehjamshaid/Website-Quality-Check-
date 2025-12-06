# ========================================================
# 1. STAGE: Python Build (Installs dependencies and system libs)
# ========================================================
# Start directly with the Python build stage
FROM python:3.11-slim AS build

# CORRECTED: Use verified system dependencies required for WeasyPrint 
# and other libraries on the Debian/slim base image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    # WeasyPrint/Pango/Harfbuzz build dependencies
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libharfbuzz-subset0 \
    libxml2-dev \
    libxslt1-dev \
    # General build dependencies
    build-essential \
    libssl-dev \
    libffi-dev \
    # Image processing dependencies (for Pillow/Matplotlib)
    libjpeg-dev \
    zlib1g-dev \
    # Clean up APT cache to keep image small
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
# Install Python Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ========================================================
# 2. STAGE: Final Application Image (Runtime)
# ========================================================
FROM python:3.11-slim
WORKDIR /app

# Final runtime dependencies (without the -dev headers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # WeasyPrint/Pango/Harfbuzz runtime libs
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libxml2 \
    libxslt1.1 \
    # Other common runtime libs
    libgomp1 \
    libjpeg62-turbo \
    # Clean up APT cache
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from build stage
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
# Copy entry point scripts/executables
COPY --from=build /usr/local/bin/ /usr/local/bin/

# Copy application code (Procfile, app.py, templates, etc.)
COPY . .

# Set environment variable for Flask
ENV FLASK_APP=app

# Default command (overridden by Procfile on Railway)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
