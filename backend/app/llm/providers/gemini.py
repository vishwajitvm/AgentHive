import httpx
from app.llm.providers.base import BaseLLMProvider
from app.logging.logger import get_logger

logger = get_logger(__name__)

class GeminiProvider(BaseLLMProvider):
    """Google Gemini model provider adapter utilizing direct REST endpoints."""

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
        model = model_name or "gemini-1.5-flash"
        if not api_key:
            raise ValueError("Gemini API key is required but missing.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
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
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info("Calling Gemini API", model=model, url=url.split("?")[0])
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                error_msg = f"Gemini API returned status {response.status_code}: {response.text}"
                logger.error("Gemini API error", status_code=response.status_code, error=response.text)
                raise Exception(error_msg)
                
            resp_data = response.json()
            try:
                candidates = resp_data.get("candidates", [])
                if not candidates:
                    raise Exception("No response candidates returned by Gemini.")
                
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    raise Exception("Empty response part list from Gemini candidates.")
                    
                text_out = parts[0].get("text", "")
                return text_out
            except (KeyError, IndexError) as e:
                logger.exception("Failed to parse Gemini response payload", error=str(e), payload=resp_data)
                raise Exception("Failed to parse Gemini response payload") from e
