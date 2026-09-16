# Tatkhalsa AI Agency - Deployment Config

## Quick Deploy to Railway

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Tatkhalsa AI Agency v2.0"
   git remote add origin https://github.com/YOUR_USERNAME/tatkhalsa-agency.git
   git push -u origin main
   ```

2. **Deploy on Railway:**
   - Go to https://railway.app
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repo
   - Railway will auto-detect Dockerfile and deploy

3. **Set Environment Variables in Railway:**
   - `STREAMLIT_SERVER_PORT` = 8501
   - `STREAMLIT_SERVER_HEADLESS` = true
   - `STREAMLIT_SERVER_ADDRESS` = 0.0.0.0

4. **Get your URL:**
   - Railway will give you a URL like `https://tatkhalsa-agency.up.railway.app`
   - Access dashboard at that URL

## Login Credentials
- **Username:** admin
- **Password:** Tatkhalsa@2024!
- **Email:** admin@tatkhalsa.in

## Custom Domain (Optional)
- In Railway project settings → Domains → Add custom domain
- Point your subdomain (e.g., `agency.tatkhalsa.in`) to Railway

## Features Included
✅ 14 autonomous agents across 4 departments  
✅ 24/7 background task processing  
✅ Live WebSocket updates  
✅ Token usage tracking with cost estimation  
✅ Secure authentication (bcrypt password)  
✅ Auto-refreshing dashboard (5s intervals)  
✅ Kanban project board  
✅ Real-time activity logs  
✅ Health check endpoint for uptime monitoring

## Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start backend
cd backend && python agency_server.py

# Start dashboard (in another terminal)
cd dashboard && streamlit run agency_dashboard.py --server.port 8501
```

## Architecture
```
┌─────────────────┐     WebSocket      ┌──────────────────┐
│  Streamlit      │ ◄─────────────────► │  Agency Backend  │
│  Dashboard      │   (port 8765)       │  (14 agents)     │
│  (port 8501)    │                     │  + HTTP Health   │
└─────────────────┘                     └──────────────────┘
```