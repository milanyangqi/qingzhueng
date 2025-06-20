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

### 本地开发
```bash
# 安装依赖
pip install -r backend/requirements.txt

# 启动服务
python backend/app.py
```

### Docker 部署
```bash
# 构建并启动
docker-compose up -d
```

访问地址：http://localhost:5001

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