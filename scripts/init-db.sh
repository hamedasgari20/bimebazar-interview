#!/bin/bash

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
while ! pg_isready -h db -p 5432 -U debug -d db; do
    echo "PostgreSQL is not ready yet. Retrying in 5 seconds..."
    sleep 5
done

echo "PostgreSQL is ready! Running migrations..."

# Run migrations
alembic upgrade head

# Check if migrations were successful
if [ $? -eq 0 ]; then
    echo "Migrations completed successfully!"
else
    echo "Migrations failed!"
    exit 1
fi
