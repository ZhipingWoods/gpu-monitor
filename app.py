#!/usr/bin/env python3
"""
GPU Monitor - Multi-server GPU Monitoring with User Tracking
"""
import asyncio
import logging
from contextlib import asynccontextmanager
import time

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.gzip import GZipMiddleware

import config
from core import auth
from core.auth import SESSION_COOKIE_NAME, create_session, validate_session, logout_session

# Setup logging
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state
monitor = None
hub = None


def get_app_state():
    """Get the monitor or hub instance"""
    global monitor, hub
    if config.MODE == 'hub':
        return hub
    return monitor


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global monitor, hub

    logger.info(f"Starting GPU Monitor in {config.MODE} mode")

    if config.MODE == 'hub':
        # Start hub for multi-node aggregation
        from core.hub import Hub
        hub = Hub(config.NODE_URLS)
        await hub.start()

        # Register hub handlers
        from core.handlers import register_hub_handlers
        register_hub_handlers(app, hub)

    elif config.MODE == 'server':
        # Start local GPU monitor
        from core.monitor import GPUMonitor
        monitor = GPUMonitor()

        # Register handlers
        from core.handlers import register_handlers
        register_handlers(app, monitor)

    else:
        # Just serve the web interface
        logger.info("Starting in client mode (no local GPU monitoring)")

    yield

    # Cleanup
    if hub:
        await hub.shutdown()
    if monitor:
        monitor.shutdown()


# Create FastAPI app
app = FastAPI(
    title="GPU Monitor",
    description="Multi-server GPU Monitoring with User Tracking",
    version="1.0.0",
    lifespan=lifespan
)

# Add Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ============== AUTH ROUTES ==============

@app.post("/api/login")
async def login(request: Request):
    """Login endpoint"""
    try:
        data = await request.json()
    except:
        return JSONResponse({"success": False, "detail": "Invalid JSON"}, status_code=400)

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return JSONResponse({"success": False, "detail": "Missing username or password"}, status_code=400)

    # Validate credentials
    if username not in config.USERS or config.USERS[username] != password:
        return JSONResponse({"success": False, "detail": "Invalid username or password"}, status_code=401)

    # Create session
    token = create_session(username)

    response = JSONResponse({"success": True, "username": username})
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=config.SESSION_LIFETIME,
        samesite="lax"
    )

    return response


@app.post("/api/logout")
async def logout(request: Request):
    """Logout endpoint"""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        logout_session(token)

    response = JSONResponse({"success": True})
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


@app.get("/api/me")
async def get_current_user(request: Request):
    """Get current authenticated user"""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)

    session_data = validate_session(token)
    if not session_data:
        return JSONResponse({"detail": "Invalid or expired session"}, status_code=401)

    return JSONResponse({"username": session_data['username']})


# ============== DATA ROUTES ==============

@app.get("/api/gpu-data")
async def get_gpu_data(request: Request):
    """Get current GPU data (requires auth)"""
    # Check auth
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token or not validate_session(token):
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)

    state = get_app_state()

    if config.MODE == 'hub' and hub:
        # In hub mode, return cluster data
        data = await hub.get_cluster_data()
        return JSONResponse({
            "gpus": {},
            "cluster_stats": data.get("cluster_stats", {}),
            "nodes": data.get("nodes", {}),
            "timestamp": time.time()
        })

    if monitor:
        gpus = await monitor.get_gpu_data()
        return JSONResponse({
            "gpus": gpus,
            "timestamp": time.time()
        })

    return JSONResponse({"gpus": {}, "timestamp": time.time()})


@app.get("/api/processes")
async def get_processes(request: Request):
    """Get GPU processes"""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token or not validate_session(token):
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)

    if monitor:
        processes = await monitor.get_processes()
        return JSONResponse({"processes": processes})

    return JSONResponse({"processes": []})


