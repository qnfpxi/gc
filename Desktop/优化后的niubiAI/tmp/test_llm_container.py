import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append('/opt/niubiai')

from services.llm_service import LLMService

async def test():
    try:
        print('Initializing config')
        config = {
            'gemini': {
                'enabled': True,
                'model_name': 'gemini-pro',
                'api_key': 'fake-key',
                'api_url': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
                'timeout': 30,
                'max_tokens': 1000,
                'temperature': 0.7,
                'get_api_key': lambda: 'fake-key',
                'backup_urls': [],
                'get_backup_url': lambda x: None,
                'get_backup_api_key': lambda x: None
            }
        }
        print('Creating LLMService instance')
        service = LLMService(config)
        print('Initializing service')
        await service.initialize()
        print('Test completed successfully')
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

async def main():
    await test()

if __name__ == '__main__':
    asyncio.run(main())