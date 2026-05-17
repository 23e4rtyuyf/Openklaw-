from app.ai.client import complete


async def ai_extract(text: str, instruction: str) -> str:
    messages = [
        {"role": "system", "content": "You extract structured data from text. Return only the extracted data, no extra commentary."},
        {"role": "user", "content": f"Text:\n{text[:6000]}\n\nInstruction: {instruction}"},
    ]
    result = await complete(messages)
    return result["content"]


async def ai_analyze(text: str, question: str) -> str:
    messages = [
        {"role": "system", "content": "You analyze text and answer questions about it concisely."},
        {"role": "user", "content": f"Text:\n{text[:6000]}\n\nQuestion: {question}"},
    ]
    result = await complete(messages)
    return result["content"]
