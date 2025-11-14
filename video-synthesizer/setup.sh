#!/bin/bash

# 视频合成工具 - 环境设置脚本

echo "开始设置开发环境..."
echo ""

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv venv
    echo "✓ 虚拟环境创建完成"
else
    echo "✓ 虚拟环境已存在"
fi

echo ""
echo "激活虚拟环境并安装依赖..."
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "============================================================"
echo "✓ 环境设置完成！"
echo ""
echo "使用方法："
echo "  1. 激活虚拟环境: source venv/bin/activate"
echo "  2. 运行测试: python test_example.py"
echo "  3. 启动API: python api.py"
echo "  4. 退出虚拟环境: deactivate"
echo "============================================================"
