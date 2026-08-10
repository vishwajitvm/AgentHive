import asyncio
import time
from app.llm.router import LLMRouter
from app.schemas.requests import AgentRequest

async def main():
    print("Testing LLMRouter fallback speed...")
    router = LLMRouter()
    req = AgentRequest(agent_id=1, user_input="What is the speed of light?", session_id="test_speed", capabilities=["web"])
    start = time.time()
    try:
        response, meta = await router.generate(req, "Answer concisely.", [])
        end = time.time()
        print(f"\nResponse: {response}")
        print(f"Total time taken: {end - start:.2f} seconds")
        print(f"Metadata: {meta}")
    except Exception as e:
        end = time.time()
        print(f"\nFailed! Time taken: {end - start:.2f} seconds")
        print(f"Error: {e}")

asyncio.run(main())
