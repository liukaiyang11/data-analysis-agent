# Data Analysis Agent

> 基于 DeepSeek-OCR 的 AI 数据分析可视化系统，支持图片/表格文档的智能识别、数据提取与可视化。

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18+-61dafb)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688)](https://fastapi.tiangolo.com/)
[![DeepSeek](https://img.shields.io/badge/DeepSeek--OCR-v1+-purple)](https://github.com/deepseek-ai)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ 特性

- 📸 **OCR 数据提取**：从图片/表格/PDF 中自动提取结构化数据
- 📊 **智能数据分析**：自然语言提问，自动生成数据分析结果
- 📈 **可视化图表**：自动生成柱状图、折线图、饼图等多种图表
- 🎯 **多格式支持**：支持 JPG、PNG、PDF 等多种输入格式
- 🎨 **现代界面**：React + Vite + TailwindCSS 构建

---

## 🏗️ 技术架构

```
┌──────────────────────────────────────────────┐
│                 Frontend                     │
│              (React + Vite)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ 文件上传 │ │ 数据展示 │ │ 可视化   │   │
│  └──────────┘ └──────────┘ └──────────┘   │
└───────────────────┬──────────────────────────┘
                    │
        ┌───────────▼────────────┐
        │      Backend           │
        │     (FastAPI)          │
        │  ┌──────────────────┐  │
        │  │ DeepSeek-OCR     │  │   OCR 识别
        │  │ (文档解析)       │  │
        │  └──────────────────┘  │
        │  ┌──────────────────┐  │
        │  │ 数据分析 Agent   │  │   自然语言分析
        │  │ (Qwen / LLM)    │  │
        │  └──────────────────┘  │
        └────────────────────────┘
```

---

## 📁 项目结构

```
.
├── backend/                    # 后端服务
│   ├── main.py                 # API 入口
│   ├── requirements.txt
│   ├── .env.example            # 环境变量示例
│   ├── external/
│   │   └── ocr/                # OCR 服务（DeepSeek-OCR）
│   └── ...
├── frontend/                   # 前端
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

> 💡 **模型文件**：DeepSeek-OCR 模型位于 `../data/` 目录（约 6.2GB），不纳入 Git 仓库。

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- DeepSeek-OCR 模型（约 6GB，GPU 推荐）
- 通义千问 / Qwen API Key（用于数据分析）

### 后端启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 填入 API Key、模型路径等

# 启动 OCR 服务
cd external/ocr/DeepSeek-OCR-vllm
# 参考 .env.example 配置并启动

# 启动主服务
uvicorn main:app --reload --host 0.0.0.0 --port 8708
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

---

## 📚 相关课程

- 📖 课程文档：[飞书知识库](https://scnxinvxtnbo.feishu.cn/wiki/MhlawnWR4ilPJckem2WcMhSinab)
- 🎥 视频教程：[课程链接](#)（待补充）

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
