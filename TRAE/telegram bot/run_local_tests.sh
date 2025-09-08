#!/bin/bash

# 本地测试运行脚本
echo "🚀 开始运行本地测试..."

# 检查Python版本
echo "🔧 检查Python版本..."
python3 --version

# 检查pytest是否安装
echo "🔧 检查测试工具..."
if ! python3 -c "import pytest" &> /dev/null
then
    echo "❌ pytest未安装，正在安装..."
    pip3 install pytest
fi

# 运行API测试
echo "🧪 运行API测试..."
python3 -m pytest tests/test_api.py -v

# 运行产品单元测试
echo "🧪 运行产品单元测试..."
python3 -m pytest tests/test_products_unit.py -v

# 运行健康检查API测试
echo "🧪 运行健康检查API测试..."
python3 -m pytest tests/test_health_api.py -v

# 运行所有可运行的测试
echo "🧪 运行所有单元测试..."
python3 -m pytest tests/test_api.py tests/test_products_unit.py tests/test_health_api.py -v --tb=short

echo "✅ 所有本地测试运行完成！"