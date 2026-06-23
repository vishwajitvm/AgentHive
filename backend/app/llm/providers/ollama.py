import httpx
from app.llm.providers.base import BaseLLMProvider
from app.logging.logger import get_logger

logger = get_logger(__name__)

class OllamaProvider(BaseLLMProvider):
    """Local Ollama model provider adapter calling Ollama chat endpoints."""

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
        model = model_name or "llama3"
        host = base_url or "http://ollama:11434"
        url = f"{host.rstrip('/')}/api/chat"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.2
            }
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info("Calling Ollama API", model=model, url=url)
            try:
                response = await client.post(url, json=payload)
            except httpx.ConnectError as ce:
                logger.error("Ollama connection failed", error=str(ce))
                raise Exception("Ollama service is offline or unreachable.") from ce

            if response.status_code == 404:
                # Typically signifies model is not downloaded
                error_msg = f"Ollama model '{model}' was not found. Download it first."
                logger.error("Ollama model missing", model=model)
                raise Exception(error_msg)
            elif response.status_code != 200:
                error_msg = f"Ollama returned status {response.status_code}: {response.text}"
                logger.error("Ollama error status", status_code=response.status_code)
                raise Exception(error_msg)

            resp_data = response.json()
            try:
                message = resp_data.get("message", {})
                content = message.get("content", "")
                return content
            except (KeyError, TypeError) as e:
                logger.exception("Failed to parse Ollama response", error=str(e), payload=resp_data)
                raise Exception("Failed to parse Ollama response") from e
