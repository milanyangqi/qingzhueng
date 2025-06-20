# 使用Python 3.9官方镜像作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=backend/app.py
ENV FLASK_ENV=production

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY backend/requirements.txt /app/backend/

# 安装Python依赖
RUN pip install --no-cache-dir -r backend/requirements.txt

# 复制应用代码
COPY . /app/

# 创建数据目录
RUN mkdir -p /app/data

# 设置权限
RUN chmod -R 755 /app

# 暴露端口
EXPOSE 5001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/ || exit 1

# 启动命令
CMD ["python", "backend/app.py"]