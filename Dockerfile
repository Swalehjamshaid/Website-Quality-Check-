# --- STAGE 1: Node.js Dependencies (Modified) ---
FROM docker.io/library/node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
# FIX: Change 'npm ci' to 'npm install' to fix the EUSAGE error 
# due to missing package-lock.json.
RUN npm install --only=production --legacy-peer-deps

# --- STAGE 2: Python Build (WeasyPrint Dependencies) ---
FROM python:3.11-slim AS build
# Install system dependencies needed by WeasyPrint (PDF generation)
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libharfbuzz-icu0 \
    libtiff-tools \
    libxml2-dev \
    libxslt1-dev \
    libssl-dev \
    libffi-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
# Install Python Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# --- STAGE 3: Final Application Image ---
FROM python:3.11-slim
WORKDIR /app

# Re-install runtime dependencies for WeasyPrint
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libharfbuzz-icu0 \
    libtiff-tools \
    libxml2 \
    libxslt1.1 \
    libgomp1 \
    libjpeg62-turbo \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from build stage
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build /usr/local/bin/ /usr/local/bin/

# Copy Node.js built files (assuming the Node.js step creates static files)
COPY --from=deps /app/node_modules /app/node_modules

# Copy application code
COPY . .

# Set environment variable for Railway
ENV FLASK_APP=app

# Default command for the web process (overridden by Procfile)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
