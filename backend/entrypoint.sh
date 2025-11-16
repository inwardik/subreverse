#!/bin/bash
set -e

echo "Starting backend entrypoint script..."

# Function to wait for PostgreSQL to be ready
wait_for_postgres() {
    echo "Waiting for PostgreSQL to be ready..."

    # Extract connection details from POSTGRES_URL
    # Format: postgresql+asyncpg://user:password@host:port/database
    DB_HOST=$(echo $POSTGRES_URL | sed -e 's|.*@\(.*\):.*|\1|')
    DB_PORT=$(echo $POSTGRES_URL | sed -e 's|.*:\([0-9]*\)/.*|\1|')
    DB_USER=$(echo $POSTGRES_URL | sed -e 's|.*://\(.*\):.*@.*|\1|')
    DB_NAME=$(echo $POSTGRES_URL | sed -e 's|.*/\(.*\)$|\1|')

    echo "Connecting to PostgreSQL at $DB_HOST:$DB_PORT..."

    # Wait for PostgreSQL to be ready (max 30 seconds)
    for i in {1..30}; do
        if python3 -c "
import asyncio
import asyncpg
import sys

async def check_db():
    try:
        conn = await asyncpg.connect(
            host='$DB_HOST',
            port=$DB_PORT,
            user='$DB_USER',
            database='$DB_NAME',
            password='$(echo $POSTGRES_URL | sed -e 's|.*://.*:\(.*\)@.*|\1|')'
        )
        await conn.close()
        return True
    except Exception as e:
        return False

result = asyncio.run(check_db())
sys.exit(0 if result else 1)
" 2>/dev/null; then
            echo "PostgreSQL is ready!"
            return 0
        fi
        echo "Attempt $i/30: PostgreSQL is not ready yet, waiting..."
        sleep 1
    done

    echo "ERROR: PostgreSQL did not become ready in time"
    exit 1
}

# Wait for PostgreSQL
wait_for_postgres

# Run database migrations
echo "Running database migrations..."
cd /app/backend
alembic upgrade head
echo "✓ Migrations applied successfully!"

# Start the application
echo "Starting FastAPI application..."
cd /app
exec uvicorn backend.src.main:app --host 0.0.0.0 --port 8000
