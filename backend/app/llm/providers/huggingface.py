import httpx
from app.llm.providers.base import BaseLLMProvider
from app.logging.logger import get_logger

logger = get_logger(__name__)

class HuggingFaceProvider(BaseLLMProvider):
    """Hugging Face Inference API adapter."""
    fallback_models = [
        "meta-llama/Llama-3.3-70B-Instruct",
        "meta-llama/Llama-3.1-8B-Instruct",
        "Qwen/Qwen2.5-72B-Instruct",
        "Qwen/Qwen2.5-7B-Instruct",
        "deepseek-ai/DeepSeek-V3",
        "deepseek-ai/DeepSeek-R1",
        "google/gemma-4-31B-it",
        "google/gemma-3-27b-it",
        "microsoft/phi-4",
        "CohereLabs/c4ai-command-r-08-2024",
        "moonshotai/Kimi-K3",
        "zai-org/GLM-5.2"
    ]

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
        # Sequencing massive models if no specific model is requested
        models_to_try = [model_name] if model_name else [
            "meta-llama/Llama-3.3-70B-Instruct",
            "meta-llama/Llama-3.1-8B-Instruct",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "Qwen/Qwen2.5-72B-Instruct",
            "microsoft/Phi-3.5-mini-instruct",
            "meta-llama/Llama-3.2-1B-Instruct"
        ]

        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        last_error = None
        for model in models_to_try:
            url = "https://router.huggingface.co/v1/chat/completions"
            
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.2
            }
            
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    logger.info("Calling Hugging Face Inference API", model=model, url=url)
                    response = await client.post(url, json=payload, headers=headers)
                    
                    if response.status_code != 200:
                        error_msg = f"Hugging Face returned status {response.status_code}: {response.text}"
                        logger.warning("Hugging Face API error for model", model=model, status_code=response.status_code)
                        last_error = Exception(error_msg)
                        continue

                    resp_data = response.json()
                    # Text generation API returns a list of objects like [{"generated_text": "..."}]
                    if isinstance(resp_data, list) and len(resp_data) > 0:
                        return resp_data[0].get("generated_text", "")
                    elif isinstance(resp_data, dict):
                        # In case of chat payload structure
                        choices = resp_data.get("choices", [])
                        if choices:
                            return choices[0].get("message", {}).get("content", "")
                            
                    last_error = Exception("Unknown Hugging Face response format.")
                    
            except Exception as e:
                logger.warning("Failed to call HuggingFace model", model=model, error=str(e))
                last_error = e

        raise last_error or Exception("All Hugging Face fallback models failed.")
