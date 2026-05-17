import httpx


async def scrape_url(url: str) -> str:
    try:
        import html2text
        async with httpx.AsyncClient(timeout=30, follow_redirects=True,
                                      headers={"User-Agent": "Mozilla/5.0 (compatible; OpenKlaw/1.0)"}) as c:
            resp = await c.get(url)
            resp.raise_for_status()
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = True
            h.body_width = 0
            return h.handle(resp.text)[:8000]
    except ImportError:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as c:
            resp = await c.get(url)
            return resp.text[:8000]
    except Exception as e:
        return f"Error scraping {url}: {e}"


async def fetch_rss(url: str, limit: int = 10) -> list:
    import xml.etree.ElementTree as ET
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            resp = await c.get(url)
        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = []
        # RSS 2.0
        for item in root.iter("item"):
            entries.append({
                "title": (item.findtext("title") or "").strip(),
                "link": (item.findtext("link") or "").strip(),
                "published": (item.findtext("pubDate") or "").strip(),
                "summary": (item.findtext("description") or "")[:500].strip(),
            })
        # Atom
        if not entries:
            for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
                link_el = entry.find("{http://www.w3.org/2005/Atom}link")
                entries.append({
                    "title": (entry.findtext("{http://www.w3.org/2005/Atom}title") or "").strip(),
                    "link": link_el.get("href", "") if link_el is not None else "",
                    "published": (entry.findtext("{http://www.w3.org/2005/Atom}published") or "").strip(),
                    "summary": (entry.findtext("{http://www.w3.org/2005/Atom}summary") or "")[:500].strip(),
                })
        return entries[:limit]
    except Exception as e:
        return [{"error": str(e)}]
