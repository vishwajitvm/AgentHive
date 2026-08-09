import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def update_db():
    async with AsyncSessionLocal() as db:
        await db.execute(text("UPDATE model_policies SET primary_provider = 'gemini', secondary_provider = 'nvidia', fallback_order = 'gemini,nvidia,huggingface,groq,openai,ollama' WHERE is_active = true;"))
        await db.commit()
        print("DB updated")

if __name__ == "__main__":
    asyncio.run(update_db())
