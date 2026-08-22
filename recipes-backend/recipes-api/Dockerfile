# 1. Base image
FROM python:3.11-slim

# 2. Prevent Python from writing .pyc files and enable unbuffered stdout/stderr logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 4. Set working directory inside the container
WORKDIR /app

# 5. Install system dependencies if compiling packages (e.g., libpq for postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt-get/lists/*

# 6. Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# 7. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 8. Copy application code
COPY . .

# 9. Expose the API port
EXPOSE 5000

# 10. Run the application
CMD ["python", "app.py"]