import httpx
from app.llm.providers.base import BaseLLMProvider
from app.logging.logger import get_logger

logger = get_logger(__name__)

class HuggingFaceProvider(BaseLLMProvider):
    """Hugging Face Inference API adapter."""

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
        # Default to a lightweight conversational model
        model = model_name or "meta-llama/Llama-3.2-1B-Instruct"
        url = f"https://api-inference.huggingface.co/models/{model}"

        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        # Combine prompts for standard text-generation task
        full_input = ""
        if system_prompt:
            full_input += f"System: {system_prompt}\n"
        full_input += f"User: {prompt}\nAssistant:"

        payload = {
            "inputs": full_input,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.2,
                "return_full_text": False
            },
            "options": {
                "wait_for_model": True
            }
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info("Calling Hugging Face Inference API", model=model, url=url)
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                error_msg = f"Hugging Face returned status {response.status_code}: {response.text}"
                logger.error("Hugging Face API error", status_code=response.status_code)
                raise Exception(error_msg)

            resp_data = response.json()
            try:
                # Text generation API returns a list of objects like [{"generated_text": "..."}]
                if isinstance(resp_data, list) and len(resp_data) > 0:
                    text_out = resp_data[0].get("generated_text", "")
                    return text_out
                elif isinstance(resp_data, dict):
                    # In case of chat payload structure
                    choices = resp_data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
                raise Exception("Unknown Hugging Face response format.")
            except Exception as e:
                logger.exception("Failed to parse Hugging Face response", error=str(e), payload=resp_data)
                raise Exception("Failed to parse Hugging Face response") from e
