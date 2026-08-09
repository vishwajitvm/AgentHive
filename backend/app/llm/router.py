import time
import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import LLMRouteError
from app.core.security import decrypt_secret
from app.core.models import Secret
from app.llm.models import ModelProvider, ModelPolicy
from app.llm.policy import get_active_policy
from app.logs.models import LLMCall

# Import adapters
from app.llm.providers.gemini import GeminiProvider
from app.llm.providers.ollama import OllamaProvider
from app.llm.providers.openai import OpenAIProvider
from app.llm.providers.huggingface import HuggingFaceProvider
from app.llm.providers.groq import GroqProvider
from app.llm.providers.nvidia import NvidiaProvider

from app.logging.logger import get_logger

logger = get_logger(__name__)

class LLMRouter:
    """Provider-agnostic LLM router.

    Resolves active model fallback policies, loops through configured providers,
    handles errors and timeouts, logs tokens and latency, and executes fallbacks.
    """

    def __init__(self):
        self.providers = {
            "gemini": GeminiProvider(),
            "ollama": OllamaProvider(),
            "openai": OpenAIProvider(),
            "huggingface": HuggingFaceProvider(),
            "groq": GroqProvider(),
            "nvidia": NvidiaProvider()
        }

    async def _get_api_key(self, db: AsyncSession, provider: ModelProvider) -> Optional[str]:
        """Fetches API key from secrets table or environment fallback."""
        if provider.api_key_secret_id:
            res = await db.execute(select(Secret).where(Secret.id == provider.api_key_secret_id))
            secret = res.scalar_one_or_none()
            if secret and secret.encrypted_value:
                try:
                    return decrypt_secret(secret.encrypted_value)
                except Exception as e:
                    logger.error("Failed to decrypt secret for provider", provider=provider.provider_name, error=str(e))
        
        # Env fallback keys
        from app.core.config import settings
        env_keys = {
            "gemini": getattr(settings, "gemini_api_key", ""),
            "openai": getattr(settings, "openai_api_key", ""),
            "huggingface": getattr(settings, "huggingface_api_key", ""),
            "groq": getattr(settings, "groq_api_key", "")
        }
        logger.info("Env keys dump", gemini_has_key=bool(env_keys.get("gemini")), openai_has_key=bool(env_keys.get("openai")))
        return env_keys.get(provider.provider_type.strip().lower(), "")

    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        agent_run_id: int = None,
        db: AsyncSession = None,
        model_override: str = None,
        provider_override: str = None
    ) -> str:
        if not db:
            raise ValueError("Database session is required for LLMRouter.generate")

        request_id = str(uuid.uuid4())
        policy = await get_active_policy(db)
        
        # Determine providers list to try
        fallback_names = [p.strip().lower() for p in policy.fallback_order.split(",") if p.strip()]
        
        # Reorder if there is a primary/secondary override
        primary = (provider_override or policy.primary_provider).lower()
        if primary in fallback_names:
            fallback_names.remove(primary)
            fallback_names.insert(0, primary)
            
        logger.info("LLM Router starting generation", request_id=request_id, fallback_chain=fallback_names)

        last_error = None
        
        for p_name in fallback_names:
            # Query provider info
            result = await db.execute(
                select(ModelProvider).where(ModelProvider.provider_type == p_name)
            )
            provider = result.scalar_one_or_none()
            
            # If not configured in DB, try to build a default one
            if not provider:
                from app.core.config import settings
                default_models = {
                    "gemini": "gemini-1.5-flash",
                    "ollama": settings.ollama_default_model,
                    "openai": "gpt-4o-mini",
                    "huggingface": "meta-llama/Llama-3.2-1B-Instruct",
                    "groq": "llama-3.3-70b-versatile",
                    "nvidia": "meta/llama-3.3-70b-instruct"
                }
                provider = ModelProvider(
                    provider_name=p_name.capitalize(),
                    provider_type=p_name,
                    default_model=default_models.get(p_name, "unknown"),
                    enabled=True,
                    health_status="unknown"
                )
                db.add(provider)
                await db.commit()
                await db.refresh(provider)

            if not provider.enabled:
                logger.debug("Provider is disabled, skipping in fallback chain", provider=p_name)
                continue

            adapter = self.providers.get(p_name)
            if not adapter:
                logger.warning("No adapter found for provider type, skipping", provider=p_name)
                continue

            api_key = await self._get_api_key(db, provider)
            logger.info("Resolved API Key for provider", provider=p_name, has_key=bool(api_key))
            model = model_override or provider.default_model

            # Try execution with retries
            for attempt in range(policy.retry_count + 1):
                start_time = time.perf_counter()
                try:
                    logger.info("Attempting generation", provider=p_name, model=model, attempt=attempt)
                    response_text = await adapter.generate(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        max_tokens=policy.max_output_tokens,
                        timeout=float(policy.timeout_seconds),
                        model_name=model,
                        api_key=api_key,
                        base_url=provider.base_url
                    )
                    
                    latency_ms = int((time.perf_counter() - start_time) * 1000)
                    
                    # Estimate token usage
                    prompt_tokens = len(prompt) // 4
                    completion_tokens = len(response_text) // 4
                    
                    # Save call record
                    llm_call = LLMCall(
                        agent_run_id=agent_run_id,
                        request_id=request_id,
                        provider=p_name,
                        model=model,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        latency_ms=latency_ms,
                        status="success",
                        response_text=response_text
                    )
                    db.add(llm_call)
                    await db.commit()
                    
                    logger.info("LLM Generation succeeded", provider=p_name, latency_ms=latency_ms)
                    return response_text
                    
                except Exception as exc:
                    latency_ms = int((time.perf_counter() - start_time) * 1000)
                    last_error = exc
                    
                    # Save error call record
                    llm_call = LLMCall(
                        agent_run_id=agent_run_id,
                        request_id=request_id,
                        provider=p_name,
                        model=model,
                        prompt_tokens=len(prompt) // 4,
                        completion_tokens=0,
                        latency_ms=latency_ms,
                        status="error",
                        failure_reason=str(exc),
                        fallback_reason=f"Attempt {attempt} failed. Fallback triggered."
                    )
                    db.add(llm_call)
                    await db.commit()
                    
                    logger.warn("LLM Attempt failed", provider=p_name, error=str(exc), latency_ms=latency_ms)
                    # Pause briefly before retry
                    import asyncio
                    await asyncio.sleep(0.5)
                    
        # All fallbacks failed
        logger.error("All providers in fallback chain failed", errors=str(last_error))
        raise LLMRouteError(f"All LLM providers failed. Last error: {str(last_error)}")

    async def generate_parallel(
        self,
        prompt: str,
        system_prompt: str = None,
        providers: List[str] = None,
        agent_run_id: int = None,
        db: AsyncSession = None,
        model_override: str = None,
        timeout: float = 30.0
    ) -> str:
        """Query multiple configured LLM providers concurrently (speculative racing).

        Uses asyncio.wait(..., return_when=FIRST_COMPLETED) to return the fastest
        non-error response and cancel pending slower calls.
        """
        import asyncio
        from app.core.config import settings

        request_id = str(uuid.uuid4())
        
        # Determine providers list
        if not providers:
            if db:
                try:
                    policy = await get_active_policy(db)
                    providers = [p.strip().lower() for p in policy.fallback_order.split(",") if p.strip()]
                except Exception:
                    providers = [p.strip().lower() for p in settings.parallel_llm_default_providers.split(",") if p.strip()]
            else:
                providers = [p.strip().lower() for p in settings.parallel_llm_default_providers.split(",") if p.strip()]

        # Filter out valid provider adapters
        target_providers = [p for p in providers if p in self.providers]
        if not target_providers:
            target_providers = ["gemini", "groq", "ollama"]

        logger.info("LLM Router starting parallel speculative racing", request_id=request_id, providers=target_providers)

        # Pre-resolve API keys and provider models sequentially (avoids concurrent DB session access)
        provider_configs = []
        default_models = {
            "gemini": "gemini-1.5-flash",
            "ollama": settings.ollama_default_model,
            "openai": "gpt-4o-mini",
            "huggingface": "meta-llama/Llama-3.2-1B-Instruct",
            "groq": "llama-3.3-70b-versatile",
            "nvidia": "meta/llama-3.3-70b-instruct"
        }

        for p_name in target_providers:
            adapter = self.providers.get(p_name)
            if not adapter:
                continue
            
            api_key = ""
            base_url = None
            model = model_override or default_models.get(p_name, "unknown")
            
            if db:
                try:
                    res = await db.execute(select(ModelProvider).where(ModelProvider.provider_type == p_name))
                    provider_db = res.scalar_one_or_none()
                    if provider_db:
                        if not provider_db.enabled:
                            continue
                        api_key = await self._get_api_key(db, provider_db)
                        base_url = provider_db.base_url
                        if not model_override:
                            model = provider_db.default_model
                    else:
                        api_key = getattr(settings, f"{p_name}_api_key", "")
                except Exception as e:
                    logger.warning("Failed to pre-resolve provider from DB in generate_parallel", provider=p_name, error=str(e))
                    api_key = getattr(settings, f"{p_name}_api_key", "")
            else:
                api_key = getattr(settings, f"{p_name}_api_key", "")

            provider_configs.append({
                "p_name": p_name,
                "adapter": adapter,
                "api_key": api_key,
                "base_url": base_url,
                "model": model
            })

        if not provider_configs:
            # Fallback to standard sequential generate if no parallel configs prepared
            if db:
                return await self.generate(prompt=prompt, system_prompt=system_prompt, agent_run_id=agent_run_id, db=db)
            raise LLMRouteError("No valid LLM providers available for parallel racing.")

        async def _call_provider(config: dict) -> dict:
            p_name = config["p_name"]
            adapter = config["adapter"]
            start_time = time.perf_counter()
            try:
                res_text = await adapter.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=settings.default_max_output_tokens,
                    timeout=float(timeout),
                    model_name=config["model"],
                    api_key=config["api_key"],
                    base_url=config["base_url"]
                )
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                return {
                    "status": "success",
                    "provider": p_name,
                    "model": config["model"],
                    "response": res_text,
                    "latency_ms": latency_ms
                }
            except Exception as exc:
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                return {
                    "status": "error",
                    "provider": p_name,
                    "model": config["model"],
                    "error": str(exc),
                    "latency_ms": latency_ms
                }

        # Launch concurrent tasks
        task_map = {
            asyncio.create_task(_call_provider(cfg)): cfg
            for cfg in provider_configs
        }

        pending = set(task_map.keys())
        winner_result = None

        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED, timeout=timeout)
            
            if not done:
                # Timed out waiting for remaining tasks
                break

            for completed_task in done:
                try:
                    res = completed_task.result()
                    if res.get("status") == "success":
                        winner_result = res
                        break
                except Exception as e:
                    logger.warning("Parallel LLM racing task exception", error=str(e))

            if winner_result:
                break

        # Cancel remaining pending tasks
        for p_task in pending:
            p_task.cancel()

        if winner_result:
            logger.info("Parallel LLM race won", provider=winner_result["provider"], latency_ms=winner_result["latency_ms"])
            if db:
                try:
                    llm_call = LLMCall(
                        agent_run_id=agent_run_id,
                        request_id=request_id,
                        provider=winner_result["provider"],
                        model=winner_result["model"],
                        prompt_tokens=len(prompt) // 4,
                        completion_tokens=len(winner_result["response"]) // 4,
                        latency_ms=winner_result["latency_ms"],
                        status="success",
                        response_text=winner_result["response"]
                    )
                    db.add(llm_call)
                    await db.commit()
                except Exception as dbe:
                    logger.warning("Failed to log parallel LLM call to DB", error=str(dbe))

            return winner_result["response"]

        # If all parallel tasks failed or timed out, fallback to standard generate if db available
        logger.warning("All parallel LLM providers failed or timed out. Falling back to sequential generate.")
        if db:
            return await self.generate(prompt=prompt, system_prompt=system_prompt, agent_run_id=agent_run_id, db=db)

        raise LLMRouteError("All parallel LLM provider calls failed or timed out.")

router = LLMRouter()

