#!/bin/bash
# =============================================================================
# DeepSeek OCR vLLM 快速启动脚本
# =============================================================================

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 读取 .env 配置
if [ -f "${SCRIPT_DIR}/.env" ]; then
    export $(grep -v '^#' "${SCRIPT_DIR}/.env" | xargs)
else
    print_error "未找到 .env 配置文件"
    print_info "请复制 .env.example 为 .env 并修改配置"
    exit 1
fi

# 检查 Python 解释器路径
if [ -n "$PYTHON_PATH" ] && [ -f "$PYTHON_PATH" ]; then
    # 使用指定的 Python 路径（miniconda 方式）
    PYTHON_CMD="$PYTHON_PATH"
    print_info "使用指定 Python: $PYTHON_PATH"
else
    # 使用 conda 环境
    if ! command -v conda &> /dev/null; then
        print_error "未找到 conda 命令，请安装 conda 或设置 PYTHON_PATH"
        exit 1
    fi
    PYTHON_CMD="conda run -n ${CONDA_ENV_NAME} python"
    print_info "使用 conda 环境: ${CONDA_ENV_NAME}"
fi

print_info "DeepSeek OCR vLLM 快速启动..."

# 检查环境和依赖
print_info "检查环境和依赖..."

if [ -n "$PYTHON_PATH" ]; then
    # 使用指定 Python 路径（miniconda 方式）
    if ! $PYTHON_CMD -c "import vllm" &>/dev/null; then
        print_info "安装依赖包..."
        $PYTHON_CMD -m pip install -r "${SCRIPT_DIR}/requirements.txt"
    fi
else
    # 使用 conda 环境
    if ! conda env list | grep -q "^${CONDA_ENV_NAME}\s"; then
        print_info "创建conda环境..."
        conda create -n "${CONDA_ENV_NAME}" python="${PYTHON_VERSION}" -y
    fi

    if ! conda run -n "${CONDA_ENV_NAME}" python -c "import vllm" &>/dev/null; then
        print_info "安装依赖包..."
        conda run -n "${CONDA_ENV_NAME}" pip install -r "${SCRIPT_DIR}/requirements.txt"
    fi
fi

# 检查模型路径
if [ ! -d "$MODEL_PATH" ]; then
    print_warning "模型路径不存在: $MODEL_PATH"
    print_info "请修改 .env 文件中的 MODEL_PATH 变量"
    exit 1
fi

# 创建日志目录
mkdir -p "${SCRIPT_DIR}/logs"

# 启动服务
print_info "启动服务 (端口 ${PORT}, GPU ${GPU_ID})..."
LOG_FILE="${SCRIPT_DIR}/logs/deepseek_ocr_server_${PORT}_$(date +%Y%m%d_%H%M%S).log"

# 启动服务
if [ -n "$PYTHON_PATH" ]; then
    # 使用指定 Python 路径（miniconda 方式）
    cat > /tmp/quick_start.py << EOF
import subprocess
import sys
import os

cmd = [
    sys.executable, "deepseek_ocr_server.py",
    "--model-path", "${MODEL_PATH}",
    "--gpu-id", "${GPU_ID}",
    "--port", "${PORT}",
    "--host", "${HOST}",
    "--cpu-workers", "${CPU_WORKERS}"
]

print(f"[INFO] 启动命令: {' '.join(cmd)}")
print(f"[INFO] 日志文件: ${LOG_FILE}")

with open("${LOG_FILE}", 'w') as log_file:
    process = subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT, text=True)

print(f"[SUCCESS] 服务已启动 (PID: {process.pid})")
print(f"[INFO] API文档: http://${HOST}:${PORT}/docs")
print(f"[INFO] 健康检查: curl http://${HOST}:${PORT}/health")
EOF

    $PYTHON_CMD /tmp/quick_start.py
else
    # 使用 conda 环境
    cat > /tmp/quick_start.py << EOF
import subprocess
import sys
import os

cmd = [
    sys.executable, "deepseek_ocr_server.py",
    "--model-path", "${MODEL_PATH}",
    "--gpu-id", "${GPU_ID}",
    "--port", "${PORT}",
    "--host", "${HOST}",
    "--cpu-workers", "${CPU_WORKERS}"
]

print(f"[INFO] 启动命令: {' '.join(cmd)}")
print(f"[INFO] 日志文件: ${LOG_FILE}")

with open("${LOG_FILE}", 'w') as log_file:
    process = subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT, text=True)

print(f"[SUCCESS] 服务已启动 (PID: {process.pid})")
print(f"[INFO] API文档: http://${HOST}:${PORT}/docs")
print(f"[INFO] 健康检查: curl http://${HOST}:${PORT}/health")
EOF

    conda run -n "${CONDA_ENV_NAME}" python /tmp/quick_start.py
fi

rm -f /tmp/quick_start.py

print_success "启动完成!"
print_info "使用以下命令监控:"
echo "  tail -f ${LOG_FILE}"
echo "  curl http://${HOST}:${PORT}/health"