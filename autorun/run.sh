#!/bin/bash

echo "========================================"
echo "Orchestrator + Cursor Worker 工作流"
echo "========================================"
echo ""

cd "$(dirname "$0")"

echo "检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python，请先安装 Python 3.8+"
    exit 1
fi

python3 --version
echo ""
echo "启动 Orchestrator..."
echo ""

python3 orchestrator.py

