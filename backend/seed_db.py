import asyncio
from app.core.database import get_db, AsyncSessionLocal
from app.api.routes.agents import create_agent, AgentCreate

async def seed_agents():
    print("Seeding valid agents...")
    async with AsyncSessionLocal() as db:
        agent1 = AgentCreate(
            name="Developer Assistant",
            slug="dev_assistant",
            description="A highly capable AI developer that can write code and manage workspace files locally.",
            how_to_use="1. Upload your code files to the workspace if needed.\n2. Ask the agent to modify, debug, or write new code.\n3. The agent will read your files, execute python code to test its logic, and save the final code back to the workspace.",
            agent_type="developer_agent",
            prompt_content="You are a senior software engineer. Write, debug, and execute code based on user requests.",
            tools_enabled=["code_tool", "file_tool"],
            memory_enabled=True,
            allow_uploads=True,
            max_steps=15,
            timeout_seconds=120
        )
        agent2 = AgentCreate(
            name="Research Analyst",
            slug="research_analyst",
            description="Searches the web and processes Youtube video transcripts to extract facts.",
            how_to_use="1. Ask a complex question or provide a YouTube URL.\n2. The agent will search the internet or extract the transcript.\n3. You will receive a detailed factual summary based on the retrieved information.",
            agent_type="research_agent",
            prompt_content="You are a research analyst. Scrape information and extract video transcripts to answer questions.",
            tools_enabled=["search_tool", "youtube_transcript_tool"],
            memory_enabled=True,
            allow_uploads=False,
            max_steps=10,
            timeout_seconds=120
        )
        try:
            await create_agent(agent1, db)
            await create_agent(agent2, db)
            print("Successfully seeded agents.")
        except Exception as e:
            print(f"Error seeding agents: {e}")

if __name__ == "__main__":
    asyncio.run(seed_agents())
