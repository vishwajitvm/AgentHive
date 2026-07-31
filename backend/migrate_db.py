import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings
from app.core.database import Base
from app.core.models import User, UserSession, UserToolCredential

async def main():
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        print("Running table alterations...")
        await conn.execute(text('''
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255), 
            ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN DEFAULT FALSE, 
            ADD COLUMN IF NOT EXISTS two_factor_secret VARCHAR(255), 
            ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN DEFAULT FALSE, 
            ADD COLUMN IF NOT EXISTS google_id VARCHAR(255) UNIQUE;
        '''))
        print("Running create_all for new tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Schema updated!")

if __name__ == "__main__":
    asyncio.run(main())
