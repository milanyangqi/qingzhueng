#!/bin/bash

# 青竹英语网站启动脚本
# 作者：AI助手
# 更新日期：$(date +"%Y-%m-%d")
# 版本：1.1.0

# 颜色定义
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
RED="\033[0;31m"
CYAN="\033[0;36m"
NC="\033[0m" # No Color

# 显示帮助信息
show_help() {
    echo -e "${CYAN}青竹英语学习系统 - 启动脚本${NC}"
    echo -e "${YELLOW}使用方法: $0 [选项]${NC}"
    echo ""
    echo -e "${GREEN}可用选项:${NC}"
    echo -e "  ${BLUE}start${NC}        使用Docker启动应用（主项目+打字练习）"
    echo -e "  ${BLUE}start-local${NC}  使用本地环境启动应用（主项目+打字练习）"
    echo -e "  ${BLUE}stop${NC}         停止应用"
    echo -e "  ${BLUE}restart${NC}      重启应用"
    echo -e "  ${BLUE}status${NC}       查看应用状态"
    echo -e "  ${BLUE}logs${NC}         查看所有应用日志"
    echo -e "  ${BLUE}logs flask${NC}   查看Flask应用日志"
    echo -e "  ${BLUE}logs typing${NC}  查看打字练习应用日志"
    echo -e "  ${BLUE}build${NC}        构建Docker镜像"
    echo -e "  ${BLUE}init-admin${NC}   初始化管理员账号"
    echo -e "  ${BLUE}help${NC}         显示此帮助信息"
    echo ""
    echo -e "${YELLOW}示例:${NC}"
    echo -e "  $0 start          # 使用Docker启动应用"
    echo -e "  $0 start-local    # 使用本地环境启动应用"
    echo -e "  $0 stop           # 停止应用"
    echo -e "  $0 logs           # 查看所有应用日志"
    echo -e "  $0 logs flask     # 查看Flask应用日志"
    echo -e "  $0 logs typing    # 查看打字练习应用日志"
    echo ""
    echo -e "${CYAN}访问地址:${NC}"
    echo -e "  主项目: http://localhost:5001"
    echo -e "  打字练习: http://localhost:3000"
    echo ""
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}错误: Docker未安装。请先安装Docker。${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}错误: Docker Compose未安装。请先安装Docker Compose。${NC}"
        exit 1
    fi
}

# 检查Python环境
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}错误: Python3未安装。请先安装Python3。${NC}"
        exit 1
    fi
}

# 启动应用（Docker方式）
start_docker() {
    echo -e "${YELLOW}正在使用Docker启动应用...${NC}"
    
    # 检查并创建必要的目录
    mkdir -p data logs uploads
    
    # 设置目录权限
    chmod 755 data logs uploads
    
    # 启动应用
    docker-compose up -d
    
    # 等待应用启动
    echo -e "${YELLOW}等待应用启动...${NC}"
    sleep 15
    
    # 检查应用状态
    if docker-compose ps | grep -q "qingzhu_english.*Up" && docker-compose ps | grep -q "qingzhu_typing.*Up"; then
        echo -e "${GREEN}应用启动成功！${NC}"
        echo -e "${CYAN}主项目访问地址: http://localhost:5001${NC}"
        echo -e "${CYAN}打字练习访问地址: http://localhost:3000${NC}"
        echo -e "${CYAN}管理员账号: admin${NC}"
        echo -e "${CYAN}管理员密码: admin123${NC}"
    else
        echo -e "${RED}应用启动失败，请检查日志${NC}"
        docker-compose logs
        exit 1
    fi
}

# 在本地环境启动应用
start_local() {
    echo -e "${YELLOW}正在本地环境启动应用...${NC}"
    check_python
    
    # 检查Node.js版本
    if ! command -v node &> /dev/null; then
        echo -e "${RED}Node.js 未安装，请先安装Node.js${NC}"
        exit 1
    fi
    
    # 检查并创建必要的目录
    mkdir -p data logs uploads
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}创建Python虚拟环境...${NC}"
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate || { echo -e "${RED}无法激活虚拟环境${NC}"; exit 1; }
    
    # 安装Python依赖
    echo -e "${YELLOW}安装依赖...${NC}"
    pip install -r backend/requirements.txt
    
    # 安装Node.js依赖（如果需要）
    if [ -d "typing" ] && [ -f "typing/package.json" ]; then
        echo -e "${YELLOW}安装打字练习项目依赖...${NC}"
        cd typing
        npm install
        cd ..
    fi
    
    # 设置环境变量
    export FLASK_APP=backend/app.py
    export FLASK_ENV=development
    export DATABASE_URL=sqlite:///data/app.db
    
    # 启动Flask应用
    echo -e "${YELLOW}启动Flask应用...${NC}"
    nohup python backend/app.py > logs/app.log 2>&1 &
    
    # 启动打字练习应用（如果存在）
    if [ -d "typing" ] && [ -f "typing/package.json" ]; then
        echo -e "${YELLOW}启动打字练习应用...${NC}"
        cd typing
        nohup npm start > ../logs/typing.log 2>&1 &
        cd ..
    fi
    
    # 等待应用启动
    sleep 8
    
    # 检查应用是否启动成功
    flask_running=$(pgrep -f "python backend/app.py")
    typing_running=$(pgrep -f "npm start")
    
    if [ ! -z "$flask_running" ]; then
        echo -e "${GREEN}Flask应用启动成功！${NC}"
        echo -e "${CYAN}主项目访问地址: http://localhost:5001${NC}"
        echo -e "${CYAN}Flask日志文件: logs/app.log${NC}"
    else
        echo -e "${RED}Flask应用启动失败，请检查日志文件${NC}"
        cat logs/app.log
    fi
    
    if [ ! -z "$typing_running" ]; then
        echo -e "${GREEN}打字练习应用启动成功！${NC}"
        echo -e "${CYAN}打字练习访问地址: http://localhost:3000${NC}"
        echo -e "${CYAN}打字练习日志文件: logs/typing.log${NC}"
    elif [ -d "typing" ]; then
        echo -e "${YELLOW}打字练习应用启动失败，请检查日志文件${NC}"
        if [ -f "logs/typing.log" ]; then
            cat logs/typing.log
        fi
    fi
    
    if [ -z "$flask_running" ]; then
        exit 1
    fi
}

