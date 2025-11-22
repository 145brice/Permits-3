#!/bin/bash
# Start Contractor Leads in Production Mode

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if app is already running
if lsof -ti:8080 > /dev/null 2>&1; then
    echo "⚠️  App already running on port 8080"
    echo "Stop it with: ./stop.sh"
    exit 1
fi

# Start with gunicorn
echo "🚀 Starting Contractor Leads SaaS (Production Mode)"
echo "================================================="
echo ""
echo "🌐 URL: http://localhost:5003"
echo "📊 Workers: 4"
echo "⏱️  Timeout: 120s"
echo ""

# Start gunicorn in background
gunicorn -w 4 -b 0.0.0.0:8080 --timeout 120 --daemon --pid gunicorn.pid app_backend:app

echo "✅ Application started!"
echo ""
echo "📝 Logs: Check gunicorn logs in current directory"
echo "🛑 Stop: ./stop.sh or kill -9 \$(cat gunicorn.pid)"
echo ""
