import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def test():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text('SELECT slug, timeout_seconds FROM agents LIMIT 5;'))
        print(res.fetchall())

if __name__ == "__main__":
    asyncio.run(test())
