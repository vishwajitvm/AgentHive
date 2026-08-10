import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def update_db():
    async with AsyncSessionLocal() as db:
        # Update agent timeouts
        await db.execute(text('UPDATE agents SET timeout_seconds = 1200;'))
        
        # Update model policy fallback orders
        await db.execute(text("UPDATE model_policies SET fallback_order = 'gemini,huggingface,groq,openai,ollama';"))
        
        await db.commit()
        print("Database updated successfully.")

if __name__ == "__main__":
    asyncio.run(update_db())
