#!/bin/sh

# Run database migrations
echo "🗄️ Running database migrations..."

# Check current migration state and apply if needed
echo "🔄 Running incremental migrations..."
flask db upgrade head
echo "✅ Migrations applied"

# Start the application
echo "🚀 Starting CareSync APIs..."
waitress-serve --host 0.0.0.0 --port 4100 --call run:create_app
