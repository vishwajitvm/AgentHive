class LLMRouter:
    """Provider-agnostic LLM router placeholder.

    Final implementation should:
    - read model policy from database
    - try primary provider first
    - apply fallback chain
    - log token usage and fallback reason
    - normalize response
    """

    async def generate(self, request):
        raise NotImplementedError("LLMRouter.generate is planned for Phase 4")
