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
COPY state/ ./state/
COPY logs/ ./logs/

# Create necessary directories
RUN mkdir -p /app/state /app/logs

# Expose ports
EXPOSE 8501 8765

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run both services using a process manager
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]