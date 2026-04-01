#!/bin/bash
# 启动后端服务脚本

echo "========================================"
echo "Enterprise Knowledge Hub API"
echo "========================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查虚拟环境
if [ -d "../.venv" ]; then
    echo "Activating virtual environment..."
    source ../.venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# 设置环境变量
export DEBUG=true
export HOST=0.0.0.0
export PORT=8000

echo "Starting server..."
echo "API Docs: http://localhost:8000/docs"
echo ""

# 启动服务
python -m uvicorn app.main:app \
    --host $HOST \
    --port $PORT \
    --reload \
    --log-level info
