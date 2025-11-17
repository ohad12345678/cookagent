#!/bin/bash

echo "🚀 Starting Payslip Analysis System..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file with your ANTHROPIC_API_KEY"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    echo "Please start Docker Desktop"
    exit 1
fi

echo "✓ Docker is running"
echo "✓ .env file found"
echo ""

# Build and start containers
echo "Building and starting containers..."
docker-compose up --build -d

# Wait for services
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✅ System is ready!"
    echo ""
    echo "🌐 Open your browser:"
    echo "   Frontend: http://localhost:8080"
    echo "   API:      http://localhost:3000"
    echo ""
    echo "📊 View logs:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🛑 Stop system:"
    echo "   docker-compose down"
    echo ""
else
    echo ""
    echo "❌ Error: Services failed to start"
    echo "Check logs: docker-compose logs"
    exit 1
fi
