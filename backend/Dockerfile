FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-docker.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-docker.txt

# Copy application
COPY . .

# Create DRL model directory (models mounted or copied at deploy)
RUN mkdir -p /app/ai/saved_models/drl

ENV DRL_MODEL_DIR=/app/ai/saved_models/drl

# Expose port
EXPOSE ${PORT:-8000}

# Run migrations then start application
CMD ["python", "startup.py"]
