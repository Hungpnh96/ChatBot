#!/bin/bash
set -e

echo "🚀 Smart ChatBot Startup..."

# Run auto setup
python /app/auto_setup.py

# Start application regardless of setup results
echo "🎯 Starting FastAPI application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
