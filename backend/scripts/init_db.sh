#!/bin/bash
# Initialize database with migrations and admin user

set -e

echo "🔧 Initializing Arborescent Trust database..."
echo ""

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "✓ Running inside Docker container"
else
    echo "⚠️  Running on host system"
fi

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "${DATABASE_HOST:-localhost}" -U "${DATABASE_USER:-invitetree}" -d "${DATABASE_NAME:-invite_tree_db}" -c '\q' 2>/dev/null; do
  echo "   PostgreSQL is unavailable - sleeping"
  sleep 1
done
echo "✓ PostgreSQL is ready!"
echo ""

# Generate migration if needed
echo "📝 Checking for migrations..."
MIGRATION_COUNT=$(ls -1 alembic/versions/*.py 2>/dev/null | wc -l)

if [ $MIGRATION_COUNT -eq 0 ]; then
    echo "   No migrations found, generating initial migration..."
    alembic revision --autogenerate -m "Initial schema"
    echo "✓ Initial migration generated"
else
    echo "✓ Found $MIGRATION_COUNT existing migration(s)"
fi
echo ""

# Run migrations
echo "🚀 Running database migrations..."
alembic upgrade head
echo "✓ Migrations complete!"
echo ""

# Create admin user
echo "👤 Creating admin user..."
python -m app.scripts.create_admin
echo ""

echo "✅ Database initialization complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. Start the API: docker-compose up -d"
echo "   2. Access docs: http://localhost:8000/docs"
echo "   3. Use the invite tokens shown above to register users"
echo ""

