from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.core.database import Base

class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    owner_type = Column(String(50), nullable=False)  # agent, user
    owner_id = Column(Integer, nullable=False)
    content_summary = Column(Text, nullable=False)
    content_hash = Column(String(64), unique=True, index=True, nullable=False)
    embedding = Column(Vector(768), nullable=True)  # pgvector embedding vector (768 dimensions)
    metadata_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
