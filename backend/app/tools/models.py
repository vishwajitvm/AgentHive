from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Tool(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, default="general")
    input_schema = Column(JSON, default=dict, nullable=False)
    output_schema = Column(JSON, default=dict, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    requires_auth = Column(Boolean, default=False, nullable=False)
    required_env_keys = Column(JSON, default=list, nullable=False)
    safe_mock_mode = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
