from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    project_name: str = "AgentHive"
    app_env: str = "development"
    app_debug: bool = True
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_cors_origins: str = "http://localhost:3000"
    database_url: str = "postgresql+psycopg://agenthive:agenthive@postgres:5432/agenthive"
    redis_url: str = "redis://redis:6379/0"
    ollama_base_url: str = "http://ollama:11434"
    default_primary_provider: str = "gemini"
    default_secondary_provider: str = "ollama"
    default_fallback_order: str = "gemini,ollama,huggingface,groq,openai"
    log_level: str = "INFO"
    log_format: str = "json"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
