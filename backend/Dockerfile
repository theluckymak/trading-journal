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

# Create startup script that runs migrations then starts the app
RUN echo '#!/bin/sh\nalembic upgrade head\nexec uvicorn app.main:app --host 0.0.0.0 --port 8000' > /app/start.sh && \
    chmod +x /app/start.sh

# Run application with migrations
CMD ["/bin/sh", "/app/start.sh"]
