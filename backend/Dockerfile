FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/app /app/app
COPY backend/agents.py /app/agents.py
COPY backend/tasks.py /app/tasks.py
COPY backend/tools /app/tools
COPY backend/config.py /app/config.py

# Create upload directory
RUN mkdir -p /app/uploads /app/data

# Add app to Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose port
EXPOSE 9000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]
