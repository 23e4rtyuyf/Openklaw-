import os
from typing import Optional

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
AI_BASE_URL = os.getenv("AI_BASE_URL", "") or None

# Auto-detect provider: prefer Anthropic when its key is present (Replit sets this automatically)
_default_provider = "anthropic" if ANTHROPIC_API_KEY else "openai"
_default_model = "claude-3-5-haiku-20241022" if _default_provider == "anthropic" else "gpt-4o-mini"

AI_PROVIDER = os.getenv("AI_PROVIDER", _default_provider)
AI_MODEL = os.getenv("AI_MODEL", _default_model)


async def complete(
    messages: list[dict],
    tools: Optional[list[dict]] = None,
    model: Optional[str] = None,
) -> dict:
    """Unified async LLM call. Returns {'content': str, 'tool_calls': list}."""
    m = model or AI_MODEL

    if AI_PROVIDER == "anthropic":
        return await _anthropic_complete(messages, tools, m)
    else:
        return await _openai_complete(messages, tools, m)


async def _openai_complete(messages, tools, model):
    from openai import AsyncOpenAI

    kwargs = {"api_key": OPENAI_API_KEY}
    if AI_BASE_URL:
        kwargs["base_url"] = AI_BASE_URL

    client = AsyncOpenAI(**kwargs)
    params = {"model": model, "messages": messages}
    if tools:
        params["tools"] = tools
        params["tool_choice"] = "auto"

    resp = await client.chat.completions.create(**params)
    msg = resp.choices[0].message
    tool_calls = []
    if msg.tool_calls:
        for tc in msg.tool_calls:
            import json
            tool_calls.append({
                "id": tc.id,
                "name": tc.function.name,
                "arguments": json.loads(tc.function.arguments),
            })
    return {"content": msg.content or "", "tool_calls": tool_calls}


async def _anthropic_complete(messages, tools, model):
    import anthropic
    import json

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    system = None
    filtered = []
    for m in messages:
        if m["role"] == "system":
            system = m["content"]
        else:
            filtered.append(m)

    params = {"model": model, "max_tokens": 4096, "messages": filtered}
    if system:
        params["system"] = system
    if tools:
        anthropic_tools = [
            {
                "name": t["function"]["name"],
                "description": t["function"].get("description", ""),
                "input_schema": t["function"].get("parameters", {"type": "object", "properties": {}}),
            }
            for t in tools
        ]
        params["tools"] = anthropic_tools

    resp = await client.messages.create(**params)
    content = ""
    tool_calls = []
    for block in resp.content:
        if block.type == "text":
            content = block.text
        elif block.type == "tool_use":
            tool_calls.append({"id": block.id, "name": block.name, "arguments": block.input})
    return {"content": content, "tool_calls": tool_calls}
