#!/bin/bash
set -e

echo "🚀 Cerebro Backend Startup"

# Load environment variables (if exists, otherwise use docker-compose env vars)
if [ -f /app/.env ]; then
    source /app/.env
fi

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
DB_HOST=${DB_HOST:-postgres}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-cerebro}
DB_PASSWORD=${DB_PASSWORD:-cerebro}
DB_NAME=${DB_NAME:-cerebro_db}

max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" 2>/dev/null; then
        echo "✅ PostgreSQL is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "  Attempt $attempt/$max_attempts..."
    sleep 1
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ PostgreSQL failed to start"
    exit 1
fi

# Apply schema migrations
echo "📊 Applying database schema..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f /app/modulo3_armazenamento/schema.sql || {
    echo "❌ Failed to apply schema"
    exit 1
}
echo "✅ Schema applied!"

# Apply Module 4 schema migration (new tables and columns)
echo "📊 Applying Module 4 schema migration..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f /app/modulo4_processamento/schema_migration.sql || {
    echo "❌ Failed to apply Module 4 schema migration"
    exit 1
}
echo "✅ Module 4 schema migration applied!"

# Start the backend
echo "🎙️  Starting Cerebro backend..."
exec python /app/main.py
