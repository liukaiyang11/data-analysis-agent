#!/bin/bash
# =============================================================================
# DeepSeek OCR vLLM 服务启动脚本
# 功能: 创建conda环境、安装依赖、启动服务、监控状态
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="${SCRIPT_DIR}/logs"

# 读取 .env 配置
if [ -f "${SCRIPT_DIR}/.env" ]; then
    export $(grep -v '^#' "${SCRIPT_DIR}/.env" | xargs)
else
    echo -e "${RED}[ERROR]${NC} 未找到 .env 配置文件"
    echo -e "${YELLOW}[INFO]${NC} 请复制 .env.example 为 .env 并修改配置"
    exit 1
fi

# 检查 Python 解释器路径
if [ -n "$PYTHON_PATH" ] && [ -f "$PYTHON_PATH" ]; then
    # 使用指定的 Python 路径（miniconda 方式）
    PYTHON_CMD="$PYTHON_PATH"
    USE_DIRECT_PYTHON=true
    print_info "使用指定 Python: $PYTHON_PATH"
else
    # 使用 conda 环境
    if ! command -v conda &> /dev/null; then
        print_error "未找到 conda 命令，请安装 conda 或设置 PYTHON_PATH"
        exit 1
    fi
    PYTHON_CMD="conda run -n ${CONDA_ENV_NAME} python"
    USE_DIRECT_PYTHON=false
    print_info "使用 conda 环境: ${CONDA_ENV_NAME}"
fi

# 创建日志目录
mkdir -p "${LOGS_DIR}"

# 日志文件路径
SETUP_LOG="${LOGS_DIR}/setup_$(date +%Y%m%d_%H%M%S).log"
SERVICE_LOG="${LOGS_DIR}/deepseek_ocr_server_${PORT}.log"

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}=====================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}=====================================${NC}"
}

# 检查系统依赖
check_system_dependencies() {
    print_header "检查系统依赖"

    # 检查 Python 环境
    if [ "$USE_DIRECT_PYTHON" = "true" ]; then
        if [ ! -f "$PYTHON_CMD" ]; then
            print_error "指定的 Python 路径不存在: $PYTHON_CMD"
            exit 1
        fi
        print_info "Python 环境: $PYTHON_CMD"
    else
        if ! command -v conda &> /dev/null; then
            print_error "conda 未安装或未在PATH中"
            exit 1
        fi
        print_info "Conda 环境: ${CONDA_ENV_NAME}"
    fi

    # 检查 GPU
    if ! command -v nvidia-smi &> /dev/null; then
        print_error "nvidia-smi 不可用，请检查CUDA驱动"
        exit 1
    fi

    # 显示GPU状态
    print_info "当前GPU状态："
    nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits | while IFS=, read -r index name used total util; do
        if [ "$util" -lt 5 ]; then
            print_success "GPU $index: $name (${used}MB/${total}MB) - 可用"
        else
            print_warning "GPU $index: $name (${used}MB/${total}MB) - 使用中 (${util}%)"
        fi
    done

    # 检查模型路径
    if [ ! -d "$MODEL_PATH" ]; then
        print_warning "模型路径不存在: $MODEL_PATH"
        print_info "请修改 .env 文件中的 MODEL_PATH 变量为正确的路径"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "模型路径存在: $MODEL_PATH"
    fi

    echo
}

# 创建环境
create_environment() {
    print_header "创建环境"

    if [ "$USE_DIRECT_PYTHON" = "true" ]; then
        print_info "使用指定的 Python 路径，无需创建环境"
        echo
        return 0
    fi

    # 检查环境是否已存在
    if conda env list | grep -q "^${CONDA_ENV_NAME}\s"; then
        print_warning "Conda环境 '${CONDA_ENV_NAME}' 已存在"
        read -p "是否删除并重新创建? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "删除现有环境..."
            conda env remove -n "${CONDA_ENV_NAME}" -y
        else
            print_info "使用现有环境"
            return 0
        fi
    fi

    print_info "创建conda环境: ${CONDA_ENV_NAME} (Python ${PYTHON_VERSION})"
    conda create -n "${CONDA_ENV_NAME}" python="${PYTHON_VERSION}" -y

    print_success "Conda环境创建完成"
    echo
}

