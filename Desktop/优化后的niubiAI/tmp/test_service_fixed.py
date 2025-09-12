import asyncio
import os
import sys
import json

# 添加项目根目录到Python路径
sys.path.insert(0, '/app')

from services.llm_service import LLMService
from services.service_manager import ServiceManager

async def test():
    # 获取LLM配置
    config_path = '/app/config/llm_models.json'
    with open(config_path, 'r') as f:
        llm_configs = json.load(f)
    
    # 初始化服务
    service = LLMService(llm_configs)
    await service.initialize()
    
    try:
        # 测试非流式响应
        print("测试非流式响应...")
        response = await service.generate_response('gpt3', 'Hello, how are you?', 12345, stream=False)
        print(f'非流式响应: {response}')
        
        # 测试流式响应
        print("\n测试流式响应...")
        response_generator = await service.generate_response('gpt3', 'Tell me a short story', 12345, stream=True)
        print("流式响应:")
        async for chunk in response_generator:
            print(chunk, end='')
        print("\n流式响应完成")
        
    except Exception as e:
        print(f'错误: {e}')
        import traceback
        traceback.print_exc()

asyncio.run(test())