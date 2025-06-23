# 使用Node.js 18官方镜像
FROM node:18-alpine

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV NODE_ENV=production
ENV PORT=3000

# 复制package文件
COPY package*.json ./
COPY pnpm-lock.yaml ./

# 安装pnpm并安装依赖
RUN npm install -g pnpm && \
    pnpm install --frozen-lockfile

# 复制应用代码
COPY . .

# 构建应用
RUN pnpm build

# 创建非root用户
RUN addgroup -g 1001 -S nodejs && \
    adduser -S typing -u 1001

# 更改文件所有权
RUN chown -R typing:nodejs /app
USER typing

# 暴露端口
EXPOSE 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# 启动命令
CMD ["pnpm", "preview", "--host", "0.0.0.0", "--port", "3000"]