# 安装依赖
install_dependencies() {
    print_header "安装依赖包"

    if [ ! -f "${SCRIPT_DIR}/requirements.txt" ]; then
        print_error "requirements.txt 文件不存在"
        exit 1
    fi

    print_info "激活conda环境并安装依赖..."

    cat > /tmp/install_deps.py << 'EOF'
import subprocess
import sys
import os

def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        print(f"ERROR: 安装失败: {package}")
        return False

def main():
    print("[INFO] 开始安装依赖包...")
    print("[INFO] 升级pip...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=False)

    requirements_file = "requirements.txt"
    if not os.path.exists(requirements_file):
        print(f"ERROR: {requirements_file} 不存在")
        return False

    print(f"[INFO] 从 {requirements_file} 安装依赖...")

    special_packages = []
    regular_packages = []

    with open(requirements_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '@ file://' in line:
                    special_packages.append(line)
                else:
                    regular_packages.append(line)

    print(f"[INFO] 安装 {len(regular_packages)} 个常规包...")
    failed_packages = []

    for i, package in enumerate(regular_packages, 1):
        print(f"[{i}/{len(regular_packages)}] 安装: {package}")
        if not install_package(package):
            failed_packages.append(package)

    if special_packages:
        print(f"[INFO] 安装 {len(special_packages)} 个特殊包...")
        for package in special_packages:
            print(f"特殊包: {package}")
            install_package(package)

    if failed_packages:
        print(f"\nWARNING: {len(failed_packages)} 个包安装失败:")
        for pkg in failed_packages:
            print(f"  - {pkg}")
        print("\n[INFO] 尝试使用 --force-reinstall 重新安装失败的包...")
        for package in failed_packages:
            print(f"重新安装: {package}")
            install_package(f"--force-reinstall {package}")

    print("[SUCCESS] 依赖安装完成!")
    return True

if __name__ == "__main__":
    main()
EOF

    $PYTHON_CMD /tmp/install_deps.py
    rm -f /tmp/install_deps.py

    print_success "依赖安装完成"
    echo
}

# 启动服务
start_service() {
    print_header "启动 DeepSeek OCR 服务"

    print_info "启动服务 (端口 ${PORT}, GPU ${GPU_ID})..."

    cat > /tmp/start_service.py << EOF
import subprocess
import sys
import os

def start_server():
    cmd = [
        sys.executable, "deepseek_ocr_server.py",
        "--model-path", "${MODEL_PATH}",
        "--gpu-id", "${GPU_ID}",
        "--port", "${PORT}",
        "--host", "${HOST}",
        "--cpu-workers", "${CPU_WORKERS}"
    ]

    print(f"[INFO] 启动命令: {' '.join(cmd)}")
    print(f"[INFO] 日志文件: ${SERVICE_LOG}")

    with open("${SERVICE_LOG}", 'w') as log_file:
        process = subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT, text=True)

    print(f"[SUCCESS] 服务已启动 (PID: {process.pid})")
    return process.pid

if __name__ == "__main__":
    start_server()
EOF

    $PYTHON_CMD /tmp/start_service.py
    rm -f /tmp/start_service.py

    print_success "服务启动完成"
    echo
}

# 监控服务状态
monitor_service() {
    print_header "监控服务状态"

    cat > /tmp/monitor_service.py << 'EOF'
import subprocess
import time
import requests
import json
import os

def check_service(port):
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] 服务 (端口 {port}): 运行正常")
            print(f"   状态: {data.get('status', 'unknown')}")
            if 'model_ready' in data:
                print(f"   模型就绪: {'是' if data['model_ready'] else '否'}")
            if 'cpu_workers' in data:
                print(f"   CPU工作线程: {data['cpu_workers']}")
            if 'gpu_workers' in data:
                print(f"   GPU工作线程: {data['gpu_workers']}")
            return True
        else:
            print(f"[ERROR] 服务 (端口 {port}): HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] 服务 (端口 {port}): 连接失败")
        return False
    except Exception as e:
        print(f"[ERROR] 服务 (端口 {port}): {e}")
        return False

def show_recent_logs(log_file, lines=20):
    if os.path.exists(log_file):
        print(f"\n[INFO] 最近日志 ({log_file}):")
        print("-" * 60)
        try:
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                for line in recent_lines:
                    print(line.rstrip())
        except Exception as e:
            print(f"读取日志失败: {e}")
        print("-" * 60)
    else:
        print(f"[WARNING] 日志文件不存在: {log_file}")

def main():
    print("[INFO] 监控 DeepSeek OCR 服务状态")
    print("=" * 60)

    port = ${PORT}

    if not check_service(port):
        print("\n[WARNING] 服务未运行或无法访问")
        return

    # 显示GPU使用情况
    print(f"\n[INFO] GPU使用情况:")
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=index,memory.used,memory.total,utilization.gpu',
                               '--format=csv,noheader,nounits'],
                              capture_output=True, text=True, timeout=5)
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                parts = line.split(', ')
                if len(parts) >= 4:
                    gpu_id, mem_used, mem_total, util = parts[:4]
                    print(f"   GPU {gpu_id}: {mem_used}MB/{mem_total}MB ({util}%)")
    except:
        print("   无法获取GPU信息")

    print(f"\n[INFO] 可用命令:")
    print(f"   测试API: curl http://localhost:{port}/health")
    print(f"   文档地址: http://localhost:{port}/docs")

    answer = input("\n是否查看最近日志? (y/N): ").strip().lower()
    if answer in ['y', 'yes']:
        show_recent_logs("${SERVICE_LOG}")

