import httpx
from app.llm.providers.base import BaseLLMProvider
from app.logging.logger import get_logger

logger = get_logger(__name__)

class GeminiProvider(BaseLLMProvider):
    """Google Gemini model provider adapter utilizing direct REST endpoints."""
    fallback_models = [
        "gemini-2.0-flash",
        "gemini-2.0-pro-exp",
        "gemini-2.0-flash-lite",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b"
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
        models_to_try = [model_name] if model_name else [
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ]
        
        if not api_key:
            raise ValueError("Gemini API key is required but missing.")

        # Build contents payload
        contents = [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.2
            }
        }
        
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [
                    {"text": system_prompt}
                ]
            }

        headers = {"Content-Type": "application/json"}
        
        last_error = None
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    logger.info("Calling Gemini API", model=model, url=url.split("?")[0])
                    response = await client.post(url, json=payload, headers=headers)
                    
                    if response.status_code != 200:
                        error_msg = f"Gemini API returned status {response.status_code}: {response.text}"
                        logger.error("Gemini API error", status_code=response.status_code, error=response.text, model=model)
                        last_error = Exception(error_msg)
                        continue
                        
                    resp_data = response.json()
                    candidates = resp_data.get("candidates", [])
                    if not candidates:
                        raise Exception("No response candidates returned by Gemini.")
                    
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if not parts:
                        raise Exception("Empty response part list from Gemini candidates.")
                        
                    text_out = parts[0].get("text", "")
                    return text_out
            except Exception as e:
                logger.warning("Failed to call Gemini model", model=model, error=str(e))
                last_error = e
                
        raise last_error or Exception("All Gemini fallback models failed.")
