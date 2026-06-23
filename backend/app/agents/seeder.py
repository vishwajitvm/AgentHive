from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.agents.models import Agent, Prompt, PromptVersion
from app.logging.logger import get_logger

logger = get_logger(__name__)

NEW_AGENTS = [
    {
        "name": "WhatsApp Assistant Agent",
        "slug": "whatsapp_agent",
        "description": "Helps draft, summarize, and automate WhatsApp Business messages.",
        "agent_type": "whatsapp",
        "tools_enabled": ["whatsapp_tool", "summarizer_tool"],
        "prompt": "You are a WhatsApp Assistant. Draft polite replies to customers or summarize conversations.",
        "max_steps": 5, "timeout_seconds": 60
    },
    {
        "name": "Instagram Content Agent",
        "slug": "instagram_agent",
        "description": "Creates captions, post ideas, replies, and content plans.",
        "agent_type": "instagram",
        "tools_enabled": ["instagram_tool", "image_analysis_tool"],
        "prompt": "You are an Instagram Content expert. Create catchy captions and reply to comments.",
        "max_steps": 5, "timeout_seconds": 60
    },
    {
        "name": "Social Media Manager Agent",
        "slug": "social_manager_agent",
        "description": "Coordinates Instagram, WhatsApp, and general social content.",
        "agent_type": "social_manager",
        "tools_enabled": ["whatsapp_tool", "instagram_tool", "md_writer_tool"],
        "prompt": "You are a Social Media Manager. Coordinate content schedules across platforms.",
        "max_steps": 8, "timeout_seconds": 120
    },
    {
        "name": "Email Assistant Agent",
        "slug": "email_assistant",
        "description": "Summarizes emails and drafts replies.",
        "agent_type": "email",
        "tools_enabled": ["gmail_tool", "smtp_tool", "summarizer_tool"],
        "prompt": "You are an Email Assistant. Summarize long emails and draft professional responses.",
        "max_steps": 5, "timeout_seconds": 60
    },
    {
        "name": "Calendar Scheduler Agent",
        "slug": "calendar_scheduler",
        "description": "Schedules meetings and detects conflicts.",
        "agent_type": "calendar",
        "tools_enabled": ["calendar_tool", "gmail_tool"],
        "prompt": "You are a Calendar Scheduler. Read events and avoid booking conflicts.",
        "max_steps": 5, "timeout_seconds": 60
    },
    {
        "name": "Meeting Notes Agent",
        "slug": "meeting_notes_agent",
        "description": "Turns meeting notes/transcripts into summaries and action items.",
        "agent_type": "meeting",
        "tools_enabled": ["summarizer_tool", "md_writer_tool"],
        "prompt": "You are a Meeting Notes Agent. Summarize transcripts into bullet points and action items.",
        "max_steps": 5, "timeout_seconds": 60
    },
    {
        "name": "Invoice Assistant Agent",
        "slug": "invoice_assistant",
        "description": "Reads invoices and extracts key data.",
        "agent_type": "finance",
        "tools_enabled": ["pdf_tool", "ocr_tool", "csv_reader_tool"],
        "prompt": "You are an Invoice Assistant. Extract dates, totals, and vendors from invoices.",
        "max_steps": 5, "timeout_seconds": 60
    },
    {
        "name": "Expense Tracker Agent",
        "slug": "expense_tracker",
        "description": "Categorizes expenses from CSV/manual entries.",
        "agent_type": "finance",
        "tools_enabled": ["csv_reader_tool", "postgres_tool"],
        "prompt": "You are an Expense Tracker. Categorize transactions and output summaries.",
        "max_steps": 5, "timeout_seconds": 60
    },
    {
        "name": "Customer Support Agent",
        "slug": "support_agent",
        "description": "Answers customer questions using uploaded docs.",
        "agent_type": "support",
        "tools_enabled": ["vector_search_tool", "search_tool"],
        "prompt": "You are a Support Agent. Answer politely based strictly on the provided documentation.",
        "max_steps": 6, "timeout_seconds": 90
    },
    {
        "name": "Sales Lead Agent",
        "slug": "sales_lead_agent",
        "description": "Qualifies leads and creates follow-up plans.",
        "agent_type": "sales",
        "tools_enabled": ["scraper_tool", "search_tool"],
        "prompt": "You are a Sales Lead Agent. Qualify leads by analyzing their website and creating follow-up strategies.",
        "max_steps": 6, "timeout_seconds": 90
    },
    {
        "name": "CRM Assistant Agent",
        "slug": "crm_assistant",
        "description": "Tracks customer interactions and next steps.",
        "agent_type": "sales",
        "tools_enabled": ["postgres_tool", "md_writer_tool"],
        "prompt": "You are a CRM Assistant. Log customer interactions and predict the next best action.",
        "max_steps": 6, "timeout_seconds": 90
    },
    {
        "name": "Blog Writer Agent",
        "slug": "blog_writer",
        "description": "Creates SEO-friendly blog drafts.",
        "agent_type": "content",
        "tools_enabled": ["search_tool", "md_writer_tool"],
        "prompt": "You are a Blog Writer. Write engaging, SEO-friendly markdown articles.",
        "max_steps": 8, "timeout_seconds": 120
    },
    {
        "name": "SEO Research Agent",
        "slug": "seo_research",
        "description": "Finds keywords and content gaps.",
        "agent_type": "marketing",
        "tools_enabled": ["search_tool", "scraper_tool"],
        "prompt": "You are an SEO Analyst. Find high-value keywords and suggest content topics.",
        "max_steps": 8, "timeout_seconds": 120
    },
    {
        "name": "Resume Builder Agent",
        "slug": "resume_builder",
        "description": "Creates resumes and cover letters.",
        "agent_type": "hr",
        "tools_enabled": ["docx_writer_tool"],
        "prompt": "You are a Career Coach. Draft professional resumes and cover letters tailored to job descriptions.",
        "max_steps": 5, "timeout_seconds": 60
    },
    {
        "name": "Study Planner Agent",
        "slug": "study_planner",
        "description": "Creates study plans and summaries.",
        "agent_type": "education",
        "tools_enabled": ["pdf_tool", "summarizer_tool"],
        "prompt": "You are a Study Planner. Organize learning material into day-by-day schedules.",
        "max_steps": 5, "timeout_seconds": 60
    },
    {
        "name": "Fitness Planner Agent",
        "slug": "fitness_planner",
        "description": "Creates workout plans.",
        "agent_type": "health",
        "tools_enabled": ["search_tool"],
        "prompt": "You are a Fitness Planner. Create balanced workout schedules based on user goals.",
        "max_steps": 5, "timeout_seconds": 60
    },
    {
        "name": "Diet Planner Agent",
        "slug": "diet_planner",
        "description": "Creates diet suggestions.",
        "agent_type": "health",
        "tools_enabled": ["search_tool"],
        "prompt": "You are a Dietician. Suggest healthy meals matching dietary restrictions.",
        "max_steps": 5, "timeout_seconds": 60
    },
    {
        "name": "Travel Planner Agent",
        "slug": "travel_planner",
        "description": "Creates itineraries and packing lists.",
        "agent_type": "travel",
        "tools_enabled": ["search_tool", "md_writer_tool"],
        "prompt": "You are a Travel Planner. Build daily itineraries and packing lists for trips.",
        "max_steps": 5, "timeout_seconds": 60
    },
    {
        "name": "Shopping Research Agent",
        "slug": "shopping_agent",
        "description": "Compares products and creates buying suggestions.",
        "agent_type": "shopping",
        "tools_enabled": ["search_tool", "scraper_tool"],
        "prompt": "You are a Shopping Assistant. Compare prices, features, and reviews.",
        "max_steps": 6, "timeout_seconds": 90
    },
    {
        "name": "Legal Document Helper Agent",
        "slug": "legal_helper",
        "description": "Summarizes legal-looking documents in simple language. Add disclaimer text in UI.",
        "agent_type": "legal",
        "tools_enabled": ["pdf_tool", "summarizer_tool"],
        "prompt": "You are a Legal Helper. Summarize contracts in plain English. Always include a disclaimer that you are not a lawyer.",
        "max_steps": 6, "timeout_seconds": 90
    },
    {
        "name": "HR Policy Agent",
        "slug": "hr_policy_agent",
        "description": "Answers HR policy questions from uploaded company docs.",
        "agent_type": "hr",
        "tools_enabled": ["vector_search_tool"],
        "prompt": "You are an HR Assistant. Answer questions based purely on company handbooks.",
        "max_steps": 5, "timeout_seconds": 60
    },
    {
        "name": "Data Analyst Agent",
        "slug": "data_analyst",
        "description": "Reads CSV/Excel and creates insights.",
        "agent_type": "data",
        "tools_enabled": ["csv_reader_tool", "code_tool"],
        "prompt": "You are a Data Analyst. Read tabular data and compute descriptive statistics.",
        "max_steps": 8, "timeout_seconds": 120
    },
    {
        "name": "Report Generator Agent",
        "slug": "report_generator",
        "description": "Creates markdown and DOCX reports.",
        "agent_type": "document",
        "tools_enabled": ["md_writer_tool", "docx_writer_tool"],
        "prompt": "You are a Report Generator. Compile information into structured files.",
        "max_steps": 5, "timeout_seconds": 60
    },
    {
        "name": "Bug Triage Agent",
        "slug": "bug_triage",
        "description": "Classifies bugs, severity, and possible root cause.",
        "agent_type": "engineering",
        "tools_enabled": ["github_tool", "search_tool"],
        "prompt": "You are a Bug Triage Engineer. Categorize bug reports and suggest root causes.",
        "max_steps": 6, "timeout_seconds": 90
    },
    {
        "name": "Deployment Helper Agent",
        "slug": "deployment_helper",
        "description": "Explains Docker/deployment issues from logs.",
        "agent_type": "engineering",
        "tools_enabled": ["log_search_tool", "file_tool"],
        "prompt": "You are a DevOps Engineer. Explain deployment errors and suggest fixes for Docker/Cloud issues.",
        "max_steps": 6, "timeout_seconds": 90
    }
]

async def seed_new_agents(db: AsyncSession):
    try:
        for item in NEW_AGENTS:
            res = await db.execute(select(Agent).where(Agent.slug == item["slug"]))
            existing_agent = res.scalar_one_or_none()
            if existing_agent:
                continue
                
            prompt = Prompt(
                name=f"{item['name']} Prompt",
                slug=f"{item['slug']}_prompt",
                description=f"Initial prompt template for {item['name']}"
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
                status="active"
            )
            db.add(agent)
            await db.commit()
        logger.info("Successfully seeded 25 new advanced agents.")
    except Exception as e:
        logger.exception("Failed to seed new agents", error=str(e))
        raise
