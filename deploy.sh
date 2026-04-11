#!/bin/bash

# ========================================
# 企业知识库部署脚本
# ========================================

set -e

echo "========================================"
echo "  企业知识库 Docker 部署"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装，请先安装 Docker${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: Docker Compose 未安装，请先安装 Docker Compose${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker 环境检查通过${NC}"
echo ""

# 检查 .env 文件
if [ ! -f .env ]; then
    echo -e "${YELLOW}警告: .env 文件不存在${NC}"
    echo "正在从 .env.example 创建 .env 文件..."
    cp .env.example .env
    echo -e "${YELLOW}请编辑 .env 文件，填入正确的 API Keys${NC}"
    echo ""
fi

# 显示当前配置
echo "当前配置:"
echo "  - 前端端口: $(grep FRONTEND_PORT .env 2>/dev/null | cut -d'=' -f2 || echo '80')"
echo "  - 后端端口: $(grep BACKEND_PORT .env 2>/dev/null | cut -d'=' -f2 || echo '8000')"
echo "  - MySQL端口: $(grep MYSQL_PORT .env 2>/dev/null | cut -d'=' -f2 || echo '3306')"
echo ""

# 选择操作
echo "请选择操作:"
echo "  1) 构建并启动 (首次部署)"
echo "  2) 启动服务"
echo "  3) 停止服务"
echo "  4) 重启服务"
echo "  5) 查看日志"
echo "  6) 清理并重新部署"
echo ""
read -p "请输入选项 [1-6]: " choice

case $choice in
    1)
        echo ""
        echo -e "${GREEN}开始构建并启动服务...${NC}"
        docker-compose build --no-cache
        docker-compose up -d
        ;;
    2)
        echo ""
        echo -e "${GREEN}启动服务...${NC}"
        docker-compose up -d
        ;;
    3)
        echo ""
        echo -e "${YELLOW}停止服务...${NC}"
        docker-compose down
        ;;
    4)
        echo ""
        echo -e "${YELLOW}重启服务...${NC}"
        docker-compose restart
        ;;
    5)
        echo ""
        echo -e "${GREEN}显示日志 (Ctrl+C 退出)...${NC}"
        docker-compose logs -f
        ;;
    6)
        echo ""
        echo -e "${RED}警告: 这将删除所有容器和数据卷!${NC}"
        read -p "确认继续? [y/N]: " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            docker-compose down -v
            docker-compose build --no-cache
            docker-compose up -d
        else
            echo "已取消"
        fi
        ;;
    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "  服务状态"
echo "========================================"
docker-compose ps

echo ""
echo "========================================"
echo "  访问地址"
echo "========================================"
FRONTEND_PORT=$(grep FRONTEND_PORT .env 2>/dev/null | cut -d'=' -f2 || echo '80')
BACKEND_PORT=$(grep BACKEND_PORT .env 2>/dev/null | cut -d'=' -f2 || echo '8000')
echo "  前端: http://localhost:${FRONTEND_PORT}"
echo "  后端: http://localhost:${BACKEND_PORT}"
echo "  API文档: http://localhost:${BACKEND_PORT}/docs"
echo "========================================"
