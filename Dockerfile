# 使用Python 3.9官方镜像作为基础镜像
# 使用slim版本减小镜像体积
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
# 防止Python生成.pyc文件
ENV PYTHONDONTWRITEBYTECODE=1
# 确保Python输出不被缓冲，实时显示日志
ENV PYTHONUNBUFFERED=1
# 设置Flask应用路径
ENV FLASK_APP=backend/app.py
# 设置Flask运行环境
ENV FLASK_ENV=production
# 设置时区
ENV TZ=Asia/Shanghai

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libc-dev \
    make \
    curl \
    tzdata \
    python3-dev \
    && ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && dpkg-reconfigure -f noninteractive tzdata \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY backend/requirements.txt /app/backend/

# 安装Python依赖
# 使用--no-cache-dir减小镜像体积
# 使用国内镜像源加速下载
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r backend/requirements.txt

# 复制应用代码
COPY . /app/

# 创建必要的目录
RUN mkdir -p /app/data /app/logs /app/instance

# 设置权限
RUN chmod -R 755 /app

# 创建非root用户运行应用
RUN groupadd -r qingzhu && useradd -r -g qingzhu qingzhu
RUN chown -R qingzhu:qingzhu /app/data /app/logs /app/instance

# 创建启动脚本
RUN echo '#!/bin/sh\n\
python backend/app.py' > /app/start.sh && chmod +x /app/start.sh

# 切换到非root用户
USER qingzhu

# 暴露端口
EXPOSE 5001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5001/ || exit 1

# 启动命令
CMD ["/app/start.sh"]