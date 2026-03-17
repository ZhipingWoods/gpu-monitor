"""
GPU Monitor Configuration
"""
import os
import socket

# Server Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'gpu-monitor-secret-key-change-in-production')
HOST = '0.0.0.0'
PORT = int(os.getenv('PORT', '1312'))
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

# Demo Mode (for Vercel deployment without GPU)
DEMO_MODE = os.getenv('DEMO_MODE', 'false').lower() == 'true'

# Simple Authentication - Add users here
# Format: {'username': 'password', ...}
USERS = {
    'admin': 'admin123',
    'gpuadmin': 'gpu2024',
}

# Demo Mode Users (only active when DEMO_MODE=true)
DEMO_USERS = {
    'demo': 'demo123',
    'admin': 'admin123',
}

# Session Configuration
SESSION_LIFETIME = 3600  # seconds

# Monitoring Configuration
UPDATE_INTERVAL = float(os.getenv('UPDATE_INTERVAL', '1.0'))  # Polling interval in seconds

# Multi-Node Configuration
# MODE: 'server' (runs GPU monitor), 'hub' (aggregates multiple nodes), 'client' (connects to hub)
MODE = os.getenv('GPU_MONITOR_MODE', 'hub')

# For hub mode: list of node URLs to connect to
NODE_URLS = [url.strip() for url in os.getenv('NODE_URLS', '').split(',') if url.strip()]

# For server/client mode: node name
NODE_NAME = os.getenv('NODE_NAME', socket.gethostname())

# Hub server URL (for client mode)
HUB_URL = os.getenv('HUB_URL', 'http://localhost:1312')

# GPU Monitoring
# Use nvidia-smi fallback for older GPUs
NVIDIA_SMI = os.getenv('NVIDIA_SMI', 'false').lower() == 'true'

# Filter processes with memory > threshold (MB)
MIN_PROCESS_MEMORY = int(os.getenv('MIN_PROCESS_MEMORY', '100'))