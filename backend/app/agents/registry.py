from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.agents.models import Agent, Prompt, PromptVersion
from app.logging.logger import get_logger

logger = get_logger(__name__)

DEFAULT_AGENTS = [
    {
        "name": "Personal Assistant Agent",
        "slug": "personal_assistant",
        "description": "General assistant for organization, messaging, and daily schedules.",
        "agent_type": "personal_assistant",
        "tools_enabled": ["file_tool", "search_tool"],
        "max_steps": 8,
        "timeout_seconds": 90,
        "prompt": (
            "You are a professional Personal Assistant. Your job is to help the user organize their day, "
            "write short text drafts, search for basic facts, and manage their calendar items via files. "
            "Keep your responses friendly, concise, and professional."
        )
    },
    {
        "name": "Task Checklist Agent",
        "slug": "task_agent",
        "description": "Executes multi-step task list checklists and files status reports.",
        "agent_type": "task_agent",
        "tools_enabled": ["file_tool", "code_tool"],
        "max_steps": 10,
        "timeout_seconds": 120,
        "prompt": (
            "You are a structured Task checklist worker. You break down instructions into discrete milestones, "
            "use code tools to make math calculations, and update status logs in workspace files."
        )
    },
    {
        "name": "PDF/Document Agent",
        "slug": "pdf_agent",
        "description": "Reads uploaded files and PDFs to answer details or summarize text.",
        "agent_type": "pdf_agent",
        "tools_enabled": ["pdf_tool", "file_tool"],
        "max_steps": 6,
        "timeout_seconds": 90,
        "prompt": (
            "You are a PDF/Document Analyst. Use the pdf_tool to read and extract contents from uploaded PDFs, "
            "search the text for answers to user questions, and compile short summaries."
        )
    },
    {
        "name": "Research Analyst Agent",
        "slug": "research_agent",
        "description": "Searches the web, aggregates sources, and writes markdown reports.",
        "agent_type": "research_agent",
        "tools_enabled": ["search_tool", "file_tool", "storage_tool"],
        "max_steps": 12,
        "timeout_seconds": 180,
        "prompt": (
            "You are an expert Research Analyst. Search web contents, write drafts of reports to local files, "
            "and upload final reports to MinIO storage bucket."
        )
    },
    {
        "name": "Developer Agent",
        "slug": "developer_agent",
        "description": "Writes Python code scripts and verifies calculations.",
        "agent_type": "developer_agent",
        "tools_enabled": ["code_tool", "file_tool"],
        "max_steps": 10,
        "timeout_seconds": 120,
        "prompt": (
            "You are a Python Developer agent. Write calculations, execute simple python arithmetic logic "
            "using code tools, write clean Python scripts to local files, and output clear outputs."
        )
    }
]

async def initialize_agents(db: AsyncSession):
    """Pre-populates the database with default agent roles and prompt versions on startup."""
    try:
        for item in DEFAULT_AGENTS:
            # Check if agent already exists
            res = await db.execute(select(Agent).where(Agent.slug == item["slug"]))
            existing_agent = res.scalar_one_or_none()
            
            if existing_agent:
                continue
                
            logger.info("Initializing default agent", slug=item["slug"])
            
            # 1. Create Prompt
            prompt = Prompt(
                name=f"{item['name']} Prompt",
                slug=f"{item['slug']}_prompt",
                description=f"Initial prompt template for {item['name']}"
            )
            db.add(prompt)
            await db.commit()
            await db.refresh(prompt)
            
            # 2. Create Prompt Version
            p_ver = PromptVersion(
                prompt_id=prompt.id,
                content=item["prompt"],
                version=1
            )
            db.add(p_ver)
            await db.commit()
            await db.refresh(p_ver)
            
            # 3. Create Agent config
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
                status="active"
            )
            db.add(agent)
            await db.commit()
            
        logger.info("Default agents initialization completed.")
    except Exception as e:
        logger.exception("Failed to pre-populate default agents", error=str(e))
        raise
