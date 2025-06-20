#!/bin/bash

# 青竹英语网站启动脚本

echo "=== 青竹英语网站启动脚本 ==="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查是否在项目根目录
if [ ! -f "backend/app.py" ]; then
    echo "错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装Python依赖..."
pip install -r backend/requirements.txt

# 创建必要的目录
mkdir -p data
mkdir -p logs

# 设置环境变量
export FLASK_APP=backend/app.py
export FLASK_ENV=development

echo "启动青竹英语网站..."
echo "访问地址: http://localhost:1120"
echo "管理员账号: admin"
echo "管理员密码: admin123"
echo "按 Ctrl+C 停止服务"
echo ""

# 启动应用
python backend/app.py