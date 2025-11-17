#!/bin/bash
set -e

echo "🚀 Starting Payslip Analysis System on Railway..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
until pg_isready -h $(echo $DATABASE_URL | sed -E 's/.*@(.+):([0-9]+)\/.*/\1/') -p $(echo $DATABASE_URL | sed -E 's/.*:([0-9]+)\/.*/\1/') 2>/dev/null; do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "✓ Database is ready!"

# Initialize database tables
echo "📊 Initializing database tables..."
python -c "from app.database import init_db; init_db()"

echo "✓ Database tables created!"

# Start the application
echo "🌐 Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
