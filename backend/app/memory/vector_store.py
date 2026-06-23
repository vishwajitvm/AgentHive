import hashlib
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.memory.models import Memory
from app.memory.embeddings import get_embedding
from app.logging.logger import get_logger

logger = get_logger(__name__)

class VectorStore:
    """Vector database utility class using pgvector on PostgreSQL."""

    async def add_memory(
        self,
        owner_type: str,
        owner_id: int,
        content: str,
        db: AsyncSession,
        metadata: Dict[str, Any] = None
    ) -> Memory:
        logger.info("Adding semantic memory", owner_type=owner_type, owner_id=owner_id)
        
        # 1. Compute hash to enforce unique content items
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        
        # Check if already exists
        res = await db.execute(select(Memory).where(Memory.content_hash == content_hash))
        existing = res.scalar_one_or_none()
        if existing:
            logger.debug("Memory item with matching hash exists, skipping insert", hash=content_hash)
            return existing

        # 2. Get text embedding
        vector = await get_embedding(content)

        # 3. Create Memory record
        memory = Memory(
            owner_type=owner_type,
            owner_id=owner_id,
            content_summary=content[:500],  # Save snippet
            content_hash=content_hash,
            embedding=vector,
            metadata_json=metadata or {}
        )
        db.add(memory)
        await db.commit()
        await db.refresh(memory)
        return memory

    async def search_memories(
        self,
        owner_type: str,
        owner_id: int,
        query: str,
        db: AsyncSession,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        logger.info("Searching memories", query=query, owner_type=owner_type, owner_id=owner_id)
        
        # 1. Get embedding for the query
        query_vector = await get_embedding(query)

        # 2. Query similarity using pgvector cosine distance operator (<=> or cosine_distance)
        stmt = (
            select(Memory)
            .where(Memory.owner_type == owner_type, Memory.owner_id == owner_id)
            .order_by(Memory.embedding.cosine_distance(query_vector))
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        memories = result.scalars().all()
        
        results = []
        for mem in memories:
            results.append({
                "id": mem.id,
                "content_summary": mem.content_summary,
                "metadata": mem.metadata_json,
                "created_at": mem.created_at.isoformat() if mem.created_at else None
            })
            
        return results

vector_store = VectorStore()
