from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class ModelProvider(Base):
    __tablename__ = "model_providers"

    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String(100), unique=True, index=True, nullable=False)
    provider_type = Column(String(50), nullable=False)  # gemini, ollama, openai, huggingface, groq
    base_url = Column(String(255), nullable=True)
    api_key_secret_id = Column(Integer, ForeignKey("secrets.id", ondelete="SET NULL"), nullable=True)
    default_model = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    health_status = Column(String(50), default="unknown", nullable=False)  # healthy, unhealthy, unknown
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ModelPolicy(Base):
    __tablename__ = "model_policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    primary_provider = Column(String(50), default="gemini", nullable=False)
    secondary_provider = Column(String(50), default="ollama", nullable=False)
    fallback_order = Column(String(255), default="gemini,ollama,huggingface,groq,openai", nullable=False)  # comma separated list
    max_input_tokens = Column(Integer, default=12000, nullable=False)
    max_output_tokens = Column(Integer, default=2048, nullable=False)
    timeout_seconds = Column(Integer, default=60, nullable=False)
    retry_count = Column(Integer, default=2, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
