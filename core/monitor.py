"""
GPU Monitor - Real-time NVIDIA GPU monitoring with user tracking
"""
import asyncio
import logging
import os
from typing import Dict, List, Optional
import pynvml
import gpustat

import config

logger = logging.getLogger(__name__)


class GPUMonitor:
    """GPU Monitor using NVML with user process tracking"""

    def __init__(self):
        self.nvml_initialized = False
        self.handles = []
        self.gpu_names = []
        self._init_nvml()

    def _init_nvml(self):
        """Initialize NVML"""
        try:
            pynvml.nvmlInit()
            self.nvml_initialized = True

            # Get all GPU handles
            count = pynvml.nvmlDeviceGetCount()
            for i in range(count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                self.handles.append(handle)
                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                self.gpu_names.append(name)

            logger.info(f"NVML initialized with {count} GPU(s)")
        except pynvml.NVMLError as e:
            logger.warning(f"NVML initialization failed: {e}, falling back to nvidia-smi")
            self.nvml_initialized = False

    async def get_gpu_data(self) -> Dict:
        """Get GPU data from all GPUs with user tracking"""
        gpus = {}

        if self.nvml_initialized:
            # Use NVML for rich metrics
            gpus = await self._get_gpu_data_nvml()
        else:
            # Fallback to nvidia-smi
            gpus = await self._get_gpu_data_smi()

        # Add user tracking via gpustat
        gpus = await self._add_user_tracking(gpus)

        return gpus

    async def _get_gpu_data_nvml(self) -> Dict:
        """Get GPU data using NVML"""
        gpus = {}

        loop = asyncio.get_event_loop()

        # Collect all GPU data concurrently
        tasks = []
        for i, handle in enumerate(self.handles):
            task = loop.run_in_executor(None, self._collect_gpu_nvml, i, handle)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        for i, gpu_data in enumerate(results):
            if gpu_data:
                gpus[str(i)] = gpu_data

        return gpus

    def _collect_gpu_nvml(self, index: int, handle) -> Optional[Dict]:
        """Collect data for a single GPU using NVML"""
        try:
            gpu = {}

            # Basic info
            gpu['index'] = index
            gpu['name'] = self.gpu_names[index]

            # Utilization
            try:
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu['utilization'] = util.gpu
                gpu['memory_utilization'] = util.memory
            except pynvml.NVMLError:
                gpu['utilization'] = 0
                gpu['memory_utilization'] = 0

            # Memory
            try:
                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                gpu['memory_used'] = mem.used // (1024 * 1024)  # MB
                gpu['memory_total'] = mem.total // (1024 * 1024)  # MB
                gpu['memory_free'] = mem.free // (1024 * 1024)  # MB
            except pynvml.NVMLError:
                gpu['memory_used'] = 0
                gpu['memory_total'] = 0
                gpu['memory_free'] = 0

            # Temperature
            try:
                gpu['temperature'] = pynvml.nvmlDeviceGetTemperature(
                    handle, pynvml.NVML_TEMPERATURE_GPU)
            except pynvml.NVMLError:
                gpu['temperature'] = 0

            # Power
            try:
                gpu['power_draw'] = pynvml.nvmlDeviceGetPowerUsage(handle) // 1000  # Watts
                gpu['power_limit'] = pynvml.nvmlDeviceGetPowerManagementLimit(handle) // 1000
            except pynvml.NVMLError:
                gpu['power_draw'] = 0
                gpu['power_limit'] = 0

            # Fan speed
            try:
                gpu['fan_speed'] = pynvml.nvmlDeviceGetFanSpeed(handle)
            except pynvml.NVMLError:
                gpu['fan_speed'] = 0

            # Clocks
            try:
                gpu['clock_graphics'] = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
                gpu['clock_memory'] = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
                gpu['clock_sm'] = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM)
            except pynvml.NVMLError:
                gpu['clock_graphics'] = 0
                gpu['clock_memory'] = 0
                gpu['clock_sm'] = 0

            # Max clocks
            try:
                gpu['clock_graphics_max'] = pynvml.nvmlDeviceGetMaxClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
                gpu['clock_memory_max'] = pynvml.nvmlDeviceGetMaxClockInfo(handle, pynvml.NVML_CLOCK_MEM)
            except pynvml.NVMLError:
                gpu['clock_graphics_max'] = 0
                gpu['clock_memory_max'] = 0

            # PCIe
            try:
                pci = pynvml.nvmlDeviceGetPciInfo(handle)
                gpu['pci_bus_id'] = pci.busId
            except pynvml.NVMLError:
                gpu['pci_bus_id'] = ''

            # Performance state
            try:
                pstate = pynvml.nvmlDeviceGetPerformanceState(handle)
                gpu['performance_state'] = f'P{pstate}'
            except pynvml.NVMLError:
                gpu['performance_state'] = 'P0'

            # Users (initially empty, will be added by _add_user_tracking)
            gpu['users'] = []

            return gpu

        except Exception as e:
            logger.error(f"Error collecting GPU {index} data: {e}")
            return None

    async def _get_gpu_data_smi(self) -> Dict:
        """Get GPU data using nvidia-smi command"""
        gpus = {}

        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=index,name,utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu,power.draw,power.limit,fan.speed,clocks.gr,clocks.mem,clocks.sm,clocks.max.gr,clocks.max.mem,pci.bus,performance.state',
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line.strip():
                        continue

                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 16:
                        idx = parts[0]
                        gpus[idx] = {
                            'index': int(idx),
                            'name': parts[1],
                            'utilization': int(parts[2]),
                            'memory_utilization': int(parts[3]),
                            'memory_used': int(parts[4]),
                            'memory_total': int(parts[5]),
                            'temperature': int(parts[6]),
                            'power_draw': int(parts[7]),
                            'power_limit': int(parts[8]),
                            'fan_speed': int(parts[9]),
                            'clock_graphics': int(parts[10]),
                            'clock_memory': int(parts[11]),
                            'clock_sm': int(parts[12]),
                            'clock_graphics_max': int(parts[13]),
                            'clock_memory_max': int(parts[14]),
                            'pci_bus_id': parts[15],
                            'performance_state': parts[16] if len(parts) > 16 else 'P0',
                            'memory_free': int(parts[5]) - int(parts[4]),
                            'users': []
                        }

        except Exception as e:
            logger.error(f"Error running nvidia-smi: {e}")

        return gpus

    async def _add_user_tracking(self, gpus: Dict) -> Dict:
        """Add user process tracking using gpustat"""
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            gpu_stats = await loop.run_in_executor(None, self._get_gpu_users)

            # Map gpustat data to our GPU data
            for gpu_idx, gpu_data in gpus.items():
                users = []
                total_memory = gpu_data.get('memory_used', 0)

                # Find matching GPU in gpustat
                for stat in gpu_stats:
                    if stat['idx'] == int(gpu_idx):
                        # Collect users from processes
                        user_memory = {}
                        for proc in stat.get('processes', []):
                            username = proc.get('username', 'unknown')
                            memory = proc.get('gpu_memory_usage', 0)

                            if memory > config.MIN_PROCESS_MEMORY:
                                if username not in user_memory:
                                    user_memory[username] = 0
                                user_memory[username] += memory

                        # Convert to list with percentages
                        for username, memory in user_memory.items():
                            percent = (memory / total_memory * 100) if total_memory > 0 else 0
                            users.append({
                                'name': username,
                                'occupy': memory,
                                'percent': round(percent, 1)
                            })

                        # Sort by memory usage descending
                        users.sort(key=lambda x: x['occupy'], reverse=True)
                        break

                gpus[gpu_idx]['users'] = users

        except Exception as e:
            logger.error(f"Error getting user tracking: {e}")

        return gpus

    def _get_gpu_users(self) -> List[Dict]:
        """Get GPU users using gpustat"""
        try:
            gpu_query = gpustat.new_query()
            return gpu_query.jsonify()['gpus']
        except Exception as e:
            logger.error(f"Error querying gpustat: {e}")
            return []

    async def get_processes(self) -> List[Dict]:
        """Get GPU process information"""
        processes = []

        if not self.nvml_initialized:
            return processes

        try:
            for i, handle in enumerate(self.handles):
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
            logger.error(f"Error getting processes: {e}")

        return processes

    async def get_system_info(self) -> Dict:
        """Get system resource info"""
        import psutil

        return {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'memory_used_gb': psutil.virtual_memory().used / (1024**3),
            'memory_available_gb': psutil.virtual_memory().available / (1024**3),
            'cpu_count': psutil.cpu_count(),
        }

    def shutdown(self):
        """Shutdown NVML"""
        if self.nvml_initialized:
            try:
                pynvml.nvmlShutdown()
            except:
                pass