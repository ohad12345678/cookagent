# Multi-stage build for Railway deployment
FROM python:3.11-slim as backend-builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy application code
COPY backend/app /app/app
COPY backend/agents.py /app/agents.py
COPY backend/tasks.py /app/tasks.py
COPY backend/tools /app/tools
COPY backend/config.py /app/config.py

# Copy frontend files
COPY frontend /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

# Create necessary directories
RUN mkdir -p /app/uploads /app/data

# Add app to Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose port (Railway will assign via $PORT)
EXPOSE $PORT

# Copy and set startup script
COPY railway-start.sh /app/railway-start.sh
RUN chmod +x /app/railway-start.sh

# Run startup script
CMD ["/app/railway-start.sh"]
