import asyncio
import os
import logging
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.agents.models import Agent, Prompt, PromptVersion, AgentVersion
from app.agents.seeder import SPECIALIZED_AGENTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async_engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

AGENTS_DATA = SPECIALIZED_AGENTS

async def main():
    async with AsyncSessionLocal() as db:
        logger.info("Wiping existing agents for a clean slate...")
        await db.execute(delete(Agent))
        await db.execute(delete(Prompt))
        await db.commit()
        
        for item in AGENTS_DATA:
            prompt = Prompt(
                name=f"{item['name']} Prompt",
                slug=f"{item['slug']}_prompt",
                description=f"Prompt for {item['name']}"
            )
            db.add(prompt)
            await db.commit()
            await db.refresh(prompt)
            
            p_ver = PromptVersion(
                prompt_id=prompt.id,
                content=item["prompt"],
                version=1
            )
            db.add(p_ver)
            await db.commit()
            await db.refresh(p_ver)
            
            agent = Agent(
                name=item["name"],
                slug=item["slug"],
                description=item["description"],
                agent_type=item["agent_type"],
                prompt_id=prompt.id,
                prompt_version_id=p_ver.id,
                tools_enabled=item["tools_enabled"],
                memory_enabled=True,
                max_steps=item.get("max_steps", 10),
                timeout_seconds=item.get("timeout_seconds", 120),
                status="active",
                allow_uploads=True,
                how_to_use=item.get("how_to_use"),
                order_index=item.get("order_index", 0)
            )
            db.add(agent)
            await db.commit()
            
        logger.info(f"Successfully seeded {len(AGENTS_DATA)} elite agents!")

if __name__ == "__main__":
    asyncio.run(main())
