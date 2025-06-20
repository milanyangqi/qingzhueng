# 青竹英语网站部署指南

## 项目概述

青竹英语是一个功能完整的英语学习网站，包含用户管理、时文阅读等核心功能。本文档提供详细的部署和配置指南，确保系统正确运行。

## 快速开始

### 方法一：本地开发部署

1. **环境要求**
   - Python 3.9+
   - pip
   - 现代浏览器

2. **快速启动**
   ```bash
   # 进入项目目录
   cd myengweb
   
   # 运行启动脚本（自动初始化管理员账号）
   ./start.sh start-local
   ```

3. **手动启动**
   ```bash
   # 创建虚拟环境
   python3 -m venv venv
   source venv/bin/activate
   
   # 安装依赖
   pip install -r backend/requirements.txt
   
   # 启动应用
   python backend/app.py
   
   # 初始化管理员账号（需要单独执行）
   ./start.sh init-admin
   ```

### 方法二：Docker部署

1. **环境要求**
   - Docker
   - Docker Compose

2. **使用Docker Compose（推荐）**
   ```bash
   # 构建并启动服务（自动初始化管理员账号）
   ./start.sh start
   
   # 或者直接使用docker-compose
   docker-compose up -d
   
   # 查看日志
   docker-compose logs -f
   
   # 停止服务
   docker-compose down
   ```

3. **使用Docker**
   ```bash
   # 构建镜像
   docker build -t qingzhu-english .
   
   # 运行容器（自动初始化管理员账号）
   docker run -d -p 5001:5001 \
     -e SECRET_KEY=$(openssl rand -hex 32) \
     --name qingzhu-english qingzhu-english
   ```

## 访问信息

- **网站地址**: http://localhost:5001
- **默认管理员账号**: admin
- **默认管理员密码**: admin123

> **重要安全提示**: 首次登录后请立即修改默认管理员密码！

## 项目结构

```
myengweb/
├── backend/                 # 后端代码
│   ├── app.py              # Flask应用主文件
│   └── requirements.txt    # Python依赖
├── frontend/               # 前端代码
│   ├── templates/          # HTML模板
│   │   ├── index.html      # 首页/登录注册
│   │   ├── dashboard.html  # 用户仪表板
│   │   ├── reading.html    # 时文阅读
│   │   ├── admin.html      # 管理员后台
│   │   ├── profile.html    # 用户资料
│   │   └── my_articles.html # 我的文章
│   └── static/             # 静态资源
│       ├── css/
│       │   └── style.css   # 样式文件
│       └── js/
│           ├── auth.js     # 认证相关
│           └── reading.js  # 阅读功能
├── data/                   # 数据目录
├── logs/                   # 日志目录
├── Dockerfile              # Docker镜像构建文件
├── docker-compose.yml      # Docker Compose配置
├── start.sh               # 启动脚本
└── README.md              # 项目说明
```

## 功能特性

### 1. 用户管理
- 用户注册/登录
- 用户资料管理
- 密码安全验证

### 2. 管理员后台
- 用户管理
- 系统设置
- 数据统计

### 3. 时文阅读（核心功能）
- 文本输入和处理
- 自动生成文章标题
- 智能排版
- 重点单词标注
- 音标和翻译显示
- 单词发音功能
- 文章保存和管理

### 4. 响应式设计
- 支持桌面和移动设备
- 现代化UI界面
- 暗色主题支持

## 配置说明

### 环境变量

在生产环境中，建议设置以下环境变量：

```bash
# Flask配置
export FLASK_ENV=production
export SECRET_KEY=$(openssl rand -hex 32)  # 随机生成安全密钥

# 数据库配置
export DATABASE_URL=sqlite:///data/qingzhu_english.db
# 如果使用PostgreSQL
# export DATABASE_URL=postgresql://qingzhu:password@localhost:5432/qingzhu_english

# 管理员账号配置（可选，默认为admin/admin123）
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=secure_password_here
export ADMIN_EMAIL=admin@example.com

# 其他配置
export PORT=5001
export TZ=Asia/Shanghai
```

### 数据库

默认使用SQLite数据库，数据文件存储在 `data/` 目录中。

如需使用其他数据库，请修改 `DATABASE_URL` 环境变量，并取消注释 `docker-compose.yml` 中的相关服务配置。

#### 管理员账号初始化

系统在首次启动时会自动创建管理员账号：

- **用户名**: admin
- **密码**: admin123
- **邮箱**: admin@example.com

您也可以通过以下命令手动初始化管理员账号：

```bash
# 使用启动脚本初始化
./start.sh init-admin
```

## 生产环境部署

### 1. 服务器要求
- Linux服务器（推荐Ubuntu 20.04+）
- 2GB+ 内存
- 10GB+ 磁盘空间
- Docker和Docker Compose

### 2. 部署步骤

```bash
# 1. 克隆代码到服务器
git clone <repository-url> /opt/qingzhu-english
cd /opt/qingzhu-english

# 2. 修改配置
cp docker-compose.yml docker-compose.prod.yml
# 编辑 docker-compose.prod.yml，修改密钥等敏感信息

# 3. 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 4. 设置开机自启
sudo systemctl enable docker
```

### 3. 反向代理（可选）

使用Nginx作为反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. SSL证书（推荐）

使用Let's Encrypt获取免费SSL证书：

```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com
```

## 维护和监控

### 日志查看

```bash
# Docker Compose日志
docker-compose logs -f

# 应用日志
tail -f logs/app.log
```

### 数据备份

```bash
# 备份数据库
cp data/qingzhu_english.db backup/qingzhu_english_$(date +%Y%m%d).db

# 备份用户上传文件
tar -czf backup/uploads_$(date +%Y%m%d).tar.gz uploads/
```

### 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose down
docker-compose up -d --build
```

## 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 查看端口占用
   lsof -i :5001
   
   # 修改端口
   # 编辑 docker-compose.yml 中的端口映射
   ```

2. **数据库连接失败**
   - 检查数据目录权限
   - 确认数据库文件路径

3. **静态文件加载失败**
   - 检查文件路径
   - 确认文件权限

### 性能优化

1. **使用生产级WSGI服务器**
   ```bash
   # 安装gunicorn
   pip install gunicorn
   
   # 启动应用
   gunicorn -w 4 -b 0.0.0.0:5001 backend.app:app
   ```

2. **启用缓存**
   - 添加Redis缓存
   - 启用浏览器缓存

3. **数据库优化**
   - 添加索引
   - 定期清理日志

## 安全建议

1. **修改默认密码**
   - 首次部署后立即修改管理员密码
   - 使用强密码（至少12位，包含大小写字母、数字和特殊字符）

2. **使用HTTPS**
   - 生产环境必须使用SSL证书
   - 推荐使用Let's Encrypt免费证书

3. **定期备份**
   - 设置自动备份计划（至少每日备份一次）
   - 将备份存储在不同的物理位置

4. **更新依赖**
   - 定期更新Python包（检查安全漏洞）
   - 更新Docker镜像
   - 启用自动安全更新

5. **访问控制**
   - 使用防火墙限制访问
   - 考虑使用反向代理（如Nginx）
   - 限制管理员IP访问范围

6. **监控系统**
   - 设置日志监控和告警
   - 监控异常登录尝试

## 技术支持

如遇到问题，请检查：
1. 日志文件
2. 网络连接
3. 权限设置
4. 环境变量配置

---

**注意**: 这是一个基础版本，后续可根据实际需求添加更多功能和优化。