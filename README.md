Socket Chat - WebSocket + PyQt6 + FastAPI + SQLAlchemy
=====================================================

功能
----
- 注册、登录（JWT）
- 好友添加、列表
- 单聊消息收发（WebSocket）
- 消息持久化（PostgreSQL / SQLAlchemy）
- 桌面客户端（PyQt6）

依赖
----
- Python >= 3.12
- PostgreSQL (本地或容器)

安装
----
```bash
pip install -e .
```

环境变量（.env 文件）
---------------------
1) 复制示例并按需修改
```bash
cp .env.example .env   # Windows: copy .env.example .env
```
2) 关键项
- DATABASE_URL（Postgres 连接串）
- JWT_SECRET（JWT 密钥）
- API_BASE / WS_URL（客户端指向后端）

运行
----
```bash
# 启动后端（FastAPI + Uvicorn）
python -m server.main

# 启动客户端（PyQt6 桌面端）
python -m client.main
```

开发提示
--------
- 初次运行会自动建库表（SQLAlchemy metadata.create_all）。
- 推荐用 `pgvector` 或全文索引按需扩展搜索。
- 建议将 `.env` 加入版本忽略，避免提交敏感信息。

使用 uv 管理环境（推荐）
------------------------
1) 安装 uv（Windows PowerShell）
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```
2) 创建并使用虚拟环境（Python 3.12+）
```powershell
uv venv --python 3.12
uv pip install -e .
```
3) 运行后端与客户端
```powershell
uv run python -m server.main
uv run python -m client.main
```
