# 青竹英语 - English Learning Platform

一个功能完整的英语学习网站，提供用户管理、时文阅读等功能。

## 功能特性

### 核心功能
- 用户注册登录系统
- 用户资料管理
- 管理员后台管理
- 时文阅读模块（自动生成标题、排版、重点单词标注）

### 技术特性
- 响应式设计
- Docker 部署支持
- 模块化架构
- 可扩展的权限系统

## 项目结构

```
myengweb/
├── backend/                 # 后端服务
│   ├── app.py              # Flask 主应用
│   ├── models/             # 数据模型
│   ├── routes/             # 路由处理
│   ├── utils/              # 工具函数
│   └── requirements.txt    # Python 依赖
├── frontend/               # 前端文件
│   ├── static/            # 静态资源
│   │   ├── css/           # 样式文件
│   │   ├── js/            # JavaScript 文件
│   │   └── images/        # 图片资源
│   └── templates/         # HTML 模板
├── docker-compose.yml     # Docker 编排文件
├── Dockerfile            # Docker 镜像构建
└── README.md            # 项目说明
```

## 快速开始

### Docker 部署（推荐）

#### 一键启动
```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 访问地址
- 主项目（英语学习平台）：http://localhost:5001
- 打字练习项目：http://localhost:3000

#### 管理命令
```bash
# 停止所有服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build

# 查看特定服务日志
docker-compose logs -f web      # 主项目日志
docker-compose logs -f typing   # 打字练习日志
```

### 本地开发
```bash
# 安装依赖
pip install -r backend/requirements.txt

# 启动主项目
python backend/app.py

# 启动打字练习项目（另开终端）
cd typing
npm install
npm start
```

### 使用启动脚本
```bash
# 使用Docker启动
./start.sh start

# 使用本地环境启动
./start.sh start-local

# 查看帮助
./start.sh help
```

## 主要模块

### 1. 用户系统
- 注册/登录
- 用户资料管理
- 权限控制

### 2. 管理员后台
- 用户管理
- 系统设置
- 数据统计

### 3. 时文阅读
- 文本输入与处理
- 自动标题生成
- 智能排版
- 重点单词标注
- 音标和翻译显示
- 自定义样式

## 开发计划

- [x] 项目架构设计
- [ ] 用户系统开发
- [ ] 管理员后台
- [ ] 时文阅读模块
- [ ] Docker 部署配置
- [ ] 测试与优化