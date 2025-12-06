# ========================================================
# 1. STAGE: Node.js Dependencies (Fixes the npm ci error)
# ========================================================
FROM docker.io/library/node:20-alpine AS deps
WORKDIR /app
# The 'COPY package*.json ./' step assumes these files exist in your repo root.
COPY package*.json ./
# FIX 1: Use 'npm install' instead of 'npm ci' to bypass the missing package-lock.json error.
RUN npm install --only=production --legacy-peer-deps

# ========================================================
# 2. STAGE: Python Build (Installs Python dependencies)
# ========================================================
FROM python:3.11-slim AS build
# FIX 2: Corrected list of system dependencies required for WeasyPrint 
# and other common libraries like Matplotlib on Debian/slim.
RUN apt-get update && apt-get install -y \
    # WeasyPrint Core Dependencies
    libpango-1.0-0 \
    libharfbuzz-icu0 \
    libxml2-dev \
    libxslt1-dev \
    # General build dependencies
    build-essential \
    libssl-dev \
    libffi-dev \
    # Image processing/Matplotlib dependencies
    libjpeg-dev \
    zlib1g-dev \
    # Clean up APT cache to keep image small
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
# Install Python Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ========================================================
# 3. STAGE: Final Application Image (Runtime)
# ========================================================
FROM python:3.11-slim
WORKDIR /app

# Final runtime dependencies (without the -dev headers)
RUN apt-get update && apt-get install -y \
    # WeasyPrint/Pango/Harfbuzz runtime libs
    libpango-1.0-0 \
    libharfbuzz-icu0 \
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

# Copy Node.js built files (static assets, etc.)
COPY --from=deps /app/node_modules /app/node_modules

# Copy application code (including Procfile, app.py, templates, etc.)
COPY . .

# Set environment variable for Flask (optional, but good practice)
ENV FLASK_APP=app

# Default command (will be overridden by Procfile on Railway)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
