#!/bin/bash

# Geosocial API Deployment Script

set -e

echo "🚀 Starting deployment..."

# Pull latest changes
echo "📥 Pulling latest code..."
git pull origin main

# Build and restart services
echo "🔨 Building and restarting services..."
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Run migrations
echo "📊 Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T api alembic upgrade head

# Health check
echo "🏥 Performing health check..."
if curl -f http://localhost:8000/docs >/dev/null 2>&1; then
    echo "✅ Deployment successful! API is running."
else
    echo "❌ Deployment failed! API is not responding."
    exit 1
fi

echo "🎉 Deployment completed successfully!" 