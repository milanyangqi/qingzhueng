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
    echo -e "${BLUE}青竹英语网站启动脚本${NC}"
    echo -e "用法: $0 [选项]"
    echo -e "选项:"
    echo -e "  ${GREEN}start${NC}\t启动应用（默认使用Docker）"
    echo -e "  ${GREEN}start-local${NC}\t在本地环境启动应用"
    echo -e "  ${GREEN}stop${NC}\t停止应用"
    echo -e "  ${GREEN}restart${NC}\t重启应用"
    echo -e "  ${GREEN}status${NC}\t查看应用状态"
    echo -e "  ${GREEN}logs${NC}\t查看应用日志"
    echo -e "  ${GREEN}build${NC}\t构建Docker镜像"
    echo -e "  ${GREEN}init-admin${NC}\t初始化管理员账号"
    echo -e "  ${GREEN}help${NC}\t显示此帮助信息"
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
    docker-compose up -d
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}应用已成功启动！${NC}"
        echo -e "${BLUE}访问地址: http://localhost:5001${NC}"
        echo -e "${CYAN}默认管理员账号: admin${NC}"
        echo -e "${CYAN}默认管理员密码: admin123${NC}"
    else
        echo -e "${RED}启动失败，请检查错误信息。${NC}"
    fi
}

# 在本地环境启动应用
start_local() {
    echo -e "${YELLOW}正在本地环境启动应用...${NC}"
    check_python
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}创建Python虚拟环境...${NC}"
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate || { echo -e "${RED}无法激活虚拟环境${NC}"; exit 1; }
    
    # 安装依赖
    echo -e "${YELLOW}安装依赖...${NC}"
    pip install -r backend/requirements.txt
    
    # 创建数据目录
    mkdir -p data
    
    # 启动应用
    echo -e "${YELLOW}启动Flask应用...${NC}"
    export FLASK_APP=backend/app.py
    export FLASK_ENV=development
    python backend/app.py &
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}应用已成功启动！${NC}"
        echo -e "${BLUE}访问地址: http://localhost:5001${NC}"
        echo -e "${CYAN}默认管理员账号: admin${NC}"
        echo -e "${CYAN}默认管理员密码: admin123${NC}"
        echo -e "${YELLOW}提示: 使用 Ctrl+C 停止应用${NC}"
    else
        echo -e "${RED}启动失败，请检查错误信息。${NC}"
    fi
}

# 停止应用
stop_app() {
    echo -e "${YELLOW}正在停止应用...${NC}"
    docker-compose down
    echo -e "${GREEN}应用已停止${NC}"
    
    # 检查是否有本地Python进程需要停止
    local_pid=$(pgrep -f "python backend/app.py")
    if [ ! -z "$local_pid" ]; then
        echo -e "${YELLOW}停止本地Python进程...${NC}"
        kill $local_pid
        echo -e "${GREEN}本地进程已停止${NC}"
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
    echo -e "${YELLOW}应用状态:${NC}"
    docker-compose ps
    
    # 检查本地进程
    local_pid=$(pgrep -f "python backend/app.py")
    if [ ! -z "$local_pid" ]; then
        echo -e "${GREEN}本地Python进程正在运行，PID: $local_pid${NC}"
    else
        echo -e "${YELLOW}没有检测到本地Python进程${NC}"
    fi
}

# 查看应用日志
view_logs() {
    echo -e "${YELLOW}应用日志:${NC}"
    docker-compose logs --tail=100 -f
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
            view_logs
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