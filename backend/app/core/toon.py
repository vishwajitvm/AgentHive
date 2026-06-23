import re
from typing import List, Dict, Any

def compress_prompt(text: str) -> str:
    """Compresses prompt text by removing redundant whitespaces and blank lines."""
    if not text:
        return ""
    # Replace multiple spaces with a single space
    text = re.sub(r' +', ' ', text)
    # Replace multiple newlines with a single newline
    text = re.sub(r'\n+', '\n', text)
    return text.strip()

def summarize_tool_result(result: str, max_chars: int = 1200) -> str:
    """Summarizes tool results to keep prompts token-efficient."""
    if not result:
        return "[Empty result]"
    
    result_str = str(result).strip()
    if len(result_str) <= max_chars:
        return result_str
    
    # Take first and last parts and add warning message
    half_size = (max_chars - 100) // 2
    truncated = (
        result_str[:half_size] +
        f"\n... [TRUNCATED {len(result_str) - max_chars} characters for token optimization. Full log saved in MinIO] ...\n" +
        result_str[-half_size:]
    )
    return truncated

def format_memory_context(memories: List[Dict[str, Any]]) -> str:
    """Formats retrieved vector memories into a compact TOON representation."""
    if not memories:
        return "[No relevant memories found]"
    
    lines = []
    for idx, mem in enumerate(memories):
        summary = mem.get("content_summary", "").strip()
        lines.append(f"~M{idx}: {summary}")
    return "\n".join(lines)

def format_agent_context(system_prompt: str, history: List[Dict[str, str]], query: str = None) -> str:
    """Formats system instructions, chat history, and current task into compact TOON tags."""
    lines = []
    if system_prompt:
        lines.append(f"@sys: {system_prompt.strip()}")
    
    if history:
        lines.append("@hist:")
        for turn in history:
            role = turn.get("role", "user")
            content = turn.get("content", "").strip()
            # Compress turn content
            content_comp = compress_prompt(content)
            prefix = "u" if role == "user" else "a"
            lines.append(f" {prefix}> {content_comp}")
            
    if query:
        lines.append(f"@task: {compress_prompt(query)}")
        
    return "\n".join(lines)
