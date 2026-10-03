# VidTube - Production Dockerfile for Free Cloud Hosting (Hugging Face, Render, Koyeb, etc.)
FROM python:3.11-slim

# Install system dependencies: ffmpeg, nodejs (for yt-dlp JS challenges), curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    nodejs \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    yt-dlp \
    httpx \
    requests \
    pydantic \
    aiogram \
    aiofiles

# Copy project files
COPY . /app

# Ensure downloads directory exists with correct permissions
RUN mkdir -p /app/downloads && chmod -R 777 /app/downloads

# Expose default port
EXPOSE 8000

# Start server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