if __name__ == "__main__":
    main()
EOF

    $PYTHON_CMD /tmp/monitor_service.py
    rm -f /tmp/monitor_service.py
}

# 停止服务
stop_service() {
    print_header "停止 DeepSeek OCR 服务"

    print_info "查找运行中的服务..."

    pids=$(ps aux | grep deepseek_ocr_server | grep -v grep | awk '{print $2}')

    if [ -z "$pids" ]; then
        print_warning "没有找到运行中的服务"
        return
    fi

    print_info "发现以下进程:"
    ps aux | grep deepseek_ocr_server | grep -v grep | while IFS= read -r line; do
        pid=$(echo $line | awk '{print $2}')
        cmd=$(echo $line | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
        echo "  PID $pid: $cmd"
    done

    echo
    read -p "是否停止服务? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "停止服务..."
        echo "$pids" | xargs kill -TERM 2>/dev/null || true

        sleep 3

        remaining=$(ps aux | grep deepseek_ocr_server | grep -v grep | wc -l)
        if [ "$remaining" -gt 0 ]; then
            print_warning "部分进程仍在运行，强制终止..."
            ps aux | grep deepseek_ocr_server | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
        fi

        print_success "服务已停止"
    fi

    echo
}

# 显示使用信息
show_usage_info() {
    print_header "使用信息"

    print_info "服务已启动! 可以通过以下方式访问:"
    echo
    print_info "健康检查:"
    echo "  curl http://${HOST}:${PORT}/health"
    echo
    print_info "API文档:"
    echo "  http://${HOST}:${PORT}/docs"
    echo
    print_info "测试OCR:"
    echo "  curl -X POST \"http://${HOST}:${PORT}/ocr\" \\"
    echo "    -H \"accept: application/json\" \\"
    echo "    -H \"Content-Type: multipart/form-data\" \\"
    echo "    -F \"file=@test_image.jpg\""
    echo
    print_info "日志文件位置:"
    echo "  ${SERVICE_LOG}"
    echo
    print_info "停止服务:"
    echo "  bash $0 stop"
    echo
}

# 主菜单
main_menu() {
    while true; do
        clear
        print_header "DeepSeek OCR vLLM 管理脚本"

        echo -e "${CYAN}1)${NC} 检查系统依赖"
        echo -e "${CYAN}2)${NC} 创建/更新环境"
        echo -e "${CYAN}3)${NC} 安装依赖包"
        echo -e "${CYAN}4)${NC} 启动服务"
        echo -e "${CYAN}5)${NC} 监控服务状态"
        echo -e "${CYAN}6)${NC} 查看使用信息"
        echo -e "${CYAN}7)${NC} 停止服务"
        echo -e "${CYAN}0)${NC} 退出"
        echo

        read -p "请选择操作: " -n 1 -r
        echo

        case $REPLY in
            1)
                check_system_dependencies
                read -p "按回车键继续..."
                ;;
            2)
                create_environment
                read -p "按回车键继续..."
                ;;
            3)
                install_dependencies
                read -p "按回车键继续..."
                ;;
            4)
                start_service
                show_usage_info
                read -p "按回车键继续..."
                ;;
            5)
                monitor_service
                read -p "按回车键继续..."
                ;;
            6)
                show_usage_info
                read -p "按回车键继续..."
                ;;
            7)
                stop_service
                read -p "按回车键继续..."
                ;;
            0)
                print_info "退出脚本"
                exit 0
                ;;
            *)
                print_error "无效选择，请重新输入"
                sleep 1
                ;;
        esac
    done
}

# 检查参数
if [ "${1:-}" = "stop" ]; then
    stop_service
    exit 0
elif [ "${1:-}" = "start" ]; then
    check_system_dependencies
    start_service
    show_usage_info
elif [ "${1:-}" = "auto" ]; then
    print_info "自动模式启动..."
    check_system_dependencies
    create_environment
    install_dependencies
    start_service
    show_usage_info

    read -p "是否启动服务监控? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        while true; do
            clear
            monitor_service
            sleep 30
        done
    fi
else
    main_menu
fi