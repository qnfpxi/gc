#!/usr/bin/env python3

"""
Python 3.12兼容性测试脚本
作者: AI助手
日期: 2024-07-10

此脚本用于测试NiubiAI Bot在Python 3.12环境下的兼容性
"""

import sys
import importlib
import subprocess
import platform
from pathlib import Path


def print_header(message):
    print(f"\n{'=' * 50}")
    print(f" {message}")
    print(f"{'=' * 50}\n")


def print_success(message):
    print(f"✅ {message}")


def print_warning(message):
    print(f"⚠️ {message}")


def print_error(message):
    print(f"❌ {message}")


def check_python_version():
    print_header("检查Python版本")
    version = sys.version_info
    print(f"当前Python版本: {platform.python_version()}")
    
    if version.major == 3 and version.minor == 12:
        print_success("Python版本为3.12，符合要求")
        return True
    else:
        print_error(f"Python版本不是3.12，请使用Python 3.12运行此测试")
        return False


def check_dependencies():
    print_header("检查依赖包兼容性")
    
    # 从requirements.py312.txt读取依赖
    req_file = Path("requirements.py312.txt")
    if not req_file.exists():
        print_error("找不到requirements.py312.txt文件")
        return False
    
    dependencies = []
    with open(req_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # 提取包名（去除版本号）
                package_name = line.split("==")[0].strip()
                dependencies.append(package_name)
    
    success_count = 0
    failed_packages = []
    
    for package in dependencies:
        try:
            # 尝试导入包
            importlib.import_module(package.replace("-", "_"))
            print_success(f"成功导入 {package}")
            success_count += 1
        except ImportError as e:
            print_error(f"无法导入 {package}: {str(e)}")
            failed_packages.append(package)
    
    print(f"\n依赖检查结果: {success_count}/{len(dependencies)} 个包导入成功")
    
    if failed_packages:
        print_warning(f"以下包导入失败: {', '.join(failed_packages)}")
        print("请确保已安装所有依赖: pip install -r requirements.py312.txt")
        return False
    
    return True


def test_core_modules():
    print_header("测试核心模块")
    
    core_modules = [
        "services.llm_service",
        "app.application",
        "app.handlers",
        "app.middlewares",
        "app.utils",
        "models"
    ]
    
    success_count = 0
    failed_modules = []
    
    for module in core_modules:
        try:
            # 尝试导入模块
            importlib.import_module(module)
            print_success(f"成功导入 {module}")
            success_count += 1
        except Exception as e:
            print_error(f"导入 {module} 失败: {str(e)}")
            failed_modules.append(module)
    
    print(f"\n核心模块测试结果: {success_count}/{len(core_modules)} 个模块导入成功")
    
    if failed_modules:
        print_warning(f"以下模块导入失败: {', '.join(failed_modules)}")
        return False
    
    return True


def run_syntax_check():
    print_header("运行语法检查")
    
    try:
        # 使用Python的编译功能检查所有.py文件的语法
        result = subprocess.run(
            [sys.executable, "-m", "compileall", "."],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print_success("所有Python文件语法检查通过")
            return True
        else:
            print_error("语法检查失败")
            print(result.stderr)
            return False
    except Exception as e:
        print_error(f"运行语法检查时出错: {str(e)}")
        return False


def main():
    print_header("NiubiAI Bot - Python 3.12兼容性测试")
    
    tests = [
        ("Python版本检查", check_python_version),
        ("依赖包兼容性检查", check_dependencies),
        ("核心模块测试", test_core_modules),
        ("语法检查", run_syntax_check)
    ]
    
    results = {}
    all_passed = True
    
    for name, test_func in tests:
        print(f"\n运行测试: {name}")
        try:
            result = test_func()
            results[name] = result
            if not result:
                all_passed = False
        except Exception as e:
            print_error(f"测试 {name} 执行出错: {str(e)}")
            results[name] = False
            all_passed = False
    
    print_header("测试结果摘要")
    for name, result in results.items():
        status = "通过" if result else "失败"
        if result:
            print_success(f"{name}: {status}")
        else:
            print_error(f"{name}: {status}")
    
    if all_passed:
        print_header("所有测试通过! NiubiAI Bot与Python 3.12兼容")
    else:
        print_header("部分测试失败，请解决上述问题后再部署")


if __name__ == "__main__":
    main()