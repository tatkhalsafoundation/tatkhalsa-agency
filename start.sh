#!/bin/bash
# Start script for Tatkhalsa AI Agency (Railway-compatible)

set -e

echo "🏢 Starting Tatkhalsa AI Agency..."

# Railway provides $PORT (the single exposed port). Streamlit serves the dashboard.
# If $PORT is set (Railway/Render/Heroku), run Streamlit on that port.
# Otherwise fall back to local defaults (8501 dashboard, 8765 websocket).

PORT="${PORT:-8501}"

# Start backend (WebSocket + HTTP health on 8766) in background
echo "Starting backend agency server..."
cd /app/backend
python /app/backend/agency_server.py &
BACKEND_PID=$!

# Wait for backend health (HTTP on 8766)
echo "Waiting for backend health on :8766..."
for i in $(seq 1 20); do
    if curl -sf http://localhost:8766/health >/dev/null 2>&1; then
        echo "✅ Backend healthy"
        break
    fi
    sleep 1
done

# Start Streamlit dashboard on $PORT (streams real-time via WebSocket to backend)
echo "Starting Streamlit dashboard on port $PORT..."
cd /app/dashboard
export STREAMLIT_SERVER_PORT=$PORT
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_HEADLESS=true
exec python -m streamlit run agency_dashboard.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false