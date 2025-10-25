FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 安装构建依赖（psycopg2 需要）
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖定义与源码
COPY pyproject.toml README.md ./
COPY server ./server

# 安装依赖
RUN pip install --no-cache-dir uv \
    && uv pip install -e .

EXPOSE 8000

CMD ["uvicorn", "server.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]


