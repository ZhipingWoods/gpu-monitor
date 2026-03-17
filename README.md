# GPU Monitor

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vue-3-42b883?style=flat-square&logo=vue.js&logoColor=white" alt="Vue">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

<p align="center">
  Lightweight Multi-Server GPU Monitoring System | Real-time | User Tracking | Segmented Visualization
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README_ZH.md">中文</a> · <a href="#demo">Live Demo</a>
</p>

---

## Features

- 🔐 **Simple Authentication** - Username/password login, easy configuration
- 👥 **User Tracking** - Shows which user is using which GPU and how much memory
- 📊 **Segmented Progress Bars** - Visual representation of GPU memory by user
- 🖥️ **Multi-Server Monitoring** - Hub mode aggregates multiple node data
- 📈 **Full Metrics** - Utilization, temperature, power, clocks (expandable/collapsible)
- ⚡ **Real-time Push** - WebSocket low-latency updates
- 🐳 **Docker Support** - Quick deployment

---

## Quick Start

### Option 1: Docker Deployment (Recommended)

```bash
# Clone project
git clone https://github.com/your-repo/gpu-monitor.git
cd gpu-monitor

# Start service
docker-compose up --build
```

Visit `http://localhost:1312`

### Option 2: Local Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Modify configuration (optional)
# Edit config.py to add users:
# USERS = {
#     'admin': 'your-password',
#     'yourname': 'your-password',
# }

# 3. Start Hub server
python app.py
```

Visit `http://localhost:1312`

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GPU Monitor Hub                         │
│                        Port 1312                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Server 1   │  │  Server 2   │  │  Server N   │         │
│  │  2x2080Ti   │  │  4x3090     │  │  A100 x8    │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│    client.py        client.py        client.py              │
│         └────────────────┼────────────────┘                 │
│                          │                                  │
│                    REST API + WebSocket                     │
│                          │                                  │
│                    Browser Dashboard                        │
└─────────────────────────────────────────────────────────────┘
```

### Three Run Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `hub` | Aggregates multiple node data | Main server, displays all GPU server status |
| `server` | Local GPU monitoring | Single server, monitor local GPU |
| `client` | Client reporting | Deploy on each GPU server |

---

## Usage Guide

### 1. Start Hub Server (Monitoring Center)

Run on the main server:

```bash
# Default hub mode
python app.py
```

### 2. Run Client on Each GPU Server

```bash
# Basic usage
python client.py --server http://<Hub-IP>:1312 --name "server-name"

# Full parameters
python client.py \
  --server http://192.168.1.100:1312 \
  --name "2080Ti-Server-1" \
  --interval 1.0

# Run in background
nohup python client.py --server http://192.168.1.100:1312 --name "Server-1" &
```

### 3. Configure Node URLs (Optional)

If using REST polling mode instead of client reporting, set on Hub server:

```bash
# docker-compose.yml or environment variable
NODE_URLS=http://server1:1312,http://server2:1312,http://server3:1312
```

---

## Configuration

Edit `config.py`:

```python
# User authentication configuration
USERS = {
    'admin': 'admin123',      # Change default password!
    'gpuadmin': 'gpu2024',
    'yourname': 'your-pass',
}

# Server configuration
HOST = '0.0.0.0'
PORT = 1312                  # Port

# Monitoring configuration
UPDATE_INTERVAL = 1.0        # Update interval (seconds)
MODE = 'hub'                 # Run mode: hub / server / client

# Client configuration
HUB_URL = 'http://localhost:1312'
NODE_NAME = 'my-gpu-server'  # This server's name
```

---

## API Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/` | GET | Main page | Required |
| `/login` | GET | Login page | - |
| `/api/login` | POST | Login | - |
| `/api/logout` | POST | Logout | Required |
| `/api/me` | GET | Current user | Required |
| `/api/gpu-data` | GET | GPU data | Required |
| `/api/cluster` | GET | Cluster data | Required |
| `/api/processes` | GET | GPU processes | Required |
| `/ws` | WebSocket | Real-time push | - |

---

## Demo Mode

This project supports deployment to Vercel for online demo:

```bash
# Demo mode (uses mock data)
DEMO_MODE=true python app.py
```

Or deploy directly to Vercel - it will automatically use demo mode.

**Demo includes:**
- 4 simulated GPU servers (2080Ti, 3090, A100, V100)
- Auto-refreshing data every 5 seconds
- Full dashboard functionality
- User memory tracking visualization

**Demo Account (Auto-login in Demo Mode):**
- Username: `demo`
- Password: `demo123`

**Production Account (Configure in config.py):**
- Username: `admin`
- Password: `admin123`

---

## Tech Stack

- **Backend**: FastAPI + Uvicorn + AsyncIO
- **GPU Data**: pynvml (NVML) + gpustat
- **Frontend**: Vue 3 + Element Plus
- **Communication**: WebSocket (real-time push)
- **Deployment**: Docker, Vercel

---

## Acknowledgments

This project is built upon the following open source projects:

- **[gpu-hot](https://github.com/psalias2006/gpu-hot)** - Real-time NVIDIA GPU monitoring dashboard
  - FastAPI + AsyncIO high-performance architecture
  - Rich NVML metrics collection
  - Hub mode for multi-node aggregation

Special thanks to the authors and contributors of these projects!

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Issues & Feedback

If you have any questions or suggestions, feel free to open an issue or submit a PR.
