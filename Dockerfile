# --- STAGE 3: Final Application Image (Runtime) ---
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
