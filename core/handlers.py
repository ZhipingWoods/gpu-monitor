"""
WebSocket Handlers for real-time data streaming
"""
import asyncio
import json
import logging
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect

import config

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept and track a new connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.debug(f"Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a connection"""
        self.active_connections.discard(websocket)
        logger.debug(f"Client disconnected. Total: {len(self.active_connections)}")

    async def send_personal(self, message: dict, websocket: WebSocket):
        """Send message to a specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to client: {e}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return

        # Create a copy to avoid modification during iteration
        connections = list(self.active_connections)

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.debug(f"Error broadcasting to client: {e}")
                self.disconnect(connection)


# Global connection manager
manager = ConnectionManager()


async def monitor_loop(monitor, interval: float = None):
    """Background loop to collect and broadcast GPU data"""
    interval = interval or config.UPDATE_INTERVAL

    while True:
        try:
            # Collect data
            gpus = await monitor.get_gpu_data()
            processes = await monitor.get_processes()
            system = await monitor.get_system_info()

            # Prepare message
            message = {
                'mode': 'default',
                'node_name': config.NODE_NAME,
                'gpus': gpus,
                'processes': processes,
                'system': system
            }

            # Broadcast to all clients
            await manager.broadcast(message)

        except Exception as e:
            logger.error(f"Error in monitor loop: {e}")

        await asyncio.sleep(interval)


async def hub_monitor_loop(hub, interval: float = None):
    """Background loop for hub mode to collect and broadcast cluster data"""
    interval = interval or config.UPDATE_INTERVAL

    while True:
        try:
            # Get cluster data
            data = await hub.get_cluster_data()

            # Add system info
            import psutil
            data['system'] = {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent,
            }

            # Broadcast to all clients
            await manager.broadcast(data)

        except Exception as e:
            logger.error(f"Error in hub monitor loop: {e}")

        await asyncio.sleep(interval)


async def handle_websocket(websocket: WebSocket, monitor_or_hub):
    """Handle WebSocket connection"""
    await manager.connect(websocket)

    try:
        while True:
            # Wait for messages from client (can be used for configuration)
            data = await websocket.receive_text()
            logger.debug(f"Received: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


def register_handlers(app, monitor):
    """Register WebSocket handlers for single-node mode"""
    from app import app as fastapi_app

    @fastapi_app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await handle_websocket(websocket, monitor)

    # Start background monitor loop
    asyncio.create_task(monitor_loop(monitor))


def register_hub_handlers(app, hub):
    """Register WebSocket handlers for hub mode"""
    from app import app as fastapi_app

    @fastapi_app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await handle_websocket(websocket, hub)

    # Start background hub monitor loop
    asyncio.create_task(hub_monitor_loop(hub))