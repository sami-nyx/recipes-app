# 1. Base image
FROM python:3.11-slim

# 2. Prevent Python from writing .pyc files and enable unbuffered stdout/stderr logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. Set working directory inside the container
WORKDIR /app

# 4. Install system dependencies if compiling packages (e.g., libpq for postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt-get/lists/*

# 5. Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# 6. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copy application code
COPY . .

# 8. Expose Flask port
EXPOSE 5000

# 9. Run with Gunicorn or Flask WSGI server
CMD ["python", "/app/app.py"]