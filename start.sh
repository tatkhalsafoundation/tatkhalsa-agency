#!/bin/bash
# Start script for Tatkhalsa AI Agency (file-based daemon, single-port Streamlit)

set -e
echo "🏢 Starting Tatkhalsa AI Agency..."

# Railway provides $PORT (the single exposed port). Streamlit serves the dashboard.
PORT="${PORT:-8501}"

# Ensure state/log dirs exist
mkdir -p /app/state /app/logs

# Start the agent daemon in the background (writes state to /app/state JSON)
echo "Starting agent daemon..."
cd /app
python /app/backend/agency_server.py &
BACKEND_PID=$!
echo "Agent daemon PID: $BACKEND_PID"

sleep 3

# Start Streamlit dashboard on $PORT — the ONLY internet-facing process
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