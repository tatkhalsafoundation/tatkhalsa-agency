# Dockerfile for Tatkhalsa AI Agency
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY dashboard/ ./dashboard/

# Create necessary directories (created at runtime, not in git)
RUN mkdir -p /app/state /app/logs

# Expose ports (Railway uses $PORT dynamically, these are for reference)
EXPOSE 8501 8765 8766

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run both services using start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]