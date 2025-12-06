FROM python:3.11-slim

# System deps for WeasyPrint, Pillow, Matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo-dev zlib1g-dev libfreetype6-dev \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port (Render uses $PORT)
EXPOSE $PORT

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT"]
