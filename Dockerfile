FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
    PIP_TRUSTED_HOST=mirrors.aliyun.com

WORKDIR /app

# 依赖均使用 Python 轮子（包含 psycopg2-binary），无需系统编译依赖，减少构建体积与耗时

# 复制依赖定义与源码
COPY pyproject.toml README.md ./
COPY server ./server

# 安装依赖（使用国内源，不创建虚拟环境，减小构建复杂度）
RUN pip install --no-cache-dir \
      fastapi \
      "uvicorn[standard]" \
      sqlalchemy \
      psycopg2-binary \
      pydantic \
      pydantic-settings \
      passlib \
      pyjwt \
      python-multipart \
      email-validator

EXPOSE 8000

CMD ["uvicorn", "server.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]