@app.get("/api/system")
async def get_system_info(request: Request):
    """Get system info"""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token or not validate_session(token):
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)

    if monitor:
        system = await monitor.get_system_info()
        return JSONResponse(system)

    return JSONResponse({})


@app.get("/api/cluster")
async def get_cluster(request: Request):
    """Get cluster data (hub mode)"""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token or not validate_session(token):
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)

    if not hub:
        return JSONResponse({"detail": "Not in hub mode"}, status_code=400)

    data = await hub.get_cluster_data()
    return JSONResponse(data)


@app.post("/api/report")
async def receive_node_report(request: Request):
    """Receive GPU data from client nodes"""
    try:
        data = await request.json()
    except:
        return JSONResponse({"detail": "Invalid JSON"}, status_code=400)

    node_name = data.get('node_name')
    gpus = data.get('gpus', {})
    system = data.get('system', {})

    if not node_name:
        return JSONResponse({"detail": "Missing node_name"}, status_code=400)

    if hub and node_name in hub.nodes:
        hub.nodes[node_name]['gpus'] = gpus
        hub.nodes[node_name]['system'] = system
        hub.nodes[node_name]['status'] = 'online'
        hub.nodes[node_name]['last_update'] = data.get('timestamp')

    return JSONResponse({"status": "ok"})


# ============== PAGE ROUTES ==============

@app.get("/")
async def index(request: Request):
    """Main dashboard page"""
    # Check if authenticated
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token or not validate_session(token):
        # Redirect to login
        with open("templates/login.html", "r") as f:
            return HTMLResponse(content=f.read())

    # Serve dashboard (index for normal, demo for demo mode)
    template = "templates/demo.html" if config.DEMO_MODE else "templates/index.html"
    with open(template, "r") as f:
        return HTMLResponse(content=f.read())


@app.get("/login")
async def login_page(request: Request):
    """Login page"""
    with open("templates/login.html", "r") as f:
        return HTMLResponse(content=f.read())


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# ============== DEMO MODE ROUTES ==============
# For Vercel deployment without GPU access
if config.DEMO_MODE:
    import demo_data
    from core.auth import create_session

    # Demo auto-login endpoint
    @app.get("/api/demo/login")
    async def demo_auto_login():
        """Auto-login for demo mode"""
        token = create_session('demo')
        response = JSONResponse({
            "success": True,
            "username": "demo",
            "demo_mode": True
        })
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=token,
            httponly=True,
            max_age=3600,
            samesite="lax"
        )
        return response

    @app.get("/demo")
    async def demo_page():
        """Demo page without authentication"""
        with open("templates/demo.html", "r") as f:
            return HTMLResponse(content=f.read())

    @app.get("/api/demo/cluster")
    async def demo_cluster():
        """Demo cluster data"""
        return JSONResponse(demo_data.generate_demo_cluster_data())

    @app.get("/api/demo/gpu-data")
    async def demo_gpu_data():
        """Demo GPU data"""
        return JSONResponse(demo_data.generate_demo_gpu_data())

    # Override main routes to bypass auth in demo mode
    @app.get("/")
    async def index_demo(request: Request):
        """Demo dashboard page"""
        with open("templates/demo.html", "r") as f:
            return HTMLResponse(content=f.read())

    @app.get("/api/gpu-data")
    async def get_gpu_data_demo():
        """Get demo GPU data"""
        return JSONResponse(demo_data.generate_demo_gpu_data())

    @app.get("/api/cluster")
    async def get_cluster_demo():
        """Get demo cluster data"""
        return JSONResponse(demo_data.generate_demo_cluster_data())

    logger.info("Demo mode enabled - serving mock data")

# ============== MAIN ==============

if __name__ == '__main__':
    import uvicorn

    logger.info(f"Starting GPU Monitor on {config.HOST}:{config.PORT}")
    logger.info(f"Mode: {config.MODE}")

    if config.MODE == 'hub':
        logger.info(f"Hub URLs: {config.NODE_URLS}")

    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")