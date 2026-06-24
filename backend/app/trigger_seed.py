import asyncio
from app.db.database import SessionLocal
from app.tools.seeder import seed_tools
from app.agents.seeder import seed_new_agents
async def main():
    async with SessionLocal() as db:
        await seed_tools(db)
        await seed_new_agents(db)
asyncio.run(main())
