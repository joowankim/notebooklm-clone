"""RAG agent prompts."""

SYSTEM_PROMPT = """You are a helpful research assistant that answers questions based ONLY on the provided source materials.

CRITICAL RULES:
1. Answer ONLY using information from the provided sources
2. EVERY factual claim MUST have a citation in the format [1], [2], etc.
3. If the answer is not in the sources, say "I cannot find this information in the provided sources."
4. Do NOT make up information or use your training knowledge
5. Be concise and direct in your answers
6. Use multiple citations if a statement draws from multiple sources

Citation format:
- Use [1], [2], etc. inline with the text
- Each number corresponds to a source provided to you
- A single sentence may have multiple citations if it synthesizes multiple sources

Example:
"The project was started in 2020 [1] and has grown to over 1000 contributors [2]."
"""


def format_sources(sources: list[dict]) -> str:
    """Format sources for the prompt.

    Args:
        sources: List of dicts with 'index', 'title', 'url', 'content' keys.

    Returns:
        Formatted string with numbered sources.
    """
    formatted_parts = []
    for source in sources:
        idx = source["index"]
        title = source.get("title") or "Untitled"
        url = source["url"]
        content = source["content"]

        formatted_parts.append(
            f"[{idx}] {title}\nURL: {url}\n\n{content}\n"
        )

    return "\n---\n".join(formatted_parts)


def format_user_prompt(question: str, sources_text: str) -> str:
    """Format the user prompt with question and sources."""
    return f"""Based on the following sources, answer this question: {question}

SOURCES:
{sources_text}

Remember: Use citations [1], [2], etc. for every factual claim. If the information is not in the sources, say so."""


def format_conversation_context(conversation_history: list[dict]) -> str:
    """Format conversation history for context.

    Args:
        conversation_history: List of dicts with 'role' and 'content' keys.

    Returns:
        Formatted conversation history string.
    """
    if not conversation_history:
        return ""

    parts = ["PREVIOUS CONVERSATION:"]
    for msg in conversation_history:
        role = msg["role"].upper()
        content = msg["content"]
        # Truncate long messages for context
        if len(content) > 500:
            content = content[:500] + "..."
        parts.append(f"{role}: {content}")

    parts.append("\nNow answer the current question:\n")
    return "\n".join(parts)


def format_user_prompt_with_history(
    question: str, sources_text: str, conversation_history: list[dict]
) -> str:
    """Format the user prompt with conversation history and sources."""
    history_context = format_conversation_context(conversation_history)

    return f"""{history_context}Based on the following sources, answer this question: {question}

SOURCES:
{sources_text}

Remember: Use citations [1], [2], etc. for every factual claim. If the information is not in the sources, say so."""
