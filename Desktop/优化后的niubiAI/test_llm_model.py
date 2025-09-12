#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NiubiAI LLM模型测试脚本
用于测试LLM模型能否成功对接和输出
"""

import asyncio
import json
import os
import sys
import requests

# 检查项目结构
print("检查项目结构...")
os.system("ls -la")
print("\n检查服务目录...")
os.system("ls -la services/ 2>/dev/null || echo '服务目录不存在'")
print("\n检查配置目录...")
os.system("ls -la config/ 2>/dev/null || echo '配置目录不存在'")
print("\n检查NiubiAI目录...")
os.system("ls -la NiubiAI/ 2>/dev/null || echo 'NiubiAI目录不存在'")

# 简单测试LLM API连接
def test_openai_connection():
    print("\n测试OpenAI API连接...")
    try:
        response = requests.get("https://api.openai.com", timeout=5)
        print(f"OpenAI API状态码: {response.status_code}")
        return True
    except Exception as e:
        print(f"OpenAI API连接失败: {e}")
        return False

def test_anthropic_connection():
    print("\n测试Anthropic API连接...")
    try:
        response = requests.get("https://api.anthropic.com", timeout=5)
        print(f"Anthropic API状态码: {response.status_code}")
        return True
    except Exception as e:
        print(f"Anthropic API连接失败: {e}")
        return False


def find_llm_config_file():
    """查找LLM配置文件"""
    possible_paths = [
        os.path.join(os.getcwd(), "NiubiAI", "config", "llm_models.json"),
        os.path.join(os.getcwd(), "config", "llm_models.json"),
        "/opt/niubiai/NiubiAI/config/llm_models.json",
        "/opt/niubiai/config/llm_models.json"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"找到LLM配置文件: {path}")
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"成功加载LLM配置文件，包含 {len(config)} 个模型配置")
                for model_name in config.keys():
                    print(f"  - {model_name}")
                return path, config
            except Exception as e:
                print(f"加载配置文件失败: {e}")
    
    print("错误: 未找到LLM配置文件")
    return None, None

class LLMTester:
    """LLM模型测试类"""

    def __init__(self, model_name=None):
        """初始化LLM测试器"""
        self.model_name = model_name
        self.config_path, self.llm_configs = find_llm_config_file()
        self.llm_service = None

    def test_model_config(self, model_name=None):
        """测试指定模型的配置"""
        if not self.llm_configs:
            print("错误: 未加载LLM配置")
            return False
            
        model = model_name or self.model_name
        if not model:
            # 如果未指定模型，测试所有模型配置
            return self.test_all_model_configs()
            
        if model not in self.llm_configs:
            print(f"错误: 模型 {model} 不存在于配置中")
            return False
            
        config = self.llm_configs[model]
        print(f"\n正在测试模型配置: {model}")
        print("-" * 50)
        
        # 检查必要的配置项
        required_fields = ["api_url", "model_name", "enabled"]
        for field in required_fields:
            if field not in config:
                print(f"错误: 缺少必要的配置项 '{field}'")
                return False
            print(f"✓ 配置项 '{field}' 存在: {config[field]}")
            
        # 检查API URL
        api_url = config.get("api_url", "")
        if not api_url:
            print("错误: API URL为空")
            return False
            
        print(f"✓ API URL: {api_url}")
        
        # 检查模型是否启用
        if not config.get("enabled", False):
            print(f"警告: 模型 {model} 已禁用")
            
        print("-" * 50)
        print(f"模型 {model} 配置测试完成")
        return True
        
    def test_all_model_configs(self):
        """测试所有模型配置"""
        if not self.llm_configs:
            print("错误: 未加载LLM配置")
            return False
            
        success_count = 0
        total_count = len(self.llm_configs)
        
        print(f"\n开始测试所有模型配置 (共 {total_count} 个)...")
        
        for model_name in self.llm_configs:
            if self.test_model_config(model_name):
                success_count += 1
                
        print(f"\n配置测试完成: {success_count}/{total_count} 个模型配置测试成功")
        return success_count > 0


def main():
    """主函数"""
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='测试NiubiAI LLM模型')
    parser.add_argument('--model', '-m', help='要测试的模型名称')
    parser.add_argument('--all', '-a', action='store_true', 
                        help='测试所有模型配置')
    parser.add_argument('--check-api', '-c', action='store_true',
                        help='检查API连接')
    args = parser.parse_args()

    # 检查项目环境
    print("\n" + "=" * 50)
    print("NiubiAI LLM模型测试")
    print("=" * 50)
    
    # 测试API连接
    if args.check_api:
        print("\n测试API连接...")
        test_openai_connection()
        test_anthropic_connection()
    
    # 创建测试器实例
    tester = LLMTester(args.model)
    
    # 如果没有找到配置文件，退出
    if not tester.llm_configs:
        return 1
    
    # 执行配置测试
    if args.all or not args.model:
        success = tester.test_all_model_configs()
    else:
        success = tester.test_model_config(args.model)
    
    print("\n" + "=" * 50)
    if success:
        print("LLM模型配置测试成功!")
    else:
        print("LLM模型配置测试失败!")
    print("=" * 50)
    
    return 0 if success else 1


if __name__ == "__main__":
    # 运行主函数
    sys.exit(main())