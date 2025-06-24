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
ENV NODE_ENV=production
ENV DOCKER_BUILD=true
ENV VITE_MAIN_APP_URL=http://localhost:5001
ENV VITE_BASE=/typing/

# 暴露端口
EXPOSE 3000

# 构建生产版本
RUN pnpm build

# 安装serve工具来提供静态文件服务
RUN npm install -g serve

# 启动命令 - 在生产模式下运行
CMD ["serve", "-s", "dist", "-l", "3000"]