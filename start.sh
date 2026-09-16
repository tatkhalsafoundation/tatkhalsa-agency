#!/bin/bash
# Start script for Tatkhalsa AI Agency

set -e

echo "🏢 Starting Tatkhalsa AI Agency..."

# Start backend in background
echo "Starting backend agency server..."
cd /app/backend
python agency_server.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Check if backend is running
if ! curl -f http://localhost:8765/health 2>/dev/null; then
    # Try WebSocket connection test
    python -c "
import asyncio
import websockets
async def test():
    try:
        async with websockets.connect('ws://localhost:8765') as ws:
            await ws.send('{\"type\": \"ping\"}')
            resp = await ws.recv()
            print('Backend WebSocket OK')
    except Exception as e:
        print('Backend not ready:', e)
        exit(1)
asyncio.run(test())
" || exit 1
fi

echo "✅ Backend running on ws://localhost:8765"

# Start Streamlit dashboard
echo "Starting Streamlit dashboard..."
cd /app/dashboard
exec streamlit run agency_dashboard.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --browser.gatherUsageStats=false