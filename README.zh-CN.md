# Energy-Grid-Core

[English README](README.md)

Energy-Grid-Core 是一个面向“能源监控与设备状态管理”的通用后端基础项目，适合用作遥测密集型后端系统的架构骨架。项目重点提供清晰、可扩展的模块边界，用于组织设备接入、实时数据处理、历史存储和预测集成能力。

## 这个仓库提供什么

- 设备连接池管理
- 实时遥测数据接入管线
- 历史数据存储抽象及默认 SQLAlchemy 实现
- 可插拔的预测接口
- 基于 FastAPI 的监控、历史查询和预测 API

## 架构特点

- **高并发接入**：遥测数据通过有界 `asyncio.Queue` 缓冲，并按批次刷写
- **模块边界清晰**：API、核心基础设施、模型、服务层相互分离
- **存储可替换**：历史存储通过 `HistoryStoragePort` 抽象，便于切换底层实现
- **预测易扩展**：预测能力通过 `ForecastProvider` 抽象，便于接入具体模型

## 默认技术栈

- Python `3.11`
- FastAPI
- SQLAlchemy 2.0
- SQLite（本地开发默认）
- pytest + httpx

## 项目结构

```text
project-root/
├── app/
│   ├── api/             # 路由层
│   ├── core/            # 配置、生命周期、日志、错误处理
│   ├── models/          # ORM 模型
│   └── services/        # 业务与基础设施服务
├── tests/               # 自动化测试
├── .env.example         # 环境变量模板
├── pyproject.toml
├── requirements.txt
└── main.py
```

## API 列表

- `POST /api/v1/devices/connect`
- `DELETE /api/v1/devices/{device_id}`
- `POST /api/v1/monitoring/ingest`
- `GET /api/v1/monitoring/overview`
- `GET /api/v1/history/{device_id}`
- `POST /api/v1/forecast/{device_id}`

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000
```

运行测试：

```bash
source .venv/bin/activate
pytest
```

## 配置说明

项目运行配置全部通过环境变量控制。默认 `.env.example` 中的关键配置包括：

- `APP_VERSION=0.0.0.1`
- `HISTORY_STORAGE_BACKEND=sqlalchemy`
- `DATABASE_URL=sqlite:///./energy_grid_core.db`

## 仓库说明

- 仓库已整理为适合公开展示的 GitHub 项目
- 不包含硬编码密钥或环境专属地址
- `.env`、`.venv`、`.DS_Store`、SQLite 数据文件等本地产物已忽略
- 依赖版本已固定到当前验证通过的版本，便于复现安装环境

## 许可证

详见 [LICENSE](LICENSE)。

当前仓库许可证状态为 `All rights reserved`，这意味着源码可见，但当前并不是采用开源许可证发布的代码仓库。
