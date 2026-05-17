import httpx


async def tavily_search(query: str, api_key: str, max_results: int = 5) -> list:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post("https://api.tavily.com/search",
                         json={"api_key": api_key, "query": query, "max_results": max_results,
                               "search_depth": "basic"})
        if r.status_code != 200:
            return [{"error": r.text}]
        results = r.json().get("results", [])
        return [{"title": res.get("title"), "url": res.get("url"),
                 "snippet": res.get("content", "")[:500]} for res in results]


async def perplexity_ask(question: str, api_key: str) -> str:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post("https://api.perplexity.ai/chat/completions",
                         headers={"Authorization": f"Bearer {api_key}",
                                   "Content-Type": "application/json"},
                         json={"model": "sonar", "messages": [{"role": "user", "content": question}]})
        if r.status_code != 200:
            return f"Perplexity error: {r.text}"
        return r.json().get("choices", [{}])[0].get("message", {}).get("content", "")


async def web_search(query: str, api_key: str, provider: str = "tavily") -> list:
    if provider == "perplexity":
        answer = await perplexity_ask(query, api_key)
        return [{"title": "Perplexity answer", "snippet": answer}]
    return await tavily_search(query, api_key)
