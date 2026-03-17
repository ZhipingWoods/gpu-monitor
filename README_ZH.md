# GPU Monitor

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vue-3-42b883?style=flat-square&logo=vue.js&logoColor=white" alt="Vue">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

<p align="center">
  轻量级多服务器 GPU 监控系统 | 实时监控 | 用户占用跟踪 | 分段��视化
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README_ZH.md">中文</a> · <a href="#demo">在线演示</a>
</p>

---

## 特性

- 🔐 **简单认证** - 用户名密码登录，配置简单
- 👥 **用户跟踪** - 显示每个 GPU 上谁在用，占用多少显存
- 📊 **分段进度条** - 可视化各用户的显存占用比例
- 🖥️ **多服务器监控** - Hub 模式聚合多个节点数据
- 📈 **完整指标** - 利用率、温度、功率、时钟等 (可展开/收起)
- ⚡ **实时推送** - WebSocket 低延迟更新
- 🐳 **Docker 支持** - 快速部署

---

## 快速开始

### 方式一：Docker 部署 (推荐)

```bash
# 克隆项目
git clone https://github.com/your-repo/gpu-monitor.git
cd gpu-monitor

# 启动服务
docker-compose up --build
```

访问 `http://localhost:1312`

### 方式二：本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 修改配置 (可选)
# 编辑 config.py 添加用户:
# USERS = {
#     'admin': 'your-password',
#     'yourname': 'your-password',
# }

# 3. 启动 Hub 服务器
python app.py
```

访问 `http://localhost:1312`

---

## 架构说明

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

### 三种运行模式

| 模式 | 说明 | 用途 |
|------|------|------|
| `hub` | 聚合多个节点数据 | 主服务器，显示所有 GPU 服务器状态 |
| `server` | 本地 GPU 监控 | 单台服务器，监控本地 GPU |
| `client` | 客户端上报 | 部署在各 GPU 服务器上 |

---

## 使用指南

### 1. 启动 Hub 服务器 (监控中心)

在主服务器上运行:

```bash
# 默认 hub 模式
python app.py
```

### 2. 在各 GPU 服务器上运行客户端

```bash
# 基本用法
python client.py --server http://<Hub-IP>:1312 --name "服务器名称"

# 完整参数
python client.py \
  --server http://192.168.1.100:1312 \
  --name "2080Ti-Server-1" \
  --interval 1.0

# 后台运行
nohup python client.py --server http://192.168.1.100:1312 --name "Server-1" &
```

### 3. 配置节点 URL (可选)

如果使用 REST 轮询模式而非客户端上报，可以在 Hub 服务器上设置:

```bash
# docker-compose.yml 或环境变量
NODE_URLS=http://server1:1312,http://server2:1312,http://server3:1312
```

---

## 配置说明

编辑 `config.py`:

```python
# 用户认证配置
USERS = {
    'admin': 'admin123',      # 修改默认密码!
    'gpuadmin': 'gpu2024',
    'yourname': 'your-pass',
}

# 服务器配置
HOST = '0.0.0.0'
PORT = 1312                  # 端口

# 监控配置
UPDATE_INTERVAL = 1.0        # 更新间隔 (秒)
MODE = 'hub'                 # 运行模式: hub / server / client

# 客户端配置
HUB_URL = 'http://localhost:1312'
NODE_NAME = 'my-gpu-server'  # 本服务器名称
```

---

## API 接口

| 接口 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/` | GET | 主页面 | 需要 |
| `/login` | GET | 登录页面 | - |
| `/api/login` | POST | 登录 | - |
| `/api/logout` | POST | 登出 | 需要 |
| `/api/me` | GET | 当前用户 | 需要 |
| `/api/gpu-data` | GET | GPU 数据 | 需要 |
| `/api/cluster` | GET | 集群数据 | 需要 |
| `/api/processes` | GET | GPU 进程 | 需要 |
| `/ws` | WebSocket | 实时推送 | - |

---

## 界面预览

### 登录页
简洁的登录界面，支持中英文。

### 集群总览
- 所有服务器 GPU 使用情况表格
- 分段进度条显示用户占用
- 在线/离线状态指示

### 节点详情
- 单个服务器的完整 GPU 信息
- 可展开/收起的详细指标
- 用户显存分段可视化

---

## Vercel 演示

本项目支持部署到 Vercel 进行在线演示:

```bash
# 演示模式 (使用模拟数据)
DEMO_MODE=true python app.py
```

访问 Vercel 部署的链接即可查看 Demo。

**演示账号 (Demo Mode 自动登录):**
- 用户名: `demo`
- 密码: `demo123`

**生产环境账号 (需自行配置):**
- 用户名: `admin`
- 密码: `admin123`

---

## 技术栈

- **后端**: FastAPI + Uvicorn + AsyncIO
- **GPU 数据**: pynvml (NVML) + gpustat
- **前端**: Vue 3 + Element Plus
- **通信**: WebSocket (实时推送)
- **部署**: Docker, Vercel

---

## 致谢

本项目基于以下开源项目:

- **[gpu-hot](https://github.com/psalias2006/gpu-hot)** - Real-time NVIDIA GPU monitoring dashboard
  - FastAPI + AsyncIO 高性能架构
  - 丰富的 NVML 指标收集
  - Hub 模式多节点聚合

感谢以上项目的作者和贡献者!

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## 问题反馈

如有问题或建议,欢迎提交 Issue 或 PR。
