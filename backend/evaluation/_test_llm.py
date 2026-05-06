import asyncio
from services.llm_client import llm_client

async def test():
    r = await llm_client.generate(
        prompt='Respond with a JSON object: {"status": "ok", "provider": "unknown"}',
        expect_json=True
    )
    print("RESULT:", r)

asyncio.run(test())
