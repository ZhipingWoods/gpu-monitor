#!/usr/bin/env python3
"""
GPU Monitor - Multi-server GPU Monitoring with User Tracking
Demo Mode: Mock data for Vercel deployment
"""
import random
import time
from datetime import datetime


def generate_demo_cluster_data():
    """Generate demo cluster data for showcase"""
    # Simulated GPU servers with realistic data
    nodes = {
        '2080Ti-Server-1': {
            'status': 'online',
            'last_update': datetime.now().isoformat(),
            'gpus': {
                '0': {
                    'index': 0,
                    'name': 'GeForce RTX 2080 Ti',
                    'utilization': random.randint(60, 95),
                    'memory_utilization': random.randint(70, 95),
                    'memory_used': random.randint(8000, 10500),
                    'memory_total': 11000,
                    'memory_free': random.randint(500, 3000),
                    'temperature': random.randint(55, 75),
                    'power_draw': random.randint(200, 260),
                    'power_limit': 260,
                    'fan_speed': random.randint(40, 70),
                    'clock_graphics': random.randint(1500, 1800),
                    'clock_memory': random.randint(7000, 8000),
                    'clock_sm': random.randint(1500, 1800),
                    'clock_graphics_max': 1935,
                    'clock_memory_max': 8000,
                    'performance_state': 'P0',
                    'users': [
                        {'name': 'zhangsan', 'occupy': 6000, 'percent': 54.5},
                        {'name': 'lisi', 'occupy': 3500, 'percent': 31.8},
                        {'name': 'wangwu', 'occupy': 1000, 'percent': 9.1}
                    ]
                },
                '1': {
                    'index': 1,
                    'name': 'GeForce RTX 2080 Ti',
                    'utilization': random.randint(20, 50),
                    'memory_utilization': random.randint(30, 60),
                    'memory_used': random.randint(3000, 6000),
                    'memory_total': 11000,
                    'memory_free': random.randint(5000, 8000),
                    'temperature': random.randint(40, 55),
                    'power_draw': random.randint(100, 180),
                    'power_limit': 260,
                    'fan_speed': random.randint(30, 45),
                    'clock_graphics': random.randint(300, 1200),
                    'clock_memory': random.randint(4000, 7000),
                    'clock_sm': random.randint(300, 1200),
                    'clock_graphics_max': 1935,
                    'clock_memory_max': 8000,
                    'performance_state': 'P2',
                    'users': [
                        {'name': 'chenliu', 'occupy': 5000, 'percent': 45.5},
                        {'name': 'zhaoliu', 'occupy': 1000, 'percent': 9.1}
                    ]
                }
            }
        },
        '3090-Workstation': {
            'status': 'online',
            'last_update': datetime.now().isoformat(),
            'gpus': {
                '0': {
                    'index': 0,
                    'name': 'GeForce RTX 3090',
                    'utilization': random.randint(80, 100),
                    'memory_utilization': random.randint(85, 98),
                    'memory_used': random.randint(20000, 24000),
                    'memory_total': 24576,
                    'memory_free': random.randint(500, 4500),
                    'temperature': random.randint(60, 80),
                    'power_draw': random.randint(300, 350),
                    'power_limit': 350,
                    'fan_speed': random.randint(50, 80),
                    'clock_graphics': random.randint(1600, 1900),
                    'clock_memory': random.randint(9000, 10000),
                    'clock_sm': random.randint(1600, 1900),
                    'clock_graphics_max': 1965,
                    'clock_memory_max': 10000,
                    'performance_state': 'P0',
                    'users': [
                        {'name': 'train_user', 'occupy': 18000, 'percent': 73.3},
                        {'name': 'eval_user', 'occupy': 5000, 'percent': 20.3}
                    ]
                },
                '1': {
                    'index': 1,
                    'name': 'GeForce RTX 3090',
                    'utilization': random.randint(40, 70),
                    'memory_utilization': random.randint(50, 80),
                    'memory_used': random.randint(12000, 18000),
                    'memory_total': 24576,
                    'memory_free': random.randint(6500, 12500),
                    'temperature': random.randint(50, 65),
                    'power_draw': random.randint(200, 280),
                    'power_limit': 350,
                    'fan_speed': random.randint(35, 55),
                    'clock_graphics': random.randint(1200, 1600),
                    'clock_memory': random.randint(6000, 9000),
                    'clock_sm': random.randint(1200, 1600),
                    'clock_graphics_max': 1965,
                    'clock_memory_max': 10000,
                    'performance_state': 'P2',
                    'users': [
                        {'name': 'preprocess', 'occupy': 15000, 'percent': 61.1}
                    ]
                }
            }
        },
        'A100-Node-1': {
            'status': 'online',
            'last_update': datetime.now().isoformat(),
            'gpus': {
                '0': {
                    'index': 0,
                    'name': 'NVIDIA A100-SXM4-40GB',
                    'utilization': random.randint(90, 100),
                    'memory_utilization': random.randint(90, 98),
                    'memory_used': random.randint(35000, 40000),
                    'memory_total': 40960,
                    'memory_free': random.randint(960, 5960),
                    'temperature': random.randint(55, 70),
                    'power_draw': random.randint(280, 350),
                    'power_limit': 400,
                    'fan_speed': random.randint(30, 50),
                    'clock_graphics': random.randint(1300, 1500),
                    'clock_memory': random.randint(2500, 3000),
                    'clock_sm': random.randint(1300, 1500),
                    'clock_graphics_max': 1695,
                    'clock_memory_max': 3200,
                    'performance_state': 'P0',
                    'users': [
                        {'name': 'ml_trainer', 'occupy': 35000, 'percent': 85.5},
                    ]
                },
                '1': {
                    'index': 1,
                    'name': 'NVIDIA A100-SXM4-40GB',
                    'utilization': random.randint(70, 90),
                    'memory_utilization': random.randint(75, 90),
                    'memory_used': random.randint(30000, 36000),
                    'memory_total': 40960,
                    'memory_free': random.randint(4960, 10960),
                    'temperature': random.randint(50, 65),
                    'power_draw': random.randint(250, 320),
                    'power_limit': 400,
                    'fan_speed': random.randint(25, 40),
                    'clock_graphics': random.randint(1200, 1400),
                    'clock_memory': random.randint(2000, 2800),
                    'clock_sm': random.randint(1200, 1400),
                    'clock_graphics_max': 1695,
                    'clock_memory_max': 3200,
                    'performance_state': 'P0',
                    'users': [
                        {'name': 'inference_svc', 'occupy': 28000, 'percent': 68.4},
                        {'name': 'batch_job', 'occupy': 8000, 'percent': 19.5}
                    ]
                },
                '2': {
                    'index': 2,
                    'name': 'NVIDIA A100-SXM4-40GB',
                    'utilization': random.randint(10, 30),
                    'memory_utilization': random.randint(5, 20),
                    'memory_used': random.randint(2000, 8000),
                    'memory_total': 40960,
                    'memory_free': random.randint(32960, 38960),
                    'temperature': random.randint(35, 45),
                    'power_draw': random.randint(80, 150),
                    'power_limit': 400,
                    'fan_speed': random.randint(20, 30),
                    'clock_graphics': random.randint(210, 1200),
                    'clock_memory': random.randint(1215, 2000),
                    'clock_sm': random.randint(210, 1200),
                    'clock_graphics_max': 1695,
                    'clock_memory_max': 3200,
                    'performance_state': 'P8',
                    'users': []
                },
                '3': {
                    'index': 3,
                    'name': 'NVIDIA A100-SXM4-40GB',
                    'utilization': random.randint(50, 80),
                    'memory_utilization': random.randint(60, 85),
                    'memory_used': random.randint(24000, 32000),
                    'memory_total': 40960,
                    'memory_free': random.randint(8960, 16960),
                    'temperature': random.randint(45, 60),
                    'power_draw': random.randint(200, 300),
                    'power_limit': 400,
                    'fan_speed': random.randint(25, 45),
                    'clock_graphics': random.randint(1100, 1500),
                    'clock_memory': random.randint(2000, 2800),
                    'clock_sm': random.randint(1100, 1500),
                    'clock_graphics_max': 1695,
                    'clock_memory_max': 3200,
                    'performance_state': 'P0',
                    'users': [
                        {'name': 'distributed_train', 'occupy': 25000, 'percent': 61.0},
                        {'name': 'data_loader', 'occupy': 6000, 'percent': 14.6}
                    ]
                }
            }
        },
        'V100-Cluster': {
            'status': 'offline',
            'last_update': datetime.now().isoformat(),
            'gpus': {}
        }
    }

    return {
        'mode': 'hub',
        'cluster_stats': {
            'total_nodes': 4,
            'online_nodes': 3,
            'offline_nodes': 1,
            'total_gpus': 10
        },
        'nodes': nodes
    }


def generate_demo_gpu_data():
    """Generate single server GPU data for demo"""
    return {
        'mode': 'default',
        'node_name': 'demo-server',
        'gpus': generate_demo_cluster_data()['nodes']['2080Ti-Server-1']['gpus'],
        'processes': [
            {'pid': 1234, 'name': 'python', 'gpu_id': 0, 'memory': 6000},
            {'pid': 5678, 'name': 'python', 'gpu_id': 0, 'memory': 3500},
            {'pid': 9012, 'name': 'python', 'gpu_id': 1, 'memory': 5000}
        ],
        'system': {
            'cpu_percent': random.randint(20, 60),
            'memory_percent': random.randint(40, 80),
            'memory_total_gb': 64,
            'memory_used_gb': random.randint(20, 40)
        }
    }