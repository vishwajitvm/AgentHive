import asyncio
import os
import json
import logging
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.agents.models import Agent, Prompt, PromptVersion, AgentVersion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async_engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

AGENTS_DATA = [
    {
        "name": "End Truth Fact-Checker",
        "slug": "end_truth_agent",
        "description": "Cross-references URLs, articles, and videos against trusted sources to check for factual accuracy.",
        "agent_type": "research",
        "tools_enabled": ["youtube_transcript_tool", "scraper_tool", "search_tool", "md_writer_tool"],
        "prompt": "You are the 'End Truth' Fact-Checker. Given a URL, first determine if it is a video or article. If video, use youtube_transcript_tool. If article, use scraper_tool. Isolate key claims and use search_tool to fact-check them against trusted sources. Return a structured markdown report rating the authenticity.",
        "max_steps": 10, "timeout_seconds": 120,
        "how_to_use": "1. Provide a YouTube URL or Article link to verify.\n2. Watch as the agent extracts the transcript, isolates claims, and searches the web.\n3. The final result is a Markdown report showing the authenticity rating.",
        "order_index": 1
    },
    {
        "name": "Developer Assistant",
        "slug": "dev_assistant",
        "description": "A highly capable AI developer that can write code and manage workspace files locally.",
        "agent_type": "developer",
        "tools_enabled": ["code_tool", "file_tool"],
        "prompt": "You are a senior software engineer. Write, debug, and execute python code based on user requests.",
        "max_steps": 10, "timeout_seconds": 120,
        "how_to_use": "1. Tell the agent what script you want to write.\n2. It will execute Python code to test it, and save the final file.",
        "order_index": 2
    },
    {
        "name": "Research Analyst",
        "slug": "research_analyst",
        "description": "Searches the web and processes Youtube video transcripts to extract facts.",
        "agent_type": "research",
        "tools_enabled": ["search_tool", "youtube_transcript_tool"],
        "prompt": "You are a research analyst. Scrape information and extract video transcripts to answer questions.",
        "max_steps": 10, "timeout_seconds": 120,
        "how_to_use": "1. Ask a question or provide a topic.\n2. It will search the web and write you an answer.",
        "order_index": 3
    }
]

# Generate 47 more agents using valid tools!
VALID_TOOLS = ["file_tool", "pdf_tool", "search_tool", "storage_tool", "code_tool", "youtube_transcript_tool", "scraper_tool", "md_writer_tool"]

templates = [
    ("Blog Writer", "content", ["search_tool", "md_writer_tool"], "Writes comprehensive SEO blog posts and saves them to markdown."),
    ("Financial Analyst", "finance", ["pdf_tool", "code_tool"], "Analyzes financial PDFs and computes statistics using python code."),
    ("Legal Reader", "legal", ["pdf_tool", "search_tool"], "Reads legal PDFs and searches terms on the web."),
    ("Cloud Architect", "engineering", ["search_tool", "md_writer_tool"], "Researches cloud architectures and writes design docs."),
    ("Math Tutor", "education", ["code_tool"], "Solves complex equations using Python code execution."),
    ("YouTube Summarizer", "content", ["youtube_transcript_tool", "md_writer_tool"], "Summarizes long YouTube videos into crisp markdown notes."),
    ("News Scraper", "research", ["scraper_tool", "search_tool"], "Scrapes current news articles and summarizes the sentiment."),
    ("Storage Manager", "devops", ["storage_tool", "file_tool"], "Syncs local workspace files to cloud storage buckets."),
    ("SEO Keyword Planner", "marketing", ["search_tool", "md_writer_tool"], "Finds keywords and writes strategy docs."),
    ("Data Cleaner", "data", ["file_tool", "code_tool"], "Reads local files, cleans data using python, and overwrites."),
]

# Populate up to 50
count = 4
for i in range(50 - len(AGENTS_DATA)):
    template = templates[i % len(templates)]
    AGENTS_DATA.append({
        "name": f"{template[0]} {count}",
        "slug": f"agent_{count}",
        "description": template[3],
        "agent_type": template[1],
        "tools_enabled": template[2],
        "prompt": f"You are a {template[0]}. Use your tools to achieve the user's objective.",
        "max_steps": 8, "timeout_seconds": 90,
        "how_to_use": "1. Just ask for what you need.\n2. Monitor the execution trace.",
        "order_index": count
    })
    count += 1

async def main():
    async with AsyncSessionLocal() as db:
        logger.info("Wiping existing agents for a clean slate of 50 agents...")
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
                max_steps=item["max_steps"],
                timeout_seconds=item["timeout_seconds"],
                status="active",
                allow_uploads=True,
                how_to_use=item["how_to_use"],
                order_index=item["order_index"]
            )
            db.add(agent)
            await db.commit()
            
        logger.info(f"Successfully seeded {len(AGENTS_DATA)} valid agents!")

if __name__ == "__main__":
    asyncio.run(main())
