"""
Hub - Multi-node GPU monitoring aggregation
"""
import asyncio
import logging
import time
from typing import Dict, Optional, List
import aiohttp
from datetime import datetime

import config

logger = logging.getLogger(__name__)


class Hub:
    """Hub for aggregating data from multiple GPU nodes"""

    def __init__(self, node_urls: list = None):
        self.node_urls = node_urls or config.NODE_URLS
        self.nodes: Dict[str, dict] = {}
        self.url_to_node: Dict[str, str] = {}
        self._running = False
        self._tasks = []

    async def start(self):
        """Start the hub and connect to all nodes"""
        self._running = True
        logger.info(f"Starting hub with {len(self.node_urls)} nodes")

        for url in self.node_urls:
            node_name = url.split('://')[-1].split(':')[0]
            self.nodes[node_name] = {
                'url': url,
                'status': 'offline',
                'gpus': {},
                'processes': [],
                'system': {},
                'last_update': None
            }
            self.url_to_node[url] = node_name

        # Start connection tasks
        for url in self.node_urls:
            task = asyncio.create_task(self._connect_and_listen(url))
            self._tasks.append(task)

    async def _connect_and_listen(self, url: str):
        """Connect to a node and listen for data"""
        node_name = self.url_to_node.get(url, url)

        while self._running:
            try:
                # Try to connect via HTTP first (polling mode)
                await self._poll_node(url, node_name)
            except Exception as e:
                logger.debug(f"Node {node_name} error: {e}")
                if node_name in self.nodes:
                    self.nodes[node_name]['status'] = 'offline'

            # Wait before next attempt
            await asyncio.sleep(config.UPDATE_INTERVAL)

    async def _poll_node(self, url: str, node_name: str):
        """Poll a node for GPU data"""
        try:
            # Try REST API
            api_url = f"{url}/api/gpu-data"
            timeout = aiohttp.ClientTimeout(total=5)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Update node data
                        if node_name in self.nodes:
                            self.nodes[node_name]['gpus'] = data.get('gpus', {})
                            self.nodes[node_name]['status'] = 'online'
                            self.nodes[node_name]['last_update'] = datetime.now().isoformat()

                            # Try to get processes
                            try:
                                async with session.get(f"{url}/api/processes") as proc_resp:
                                    if proc_resp.status == 200:
                                        proc_data = await proc_resp.json()
                                        self.nodes[node_name]['processes'] = proc_data.get('processes', [])
                            except:
                                pass

                            # Try to get system info
                            try:
                                async with session.get(f"{url}/api/system") as sys_resp:
                                    if sys_resp.status == 200:
                                        sys_data = await sys_resp.json()
                                        self.nodes[node_name]['system'] = sys_data
                            except:
                                pass

        except asyncio.TimeoutError:
            if node_name in self.nodes:
                self.nodes[node_name]['status'] = 'offline'
        except Exception as e:
            logger.debug(f"Polling {node_name}: {e}")
            if node_name in self.nodes:
                self.nodes[node_name]['status'] = 'offline'

    async def get_cluster_data(self) -> Dict:
        """Get aggregated cluster data"""
        online_count = sum(1 for n in self.nodes.values() if n['status'] == 'online')
        total_gpus = sum(len(n['gpus']) for n in self.nodes.values())

        # Build cluster data
        nodes_data = {}
        for node_name, node in self.nodes.items():
            nodes_data[node_name] = {
                'status': node['status'],
                'gpus': node['gpus'],
                'last_update': node['last_update']
            }

        return {
            'mode': 'hub',
            'cluster_stats': {
                'total_nodes': len(self.nodes),
                'online_nodes': online_count,
                'offline_nodes': len(self.nodes) - online_count,
                'total_gpus': total_gpus
            },
            'nodes': nodes_data
        }

    async def shutdown(self):
        """Shutdown the hub"""
        self._running = False

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        self._tasks.clear()
        logger.info("Hub shutdown complete")


class ClientNode:
    """Client node that connects to a hub and reports local GPU data"""

    def __init__(self, hub_url: str, node_name: str):
        self.hub_url = hub_url.rstrip('/')
        self.node_name = node_name
        self._running = False
        self._session = None

    async def start(self, monitor):
        """Start reporting to hub"""
        self._running = True
        logger.info(f"Client starting, reporting to {self.hub_url}")

        while self._running:
            try:
                # Collect GPU data
                gpus = await monitor.get_gpu_data()
                processes = await monitor.get_processes()
                system = await monitor.get_system_info()

                # Send to hub
                await self._report_to_hub(gpus, processes, system)

            except Exception as e:
                logger.error(f"Error reporting to hub: {e}")

            await asyncio.sleep(config.UPDATE_INTERVAL)

    async def _report_to_hub(self, gpus: Dict, processes: List, system: Dict):
        """Report GPU data to hub"""
        try:
            if not self._session:
                self._session = aiohttp.ClientSession()

            data = {
                'node_name': self.node_name,
                'gpus': gpus,
                'processes': processes,
                'system': system,
                'timestamp': datetime.now().isoformat()
            }

            async with self._session.post(
                f"{self.hub_url}/api/report",
                json=data,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    logger.debug(f"Successfully reported to hub")
                else:
                    logger.warning(f"Hub returned status {response.status}")

        except Exception as e:
            logger.debug(f"Failed to report to hub: {e}")

    async def stop(self):
        """Stop the client"""
        self._running = False
        if self._session:
            await self._session.close()
            self._session = None