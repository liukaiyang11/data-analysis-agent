#!/bin/bash

echo "🚀 启动赋范空间 AI全自动数据分析系统..."
echo "📦 项目目录: $(pwd)"
echo ""

# 检查 node_modules 是否存在
if [ ! -d "node_modules" ]; then
    echo "⚠️  未找到 node_modules，开始安装依赖..."
    npm install
    echo "✅ 依赖安装完成"
    echo ""
fi

echo "🔧 启动开发服务器..."
echo "🌐 访问地址: http://localhost:3000"
echo ""
echo "提示: 按 Ctrl+C 停止服务器"
echo "================================"
echo ""

npm run dev
