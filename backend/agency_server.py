import asyncio
import json
import os
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum

import websockets
from aiohttp import web

STATE_FILE = os.path.expanduser("~/tatkhalsa-agency/state/agency_state.json")
LOG_FILE = os.path.expanduser("~/tatkhalsa-agency/logs/agency.log")

# Token pricing (approximate)
TOKEN_PRICING = {
    "gpt-4o": {"input": 0.005 / 1000, "output": 0.015 / 1000},
    "gpt-4o-mini": {"input": 0.00015 / 1000, "output": 0.0006 / 1000},
}

class AgentStatus(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    WAITING = "waiting"
    ERROR = "error"

@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_cost: float = 0.0
    model: str = "gpt-4o-mini"

@dataclass
class AgentTask:
    id: str
    agent_id: str
    department: str
    description: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[str] = None
    token_usage: Optional[TokenUsage] = None

# Default state structure
DEFAULT_STATE = {
    "agency": {
        "name": "Tatkhalsa AI Agency",
        "version": "2.0",
        "departments": {
            "executive": {
                "name": "Executive Office",
                "agents": {
                    "ceo": {"name": "CEO Agent", "role": "Strategic Planning & Goal Management", "status": "idle", "current_task": None},
                    "manager": {"name": "Operations Manager", "role": "Task Assignment & Coordination", "status": "idle", "current_task": None}
                }
            },
            "growth": {
                "name": "Growth Department (SEO/AEO/GEO)",
                "agents": {
                    "seo_lead": {"name": "Senior SEO Lead", "role": "Technical SEO & Strategy", "status": "idle", "current_task": None},
                    "seo_specialist": {"name": "SEO Specialist", "role": "On-page & Technical Optimization", "status": "idle", "current_task": None},
                    "aeo_specialist": {"name": "AEO Specialist", "role": "Answer Engine Optimization", "status": "idle", "current_task": None},
                    "geo_specialist": {"name": "GEO Specialist", "role": "Generative Engine Optimization", "status": "idle", "current_task": None},
                    "researcher": {"name": "Social Media Researcher", "role": "Trend Analysis & Competitor Intel", "status": "idle", "current_task": None}
                }
            },
            "content": {
                "name": "Content & Design Department",
                "agents": {
                    "designer": {"name": "Web Designer", "role": "UI/UX & Landing Pages", "status": "idle", "current_task": None},
                    "frontend_dev": {"name": "Frontend Developer", "role": "Implementation & Deployment", "status": "idle", "current_task": None},
                    "content_strategist": {"name": "Content Strategist", "role": "Copywriting & Messaging", "status": "idle", "current_task": None},
                    "social_media": {"name": "Social Media Manager", "role": "Content Creation & Scheduling", "status": "idle", "current_task": None}
                }
            },
            "intelligence": {
                "name": "Intelligence & Operations",
                "agents": {
                    "data_analyst": {"name": "Data Analyst", "role": "Metrics & Performance Tracking", "status": "idle", "current_task": None},
                    "logistics": {"name": "Logistics Coordinator", "role": "Blood Drive Operations", "status": "idle", "current_task": None},
                    "donor_relations": {"name": "Donor Relations", "role": "Outreach & Retention", "status": "idle", "current_task": None},
                    "grant_researcher": {"name": "Grant Researcher", "role": "Funding Opportunities", "status": "idle", "current_task": None}
                }
            }
        },
        "metrics": {
            "total_tokens_today": 0,
            "total_cost_today": 0.0,
            "tasks_completed": 0,
            "uptime_seconds": 0
        },
        "projects": [],
        "logs": []
    }
}

class AgencyState:
    def __init__(self):
        self.state = self.load_state()
        self.websocket_clients = set()
        self.running = True
        self.start_time = time.time()
    
    def load_state(self) -> Dict:
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    loaded = json.load(f)
                return self._merge_defaults(loaded, DEFAULT_STATE)
            except Exception as e:
                print(f"Error loading state: {e}, using defaults")
                return DEFAULT_STATE.copy()
        return DEFAULT_STATE.copy()
    
    def _merge_defaults(self, loaded: Dict, defaults: Dict) -> Dict:
        result = defaults.copy()
        for key, value in loaded.items():
            if key in result and isinstance(value, dict) and isinstance(result[key], dict):
                result[key] = self._merge_defaults(value, result[key])
            else:
                result[key] = value
        return result
    
    def save_state(self):
        self.state["agency"]["metrics"]["uptime_seconds"] = int(time.time() - self.start_time)
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")
    
    def log(self, level: str, agent: str, message: str, tokens: TokenUsage = None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "agent": agent,
            "message": message,
            "tokens": asdict(tokens) if tokens else None
        }
        self.state["agency"]["logs"].insert(0, entry)
        if len(self.state["agency"]["logs"]) > 500:
            self.state["agency"]["logs"] = self.state["agency"]["logs"][:500]
        
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(f"[{entry['timestamp']}] [{level}] [{agent}] {message}\n")
        except:
            pass
        
        asyncio.create_task(self.broadcast({"type": "log", "data": entry}))
    
    def update_agent_status(self, dept: str, agent_id: str, status: str, task: str = None):
        try:
            if dept in self.state["agency"]["departments"] and agent_id in self.state["agency"]["departments"][dept]["agents"]:
                self.state["agency"]["departments"][dept]["agents"][agent_id]["status"] = status
                if task:
                    self.state["agency"]["departments"][dept]["agents"][agent_id]["current_task"] = task
                self.save_state()
                asyncio.create_task(self.broadcast({"type": "agent_update", "data": {
                    "department": dept, "agent_id": agent_id, "status": status, "task": task
                }}))
        except Exception as e:
            print(f"Error updating agent status: {e}")
    
    def add_token_usage(self, agent: str, usage: TokenUsage):
        self.state["agency"]["metrics"]["total_tokens_today"] += usage.input_tokens + usage.output_tokens
        self.state["agency"]["metrics"]["total_cost_today"] += usage.total_cost
        self.save_state()
        asyncio.create_task(self.broadcast({"type": "metrics_update", "data": self.state["agency"]["metrics"]}))
    
    def add_task(self, task: AgentTask):
        self.state["agency"]["projects"].insert(0, asdict(task))
        if len(self.state["agency"]["projects"]) > 100:
            self.state["agency"]["projects"] = self.state["agency"]["projects"][:100]
        self.save_state()
        asyncio.create_task(self.broadcast({"type": "task_added", "data": asdict(task)}))
    
    def update_task(self, task_id: str, updates: Dict):
        for task in self.state["agency"]["projects"]:
            if task["id"] == task_id:
                task.update(updates)
                break
        self.save_state()
        asyncio.create_task(self.broadcast({"type": "task_updated", "data": {"id": task_id, **updates}}))
    
    async def register_client(self, websocket):
        self.websocket_clients.add(websocket)
        try:
            await websocket.send(json.dumps({"type": "full_state", "data": self.state}))
        except:
            pass
    
    async def unregister_client(self, websocket):
        self.websocket_clients.discard(websocket)
    
    async def broadcast(self, message: Dict):
        if self.websocket_clients:
            dead = set()
            for client in self.websocket_clients:
                try:
                    await client.send(json.dumps(message))
                except:
                    dead.add(client)
            for d in dead:
                self.websocket_clients.discard(d)

# Global state instance
agency = AgencyState()

# ===== AGENT BASE CLASS =====
class BaseAgent:
    def __init__(self, department: str, agent_id: str, name: str, role: str):
        self.department = department
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.running = True
    
    async def think(self, task: str) -> Dict:
        return {"result": "Task completed", "tokens": TokenUsage()}
    
    async def run_loop(self):
        while self.running:
            try:
                tasks = agency.state.get("agency", {}).get("projects", [])
                my_tasks = [t for t in tasks if t.get("agent_id") == self.agent_id and t.get("status") == "assigned"]
                
                if my_tasks:
                    task = my_tasks[0]
                    agency.update_agent_status(self.department, self.agent_id, AgentStatus.THINKING.value, task.get("description", ""))
                    agency.update_task(task["id"], {"status": "in_progress", "started_at": datetime.now().isoformat()})
                    
                    agency.log("INFO", self.name, f"Starting task: {task.get('description', '')}")
                    
                    agency.update_agent_status(self.department, self.agent_id, AgentStatus.WORKING.value, task.get("description", ""))
                    
                    result = await self.think(task.get("description", ""))
                    
                    usage = result.get("tokens", TokenUsage(input_tokens=100, output_tokens=50, model="gpt-4o-mini"))
                    usage.total_cost = (usage.input_tokens * TOKEN_PRICING[usage.model]["input"] + 
                                        usage.output_tokens * TOKEN_PRICING[usage.model]["output"])
                    
                    agency.add_token_usage(self.name, usage)
                    agency.update_task(task["id"], {
                        "status": "completed",
                        "completed_at": datetime.now().isoformat(),
                        "result": result.get("result", "Done"),
                        "token_usage": asdict(usage)
                    })
                    
                    agency.state["agency"]["metrics"]["tasks_completed"] += 1
                    agency.log("SUCCESS", self.name, f"Completed: {task.get('description', '')}", usage)
                
                agency.update_agent_status(self.department, self.agent_id, AgentStatus.IDLE.value)
                
            except Exception as e:
                agency.log("ERROR", self.name, f"Error in loop: {str(e)}")
                agency.update_agent_status(self.department, self.agent_id, AgentStatus.ERROR.value)
            
            await asyncio.sleep(5)

# ===== SPECIFIC AGENTS =====
class CEOAgent(BaseAgent):
    async def think(self, task: str) -> Dict:
        await asyncio.sleep(2)
        return {
            "result": f"Strategic decision made: {task}. Assigned to relevant departments.",
            "tokens": TokenUsage(input_tokens=200, output_tokens=100, model="gpt-4o")
        }

class ManagerAgent(BaseAgent):
    async def think(self, task: str) -> Dict:
        await asyncio.sleep(1)
        return {
            "result": f"Task delegated: {task}",
            "tokens": TokenUsage(input_tokens=150, output_tokens=80, model="gpt-4o-mini")
        }

class SEOAgent(BaseAgent):
    async def think(self, task: str) -> Dict:
        await asyncio.sleep(3)
        return {
            "result": f"SEO optimization complete for: {task}",
            "tokens": TokenUsage(input_tokens=300, output_tokens=200, model="gpt-4o-mini")
        }

class AEOAgent(BaseAgent):
    async def think(self, task: str) -> Dict:
        await asyncio.sleep(3)
        return {
            "result": f"AEO optimization complete: {task}",
            "tokens": TokenUsage(input_tokens=300, output_tokens=200, model="gpt-4o-mini")
        }

class GEOAgent(BaseAgent):
    async def think(self, task: str) -> Dict:
        await asyncio.sleep(3)
        return {
            "result": f"GEO optimization complete: {task}",
            "tokens": TokenUsage(input_tokens=300, output_tokens=200, model="gpt-4o-mini")
        }

class DesignerAgent(BaseAgent):
    async def think(self, task: str) -> Dict:
        await asyncio.sleep(4)
        return {
            "result": f"Design completed: {task}",
            "tokens": TokenUsage(input_tokens=400, output_tokens=300, model="gpt-4o")
        }

class ContentAgent(BaseAgent):
    async def think(self, task: str) -> Dict:
        await asyncio.sleep(2)
        return {
            "result": f"Content created: {task}",
            "tokens": TokenUsage(input_tokens=250, output_tokens=150, model="gpt-4o-mini")
        }

class DataAnalystAgent(BaseAgent):
    async def think(self, task: str) -> Dict:
        await asyncio.sleep(3)
        return {
            "result": f"Analysis complete: {task}",
            "tokens": TokenUsage(input_tokens=350, output_tokens=200, model="gpt-4o-mini")
        }

class ResearcherAgent(BaseAgent):
    async def think(self, task: str) -> Dict:
        await asyncio.sleep(4)
        return {
            "result": f"Research complete: {task}",
            "tokens": TokenUsage(input_tokens=500, output_tokens=300, model="gpt-4o")
        }

# ===== AGENT REGISTRY =====
def create_agents():
    agents = []
    
    agents.append(CEOAgent("executive", "ceo", "CEO Agent", "Strategic Planning"))
    agents.append(ManagerAgent("executive", "manager", "Operations Manager", "Task Coordination"))
    
    agents.append(SEOAgent("growth", "seo_lead", "Senior SEO Lead", "SEO Strategy"))
    agents.append(SEOAgent("growth", "seo_specialist", "SEO Specialist", "Technical SEO"))
    agents.append(AEOAgent("growth", "aeo_specialist", "AEO Specialist", "Answer Engine Opt"))
    agents.append(GEOAgent("growth", "geo_specialist", "GEO Specialist", "Generative Engine Opt"))
    agents.append(ResearcherAgent("growth", "researcher", "Social Media Researcher", "Trend Analysis"))
    
    agents.append(DesignerAgent("content", "designer", "Web Designer", "UI/UX Design"))
    agents.append(ContentAgent("content", "frontend_dev", "Frontend Developer", "Implementation"))
    agents.append(ContentAgent("content", "content_strategist", "Content Strategist", "Copywriting"))
    agents.append(ContentAgent("content", "social_media", "Social Media Manager", "Scheduling"))
    
    agents.append(DataAnalystAgent("intelligence", "data_analyst", "Data Analyst", "Metrics"))
    agents.append(DataAnalystAgent("intelligence", "logistics", "Logistics Coordinator", "Operations"))
    agents.append(ContentAgent("intelligence", "donor_relations", "Donor Relations", "Outreach"))
    agents.append(ResearcherAgent("intelligence", "grant_researcher", "Grant Researcher", "Funding"))
    
    return agents

# ===== TASK GENERATOR =====
async def task_generator():
    task_templates = [
        ("growth", "seo_specialist", "Optimize meta tags for blood donation pages"),
        ("growth", "aeo_specialist", "Structure FAQ schema for 'blood donation Punjab' queries"),
        ("growth", "geo_specialist", "Optimize content for AI citation on donation eligibility"),
        ("growth", "researcher", "Research competitor NGO content strategies"),
        ("content", "designer", "Design new hero section for emergency blood appeals"),
        ("content", "content_strategist", "Write donor thank-you email sequence"),
        ("content", "social_media", "Create Instagram carousel for blood type compatibility"),
        ("intelligence", "data_analyst", "Analyze donor retention metrics for Q3"),
        ("intelligence", "logistics", "Plan blood drive schedule for next month"),
        ("intelligence", "grant_researcher", "Research CSR funding opportunities in Punjab"),
    ]
    
    while agency.running:
        await asyncio.sleep(30)
        import random
        dept, agent_id, desc = random.choice(task_templates)
        
        task = AgentTask(
            id=str(uuid.uuid4())[:8],
            agent_id=agent_id,
            department=dept,
            description=desc,
            status="assigned",
            created_at=datetime.now().isoformat()
        )
        agency.add_task(task)
        agency.log("INFO", "System", f"New task assigned to {agent_id}: {desc}")

# ===== WEBSOCKET SERVER =====
async def websocket_handler(websocket):
    await agency.register_client(websocket)
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get("type") == "assign_task":
                    task = AgentTask(
                        id=str(uuid.uuid4())[:8],
                        agent_id=data["agent_id"],
                        department=data["department"],
                        description=data["description"],
                        status="assigned",
                        created_at=datetime.now().isoformat()
                    )
                    agency.add_task(task)
            except:
                pass
    except:
        pass
    finally:
        await agency.unregister_client(websocket)

# ===== HTTP HEALTH CHECK =====
async def health_check(request):
    return web.json_response({
        "status": "healthy",
        "uptime": int(time.time() - agency.start_time),
        "agents": len([a for d in agency.state["agency"]["departments"].values() for a in d["agents"].values()]),
        "tasks_pending": len([p for p in agency.state["agency"]["projects"] if p.get("status") == "assigned"]),
        "tasks_in_progress": len([p for p in agency.state["agency"]["projects"] if p.get("status") == "in_progress"])
    })

async def start_http_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8766)
    await site.start()
    print("✅ HTTP health server running on http://0.0.0.0:8766")

# ===== MAIN =====
async def main():
    print("🏢 Starting Tatkhalsa AI Agency...")
    
    # Start HTTP health server
    await start_http_server()
    
    # Start all agents
    agents = create_agents()
    agent_tasks = [asyncio.create_task(a.run_loop()) for a in agents]
    
    # Start task generator
    generator_task = asyncio.create_task(task_generator())
    
    # Start WebSocket server
    ws_server = await websockets.serve(websocket_handler, "0.0.0.0", 8765)
    
    agency.log("INFO", "System", "Tatkhalsa AI Agency started - 24/7 mode active")
    print("✅ Agency backend running on ws://0.0.0.0:8765")
    print("✅ Health check on http://0.0.0.0:8766/health")
    
    try:
        await asyncio.gather(*agent_tasks, generator_task, ws_server.wait_closed())
    except KeyboardInterrupt:
        agency.running = False
        for a in agents:
            a.running = False

if __name__ == "__main__":
    asyncio.run(main())