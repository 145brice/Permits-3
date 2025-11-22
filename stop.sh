#!/bin/bash
# Stop Contractor Leads

if [ -f gunicorn.pid ]; then
    PID=$(cat gunicorn.pid)
    echo "🛑 Stopping Contractor Leads (PID: $PID)"
    kill -9 $PID 2>/dev/null || true
    rm gunicorn.pid
    echo "✅ Stopped"
else
    # Fallback: kill by port
    if lsof -ti:8080 > /dev/null 2>&1; then
        echo "🛑 Stopping process on port 8080"
        lsof -ti:8080 | xargs kill -9
        echo "✅ Stopped"
    else
        echo "ℹ️  No app running on port 8080"
    fi
fi
