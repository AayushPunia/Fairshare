#!/usr/bin/env bash
# Build script for Render deployment
# Runs both frontend and backend setup

set -o errexit

echo "=== Installing frontend dependencies ==="
cd frontend
npm install
echo "=== Building React frontend ==="
npm run build
cd ..

echo "=== Installing backend dependencies ==="
cd backend
pip install -r requirements.txt
echo "=== Collecting static files ==="
python manage.py collectstatic --noinput
echo "=== Running migrations ==="
python manage.py migrate --noinput

echo "=== Build complete ==="
