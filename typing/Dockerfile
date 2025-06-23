# 使用Node.js 18 Alpine镜像
FROM node:18-alpine

# 设置工作目录
WORKDIR /app

# 复制package.json和pnpm-lock.yaml
COPY package.json pnpm-lock.yaml ./

# 安装pnpm
RUN npm install -g pnpm

# 安装依赖
RUN pnpm install

# 复制源代码
COPY . .

# 设置环境变量
ENV NODE_ENV=development
ENV DOCKER_BUILD=true

# 暴露端口
EXPOSE 3000

# 启动命令 - 在开发模式下运行
CMD ["pnpm", "dev", "--host", "0.0.0.0", "--port", "3000"]