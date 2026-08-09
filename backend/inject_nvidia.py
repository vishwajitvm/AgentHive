import asyncio
from app.core.database import AsyncSessionLocal
from app.core.models import Secret
from app.llm.models import ModelProvider, ModelPolicy
from app.core.security import encrypt_secret
from sqlalchemy import select, text

async def inject_nvidia():
    async with AsyncSessionLocal() as db:
        api_key = "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"
        
        # 1. Encrypt and store API key
        enc_key = encrypt_secret(api_key)
        secret = Secret(
            name="nvidia_api_key",
            encrypted_value=enc_key
        )
        db.add(secret)
        await db.commit()
        await db.refresh(secret)
        
        # 2. Add NVIDIA ModelProvider
        res = await db.execute(select(ModelProvider).where(ModelProvider.provider_type == "nvidia"))
        provider = res.scalar_one_or_none()
        
        if not provider:
            provider = ModelProvider(
                provider_name="NVIDIA NIM",
                provider_type="nvidia",
                default_model="meta/llama-3.1-405b-instruct",
                enabled=True,
                api_key_secret_id=secret.id
            )
            db.add(provider)
        else:
            provider.api_key_secret_id = secret.id
            provider.enabled = True
        
        await db.commit()
        
        # 3. Update Model Policy
        await db.execute(text("UPDATE model_policies SET primary_provider = 'nvidia', fallback_order = 'nvidia,gemini,huggingface,groq,openai,ollama' WHERE is_active = true;"))
        await db.commit()
        
        print("NVIDIA Provider successfully injected into database.")

if __name__ == "__main__":
    asyncio.run(inject_nvidia())
