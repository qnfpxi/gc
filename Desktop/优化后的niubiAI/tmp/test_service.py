import asyncio
from services.llm_service import LLMService

async def test():
    service = LLMService()
    await service.initialize()
    try:
        response = await service.generate_response('gpt3', 'Hello, how are you?', 12345, stream=False)
        print(f'Response: {response}')
    except Exception as e:
        print(f'Error: {e}')

asyncio.run(test())