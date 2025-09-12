#!/usr/bin/env python3

import asyncio
import sys
import json
import os

# 添加项目根目录到Python路径
sys.path.insert(0, '/opt/niubiai')
sys.path.insert(0, '/opt/niubiai/src')

async def test_gemini():
    print("开始测试Gemini模型...")
    
    try:
        # 尝试导入LLMService
        print("尝试导入LLMService...")
        from src.services.llm_service import LLMService
        print("成功导入LLMService")
    except ImportError as e:
        print(f"导入LLMService失败: {e}")
        try:
            print("尝试从services目录导入...")
            from services.llm_service import LLMService
            print("成功从services目录导入LLMService")
        except ImportError as e:
            print(f"从services目录导入失败: {e}")
            # 列出可能的目录
            print("\n列出可能的目录:")
            os.system("find /opt/niubiai -name llm_service.py | grep -v tmp")
            return
    
    # 加载配置
    config_path = '/opt/niubiai/config/llm_models.json'
    if not os.path.exists(config_path):
        print(f"错误: 配置文件不存在: {config_path}")
        # 尝试查找配置文件
        print("尝试查找配置文件:")
        os.system("find /opt/niubiai -name llm_models.json")
        return
    
    try:
        with open(config_path, 'r') as f:
            configs = json.load(f)
        print(f"成功加载配置，模型数量: {len(configs)}")
    except Exception as e:
        print(f"加载配置失败: {e}")
        return
    
    # 初始化LLM服务
    try:
        llm_service = LLMService(configs)
        await llm_service.initialize()
        print("LLM服务初始化成功")
    except Exception as e:
        print(f"LLM服务初始化失败: {e}")
        return
    
    # 测试非流式响应
    try:
        print("\n测试非流式响应:")
        # 找到一个gemini模型
        gemini_model = None
        for name, config in configs.items():
            if 'gemini' in name.lower() and config.get('enabled', False):
                gemini_model = name
                break
        
        if not gemini_model:
            print("未找到启用的Gemini模型")
            # 尝试使用其他可用模型
            for name, config in configs.items():
                if config.get('enabled', False):
                    gemini_model = name
                    print(f"使用替代模型: {gemini_model}")
                    break
        
        if not gemini_model:
            print("未找到任何启用的模型")
            return
        
        print(f"使用模型: {gemini_model}")
        response = await llm_service.generate_response(
            gemini_model, "你好，请简单介绍一下自己", 12345, stream=False
        )
        print(f"非流式响应: {response[:100]}...")
    except Exception as e:
        print(f"非流式响应测试失败: {e}")
    
    # 测试流式响应
    try:
        print("\n测试流式响应:")
        stream_gen = await llm_service.generate_response(
            gemini_model, "请列出5个编程语言及其特点", 12345, stream=True
        )
        
        print("流式响应片段:")
        async for chunk in stream_gen:
            print(f"片段: {chunk[:30]}...")
            # 只获取前3个片段
            break
        
        print("流式响应测试成功")
    except Exception as e:
        print(f"流式响应测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())