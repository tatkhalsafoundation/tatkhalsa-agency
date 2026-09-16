import streamlit as st
import asyncio
import json
import time
import threading
from datetime import datetime
from pathlib import Path
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# Page config
st.set_page_config(
    page_title="Tatkhalsa AI Agency - Live Command Center",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load auth config
def load_auth_config():
    config_path = Path(__file__).parent / "auth_config.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.load(f, Loader=SafeLoader)
    return None

# Authentication
auth_config = load_auth_config()
if auth_config:
    authenticator = stauth.Authenticate(
        auth_config['credentials'],
        auth_config['cookie']['name'],
        auth_config['cookie']['key'],
        auth_config['cookie']['expiry_days'],
        auth_config['preauthorized']
    )
    
    name, authentication_status, username = authenticator.login('main')
    
    if authentication_status == False:
        st.error('Username/password is incorrect')
        st.stop()
    elif authentication_status == None:
        st.warning('Please enter your username and password')
        st.stop()
    elif authentication_status:
        # User is authenticated - show logout in sidebar
        with st.sidebar:
            authenticator.logout('Logout', 'main')
            st.write(f'Welcome *{name}*')
else:
    st.error("Authentication not configured. Please contact admin.")
    st.stop()

# Custom CSS for the agency look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --bg-primary: #0a0f1a;
        --bg-secondary: #111827;
        --bg-card: #1a2234;
        --border: #2a3a5a;
        --text-primary: #e8edf5;
        --text-secondary: #8b9dc3;
        --accent-cyan: #00d4aa;
        --accent-blue: #3b82f6;
        --accent-amber: #fbbf24;
        --accent-red: #ef4444;
        --accent-purple: #a855f7;
    }
    
    .stApp {
        background: var(--bg-primary);
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    ::-webkit-scrollbar {width: 8px; height: 8px;}
    ::-webkit-scrollbar-track {background: var(--bg-primary);}
    ::-webkit-scrollbar-thumb {background: var(--border); border-radius: 4px;}
    ::-webkit-scrollbar-thumb:hover {background: var(--text-secondary);}
    
    .metric-card {
        background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-secondary) 100%);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        border-color: var(--accent-cyan);
        box-shadow: 0 8px 32px rgba(0, 212, 170, 0.1);
    }
    .metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--text-secondary);
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-primary);
    }
    .metric-value.tokens { color: var(--accent-cyan); }
    .metric-value.cost { color: var(--accent-amber); }
    .metric-value.tasks { color: var(--accent-blue); }
    .metric-value.uptime { color: var(--accent-purple); }
    
    .agent-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
    }
    .agent-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: var(--status-color, var(--border));
    }
    .agent-card.working::before { background: var(--accent-cyan); }
    .agent-card.thinking::before { background: var(--accent-amber); }
    .agent-card.idle::before { background: var(--border); }
    .agent-card.error::before { background: var(--accent-red); }
    .agent-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.5rem;
    }
    .agent-avatar {
        width: 36px;
        height: 36px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border);
    }
    .agent-info { flex: 1; }
    .agent-name {
        font-weight: 600;
        font-size: 0.9rem;
        color: var(--text-primary);
    }
    .agent-role {
        font-size: 0.7rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .status-badge {
        font-size: 0.65rem;
        font-weight: 600;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .status-working { background: rgba(0, 212, 170, 0.2); color: var(--accent-cyan); }
    .status-thinking { background: rgba(251, 191, 36, 0.2); color: var(--accent-amber); }
    .status-idle { background: rgba(139, 157, 195, 0.2); color: var(--text-secondary); }
    .status-error { background: rgba(239, 68, 68, 0.2); color: var(--accent-red); }
    .agent-task {
        font-size: 0.75rem;
        color: var(--text-secondary);
        padding-top: 0.5rem;
        border-top: 1px solid var(--border);
        margin-top: 0.5rem;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .dept-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border);
    }
    .dept-icon {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.25rem;
    }
    .dept-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    .dept-subtitle {
        font-size: 0.75rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    .log-container {
        background: var(--bg-primary);
        border: 1px solid var(--border);
        border-radius: 10px;
        height: 400px;
        overflow-y: auto;
        padding: 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        line-height: 1.6;
    }
    .log-entry {
        padding: 0.25rem 0;
        border-bottom: 1px solid rgba(42, 58, 90, 0.5);
    }
    .log-entry:last-child { border-bottom: none; }
    .log-time { color: var(--text-secondary); }
    .log-level { font-weight: 600; padding: 0 0.5rem; }
    .log-info { color: var(--accent-blue); }
    .log-success { color: var(--accent-cyan); }
    .log-warning { color: var(--accent-amber); }
    .log-error { color: var(--accent-red); }
    .log-agent { color: var(--accent-purple); font-weight: 500; }
    .log-message { color: var(--text-primary); }
    
    .task-board {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1rem;
    }
    .task-column {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 1rem;
    }
    .task-column-title {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--text-secondary);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border);
    }
    .task-item {
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        font-size: 0.8rem;
    }
    .task-agent {
        font-size: 0.65rem;
        color: var(--text-secondary);
        margin-bottom: 0.25rem;
    }
    .task-desc { color: var(--text-primary); }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    .pulse { animation: pulse 2s infinite; }
    
    .live-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--accent-cyan);
    }
    .live-dot {
        width: 8px;
        height: 8px;
        background: var(--accent-cyan);
        border-radius: 50%;
        animation: pulse 1.5s infinite;
    }
    
    .burn-rate {
        background: linear-gradient(90deg, var(--accent-cyan), var(--accent-blue));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
    }
    
    .stButton > button {
        background: var(--bg-card);
        border: 1px solid var(--border);
        color: var(--text-primary);
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        border-color: var(--accent-cyan);
        background: rgba(0, 212, 170, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'ws_connected' not in st.session_state:
    st.session_state.ws_connected = False
if 'agency_state' not in st.session_state:
    st.session_state.agency_state = {}
if 'last_update' not in st.session_state:
    st.session_state.last_update = 0

# Department configurations
DEPARTMENTS = {
    "executive": {
        "name": "Executive Office",
        "icon": "🎯",
        "color": "#a855f7",
        "agents": ["ceo", "manager"]
    },
    "growth": {
        "name": "Growth Department (SEO/AEO/GEO)",
        "icon": "📈",
        "color": "#3b82f6",
        "agents": ["seo_lead", "seo_specialist", "aeo_specialist", "geo_specialist", "researcher"]
    },
    "content": {
        "name": "Content & Design Department",
        "icon": "🎨",
        "color": "#ec4899",
        "agents": ["designer", "frontend_dev", "content_strategist", "social_media"]
    },
    "intelligence": {
        "name": "Intelligence & Operations",
        "icon": "🧠",
        "color": "#00d4aa",
        "agents": ["data_analyst", "logistics", "donor_relations", "grant_researcher"]
    }
}

AGENT_DISPLAY = {
    "ceo": {"name": "CEO Agent", "role": "Strategic Planning", "emoji": "👑"},
    "manager": {"name": "Operations Manager", "role": "Task Coordination", "emoji": "📋"},
    "seo_lead": {"name": "Senior SEO Lead", "role": "SEO Strategy", "emoji": "🎯"},
    "seo_specialist": {"name": "SEO Specialist", "role": "Technical SEO", "emoji": "🔍"},
    "aeo_specialist": {"name": "AEO Specialist", "role": "Answer Engine Opt", "emoji": "💬"},
    "geo_specialist": {"name": "GEO Specialist", "role": "Generative Engine Opt", "emoji": "🤖"},
    "researcher": {"name": "Social Media Researcher", "role": "Trend Analysis", "emoji": "🔬"},
    "designer": {"name": "Web Designer", "role": "UI/UX Design", "emoji": "🎨"},
    "frontend_dev": {"name": "Frontend Developer", "role": "Implementation", "emoji": "💻"},
    "content_strategist": {"name": "Content Strategist", "role": "Copywriting", "emoji": "✍️"},
    "social_media": {"name": "Social Media Manager", "role": "Scheduling", "emoji": "📱"},
    "data_analyst": {"name": "Data Analyst", "role": "Metrics", "emoji": "📊"},
    "logistics": {"name": "Logistics Coordinator", "role": "Operations", "emoji": "🚚"},
    "donor_relations": {"name": "Donor Relations", "role": "Outreach", "emoji": "🤝"},
    "grant_researcher": {"name": "Grant Researcher", "role": "Funding", "emoji": "💰"},
}

def load_state_file():
    """Load state from JSON file"""
    state_file = Path("/app/state/agency_state.json")
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def render_metric_card(label, value, css_class, help_text=None):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value {css_class}">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def render_agent_card(agent_id, agent_data, dept_info):
    display = AGENT_DISPLAY.get(agent_id, {"name": agent_id, "role": "Agent", "emoji": "🤖"})
    status = agent_data.get("status", "idle")
    current_task = agent_data.get("current_task")
    
    status_class = f"status-{status}"
    
    task_html = ""
    if current_task:
        task_html = f'<div class="agent-task">📋 {current_task[:80]}{"..." if len(current_task) > 80 else ""}</div>'
    
    st.markdown(f"""
    <div class="agent-card {status}">
        <div class="agent-header">
            <div class="agent-avatar">{display['emoji']}</div>
            <div class="agent-info">
                <div class="agent-name">{display['name']}</div>
                <div class="agent-role">{display['role']}</div>
            </div>
            <span class="status-badge {status_class}">{status}</span>
        </div>
        {task_html}
    </div>
    """, unsafe_allow_html=True)

def render_logs(logs):
    if not logs:
        return "<div style='color: var(--text-secondary); padding: 1rem; text-align: center;'>Waiting for agent activity...</div>"
    
    html = '<div class="log-container">'
    for log in logs[:50]:
        level = log.get("level", "INFO")
        level_class = f"log-{level.lower()}"
        timestamp = log.get("timestamp", "")[11:23] if log.get("timestamp") else ""
        agent = log.get("agent", "System")
        message = log.get("message", "")
        
        html += f"""
        <div class="log-entry">
            <span class="log-time">[{timestamp}]</span>
            <span class="log-level {level_class}">[{level}]</span>
            <span class="log-agent">[{agent}]</span>
            <span class="log-message">{message}</span>
        </div>
        """
    html += '</div>'
    return html

# Header
col1, col2, col3 = st.columns([3, 2, 1])
with col1:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 1rem;">
        <div style="font-size: 2rem;">🏢</div>
        <div>
            <h1 style="margin: 0; font-size: 1.5rem; font-weight: 700;">Tatkhalsa AI Agency</h1>
            <div style="font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.1em;">24/7 Autonomous Operations</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown('<div class="live-indicator"><span class="live-dot"></span>LIVE AGENCY OPERATIONS</div>', unsafe_allow_html=True)

with col3:
    if st.button("🔄 Refresh State", use_container_width=True):
        st.session_state.agency_state = load_state_file()
        st.session_state.last_update = time.time()
        st.rerun()

# Load state
state = load_state_file()
if state:
    st.session_state.agency_state = state

metrics = state.get("agency", {}).get("metrics", {})
departments = state.get("agency", {}).get("departments", {})
projects = state.get("agency", {}).get("projects", [])
logs = state.get("agency", {}).get("logs", [])

# Top Metrics Row
st.markdown("---")
mcol1, mcol2, mcol3, mcol4 = st.columns(4)
with mcol1:
    render_metric_card("TOKENS BURNED TODAY", f"{metrics.get('total_tokens_today', 0):,}", "tokens")
with mcol2:
    render_metric_card("API COST TODAY", f"${metrics.get('total_cost_today', 0):.4f}", "cost")
with mcol3:
    render_metric_card("TASKS COMPLETED", str(metrics.get('tasks_completed', 0)), "tasks")
with mcol4:
    uptime = metrics.get('uptime_seconds', 0)
    hrs, rem = divmod(uptime, 3600)
    mins, secs = divmod(rem, 60)
    render_metric_card("UPTIME", f"{hrs:02d}:{mins:02d}:{secs:02d}", "uptime")

# Token Burn Rate
if 'last_tokens' not in st.session_state:
    st.session_state.last_tokens = metrics.get('total_tokens_today', 0)
    st.session_state.last_time = time.time()

current_tokens = metrics.get('total_tokens_today', 0)
elapsed = time.time() - st.session_state.last_time
if elapsed > 0:
    burn_rate = (current_tokens - st.session_state.last_tokens) / elapsed * 60
else:
    burn_rate = 0

st.markdown(f"""
<div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 1rem; margin: 1rem 0;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <span style="color: var(--text-secondary); font-size: 0.85rem;">⚡ LIVE BURN RATE</span>
        <span class="burn-rate" style="font-size: 1.5rem;">{burn_rate:,.0f} tokens/min</span>
    </div>
    <div style="margin-top: 0.5rem; font-size: 0.75rem; color: var(--text-secondary);">Estimated hourly cost: <strong>${burn_rate * 60 * 0.00000015:.4f}</strong> (based on gpt-4o-mini pricing)</div>
</div>
""", unsafe_allow_html=True)

# Main Layout: Agents Grid + Logs
left_col, right_col = st.columns([2, 1])

with left_col:
    st.markdown("### 👥 LIVE AGENT FLEET STATUS")
    
    for dept_id, dept_info in DEPARTMENTS.items():
        dept_data = departments.get(dept_id, {})
        agents = dept_data.get("agents", {})
        
        st.markdown(f"""
        <div class="dept-header">
            <div class="dept-icon" style="background: {dept_info['color']}22; border: 1px solid {dept_info['color']}; color: {dept_info['color']};">{dept_info['icon']}</div>
            <div>
                <div class="dept-title">{dept_info['name']}</div>
                <div class="dept-subtitle">{len(agents)} agents • {sum(1 for a in agents.values() if a.get('status') == 'working')} working</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        agent_cols = st.columns(min(4, len(agents)))
        for idx, (agent_id, agent_data) in enumerate(agents.items()):
            with agent_cols[idx % len(agent_cols)]:
                render_agent_card(agent_id, agent_data, dept_info)

with right_col:
    st.markdown("### 📋 ACTIVE PROJECT BOARD")
    
    assigned = [p for p in projects if p.get("status") == "assigned"]
    in_progress = [p for p in projects if p.get("status") == "in_progress"]
    completed = [p for p in projects if p.get("status") == "completed"][:10]
    
    tab1, tab2, tab3 = st.tabs(["📥 ASSIGNED", "⚡ IN PROGRESS", "✅ COMPLETED"])
    
    with tab1:
        if assigned:
            for task in assigned[:10]:
                display = AGENT_DISPLAY.get(task.get('agent_id'), {"name": task.get('agent_id'), "emoji": "🤖"})
                st.markdown(f"""
                <div class="task-item">
                    <div class="task-agent">{display['emoji']} {display['name']}</div>
                    <div class="task-desc">{task.get('description', 'No description')}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='color: var(--text-secondary); text-align: center; padding: 2rem;'>No assigned tasks</div>", unsafe_allow_html=True)
    
    with tab2:
        if in_progress:
            for task in in_progress:
                display = AGENT_DISPLAY.get(task.get('agent_id'), {"name": task.get('agent_id'), "emoji": "🤖"})
                st.markdown(f"""
                <div class="task-item" style="border-left: 3px solid var(--accent-cyan);">
                    <div class="task-agent">{display['emoji']} {display['name']} <span class="pulse" style="color: var(--accent-cyan);">● WORKING</span></div>
                    <div class="task-desc">{task.get('description', 'No description')}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='color: var(--text-secondary); text-align: center; padding: 2rem;'>No tasks in progress</div>", unsafe_allow_html=True)
    
    with tab3:
        if completed:
            for task in completed:
                display = AGENT_DISPLAY.get(task.get('agent_id'), {"name": task.get('agent_id'), "emoji": "🤖"})
                tokens = task.get('token_usage', {})
                token_str = f" • {tokens.get('input_tokens', 0)+tokens.get('output_tokens', 0):,} tokens" if tokens else ""
                cost_str = f" • ${tokens.get('total_cost', 0):.6f}" if tokens else ""
                st.markdown(f"""
                <div class="task-item" style="border-left: 3px solid var(--accent-blue);">
                    <div class="task-agent">{display['emoji']} {display['name']}{token_str}{cost_str}</div>
                    <div class="task-desc">{task.get('description', 'No description')}</div>
                    <div style="font-size: 0.65rem; color: var(--text-secondary); margin-top: 0.25rem;">✅ {task.get('completed_at', '')[:19].replace('T', ' ')}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='color: var(--text-secondary); text-align: center; padding: 2rem;'>No completed tasks yet</div>", unsafe_allow_html=True)

# Live Logs Section
st.markdown("---")
st.markdown("### 📜 LIVE AGENT ACTIVITY STREAM")
log_html = render_logs(logs)
st.markdown(log_html, unsafe_allow_html=True)

# Auto-refresh
st.markdown("""
<script>
    setTimeout(function() {
        window.location.reload();
    }, 5000);
</script>
""", unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; padding: 1rem; color: var(--text-secondary); font-size: 0.75rem; border-top: 1px solid var(--border); margin-top: 2rem;">
    Tatkhalsa AI Agency v2.0 — Running 24/7 | Secure Admin Access
</div>
""", unsafe_allow_html=True)