# 停止应用
stop_app() {
    echo -e "${YELLOW}正在停止应用...${NC}"
    docker-compose down
    echo -e "${GREEN}Docker应用已停止${NC}"
    
    # 检查是否有本地Python进程需要停止
    local_flask_pid=$(pgrep -f "python backend/app.py")
    if [ ! -z "$local_flask_pid" ]; then
        echo -e "${YELLOW}停止本地Flask进程...${NC}"
        kill $local_flask_pid
        echo -e "${GREEN}本地Flask进程已停止${NC}"
    fi
    
    # 检查是否有本地Node.js进程需要停止
    local_node_pid=$(pgrep -f "npm start")
    if [ ! -z "$local_node_pid" ]; then
        echo -e "${YELLOW}停止本地Node.js进程...${NC}"
        kill $local_node_pid
        echo -e "${GREEN}本地Node.js进程已停止${NC}"
    fi
}

# 重启应用
restart_app() {
    echo -e "${YELLOW}正在重启应用...${NC}"
    stop_app
    sleep 2
    start_docker
}

# 查看应用状态
check_status() {
    echo -e "${YELLOW}Docker应用状态:${NC}"
    docker-compose ps
    
    echo -e "${YELLOW}本地进程状态:${NC}"
    # 检查本地Flask进程
    local_flask_pid=$(pgrep -f "python backend/app.py")
    if [ ! -z "$local_flask_pid" ]; then
        echo -e "${GREEN}本地Flask进程正在运行，PID: $local_flask_pid${NC}"
    else
        echo -e "${YELLOW}没有检测到本地Flask进程${NC}"
    fi
    
    # 检查本地Node.js进程
    local_node_pid=$(pgrep -f "npm start")
    if [ ! -z "$local_node_pid" ]; then
        echo -e "${GREEN}本地Node.js进程正在运行，PID: $local_node_pid${NC}"
    else
        echo -e "${YELLOW}没有检测到本地Node.js进程${NC}"
    fi
}

# 查看应用日志
view_logs() {
    if [ "$1" == "typing" ]; then
        echo -e "${YELLOW}打字练习应用日志:${NC}"
        if [ -f "logs/typing.log" ]; then
            tail -f logs/typing.log
        else
            docker-compose logs --tail=100 -f typing
        fi
    elif [ "$1" == "flask" ]; then
        echo -e "${YELLOW}Flask应用日志:${NC}"
        if [ -f "logs/app.log" ]; then
            tail -f logs/app.log
        else
            docker-compose logs --tail=100 -f web
        fi
    else
        echo -e "${YELLOW}所有应用日志:${NC}"
        docker-compose logs --tail=100 -f
    fi
}

# 构建Docker镜像
build_image() {
    echo -e "${YELLOW}正在构建Docker镜像...${NC}"
    docker-compose build
    echo -e "${GREEN}Docker镜像构建完成${NC}"
}

# 初始化管理员账号
init_admin() {
    echo -e "${YELLOW}正在初始化管理员账号...${NC}"
    
    # 检查是否在Docker环境中运行
    if [ "$1" == "docker" ]; then
        echo -e "${YELLOW}在Docker环境中初始化管理员账号...${NC}"
        docker-compose exec web python -c "import sys
sys.path.append('/app')
from backend.app import db, User, app
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print('管理员账号已存在')
    else:
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('管理员账号创建成功')
"
    else
        echo -e "${YELLOW}在本地环境中初始化管理员账号...${NC}"
        # 检查虚拟环境
        if [ ! -d "venv" ]; then
            echo -e "${YELLOW}创建Python虚拟环境...${NC}"
            python3 -m venv venv
        fi
        
        # 激活虚拟环境
        source venv/bin/activate || { echo -e "${RED}无法激活虚拟环境${NC}"; exit 1; }
        
        # 执行Python代码初始化管理员账号
        python -c "import sys
sys.path.append('.')
from backend.app import db, User, app
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print('管理员账号已存在')
    else:
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('管理员账号创建成功')
"
    fi
    
    echo -e "${GREEN}管理员账号初始化完成${NC}"
    echo -e "${CYAN}管理员账号: admin${NC}"
    echo -e "${CYAN}管理员密码: admin123${NC}"
    echo -e "${YELLOW}请尽快登录并修改默认密码！${NC}"
}

# 主函数
main() {
    # 如果没有参数，显示帮助信息
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi

    case "$1" in
        start)
            check_docker
            start_docker
            # 自动初始化管理员账号
            sleep 5
            init_admin docker
            ;;
        start-local)
            start_local
            # 自动初始化管理员账号
            sleep 5
            init_admin local
            ;;
        stop)
            stop_app
            ;;
        restart)
            restart_app
            ;;
        status)
            check_status
            ;;
        logs)
            view_logs "$2"
            ;;
        build)
            check_docker
            build_image
            ;;
        init-admin)
            if docker-compose ps | grep -q "qingzhu_english.*Up"; then
                init_admin docker
            else
                init_admin local
            fi
            ;;
        help)
            show_help
            ;;
        *)
            echo -e "${RED}未知选项: $1${NC}"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"