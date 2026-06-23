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
        # Default to a fast Llama3 model on Groq
        model = model_name or "llama3-8b-8192"
        host = base_url or "https://api.groq.com/openai"
        url = f"{host.rstrip('/')}/v1/chat/completions"

        if not api_key:
            raise ValueError("Groq API Key is required but missing.")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.2
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info("Calling Groq API", model=model, url=url)
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                error_msg = f"Groq API returned status {response.status_code}: {response.text}"
                logger.error("Groq API error", status_code=response.status_code)
                raise Exception(error_msg)

            resp_data = response.json()
            try:
                choices = resp_data.get("choices", [])
                if not choices:
                    raise Exception("No choices returned by Groq API.")
                content = choices[0].get("message", {}).get("content", "")
                return content
            except (KeyError, IndexError, TypeError) as e:
                logger.exception("Failed to parse Groq response", error=str(e), payload=resp_data)
                raise Exception("Failed to parse Groq response") from e
