#!/usr/bin/env bash

set -e

APP_NAME="制造业Agent Demo平台"
APP_DIR="manufacturing_mvp"
PYTHON_REQUIRED="3.11"
STREAMLIT_PORT="8501"

print_banner() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║           🏭 $APP_NAME 一键启动脚本                        ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
}

print_success() {
    echo -e "\033[32m✅ $1\033[0m"
}

print_warning() {
    echo -e "\033[33m⚠️  $1\033[0m"
}

print_error() {
    echo -e "\033[31m❌ $1\033[0m"
}

print_info() {
    echo -e "\033[36mℹ️  $1\033[0m"
}

check_python() {
    print_info "检查Python环境..."
    
    VENV_PYTHON="../venv/bin/python"
    
    if [ -f "$VENV_PYTHON" ]; then
        PYTHON_VERSION=$($VENV_PYTHON --version | cut -d' ' -f2)
        print_info "使用项目虚拟环境Python: $PYTHON_VERSION"
        print_success "Python环境检查通过"
        return 0
    fi
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装，请先安装 Python $PYTHON_REQUIRED+"
        echo "   macOS: brew install python@3.11"
        echo "   Linux: sudo apt install python3.11"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_info "当前Python版本: $PYTHON_VERSION"
    
    local major=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    local minor=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 11 ]); then
        print_error "Python版本过低，需要 $PYTHON_REQUIRED+"
        exit 1
    fi
    
    print_success "Python环境检查通过"
}

check_virtualenv() {
    print_info "检查虚拟环境..."
    VENV_DIR="../venv"
    
    if [ -d "$VENV_DIR" ]; then
        print_success "虚拟环境已存在"
        return 0
    fi
    
    print_warning "虚拟环境不存在，正在创建..."
    python3 -m venv "$VENV_DIR"
    print_success "虚拟环境创建成功"
}

activate_virtualenv() {
    print_info "激活虚拟环境..."
    VENV_DIR="../venv"
    
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
        print_success "虚拟环境激活成功"
    elif [ -f "$VENV_DIR/Scripts/activate" ]; then
        source "$VENV_DIR/Scripts/activate"
        print_success "虚拟环境激活成功"
    else
        print_error "虚拟环境激活失败"
        exit 1
    fi
}

install_dependencies() {
    print_info "检查依赖..."
    
    if ! python3 -c "import agentscope" &> /dev/null; then
        print_warning "依赖未安装，正在安装..."
        
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt
        else
            print_warning "未找到requirements.txt，安装核心依赖..."
            pip install agentscope streamlit pydantic python-dotenv
        fi
        
        print_success "依赖安装完成"
    else
        print_success "核心依赖已安装"
    fi
}

check_port() {
    print_info "检查端口 $STREAMLIT_PORT 是否被占用..."
    
    if lsof -Pi :$STREAMLIT_PORT -sTCP:LISTEN -t &> /dev/null; then
        print_warning "端口 $STREAMLIT_PORT 已被占用"
        print_info "尝试停止占用端口的进程..."
        lsof -Pi :$STREAMLIT_PORT -sTCP:LISTEN -t | xargs kill -9 2>/dev/null || true
        
        sleep 2
        
        if lsof -Pi :$STREAMLIT_PORT -sTCP:LISTEN -t &> /dev/null; then
            print_warning "端口仍被占用，将使用随机端口启动"
            STREAMLIT_PORT=""
        else
            print_success "端口已释放"
        fi
    else
        print_success "端口 $STREAMLIT_PORT 可用"
    fi
}

configure_proxy() {
    print_info "检查网络代理配置..."
    
    if [ -z "$http_proxy" ] && [ -z "$https_proxy" ]; then
        print_warning "未设置网络代理，若访问GitHub或外部API失败，请设置代理"
        print_info "示例: export http_proxy=http://127.0.0.1:10887"
        print_info "示例: export https_proxy=http://127.0.0.1:10887"
    else
        print_success "代理已配置: $http_proxy"
    fi
}

start_streamlit() {
    print_info "启动Streamlit服务..."
    
    if [ -n "$STREAMLIT_PORT" ]; then
        print_info "访问地址: http://localhost:$STREAMLIT_PORT"
        print_info "等待服务启动..."
        streamlit run app.py --server.port $STREAMLIT_PORT --server.address 0.0.0.0
    else
        print_info "访问地址: http://localhost:8501 (随机端口)"
        print_info "等待服务启动..."
        streamlit run app.py --server.address 0.0.0.0
    fi
}

main() {
    print_banner
    
    cd "$(dirname "$0")/$APP_DIR"
    
    check_python
    check_virtualenv
    activate_virtualenv
    install_dependencies
    check_port
    configure_proxy
    
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                  🚀 启动参数配置                          ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    print_info "Python版本: $(python3 --version | cut -d' ' -f2)"
    print_info "虚拟环境: $(which python)"
    print_info "端口: ${STREAMLIT_PORT:-随机}"
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                   🎯 开始启动服务                         ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    
    start_streamlit
}

main "$@"