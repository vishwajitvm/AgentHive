import asyncio
from app.core.database import AsyncSessionLocal
from app.llm.models import ModelProvider
from sqlalchemy import update

async def sync():
    async with AsyncSessionLocal() as session:
        # Update Nvidia
        await session.execute(update(ModelProvider).where(ModelProvider.provider_type == 'nvidia').values(default_model='meta/llama-3.3-70b-instruct'))
        # Update Groq
        await session.execute(update(ModelProvider).where(ModelProvider.provider_type == 'groq').values(default_model='llama-3.3-70b-versatile'))
        # Update HF
        await session.execute(update(ModelProvider).where(ModelProvider.provider_type == 'huggingface').values(default_model='meta-llama/Llama-3.3-70B-Instruct'))
        
        await session.commit()
        print("Database synchronized with verified models!")

if __name__ == "__main__":
    asyncio.run(sync())
