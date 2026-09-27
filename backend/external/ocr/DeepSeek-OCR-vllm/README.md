# DeepSeek OCR vLLM 服务 - 新手完整部署指南

> 🎯 **适用人群**：零基础小白、AI 爱好者、开发者
> ⏱️ **预计时间**：30-60分钟
> 💻 **系统要求**：Linux 服务器，NVIDIA GPU，24GB+ 内存

---

## 📚 目录

1. [系统要求](#系统要求)
2. [什么是 DeepSeek OCR](#什么是-deepseek-ocr)
3. [准备工作](#准备工作)
4. [步骤一：下载 DeepSeek OCR 模型](#步骤一下载-deepseek-ocr-模型)
5. [步骤二：下载项目代码](#步骤二下载项目代码)
6. [步骤三：配置环境](#步骤三配置环境)
7. [步骤四：启动服务](#步骤四启动服务)
8. [步骤五：测试服务](#步骤五测试服务)
9. [常见问题解答](#常见问题解答)
10. [故障排除](#故障排除)

---

## 📋 系统要求

### 硬件要求
- **GPU**: NVIDIA RTX 3090/4090 或同等级别
- **显存**: 最少 16GB，推荐 24GB+
- **内存**: 最少 32GB，推荐 64GB+
- **存储**: 至少 100GB 可用空间（模型较大）

### 软件要求
- **操作系统**: Ubuntu 18.04+ / CentOS 7+ / Rocky Linux 8+
- **CUDA**: 11.8+ 或 12.0+
- **Python**: 3.9+ （会自动安装）
- **conda/miniconda**: 必须安装

---

## 🤔 什么是 DeepSeek OCR

DeepSeek OCR 是一款基于深度学习的 OCR（光学字符识别）工具，具有以下特点：

- ✅ **高精度**：能够识别各种文档、图片中的文字
- ✅ **多格式**：支持图片、PDF 等多种输入格式
- ✅ **中文友好**：对中文识别效果优秀
- ✅ **结构化输出**：输出格式化的 Markdown 文档
- ✅ **批处理**：支持批量处理多页文档

---

## 🛠️ 准备工作

### 1. 检查 GPU 是否可用
```bash
nvidia-smi
```

**预期输出**（类似）：
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.104.05   Driver Version: 535.104.05   CUDA Version: 12.2     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|                               |                      |               MIG M. |
|===============================+======================+======================|
|   0  NVIDIA GeForce ...  Off  | 00000000:01:00.0 Off |                  N/A |
| 30%   35C    P8    25W / 450W |      0MiB / 24576MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
```

### 2. 检查 conda 是否安装
```bash
conda --version
```

**如果没有安装 conda**，请先安装 miniconda：
```bash
# 下载 miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# 安装
bash Miniconda3-latest-Linux-x86_64.sh

# 重启终端或执行
source ~/.bashrc
```

### 3. 检查磁盘空间
```bash
df -h
```
确保至少有 100GB 可用空间。

---

## 📥 步骤一：下载 DeepSeek OCR 模型

### 方法1：从 Hugging Face 下载（推荐）

```bash
# 创建模型存放目录
mkdir -p /home/你的用户名/models/

# 进入目录
cd /home/你的用户名/models/

# 克隆模型仓库
git clone https://huggingface.co/deepseek-ai/deepseek-ocr-1.5b

# 或者使用 git lfs（如果模型很大）
git lfs install
git clone https://huggingface.co/deepseek-ai/deepseek-ocr-1.5b
```

### 方法2：手动下载

1. 访问 [Hugging Face 模型页面](https://huggingface.co/deepseek-ai/deepseek-ocr-1.5b)
2. 点击 "Files and versions"
3. 下载所有文件到同一个文件夹
4. 将文件夹重命名为 `deepseek-ocr-1.5b`

### 方法3：使用 ModelScope（国内用户）

```bash
# 安装 modelscope
pip install modelscope

# 使用 Python 下载
python -c "
from modelscope import snapshot_download
model_dir = snapshot_download('deepseek-ai/deepseek-ocr-1.5b', cache_dir='/home/你的用户名/models/')
print(f'模型下载到: {model_dir}')
"
```

### 验证模型下载
```bash
ls -la /home/你的用户名/models/deepseek-ocr-1.5b/
```

**应该看到类似文件**：
```
config.json
pytorch_model.bin
tokenizer.json
vocab.json
special_tokens_map.json
... (其他配置文件)
```

---

## 📥 步骤二：下载项目代码

```bash
# 进入工作目录
cd /home/你的用户名/

# 克隆项目（如果有 Git 仓库）
git clone <你的项目仓库地址>

# 或者直接复���现有项目
# 假设项目已存在，进入项目目录
cd /path/to/your/DeepSeek-OCR-vllm
```

**确认项目结构**：
```bash
ls -la
```

**应该看到这些文件**：
```
.env.example          # 配置模板
start_server.sh       # 完整管理脚本
quick_start.sh        # 快速启动脚本
deepseek_ocr_server.py # 主程序
requirements.txt      # 依赖列表
README.md            # 说明文档
```

---

## ⚙️ 步骤三：配置环境

### 1. 创建配置文件

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
nano .env  # 或使用 vim .env
```

### 2. 修改配置文件详解

**打开 `.env` 文件后，你会看到类似内容**：

```bash
# DeepSeek OCR 服务配置
# 请根据你的实际情况修改以下配置

# ============================================================================
# 核心配置（必须修改）
# ============================================================================

# 模型路径 - 请修改为你的实际模型路径
MODEL_PATH=/path/to/your/DeepSeek-OCR

# ============================================================================
# GPU 和服务配置（可选）
# ============================================================================

# GPU ID（默认使用 GPU 3）
GPU_ID=3

# 服务端口（默认 8708）
PORT=8708

# 服务监听地址（默认 0.0.0.0，允许外部访问）
HOST=0.0.0.0

# CPU 工作线程数（默认 2，用于图像预处理）
CPU_WORKERS=2

# ============================================================================
# Python 环境配置（二选一）
# ============================================================================

# 方式1: 使用 conda 环境名称（需要 conda 命令）
CONDA_ENV_NAME=deepseek-ocr-vllm

# 方式2: 直接使用 miniconda 环境路径（推荐用于 miniconda）
# PYTHON_PATH=./data/miniconda3/envs/dso/bin/python

# Python 版本（仅在使用 conda 环境名称时需要）
PYTHON_VERSION=3.10
```

### 3. 配置说明（逐行解释）

#### 必须修改的配置：

**`MODEL_PATH`** - 模型路径
```bash
# ❌ 错误示例
MODEL_PATH=/path/to/your/DeepSeek-OCR

# ✅ 正确示例
MODEL_PATH=/home/zhangsan/models/deepseek-ocr-1.5b
```

#### 可选的 GPU 配置：

**`GPU_ID`** - 选择哪张 GPU
```bash
# 先查看可用的 GPU
nvidia-smi

# 如果有多张 GPU，选择显存大的那一张
GPU_ID=0  # 使用第 1 张 GPU
GPU_ID=1  # 使用第 2 张 GPU
# ...
```

**`PORT`** - 服务端口
```bash
# 避免使用系统保留端口
PORT=8708  # 推荐
# PORT=8080  # 如果 8708 被占用
```

#### Python 环境配置（重要！）：

**情况1：你有 conda 环境**
```bash
CONDA_ENV_NAME=myenv
# PYTHON_PATH=...  # 注释掉这行
```

**情况2：你有 miniconda 环境**
```bash
# CONDA_ENV_NAME=...  # 注释掉这行
PYTHON_PATH=/home/username/miniconda3/envs/myenv/bin/python
```

### 4. 配置检查清单

修改完成后，请检查：

- [ ] `MODEL_PATH` 是实际的模型路径，且文件夹存在
- [ ] `GPU_ID` 对应有效的 GPU
- [ ] `PORT` 没有被其他程序占用
- [ ] Python 环境配置正确（二选一）

---

## 🚀 步骤四：启动服务

### 方法1：快速启动（推荐新手）

```bash
# 给脚本添加执行权限
chmod +x quick_start.sh

# 启动服务
./quick_start.sh
```

**启动过程**（你会看到类似输出）：
```
[INFO] 使用指定 Python: /home/username/miniconda3/envs/dso/bin/python
[INFO] DeepSeek OCR vLLM 快速启动...
[INFO] 检查环境和依赖...
[INFO] 安装依赖包...
[SUCCESS] 启动完成!
[INFO] 使用以下命令监控:
  tail -f logs/deepseek_ocr_server_8708_20241030_143022.log
  curl http://localhost:8708/health
```

### 方法2：完整管理脚本

```bash
# 添加执行权限
chmod +x start_server.sh

# 启动完整管理界面
./start_server.sh
```

**菜单界面**：
```
=====================================
DeepSeek OCR vLLM 管理脚本
=====================================
1) 检查系统依赖
2) 创建/更新环境
3) 安装依赖包
4) 启动服务
5) 监控服务状态
6) 查看使用信息
7) 停止服务
0) 退出

请选择操作:
```

### 方法3：自动模式（一键安装+启动）

```bash
./start_server.sh auto
```

### 等待启动完成

**启动需要 3-10 分钟**，因为需要：
1. 检查和安装 Python 依赖包
2. 加载 OCR 模型到 GPU
3. 启动 API 服务

**成功的标志**：
```
[SUCCESS] 服务已启动 (PID: 12345)
[INFO] API文档: http://localhost:8708/docs
[INFO] 健康检查: curl http://localhost:8708/health
```

---

## 🧪 步骤五：测试服务

### 1. 健康检查

```bash
curl http://localhost:8708/health
```

**成功响应**：
```json
{
  "status": "healthy",
  "model_ready": true,
  "cpu_workers": 2,
  "gpu_workers": 1
}
```

### 2. 查看服务文档

在浏览器中打开：
```
http://你的服务器IP:8708/docs
```

你会看到 Swagger API 文档界面。

### 3. 准备测试图片

```bash
# 创建测试目录
mkdir test_images

# 上传测试图片到这个目录
# 或者从网上下载测试图片
wget https://example.com/test-document.jpg -O test_images/test.jpg
```

### 4. 测试 OCR 功能

**方法1：使用 curl**
```bash
curl -X POST "http://localhost:8708/ocr" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_images/test.jpg"
```

**方法2：使用 Python**
```python
import requests

# 图片路径
image_path = "test_images/test.jpg"

# 发送请求
with open(image_path, "rb") as f:
    response = requests.post(
        "http://localhost:8708/ocr",
        files={"file": f}
    )

# 获取结果
if response.status_code == 200:
    result = response.json()
    print("识别结果：")
    print(result["markdown"])
else:
    print(f"请求失败: {response.status_code}")
    print(response.text)
```

### 5. 测试 PDF 文档

```bash
# 测试 PDF
curl -X POST "http://localhost:8708/ocr" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_document.pdf"
```

---

## 📚 常见问题解答

### Q1: 如何查看服务是否正在运行？

```bash
# 方法1：查看进程
ps aux | grep deepseek_ocr_server

# 方法2：健康检查
curl http://localhost:8708/health

# 方法3：查看端口占用
netstat -tlnp | grep 8708
```

### Q2: 如何修改 GPU 使用哪张？

编辑 `.env` 文件中的 `GPU_ID`：
```bash
# 先查看 GPU 状态
nvidia-smi

# 选择空闲的 GPU
GPU_ID=1  # 修改为你想使用的 GPU ID
```

### Q3: 如何修改端口？

编辑 `.env` 文件中的 `PORT`：
```bash
PORT=9000  # 修改为其他端口
```

### Q4: 服务启动失败怎么办？

1. **查看日志**：
   ```bash
   tail -f logs/deepseek_ocr_server_*.log
   ```

2. **检查配置**：
   ```bash
   # 验证模型路径
   ls /your/model/path

   # 验证 GPU
   nvidia-smi

   # 验证端口
   netstat -tlnp | grep 8708
   ```

### Q5: 如何重启服务？

```bash
# 停止服务
./start_server.sh stop

# 重新启动
./quick_start.sh
```

### Q6: 如何允许外部访问？

1. **检查防火墙**：
   ```bash
   # 开放端口
   sudo ufw allow 8708

   # 或者关闭防火墙（仅限内网）
   sudo ufw disable
   ```

2. **确认监听地址**：
   ```bash
   # 确保 HOST=0.0.0.0
   grep "HOST=" .env
   ```

### Q7: 内存不足怎么办？

1. **减少 CPU 工作线程**：
   ```bash
   CPU_WORKERS=1
   ```

2. **使用更小的 GPU 批处理**：
   修改 `deepseek_ocr_server.py` 中的 `max_num_seqs`

3. **清理缓存**：
   ```bash
   # 清理系统缓存
   sudo sync && sudo sysctl vm.drop_caches=3
   ```

---

## 🚨 故障排除

### 错误1：CUDA out of memory

**症状**：
```
CUDA out of memory. Tried to allocate 2.00 GiB
```

**解决方案**：
1. 使用显存更大的 GPU
2. 减少并发处理数量
3. 重启服务释放内存

### 错误2：模型路径不存在

**症状**：
```
WARNING: 模型路径不存在: /path/to/model
```

**解决方案**：
1. 检查路径是否正确
2. 确保模型文件完整下载

### 错误3：端口被占用

**症状**：
```
Address already in use
```

**解决方案**：
```bash
# 查找占用端口的进程
sudo lsof -i :8708

# 杀死进程
sudo kill -9 PID

# 或者修改端口
PORT=8709
```

### 错误4：依赖安装失败

**症状**：
```
ERROR: Could not install packages due to EnvironmentError
```

**解决方案**：
```bash
# 清理 pip 缓存
pip cache purge

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 错误5：权限问题

**症状**：
```
Permission denied
```

**解决方案**：
```bash
# 添加执行权限
chmod +x *.sh

# 修改文件所有者（如果需要）
sudo chown -R $USER:$USER /path/to/project
```

---

## 📞 获取帮助

如果遇到问题：

1. **查看日志**：`tail -f logs/deepseek_ocr_server_*.log`
2. **检查配置**：确认 `.env` 文件配置正确
3. **查看系统资源**：`nvidia-smi`, `free -h`, `df -h`
4. **重启服务**：先停止再启动

---

## 🎉 恭喜！

如果看到这里，你已经成功部署了 DeepSeek OCR 服务！现在你可以：

- 📄 识别图片和 PDF 文档
- 🌐 通过 API 调用 OCR 功能
- 🔧 根据需要调整配置
- 📊 监控服务状态

享受高效的 OCR 识别体验吧！ 🚀