import httpx
from app.llm.providers.base import BaseLLMProvider
from app.logging.logger import get_logger

logger = get_logger(__name__)

class GroqProvider(BaseLLMProvider):
    """Groq Cloud model provider adapter."""

    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 2048,
        timeout: float = 60.0,
        model_name: str = None,
        api_key: str = None,
        base_url: str = None
    ) -> str:
        models_to_try = [model_name] if model_name else [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "qwen/qwen3.6-27b"
        ]
        
        host = base_url or "https://api.groq.com/openai"
        url = f"{host.rstrip('/')}/v1/chat/completions"

        if not api_key:
            raise ValueError("Groq API Key is required but missing.")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        last_error = None
        for model in models_to_try:
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.2
            }
            
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    logger.info("Calling Groq API", model=model, url=url)
                    response = await client.post(url, json=payload, headers=headers)
                    
                    if response.status_code != 200:
                        error_msg = f"Groq API returned status {response.status_code}: {response.text}"
                        logger.error("Groq API error", status_code=response.status_code, model=model)
                        last_error = Exception(error_msg)
                        continue

                    resp_data = response.json()
                    choices = resp_data.get("choices", [])
                    if not choices:
                        raise Exception("No choices returned by Groq API.")
                    content = choices[0].get("message", {}).get("content", "")
                    return content
            except Exception as e:
                logger.warning("Failed to call Groq model", model=model, error=str(e))
                last_error = e

        raise last_error or Exception("All Groq fallback models failed.")
