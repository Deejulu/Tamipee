#!/usr/bin/env bash
# Render.com Build Script for Tamipee Integrated Farms
# This script runs during deployment to set up the application

set -o errexit  # Exit on error

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🗄️  Running database migrations..."
python manage.py migrate --noinput

echo "📊 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "✅ Build completed successfully!"
echo "🚀 Your Tamipee Integrated Farms application is ready to deploy."

# Optional: Populate sample data (uncomment if you want sample data on first deploy)
# echo "🌱 Populating sample data..."
# python manage.py populate_sample


