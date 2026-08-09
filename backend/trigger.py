import asyncio
from app.core.database import AsyncSessionLocal
from app.agents.seeder import seed_new_agents

async def run():
    async with AsyncSessionLocal() as db:
        await seed_new_agents(db)

if __name__ == "__main__":
    asyncio.run(run())
