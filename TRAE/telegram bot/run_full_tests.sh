#!/bin/bash

# 完整测试运行脚本
echo "🚀 开始运行完整测试套件..."

# 检查Python版本
echo "🔧 检查Python版本..."
python3 --version

# 检查必要的工具
echo "🔧 检查测试工具..."
if ! python3 -c "import pytest" &> /dev/null
then
    echo "❌ pytest未安装，正在安装..."
    pip3 install pytest
fi

# 运行单元测试
echo "🧪 运行单元测试..."
python3 -m pytest tests/test_api.py tests/test_products_unit.py tests/test_health_api.py -v --tb=short

# 检查代码质量工具
echo "🎨 检查代码质量工具..."
if ! python3 -c "import flake8" &> /dev/null
then
    echo "❌ flake8未安装，正在安装..."
    pip3 install flake8
fi

# 只对我们的测试文件运行代码风格检查
echo "🎨 运行代码风格检查（仅测试文件）..."
python3 -m flake8 tests/test_api.py tests/test_products_unit.py tests/test_health_api.py --count --select=E9,F63,F7,F82 --show-source --statistics
python3 -m flake8 tests/test_api.py tests/test_products_unit.py tests/test_health_api.py --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

echo "✅ 完整测试套件运行完成！"