import asyncio
import subprocess
import sys
import os
import time
import threading
from pathlib import Path

# Add the backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

def run_backend():
    """Run the agency backend server"""
    os.chdir(str(Path(__file__).parent / "backend"))
    os.system(f'"{sys.executable}" agency_server.py')

def run_dashboard():
    """Run the Streamlit dashboard"""
    os.chdir(str(Path(__file__).parent / "dashboard"))
    os.system(f'"{sys.executable}" -m streamlit run agency_dashboard.py --server.port 8501 --server.headless true')

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║              🏢 TATKHALSA AI AGENCY - 24/7 LAUNCHER              ║
║                                                                   ║
║  Starting:                                                        ║
║  • Backend Agency Server (WebSocket: localhost:8765)             ║
║  • Live Dashboard (HTTP: localhost:8501)                          ║
║                                                                   ║
║  Agents: 14 autonomous agents across 4 departments               ║
║  Features: Live token tracking, real-time logs, task board       ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    # Start backend in background thread
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    print("✅ Backend agency server starting on ws://localhost:8765")
    time.sleep(3)
    
    # Start dashboard (blocking)
    print("✅ Dashboard starting on http://localhost:8501")
    print("\n📊 Open your browser to: http://localhost:8501")
    print("🔴 Press Ctrl+C to stop the agency\n")
    
    try:
        run_dashboard()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Tatkhalsa AI Agency...")