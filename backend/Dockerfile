# ===== 后端 Dockerfile (Django + Gunicorn) =====
FROM python:3.11-slim

# 基础环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 安装系统依赖（mysqlclient 编译需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        pkg-config \
        default-libmysqlclient-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件以利用 Docker 层缓存
COPY requirements.txt .

# 安装 Python 依赖（额外加入生产部署所需的 gunicorn 与 mysqlclient）
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn mysqlclient

# 复制项目源码
COPY . .

# 创建 gunicorn 日志目录（与 gunicorn.conf.py 中的路径保持一致）
RUN mkdir -p /www/wwwlogs/python/ai_project_QA

# 收集静态文件（DEBUG 模式下可选，失败不影响构建）
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# 使用 gunicorn 启动；命令行参数覆盖配置文件中的 bind 端口为 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "300", "--access-logfile", "-", "--error-logfile", "-"]
