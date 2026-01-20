FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-docker.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-docker.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run migrations then start application
CMD ["python", "startup.py"]
