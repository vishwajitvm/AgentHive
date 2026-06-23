from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    project_name: str = "AgentHive"
    app_env: str = "development"
    app_debug: bool = True
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Database
    database_url: str = "postgresql+psycopg://agenthive:agenthive@postgres:5432/agenthive"
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    
    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "agenthive"
    minio_secret_key: str = "agenthive123"
    minio_bucket: str = "agenthive-files"
    minio_secure: bool = False
    
    # Ollama
    ollama_base_url: str = "http://ollama:11434"
    ollama_default_model: str = "llama3"
    
    # Default Model Policy
    default_primary_provider: str = "gemini"
    default_secondary_provider: str = "ollama"
    default_fallback_order: str = "gemini,ollama,huggingface,groq,openai"
    default_max_input_tokens: int = 12000
    default_max_output_tokens: int = 2048
    default_llm_timeout_seconds: int = 60
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    enable_otel: bool = True
    otel_service_name: str = "agenthive-backend"
    loki_url: str = "http://loki:3100"
    
    # Security
    secret_key: str = "local-dev-secret-key-1234567890"
    encryption_key: str = "dGhpc2lzYTMyYnl0ZWJhc2U2NGtleWZvcmxvY2FsMTI="
    access_token_expire_minutes: int = 1440

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
