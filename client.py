#!/usr/bin/env python3
"""
GPU Monitor Client - Lightweight agent for GPU servers
Connects to hub and reports local GPU data with user tracking
"""
import argparse
import asyncio
import logging
import os
import socket
import sys
import time
from datetime import datetime

import aiohttp
import gpustat
import pynvml
import psutil

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GPUClient:
    """Lightweight GPU client that reports to hub"""

    def __init__(self, hub_url: str, node_name: str, interval: float = 1.0):
        self.hub_url = hub_url.rstrip('/')
        self.node_name = node_name or socket.gethostname()
        self.interval = interval
        self.running = False
        self.session = None
        self.nvml_initialized = False

    def _init_nvml(self):
        """Initialize NVML"""
        try:
            pynvml.nvmlInit()
            self.nvml_initialized = True
            count = pynvml.nvmlDeviceGetCount()
            logger.info(f"NVML initialized with {count} GPU(s)")
        except Exception as e:
            logger.warning(f"NVML init failed: {e}")

    async def start(self):
        """Start reporting to hub"""
        self.running = True
        self.session = aiohttp.ClientSession()

        logger.info(f"Client starting: {self.node_name}")
        logger.info(f"Reporting to: {self.hub_url}")

        self._init_nvml()

        while self.running:
            try:
                await self._report()
            except Exception as e:
                logger.error(f"Error reporting: {e}")

            await asyncio.sleep(self.interval)

    async def stop(self):
        """Stop the client"""
        self.running = False
        if self.session:
            await self.session.close()
        if self.nvml_initialized:
            try:
                pynvml.nvmlShutdown()
            except:
                pass

    async def _report(self):
        """Collect and report GPU data"""
        gpus = await self._collect_gpu_data()
        processes = self._get_processes()
        system = self._get_system_info()

        data = {
            'node_name': self.node_name,
            'gpus': gpus,
            'processes': processes,
            'system': system,
            'timestamp': datetime.now().isoformat()
        }

        try:
            async with self.session.post(
                f"{self.hub_url}/api/report",
                json=data,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    logger.debug(f"Reported to hub: {len(gpus)} GPUs")
                else:
                    logger.warning(f"Hub returned {response.status}")
        except Exception as e:
            logger.debug(f"Failed to report: {e}")

    async def _collect_gpu_data(self) -> dict:
        """Collect GPU data using gpustat for user tracking + NVML for detailed metrics"""
        gpus = {}

        try:
            # Get basic data from gpustat (includes user info)
            gpu_stats = gpustat.new_query()
            gpustat_data = gpu_stats.jsonify()['gpus']

            # Get detailed data from NVML (if available)
            nvml_data = {}
            if self.nvml_initialized:
                nvml_data = self._collect_nvml()

            # Merge data
            for stat in gpustat_data:
                idx = str(stat['idx'])
                gpu = {
                    'index': stat['idx'],
                    'name': stat['name'],
                    'utilization': stat.get('utilization.gpu', 0),
                    'memory_utilization': stat.get('utilization.memory', 0),
                    'memory_used': stat.get('memory.used', 0),
                    'memory_total': stat.get('memory.total', 0),
                    'memory_free': stat.get('memory.free', 0),
                    'temperature': stat.get('temperature.gpu', 0),
                    'power_draw': 0,
                    'power_limit': 0,
                    'fan_speed': 0,
                    'clock_graphics': 0,
                    'clock_memory': 0,
                    'clock_sm': 0,
                    'clock_graphics_max': 0,
                    'clock_memory_max': 0,
                    'performance_state': 'P0',
                    'users': []
                }

                # Get users from processes
                user_memory = {}
                for proc in stat.get('processes', []):
                    username = proc.get('username', 'unknown')
                    memory = proc.get('gpu_memory_usage', 0)

                    # Filter small processes
                    if memory > 100:  # 100MB threshold
                        if username not in user_memory:
                            user_memory[username] = 0
                        user_memory[username] += memory

                # Convert to list with percentages
                total_memory = gpu['memory_used']
                for username, memory in user_memory.items():
                    percent = (memory / total_memory * 100) if total_memory > 0 else 0
                    gpu['users'].append({
                        'name': username,
                        'occupy': memory,
                        'percent': round(percent, 1)
                    })

                # Sort by memory
                gpu['users'].sort(key=lambda x: x['occupy'], reverse=True)

                # Add NVML data if available
                if idx in nvml_data:
                    nvml_gpu = nvml_data[idx]
                    gpu['power_draw'] = nvml_gpu.get('power_draw', 0)
                    gpu['power_limit'] = nvml_gpu.get('power_limit', 0)
                    gpu['fan_speed'] = nvml_gpu.get('fan_speed', 0)
                    gpu['clock_graphics'] = nvml_gpu.get('clock_graphics', 0)
                    gpu['clock_memory'] = nvml_gpu.get('clock_memory', 0)
                    gpu['clock_sm'] = nvml_gpu.get('clock_sm', 0)
                    gpu['clock_graphics_max'] = nvml_gpu.get('clock_graphics_max', 0)
                    gpu['clock_memory_max'] = nvml_gpu.get('clock_memory_max', 0)
                    gpu['performance_state'] = nvml_gpu.get('performance_state', 'P0')

                gpus[idx] = gpu

        except Exception as e:
            logger.error(f"Error collecting GPU data: {e}")

        return gpus

    def _collect_nvml(self) -> dict:
        """Collect additional data using NVML"""
        result = {}

        if not self.nvml_initialized:
            return result

        try:
            count = pynvml.nvmlDeviceGetCount()

            for i in range(count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                gpu = {}

                try:
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu['utilization'] = util.gpu
                except:
                    pass

                try:
                    mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    gpu['memory_used'] = mem.used // (1024 * 1024)
                    gpu['memory_total'] = mem.total // (1024 * 1024)
                except:
                    pass

                try:
                    gpu['temperature'] = pynvml.nvmlDeviceGetTemperature(
                        handle, pynvml.NVML_TEMPERATURE_GPU)
                except:
                    pass

                try:
                    gpu['power_draw'] = pynvml.nvmlDeviceGetPowerUsage(handle) // 1000
                    gpu['power_limit'] = pynvml.nvmlDeviceGetPowerManagementLimit(handle) // 1000
                except:
                    pass

                try:
                    gpu['fan_speed'] = pynvml.nvmlDeviceGetFanSpeed(handle)
                except:
                    pass

                try:
                    gpu['clock_graphics'] = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
                    gpu['clock_memory'] = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
                    gpu['clock_sm'] = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM)
                except:
                    pass

                try:
                    gpu['clock_graphics_max'] = pynvml.nvmlDeviceGetMaxClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
                    gpu['clock_memory_max'] = pynvml.nvmlDeviceGetMaxClockInfo(handle, pynvml.NVML_CLOCK_MEM)
                except:
                    pass

                try:
                    pstate = pynvml.nvmlDeviceGetPerformanceState(handle)
                    gpu['performance_state'] = f'P{pstate}'
                except:
                    pass

                result[str(i)] = gpu

        except Exception as e:
            logger.error(f"Error collecting NVML: {e}")

        return result

    def _get_processes(self) -> list:
        """Get GPU processes"""
        processes = []

        if not self.nvml_initialized:
            return processes

        try:
            count = pynvml.nvmlDeviceGetCount()

            for i in range(count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                procs = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)

                for proc in procs:
                    try:
                        name = pynvml.nvmlSystemGetProcessName(proc.pid)
                        if isinstance(name, bytes):
                            name = name.decode('utf-8')
                    except:
                        name = f"PID {proc.pid}"

                    processes.append({
                        'pid': proc.pid,
                        'name': name,
                        'gpu_id': i,
                        'memory': proc.usedGpuMemory // (1024 * 1024) if proc.usedGpuMemory else 0
                    })

        except Exception as e:
            logger.debug(f"Error getting processes: {e}")

        return processes

    def _get_system_info(self) -> dict:
        """Get system resource info"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 1),
            'memory_used_gb': round(psutil.virtual_memory().used / (1024**3), 1),
        }


def main():
    parser = argparse.ArgumentParser(description='GPU Monitor Client')
    parser.add_argument('--server', '-s', type=str, default='http://localhost:1312',
                        help='Hub server URL')
    parser.add_argument('--name', '-n', type=str, default=None,
                        help='Node name (default: hostname)')
    parser.add_argument('--interval', '-i', type=float, default=1.0,
                        help='Reporting interval in seconds (default: 1.0)')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug logging')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create and start client
    client = GPUClient(args.server, args.name, args.interval)

    try:
        asyncio.run(client.start())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        asyncio.run(client.stop())


if __name__ == '__main__':
    main()