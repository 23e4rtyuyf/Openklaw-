import json
import asyncio
from datetime import datetime
from typing import Any

from app.ai.client import complete
from app.engine.tools.http_tool import fetch_url, http_post
from app.engine.tools.extract_tool import ai_extract, ai_analyze
from app.engine.tools.memory_tool import store, retrieve, compare_with_last
from app.engine.tools.notify_tool import send_notification

MAX_ITERATIONS = 15

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "fetch_url",
            "description": "HTTP GET a URL and return the page text (max 8000 chars)",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to fetch"},
                    "headers": {"type": "object", "description": "Optional HTTP headers"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "http_post",
            "description": "HTTP POST to a URL with a JSON body",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "body": {"type": "object"},
                    "headers": {"type": "object"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ai_extract",
            "description": "Extract structured data from text using AI",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The text to extract from"},
                    "instruction": {"type": "string", "description": "What to extract"},
                },
                "required": ["text", "instruction"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ai_analyze",
            "description": "Answer a question about a piece of text using AI",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "question": {"type": "string"},
                },
                "required": ["text", "question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "store",
            "description": "Save a value to the agent's persistent memory",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {},
                },
                "required": ["key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve",
            "description": "Read a value from the agent's persistent memory",
            "parameters": {
                "type": "object",
                "properties": {"key": {"type": "string"}},
                "required": ["key"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_with_last",
            "description": "Compare a value to the last stored value under a key, detect changes",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {},
                },
                "required": ["key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_notification",
            "description": "Send a message to the user via Telegram",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "The message text (supports Markdown)"},
                },
                "required": ["message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": "Complete the task and return the final result",
            "parameters": {
                "type": "object",
                "properties": {
                    "result": {"type": "string", "description": "Human-readable summary of what was accomplished"},
                },
                "required": ["result"],
            },
        },
    },
]


async def run_agent(agent_data: dict, input_data: dict = None) -> dict:
    """
    Execute an agent using the ReAct loop.
    Returns: {steps, result, status}
    """
    goal = agent_data.get("goal") or agent_data.get("description", "Complete the task")
    initial_prompt = agent_data.get("initial_prompt", "")
    memory = agent_data.get("memory", {}).copy()
    telegram_chat_id = agent_data.get("telegram_chat_id", "")

    system_msg = f"""You are an autonomous AI agent with a clear goal.

Goal: {goal}

{f'Instructions: {initial_prompt}' if initial_prompt else ''}

{f'Input data: {json.dumps(input_data)}' if input_data else ''}

Use the available tools to accomplish your goal. When done, call finish() with a summary of what you accomplished.
Be concise and efficient. Do not repeat tool calls unnecessarily."""

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": "Please complete your goal now."},
    ]

    steps = []
    result = None
    status = "success"

    for _ in range(MAX_ITERATIONS):
        response = await complete(messages, tools=TOOL_SCHEMAS)

        if response["content"]:
            messages.append({"role": "assistant", "content": response["content"]})

        tool_calls = response.get("tool_calls", [])
        if not tool_calls:
            result = response["content"] or "Task completed."
            break

        for tc in tool_calls:
            tool_name = tc["name"]
            args = tc["arguments"]
            step = {"tool": tool_name, "input": args, "output": None, "ok": True}

            try:
                output = await _dispatch_tool(tool_name, args, memory, telegram_chat_id)
                step["output"] = output

                if tool_name == "finish":
                    result = args.get("result", "Done")
                    steps.append(step)
                    return {"steps": steps, "result": result, "status": "success", "memory": memory}

            except Exception as e:
                step["output"] = f"Error: {e}"
                step["ok"] = False
                status = "failed"

            steps.append(step)

            tool_result_content = json.dumps(step["output"]) if not isinstance(step["output"], str) else step["output"]
            messages.append({
                "role": "user",
                "content": f"Tool '{tool_name}' result: {tool_result_content}",
            })

    if result is None:
        result = "Max iterations reached."
        status = "failed"

    return {"steps": steps, "result": result, "status": status, "memory": memory}


async def _dispatch_tool(name: str, args: dict, memory: dict, telegram_chat_id: str) -> Any:
    if name == "fetch_url":
        return await fetch_url(args["url"], args.get("headers"))
    elif name == "http_post":
        return await http_post(args["url"], args.get("body"), args.get("headers"))
    elif name == "ai_extract":
        return await ai_extract(args["text"], args["instruction"])
    elif name == "ai_analyze":
        return await ai_analyze(args["text"], args["question"])
    elif name == "store":
        return store(memory, args["key"], args["value"])
    elif name == "retrieve":
        return retrieve(memory, args["key"])
    elif name == "compare_with_last":
        return compare_with_last(memory, args["key"], args["value"])
    elif name == "send_notification":
        return await send_notification(args["message"], telegram_chat_id)
    elif name == "finish":
        return args.get("result", "Done")
    else:
        raise ValueError(f"Unknown tool: {name}")
