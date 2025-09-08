#!/usr/bin/env python3
"""
测试Locust负载测试脚本是否正常工作的脚本
"""

import os
import sys
import subprocess
import time

def test_locust_installation():
    """测试Locust是否正确安装"""
    print("🚀 开始测试Locust安装...")
    
    try:
        # 测试Locust是否可以导入
        import locust
        print(f"✅ Locust成功导入，版本: {locust.__version__}")
    except ImportError as e:
        print(f"❌ Locust导入失败: {e}")
        return False
    
    try:
        # 测试Locust命令行工具
        result = subprocess.run(["locust", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Locust命令行工具正常工作: {result.stdout.strip()}")
        else:
            print(f"❌ Locust命令行工具异常: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ Locust命令行工具未找到，请确保已正确安装")
        return False
    
    return True

def test_locustfile():
    """测试locustfile.py是否存在且语法正确"""
    print("\n📝 开始测试Locust测试脚本...")
    
    # 检查文件是否存在
    locustfile_path = os.path.join(os.path.dirname(__file__), "locustfile.py")
    if not os.path.exists(locustfile_path):
        print(f"❌ Locust测试脚本不存在: {locustfile_path}")
        return False
    
    print(f"✅ Locust测试脚本存在: {locustfile_path}")
    
    # 检查语法是否正确
    try:
        with open(locustfile_path, 'r') as f:
            code = f.read()
        compile(code, locustfile_path, 'exec')
        print("✅ Locust测试脚本语法正确")
    except SyntaxError as e:
        print(f"❌ Locust测试脚本语法错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 检查Locust测试脚本时发生错误: {e}")
        return False
    
    return True

def test_docker_compose_integration():
    """测试Docker Compose集成"""
    print("\n🐳 开始测试Docker Compose集成...")
    
    # 检查docker-compose.yml中是否包含locust服务
    docker_compose_path = os.path.join(os.path.dirname(__file__), "docker-compose.yml")
    if not os.path.exists(docker_compose_path):
        print(f"❌ docker-compose.yml文件不存在: {docker_compose_path}")
        return False
    
    try:
        with open(docker_compose_path, 'r') as f:
            content = f.read()
        
        if "locust:" in content:
            print("✅ docker-compose.yml中已配置Locust服务")
        else:
            print("❌ docker-compose.yml中未找到Locust服务配置")
            return False
    except Exception as e:
        print(f"❌ 检查docker-compose.yml时发生错误: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 Locust负载测试环境验证")
    print("=" * 60)
    
    # 执行所有测试
    tests = [
        test_locust_installation,
        test_locustfile,
        test_docker_compose_integration
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试执行失败: {e}")
            results.append(False)
        print("-" * 60)
    
    # 输出总结
    print("📊 测试结果总结:")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 所有测试通过 ({passed}/{total})")
        print("✅ Locust负载测试环境已准备就绪")
        print("\n下一步操作:")
        print("1. 运行: docker-compose up --build")
        print("2. 访问: http://localhost:8089 (Locust UI)")
        print("3. 访问: http://localhost:3000 (Grafana监控)")
        print("4. 在Locust UI中配置用户数并开始测试")
    else:
        print(f"⚠️  部分测试失败 ({passed}/{total})")
        print("❌ 需要修复问题后才能进行负载测试")
    
    print("=" * 60)

if __name__ == "__main__":
    main()