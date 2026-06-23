import httpx
from typing import List
from app.core.config import settings
from app.logging.logger import get_logger

logger = get_logger(__name__)

async def get_embedding(
    text: str,
    provider: str = None,
    api_key: str = None,
    model_name: str = None
) -> List[float]:
    """Generates a 768-dimensional text embedding vector using Gemini or Ollama."""
    prov = (provider or settings.default_primary_provider or "gemini").lower()
    model = model_name or ("text-embedding-004" if prov == "gemini" else "nomic-embed-text")
    
    if not text:
        return [0.0] * 768

    try:
        if prov == "gemini":
            key = api_key or settings.gemini_api_key
            if not key:
                raise ValueError("Gemini API Key is required for embeddings.")
                
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={key}"
            payload = {
                "model": f"models/{model}",
                "content": {
                    "parts": [{"text": text}]
                }
            }
            
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    embedding_vector = data.get("embedding", {}).get("values", [])
                    # Verify length or pad/truncate to 768
                    if len(embedding_vector) == 768:
                        return embedding_vector
                    elif len(embedding_vector) > 0:
                        logger.warn("Gemini embedding returned unexpected dimension size", dim=len(embedding_vector))
                        return (embedding_vector[:768] + [0.0]*768)[:768]
                else:
                    logger.error("Gemini embedding API error", status_code=resp.status_code, error=resp.text)
                    
        # Ollama local embeddings fallback
        host = settings.ollama_base_url
        url = f"{host.rstrip('/')}/api/embeddings"
        payload = {
            "model": model,
            "prompt": text
        }
        
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                embedding_vector = data.get("embedding", [])
                return (embedding_vector[:768] + [0.0]*768)[:768]
            else:
                logger.error("Ollama embedding API error", status_code=resp.status_code, error=resp.text)
                
    except Exception as e:
        logger.exception("Failed to generate embedding, falling back to mock zero-vector", error=str(e))

    # Fallback to zero vector to prevent agent crashes
    return [0.0] * 768
