#!/bin/bash
set -e

echo "🚀 Starting Payslip Analysis System on Railway..."

# Wait a bit for database (Railway handles connection)
echo "⏳ Waiting for database connection..."
sleep 5

# Initialize database tables
echo "📊 Initializing database tables..."
python -c "from app.database import init_db; init_db()" || echo "⚠️ Database init failed, will retry on startup"

echo "✓ Database ready!"

# Start the application
echo "🌐 Starting FastAPI server on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
