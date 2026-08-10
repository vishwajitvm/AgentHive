import httpx
from app.llm.providers.base import BaseLLMProvider
from app.logging.logger import get_logger

logger = get_logger(__name__)

class NvidiaProvider(BaseLLMProvider):
    """NVIDIA NIM OpenAI-compatible provider adapter."""
    fallback_models = [
        "nvidia/nemotron-4-340b-instruct",
        "nvidia/llama-3.1-nemotron-70b-instruct",
        "nvidia/nemotron-mini-4b-instruct",
        "nvidia/nemotron-3-8b-chat-steerlm",
        "nvidia/nemotron-4-mini-hindi-4b-instruct"
    ]

    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 4096,
        timeout: float = 60.0,
        model_name: str = None,
        api_key: str = None,
        base_url: str = None
    ) -> str:
        
        models_to_try = [model_name] if model_name else [
            "nvidia/nemotron-4-340b-instruct",
            "nvidia/llama-3.1-nemotron-70b-instruct",
            "nvidia/nemotron-mini-4b-instruct",
            "nvidia/nemotron-3-8b-chat-steerlm",
            "nvidia/nemotron-4-mini-hindi-4b-instruct"
        ]
        
        host = base_url or "https://integrate.api.nvidia.com"
        url = f"{host.rstrip('/')}/v1/chat/completions"

        if not api_key:
            raise ValueError("NVIDIA API Key is required but missing.")

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
                fast_timeout = min(timeout, 10.0)
                async with httpx.AsyncClient(timeout=fast_timeout) as client:
                    logger.info("Calling NVIDIA NIM API", model=model, url=url)
                    response = await client.post(url, json=payload, headers=headers)
                    
                    if response.status_code != 200:
                        error_msg = f"NVIDIA API returned status {response.status_code}: {response.text}"
                        logger.warning("NVIDIA NIM error", model=model, status_code=response.status_code)
                        last_error = Exception(error_msg)
                        continue

                    resp_data = response.json()
                    choices = resp_data.get("choices", [])
                    if not choices:
                        raise Exception("No choices returned by NVIDIA API.")
                    content = choices[0].get("message", {}).get("content", "")
                    return content
            except Exception as e:
                logger.warning("Failed to call NVIDIA model", model=model, error=str(e))
                last_error = e

        raise last_error or Exception("All NVIDIA fallback models failed.")
