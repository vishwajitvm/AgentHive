import httpx
from app.llm.providers.base import BaseLLMProvider
from app.logging.logger import get_logger

logger = get_logger(__name__)

class OpenAIProvider(BaseLLMProvider):
    """OpenAI and custom OpenAI-compatible provider adapter."""

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
        model = model_name or "gpt-4o-mini"
        host = base_url or "https://api.openai.com"
        url = f"{host.rstrip('/')}/v1/chat/completions"

        if not api_key and "api.openai.com" in url:
            raise ValueError("OpenAI API Key is required but missing.")

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
            "Content-Type": "application/json"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info("Calling OpenAI-compatible API", model=model, url=url)
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                error_msg = f"OpenAI API returned status {response.status_code}: {response.text}"
                logger.error("OpenAI-compatible error", status_code=response.status_code)
                raise Exception(error_msg)

            resp_data = response.json()
            try:
                choices = resp_data.get("choices", [])
                if not choices:
                    raise Exception("No choices returned by OpenAI API.")
                content = choices[0].get("message", {}).get("content", "")
                return content
            except (KeyError, IndexError, TypeError) as e:
                logger.exception("Failed to parse OpenAI response", error=str(e), payload=resp_data)
                raise Exception("Failed to parse OpenAI response") from e
