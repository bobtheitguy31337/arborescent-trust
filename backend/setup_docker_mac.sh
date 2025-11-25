#!/bin/bash
# Docker setup script for Arborescent Trust on macOS

set -e

echo "🐳 Setting up Arborescent Trust with Docker"
echo "==========================================="
echo ""

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found."
    echo ""
    echo "Please install Docker Desktop for Mac:"
    echo "  Option 1: brew install --cask docker"
    echo "  Option 2: Download from https://www.docker.com/products/docker-desktop/"
    echo ""
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running."
    echo ""
    echo "Please start Docker Desktop from Applications or menu bar."
    echo ""
    exit 1
fi

echo "✅ Docker is installed and running"

cd "$(dirname "$0")"

# Setup environment file
echo ""
echo "⚙️  Setting up environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    
    # Generate secure JWT secret
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Update .env file
    sed -i '' "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=${JWT_SECRET}|g" .env
    
    echo "✅ Environment file created with secure JWT secret"
else
    echo "⚠️  .env file already exists"
fi

# Start services
echo ""
echo "🚀 Starting Docker services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if PostgreSQL is ready
until docker-compose exec -T postgres pg_isready -U invitetree &> /dev/null; do
    echo "   Waiting for PostgreSQL..."
    sleep 2
done
echo "✅ PostgreSQL is ready"

# Check if Redis is ready
until docker-compose exec -T redis redis-cli ping &> /dev/null; do
    echo "   Waiting for Redis..."
    sleep 2
done
echo "✅ Redis is ready"

# Run migrations
echo ""
echo "🔄 Running database migrations..."
docker-compose exec -T api alembic upgrade head
echo "✅ Migrations complete"

# Create admin user
echo ""
echo "👤 Creating admin user..."
docker-compose exec -T api python -m app.scripts.create_admin

echo ""
echo "🎉 Setup complete!"
echo ""
echo "==========================================="
echo "Your services are running:"
echo "  • API: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo "  • PostgreSQL: localhost:5432"
echo "  • Redis: localhost:6379"
echo ""
echo "Useful commands:"
echo "  • View logs: docker-compose logs -f api"
echo "  • Stop: docker-compose down"
echo "  • Restart: docker-compose restart api"
echo "==========================================="

