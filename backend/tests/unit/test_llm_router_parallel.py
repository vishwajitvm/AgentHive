import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.llm.router import LLMRouter
from app.core.exceptions import LLMRouteError

@pytest.mark.asyncio
async def test_generate_parallel_fastest_wins():
    """Test speculative parallel racing: fastest successful provider wins and slower tasks are cancelled."""
    router = LLMRouter()

    cancelled_providers = []

    async def slow_provider(*args, **kwargs):
        try:
            await asyncio.sleep(0.5)
            return "Slow Gemini Response"
        except asyncio.CancelledError:
            cancelled_providers.append("gemini")
            raise

    async def fast_provider(*args, **kwargs):
        await asyncio.sleep(0.05)
        return "Fast Groq Response"

    router.providers["gemini"].generate = AsyncMock(side_effect=slow_provider)
    router.providers["groq"].generate = AsyncMock(side_effect=fast_provider)

    result = await router.generate_parallel(
        prompt="Test speculative prompt",
        providers=["gemini", "groq"],
        timeout=5.0
    )

    assert result == "Fast Groq Response"
    # Allow small event loop turn to confirm task cancellation cleanup
    await asyncio.sleep(0.05)
    assert "gemini" in cancelled_providers

@pytest.mark.asyncio
async def test_generate_parallel_error_resilience():
    """Test that generate_parallel skips failing providers and returns output from healthy provider."""
    router = LLMRouter()

    async def failing_provider(*args, **kwargs):
        raise RuntimeError("Provider connection reset")

    async def working_provider(*args, **kwargs):
        await asyncio.sleep(0.05)
        return "Healthy OpenAI Response"

    router.providers["openai"].generate = AsyncMock(side_effect=failing_provider)
    router.providers["groq"].generate = AsyncMock(side_effect=working_provider)

    result = await router.generate_parallel(
        prompt="Test error resilience",
        providers=["openai", "groq"],
        timeout=5.0
    )

    assert result == "Healthy OpenAI Response"

@pytest.mark.asyncio
async def test_generate_parallel_all_providers_fail_raises_error():
    """Test that LLMRouteError is raised when all parallel providers fail and no DB session is supplied."""
    router = LLMRouter()

    async def failing_provider(*args, **kwargs):
        raise RuntimeError("Provider service unavailable")

    router.providers["gemini"].generate = AsyncMock(side_effect=failing_provider)
    router.providers["groq"].generate = AsyncMock(side_effect=failing_provider)

    with pytest.raises(LLMRouteError):
        await router.generate_parallel(
            prompt="All fail test",
            providers=["gemini", "groq"],
            timeout=1.0
        )

@pytest.mark.asyncio
async def test_generate_parallel_timeout_handling():
    """Test that providers timing out triggers error fallback."""
    router = LLMRouter()

    async def timeout_provider(*args, **kwargs):
        await asyncio.sleep(2.0)
        return "Late response"

    router.providers["gemini"].generate = AsyncMock(side_effect=timeout_provider)
    router.providers["groq"].generate = AsyncMock(side_effect=timeout_provider)

    with pytest.raises(LLMRouteError):
        await router.generate_parallel(
            prompt="Timeout prompt",
            providers=["gemini", "groq"],
            timeout=0.1
        )

@pytest.mark.asyncio
async def test_generate_sequential_fallback(mock_db_session):
    """Test standard sequential fallback order execution in LLMRouter.generate()."""
    router = LLMRouter()

    mock_policy = MagicMock()
    mock_policy.fallback_order = "gemini, groq"
    mock_policy.primary_provider = "gemini"
    mock_policy.retry_count = 0
    mock_policy.max_output_tokens = 500
    mock_policy.timeout_seconds = 10

    with patch("app.llm.router.get_active_policy", new_callable=AsyncMock) as mock_get_pol:
        mock_get_pol.return_value = mock_policy
        
        # Gemini fails, Groq succeeds
        router.providers["gemini"].generate = AsyncMock(side_effect=Exception("Gemini Outage"))
        router.providers["groq"].generate = AsyncMock(return_value="Groq Fallback Output")

        result = await router.generate(prompt="Fallback test", db=mock_db_session)
        assert result == "Groq Fallback Output"
