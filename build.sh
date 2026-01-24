#!/usr/bin/env bash
# ===========================================
# RENDER BUILD SCRIPT
# Ye script Render deployment ke time run hoti hai
# ===========================================

set -o errexit  # Exit on error

echo "🚀 Installing Python dependencies..."
pip install -r requirements.txt

echo "📦 Collecting static files..."
python manage.py collectstatic --no-input

echo "🗄️ Running database migrations..."
python manage.py migrate

echo "✅ Build complete! Server ready to start."
